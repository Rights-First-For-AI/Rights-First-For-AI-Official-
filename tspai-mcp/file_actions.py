"""Native file operations using the existing authenticated execution journal.

Owner privileges, not a filesystem sandbox. UTF-8 or base64 byte pages.
Replacement preconditions detect stale content but cannot lock other apps.
"""
import base64
import codecs
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import tempfile

VERSION = '0.3.0-pre.4'
MAX_READ_BYTES = 16_000
MAX_WRITE_BYTES = 256_000


class FileActions:
    def __init__(self, executor, workspace):
        self.executor = executor
        self.workspace = Path(workspace).resolve(strict=True)
        if not self.workspace.is_dir():
            raise ValueError('workspace must be an existing directory')

    def _dispatch(self, name, args, request_id, action):
        fingerprint = hashlib.sha256(json.dumps(
            ['tspai-file-v1', name, args], ensure_ascii=False,
            sort_keys=True).encode('utf-8')).hexdigest()
        return self.executor.dispatch(fingerprint, request_id, action)

    def _path(self, value):
        if type(value) is not str or '\x00' in value or not Path(value).is_absolute():
            raise ValueError('path must be absolute and contain no NUL')
        target = Path(value)
        if os.name == 'nt':
            if value.startswith(('\\\\', '//')) or ':' in value[2:]:
                raise PermissionError('network, device and alternate stream paths denied')
            if any(Path(part).is_reserved() for part in target.parts[1:]):
                raise PermissionError('reserved Windows path denied')
        resolved = target.resolve()
        if not resolved.is_relative_to(self.workspace):
            raise PermissionError('path outside approved workspace')
        # Reject existing symlink/reparse components. This is not an OS sandbox
        # and does not prevent concurrent path replacement or hard-link aliases.
        for part in (target, *target.parents):
            try:
                info = part.lstat()
            except FileNotFoundError:
                continue
            if part.is_symlink() or getattr(info, 'st_file_attributes', 0) & 0x400:
                raise PermissionError('link or reparse path denied')
        return target

    @staticmethod
    def _number(value, minimum, maximum):
        if type(value) is not int or not minimum <= value <= maximum:
            raise ValueError('numeric argument outside allowed range')

    def read(self, path, request_id, encoding='utf-8', offset_bytes=0,
             max_bytes=MAX_READ_BYTES):
        target = self._path(path)
        if encoding not in ('utf-8', 'base64'):
            raise ValueError('encoding must be utf-8 or base64')
        self._number(offset_bytes, 0, 2**63 - 1)
        self._number(max_bytes, 4, MAX_READ_BYTES)

        def action():
            if not stat.S_ISREG(target.stat().st_mode):
                raise ValueError('regular file required')
            with target.open('rb') as stream:
                info = os.fstat(stream.fileno())
                stream.seek(offset_bytes)
                data = stream.read(max_bytes)
            if encoding == 'base64':
                content = base64.b64encode(data).decode('ascii')
            else:
                decoder = codecs.getincrementaldecoder('utf-8')('strict')
                content = decoder.decode(data, final=offset_bytes + len(data) >= info.st_size)
                pending = decoder.getstate()[0]
                if pending:
                    data = data[:-len(pending)]
            end = offset_bytes + len(data)
            complete = offset_bytes == 0 and end >= info.st_size
            return dict(ok=True, status='completed', path=path, encoding=encoding,
                        content=content, offset_bytes=offset_bytes, next_offset_bytes=end,
                        bytes_read=len(data), size_bytes=info.st_size,
                        truncated=end < info.st_size,
                        sha256=hashlib.sha256(data).hexdigest() if complete else None,
                        chunk_sha256=hashlib.sha256(data).hexdigest())
        return self._dispatch('read', [path, encoding, offset_bytes, max_bytes], request_id, action)

    def write(self, path, content, request_id, encoding='utf-8', mode='create',
              expected_sha256=None):
        target = self._path(path)
        if type(content) is not str or len(content) > MAX_WRITE_BYTES * 2:
            raise ValueError('content must be a bounded string')
        if encoding == 'utf-8':
            data = content.encode('utf-8')
        elif encoding == 'base64':
            data = base64.b64decode(content, validate=True)
        else:
            raise ValueError('encoding must be utf-8 or base64')
        if len(data) > MAX_WRITE_BYTES:
            raise ValueError('write exceeds 256000 bytes')
        if mode not in ('create', 'replace'):
            raise ValueError('mode must be create or replace')
        if mode == 'replace' and (type(expected_sha256) is not str or
                re.fullmatch('[0-9a-f]{64}', expected_sha256) is None):
            raise ValueError('replace requires the previous lowercase SHA256')
        if mode == 'create' and expected_sha256 is not None:
            raise ValueError('create does not accept expected_sha256')

        def action():
            if mode == 'create':
                try:
                    stream = target.open('xb')
                except FileExistsError:
                    return dict(ok=False, status='conflict', error_type='FileExistsError',
                                effects_rolled_back=False, bytes_written=0)
                with stream:
                    stream.write(data)
                    stream.flush()
                    os.fsync(stream.fileno())
            else:
                if not stat.S_ISREG(target.stat().st_mode) or target.is_symlink():
                    raise ValueError('replace requires a regular, non-symlink file')
                with target.open('rb') as stream:
                    before = hashlib.file_digest(stream, 'sha256').hexdigest()
                if before != expected_sha256:
                    return dict(ok=False, status='conflict', error_type='ContentChanged',
                                effects_rolled_back=False, bytes_written=0)
                temporary = None
                try:
                    with tempfile.NamedTemporaryFile(dir=target.parent, prefix='.tspai-',
                                                     delete=False) as stream:
                        temporary = Path(stream.name)
                        stream.write(data)
                        stream.flush()
                        os.fsync(stream.fileno())
                    os.replace(temporary, target)
                finally:
                    if temporary is not None:
                        temporary.unlink(missing_ok=True)
            return dict(ok=True, status='completed', path=path, encoding=encoding,
                        mode=mode, bytes_written=len(data),
                        sha256=hashlib.sha256(data).hexdigest(), effects_rolled_back=False)
        return self._dispatch('write', [path, content, encoding, mode, expected_sha256],
                              request_id, action)

    def delete(self, path, request_id, expected_sha256=None):
        """Opt-in deletion: one regular file with expected full-file SHA256,
        or an empty directory. No recursion. Uses existing audit/replay gate.
        Not an OS sandbox: optional PowerShell can bypass this interface.
        """
        target = self._path(path)
        if target == self.workspace:
            raise PermissionError('workspace root cannot be deleted')
        if expected_sha256 is not None and (
                type(expected_sha256) is not str or
                re.fullmatch('[0-9a-f]{64}', expected_sha256) is None):
            raise ValueError('expected_sha256 must be lowercase SHA256')
        def action():
            info = target.lstat()
            if stat.S_ISREG(info.st_mode):
                if expected_sha256 is None:
                    raise ValueError('file deletion requires full-file SHA256')
                with target.open('rb') as stream:
                    before = hashlib.file_digest(stream, 'sha256').hexdigest()
                if before != expected_sha256:
                    return dict(ok=False, status='conflict',
                                error_type='ContentChanged', effects_rolled_back=False)
                target.unlink()
                kind = 'file'
            elif stat.S_ISDIR(info.st_mode):
                if expected_sha256 is not None:
                    raise ValueError('directory deletion does not accept SHA256')
                target.rmdir()  # Never recursive: only empty directories.
                kind = 'empty_directory'
            else:
                raise ValueError('deletion requires regular file or empty directory')
            return dict(ok=True, status='completed', path=path, kind=kind,
                        effects_rolled_back=False)
        return self._dispatch('delete', [path, expected_sha256], request_id, action)

    def list(self, path, request_id, offset=0, limit=100):
        target = self._path(path)
        self._number(offset, 0, 1_000_000)
        self._number(limit, 1, 200)

        def action():
            entries = []
            more = False
            with os.scandir(target) as listing:
                for index, entry in enumerate(listing):
                    if index < offset:
                        continue
                    if len(entries) == limit:
                        more = True
                        break
                    entries.append(dict(name=entry.name, is_directory=entry.is_dir(),
                                        is_symlink=entry.is_symlink()))
            return dict(ok=True, status='completed', path=path, entries=entries,
                        next_offset=offset + len(entries), truncated=more,
                        order='filesystem order; concurrent directory changes may affect pages')
        return self._dispatch('list', [path, offset, limit], request_id, action)
