"""PowerShell executor for an owner-authenticated, time-limited MCP process.

Runs with the Windows user's privileges, NOT a sandbox. Never retries effects.
The audit includes output, but not script text; keep the directory private.
"""
import base64
from contextlib import contextmanager
import hashlib
import json
import os
from pathlib import Path
import sqlite3
import subprocess
import tempfile
import threading
import time
import uuid

MAX_OUTPUT = 20_000
MAX_BYTES = 2_000_000


class PowerShellExecutor:
    def __init__(self, directory, shell, *, cwd, session_seconds=3600):
        self.directory = Path(directory).resolve(strict=True)
        self.shell = str(Path(shell).resolve(strict=True))
        self.cwd = str(Path(cwd).resolve(strict=True))
        if type(session_seconds) is not int or not 1 <= session_seconds <= 43200:
            raise ValueError('invalid session duration')
        # Production constructs this only after local Windows Hello succeeds.
        self.deadline = time.monotonic() + session_seconds
        self.session_id = uuid.uuid4().hex
        self.lock = threading.Lock()
        self.db_path = self.directory / 'operations.sqlite3'
        with self.connect() as db:
            db.execute('CREATE TABLE IF NOT EXISTS operations '
                       '(id TEXT PRIMARY KEY, fingerprint TEXT NOT NULL, '
                       'session TEXT NOT NULL, started REAL NOT NULL, result TEXT)')

    @contextmanager
    def connect(self):
        db = sqlite3.connect(self.db_path, timeout=5)
        try:
            db.execute('PRAGMA synchronous=FULL')
            with db:
                yield db
        finally:
            db.close()

    def status(self):
        return {'active': time.monotonic() < self.deadline,
                'session_id': self.session_id,
                'seconds_remaining': max(0, int(self.deadline - time.monotonic()))}

    def execute(self, script, request_id, timeout_seconds=30, working_directory=None):
        if type(script) is not str or not script.strip() or len(script) > 8192:
            raise ValueError('script must contain 1..8192 characters')
        if type(timeout_seconds) is not int or not 1 <= timeout_seconds <= 120:
            raise ValueError('timeout_seconds must be 1..120')
        cwd = self.cwd
        if working_directory is not None:
            if type(working_directory) is not str or not Path(working_directory).is_absolute():
                raise ValueError('working_directory must be absolute')
            cwd = str(Path(working_directory).resolve(strict=True))
            if not Path(cwd).is_dir():
                raise ValueError('working_directory is not a directory')
        fingerprint = hashlib.sha256(json.dumps(
            [script, timeout_seconds, cwd], ensure_ascii=False).encode('utf-8')).hexdigest()
        return self.dispatch(fingerprint, request_id,
                             lambda: self.run_process(script, timeout_seconds, cwd))

    def dispatch(self, fingerprint, request_id, action):
        """Shared session/journal gate. Commit intent before any operation."""
        if type(request_id) is not str or str(uuid.UUID(request_id)) != request_id:
            raise ValueError('request_id must be a canonical UUID')
        with self.lock:
            if time.monotonic() >= self.deadline:
                raise PermissionError('session expired; restart and authenticate locally')
            with self.connect() as db:
                db.execute('BEGIN IMMEDIATE')
                old = db.execute('SELECT fingerprint,result FROM operations WHERE id=?',
                                 (request_id,)).fetchone()
                if old:
                    if old[0] != fingerprint:
                        raise ValueError('request_id already belongs to different arguments')
                    if old[1] is None:
                        return {'ok': False, 'request_id': request_id,
                                'status': 'outcome_unknown', 'replayed': True,
                                'message': 'Prior dispatch may have run. Inspect effects; do not retry.'}
                    result = json.loads(old[1])
                    result['replayed'] = True
                    return result
                # Commit before dispatch. A crash after here always prevents retry.
                db.execute('INSERT INTO operations VALUES (?,?,?,?,NULL)',
                           (request_id, fingerprint, self.session_id, time.time()))
            try:
                result = action()
            except Exception as error:
                # Effects may already exist, including on timeout or transport errors.
                result = {'ok': False, 'status': 'outcome_unknown',
                          'error_type': type(error).__name__}
            result.update(request_id=request_id, replayed=False)
            with self.connect() as db:
                db.execute('UPDATE operations SET result=? WHERE id=?',
                           (json.dumps(result, ensure_ascii=False), request_id))
            return result

    def run_process(self, script, timeout_seconds, cwd):
        if os.name != 'nt':
            raise OSError('Windows PowerShell execution requires Windows')
        # UTF-16LE transports exact script bytes; no cmd.exe or shell interpolation.
        prefix = '[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new($false)\n'
        command = base64.b64encode((prefix + script).encode('utf-16-le')).decode('ascii')
        env = os.environ.copy()
        env.pop('CONTROL_PLANE_API_KEY', None)
        with tempfile.TemporaryDirectory(prefix='ps-', dir=self.directory) as folder:
            out_path, err_path = Path(folder) / 'stdout', Path(folder) / 'stderr'
            with out_path.open('wb') as out, err_path.open('wb') as err:
                process = subprocess.Popen(
                    [self.shell, '-NoLogo', '-NoProfile', '-NonInteractive',
                     '-EncodedCommand', command], cwd=cwd, env=env,
                    stdin=subprocess.DEVNULL, stdout=out, stderr=err, shell=False,
                    creationflags=subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.CREATE_NO_WINDOW)
                end = time.monotonic() + timeout_seconds
                stopped = None
                while process.poll() is None:
                    if time.monotonic() >= end:
                        stopped = 'timeout'
                    if out_path.stat().st_size + err_path.stat().st_size > MAX_BYTES:
                        stopped = 'output_limit'
                    if stopped:
                        # Best-effort tree cleanup; detached descendants may survive.
                        taskkill = Path(os.environ['SystemRoot']) / 'System32/taskkill.exe'
                        try:
                            subprocess.run([str(taskkill), '/PID', str(process.pid), '/T', '/F'],
                                           stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                                           stderr=subprocess.DEVNULL, timeout=5, shell=False)
                        finally:
                            if process.poll() is None:
                                process.kill()
                            process.wait(timeout=5)
                        break
                    time.sleep(0.05)
            def read(path):
                with path.open('rb') as stream:
                    data = stream.read(MAX_OUTPUT * 4 + 1)
                text = data.decode('utf-8', errors='replace')
                return text[:MAX_OUTPUT], path.stat().st_size > len(data) or len(text) > MAX_OUTPUT
            stdout, out_cut = read(out_path)
            stderr, err_cut = read(err_path)
            return {'ok': stopped is None and process.returncode == 0,
                    'status': 'outcome_unknown' if stopped else 'completed',
                    'stop_reason': stopped, 'exit_code': process.returncode,
                    'stdout': stdout, 'stderr': stderr, 'truncated': out_cut or err_cut,
                    'effects_rolled_back': False}

