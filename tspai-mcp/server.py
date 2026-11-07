"""stdio MCP PowerShell extension. Authenticate once on the Windows desktop."""
import argparse
import ctypes
import io
import os
import json
import sqlite3
from contextlib import closing
import time
from pathlib import Path
import sys
import threading
import uuid

import anyio
from anyio.from_thread import start_blocking_portal
from mcp.server.fastmcp import FastMCP
from mcp.server.stdio import stdio_server
sys.path.insert(0, str(Path(__file__).resolve().parent))
from ps_executor import PowerShellExecutor
from file_actions import FileActions, VERSION
from plus1_integration import attach_plus1


def validate_selection(selected):
    """Accept exactly four explicit booleans, without truthy coercion."""
    required = set(PermissionPolicy.NAMES)
    if not isinstance(selected, dict) or set(selected) != required:
        raise ValueError('permission selection must specify exactly four flags')
    if any(type(value) is not bool for value in selected.values()):
        raise ValueError('permission selections must be booleans')
    return {name: selected[name] for name in PermissionPolicy.NAMES}


def startup_permissions(data_dir, requested):
    """First authenticated installation start is read-only, regardless of flags."""
    marker = data_dir / 'first_start_verified'
    if not marker.is_file():
        return {name: False for name in PermissionPolicy.NAMES}, True
    return {name: bool(requested.get(name, False)) for name in PermissionPolicy.NAMES}, False


class PermissionPolicy:
    """Local owner-adjustable permissions; serialize changes with operations."""
    NAMES = ('create', 'edit', 'delete', 'powershell')

    def __init__(self, audit_db=None, **flags):
        self.audit_db = audit_db
        self.lock = threading.RLock()
        self.flags = {name: bool(flags.get(name, False)) for name in self.NAMES}
        if audit_db is not None:
            with closing(sqlite3.connect(audit_db)) as db, db:
                db.execute('CREATE TABLE IF NOT EXISTS permission_changes (id INTEGER PRIMARY KEY, changed_at REAL NOT NULL, old_flags TEXT NOT NULL, new_flags TEXT NOT NULL)')

    def snapshot(self):
        with self.lock:
            return dict(self.flags)

    def authorize(self, name, operation):
        with self.lock:
            if not self.flags[name]:
                raise PermissionError(name + ' disabled by local permissions')
            return operation()

    def update(self, changes):
        with self.lock:
            if set(changes) - set(self.NAMES) or any(type(v) is not bool for v in changes.values()):
                raise ValueError('invalid permission change')
            proposed = dict(self.flags)
            proposed.update(changes)
            if proposed != self.flags and self.audit_db is not None:
                with closing(sqlite3.connect(self.audit_db)) as db, db:
                    db.execute('INSERT INTO permission_changes(changed_at,old_flags,new_flags) VALUES(?,?,?)',
                               (time.time(), json.dumps(self.flags, sort_keys=True),
                                json.dumps(proposed, sort_keys=True)))
            self.flags = proposed
            return dict(self.flags)


class SessionGate:
    """Initialize MCP while the desktop authenticates; deny dispatch until ready."""
    def __init__(self):
        self.executor = None
        self.authentication = 'pending'

    def status(self):
        if self.executor is None:
            return {'active': False, 'authentication': self.authentication,
                    'seconds_remaining': 0}
        return self.executor.status()

    def execute(self, *args, **kwargs):
        executor = self.executor
        if executor is None:
            raise PermissionError('local authentication ' + self.authentication)
        return executor.execute(*args, **kwargs)

    def dispatch(self, *args, **kwargs):
        executor = self.executor
        if executor is None:
            raise PermissionError('local authentication ' + self.authentication)
        return executor.dispatch(*args, **kwargs)


def choose_permissions(first_start, requested, *, language='en'):
    """Local UI, safe default; only available after the first verified startup."""
    if first_start:
        return {name: False for name in PermissionPolicy.NAMES}
    import tkinter as tk
    window = tk.Tk()
    ja = language == 'ja'
    window.title('TSPAI MCP — セッションの権限' if ja else 'TSPAI MCP — Session permissions')
    if ja:
        window.minsize(620, 390)
    else:
        window.geometry('620x390')
    window.attributes('-topmost', True)
    tk.Label(window, text='このセッションで許可する操作を選んでください' if ja else
             'Choose permissions for this MCP session',
             font=('', 14)).pack(pady=15)
    tk.Label(window, text='何も選ばずに進むと読み取り専用で起動します。' if ja else
             'Leave all boxes unchecked to start in read-only mode.',
             wraplength=570).pack(pady=8)
    labels = (
        {'create': 'ファイルを作成', 'edit': 'ファイルを編集・上書き',
         'delete': 'ファイルまたは空フォルダーを削除',
         'powershell': 'Windowsアカウントの権限でPowerShellを実行（ネットワークにもアクセス可能）'}
        if ja else
        {'create': 'Create files', 'edit': 'Edit or overwrite files',
         'delete': 'Delete files or empty folders',
         'powershell': 'PowerShell with your Windows account permissions, including network access'}
    )
    # Never pre-select dangerous permissions, even if command-line flags were supplied.
    choices = {name: tk.BooleanVar(value=False) for name in PermissionPolicy.NAMES}
    for name in PermissionPolicy.NAMES:
        tk.Checkbutton(window, text=labels[name], variable=choices[name],
                       wraplength=545, justify='left').pack(
            anchor='w', padx=35, pady=3)
    answer = [None]
    def finish():
        answer[0] = validate_selection({name: var.get() for name, var in choices.items()})
        window.destroy()
    tk.Button(window, text='選んだ権限で続ける' if ja else 'Continue with selected permissions',
              command=finish).pack(pady=13)
    tk.Button(window, text='起動を取り消す' if ja else 'Cancel startup', command=window.destroy).pack()
    window.mainloop()
    if answer[0] is None:
        raise PermissionError('権限の選択が取り消されました。' if ja else 'local permission selection canceled')
    return answer[0]


def report_active_permissions(policy, session_seconds, stream=None, columns=None, *, language='en'):
    """Fit related startup fields on each line without splitting fields that fit."""
    import shutil
    from datetime import datetime, timedelta, timezone
    from textwrap import wrap
    from unicodedata import east_asian_width
    if stream is None:
        stream = sys.stderr
        if language == 'ja':
            stream.reconfigure(encoding='utf-8')
    width = max(32, min(160, columns or shutil.get_terminal_size(fallback=(100, 30)).columns - 2))
    now = datetime.now().astimezone()
    flags = policy.snapshot()
    separator = ' | '
    measure = len
    wrap_line = wrap
    if language == 'ja':
        now = now.astimezone(timezone(timedelta(hours=9)))
        weekday = '月火水木金土日'[now.weekday()]
        date = f'{now.year}年{now.month}月{now.day}日（{weekday}）'
        time = now.strftime('%H:%M:%S JST (UTC+09:00)')
        permissions = tuple(
            f"{label} {'〇' if flags[key] else '✕'}"
            for label, key in (
                ('作成', 'create'), ('編集', 'edit'),
                ('削除', 'delete'), ('PowerShell', 'powershell'),
            )
        )
        groups = (
            ('TSPAI MCP', '起動確認', 'Rights First For AI'),
            ('日時', date, time),
            (f'バージョン：{VERSION}', 'Windows Hello：認証済み',
             f'セッション：{session_seconds:,}秒'),
            ('権限', '一覧・読み取り 〇', *permissions),
            ('準備完了', '権限を変更するには再起動してください。'),
            ('今日も一日、いい記録が残りますように。',),
        )
        separator = ' // '

        def measure(text):
            return sum(2 if east_asian_width(char) in 'FWA' else 1 for char in text)

        def wrap_line(text, columns):
            start = cells = 0
            for index, char in enumerate(text):
                char_width = measure(char)
                if cells + char_width > columns:
                    yield text[start:index]
                    start = index
                    cells = 0
                cells += char_width
            yield text[start:]

    else:
        left = [
            'SYSTEM INFORMATION',
            'Date: ' + now.strftime('%A, %B %d, %Y'),
            'Time: ' + now.strftime('%H:%M:%S') + ' JST (UTC+09:00)',
            'Version: ' + VERSION,
            'Windows Hello: Authenticated',
            'Session: ' + str(session_seconds) + ' seconds',
        ]
        right = [
            'ACTIVE PERMISSIONS',
            'Read / List: ENABLED',
            'File Create: ' + ('ENABLED' if flags['create'] else 'DISABLED'),
            'File Edit: ' + ('ENABLED' if flags['edit'] else 'DISABLED'),
            'File Delete: ' + ('ENABLED' if flags['delete'] else 'DISABLED'),
            'PowerShell: ' + ('ENABLED' if flags['powershell'] else 'DISABLED'),
        ]
        groups = (
            ('TSPAI MCP | Startup Confirmation', 'Rights First For AI'),
            left[:3],
            left[3:],
            right,
            ('Change permissions on the next restart.', 'TSPAI MCP is ready.'),
            ('Hope you capture something worth keeping today.',),
        )
    border = '=' * width
    lines = [border]
    for group in groups:
        line = group[0]
        for field in group[1:]:
            combined = line + separator + field
            if measure(combined) <= width:
                line = combined
            else:
                lines.extend(wrap_line(line, width))
                line = field
        lines.extend(wrap_line(line, width))
    lines.append(border)
    print('\n'.join(lines), file=stream, flush=True)


def authenticate(session_seconds, allow_create, allow_edit, allow_delete, allow_powershell,
                 first_start=False, plus1_enabled=False, *, language='en'):
    if os.name != 'nt':
        raise OSError('Windows desktop required')
    import tkinter as tk
    from tkinter import messagebox
    from hello import verify
    ja = language == 'ja'
    window = tk.Tk()
    window.title(f'TSPAI MCP — Ver. {VERSION}')
    if ja:
        window.minsize(640, 340)
    else:
        window.geometry('640x340')
    window.attributes('-topmost', True)
    tk.Label(window, text=f'Rights First For AI｜Ver. {VERSION}').pack(side='bottom', pady=8)
    if ja:
        heading = '初回起動：読み取り専用' if first_start else '選んだ権限を承認'
        restart = 'このセッションの終了後、再起動すると追加の権限を選べます。'
        intro = f'承認後{session_seconds:,}秒間、接続先に次の操作を許可します。'
        footer = '承認はこのセッションに適用されます。終了するにはMCPクライアントでサーバーを停止してください。'
        names = ('ファイルの一覧・読み取り', 'ファイルの作成', 'ファイルの上書き',
                 'ファイルまたは空フォルダーの削除', 'Windowsアカウントの権限でPowerShellを実行',
                 'PLUS1で選んだファイルをChatGPTへ送信')
        separator = '、'
    else:
        heading = 'First start: read-only mode' if first_start else 'Approve the selected permissions'
        restart = 'Restart after this session to choose additional permissions.'
        intro = f'For {session_seconds} seconds after approval, allow the connected client to use:'
        footer = 'Approval applies to the session. Stop the server in your MCP client to end it.'
        names = ('List and read files', 'create files', 'overwrite files', 'delete files or empty folders',
                 'PowerShell with your account permissions', 'PLUS1 to select a staged file and send it to ChatGPT')
        separator = ', '
    tk.Label(window, text=heading, font=('', 15)).pack(pady=20)
    if first_start:
        tk.Label(window, text=restart, font=('', 13), wraplength=570).pack(pady=8)
    permissions = separator.join(name for name, enabled in zip(
        names, (True, allow_create, allow_edit, allow_delete, allow_powershell, plus1_enabled)
    ) if enabled)
    tk.Label(window, wraplength=580, text=f'{intro}\n{permissions}\n{footer}').pack(padx=20, pady=12)
    approved = [False]
    def consent():
        button.configure(state='disabled')
        try:
            window.update_idletasks()
            api = ctypes.WinDLL('user32')
            api.GetAncestor.argtypes = [ctypes.c_void_p, ctypes.c_uint]
            api.GetAncestor.restype = ctypes.c_void_p
            hwnd = api.GetAncestor(window.winfo_id(), 2)
            prompt = (f'TSPAI MCP：選んだ権限を{session_seconds:,}秒間承認します。' if ja else
                      f'TSPAI MCP: approve selected permissions for {session_seconds} seconds')
            approved[0] = verify(hwnd, prompt, window.update)
        except Exception:
            messagebox.showerror('起動を中止しました' if ja else 'Startup stopped',
                                 'Windows Helloの承認が完了しませんでした。' if ja else
                                 'Windows Hello approval was not completed.', parent=window)
        finally:
            try:
                window.destroy()
            except tk.TclError:
                pass
    button = tk.Button(window, text='Windows Helloで承認' if ja else 'Approve with Windows Hello', command=consent)
    button.pack(pady=10)
    tk.Button(window, text='取り消す' if ja else 'Cancel', command=window.destroy).pack()
    window.mainloop()
    if approved[0] is not True:
        raise PermissionError('このPCでのWindows Hello承認が必要です。' if ja else
                              'local Windows Hello approval required')


def attach(server, executor, *, workspace, allow_write=False, allow_powershell=False,
           allow_create=None, allow_edit=None, allow_delete=False, policy=None,
           plus1_enabled=False):
    # allow_write remains a compatibility argument for existing synthetic tests.
    if allow_create is None:
        allow_create = allow_write
    if allow_edit is None:
        allow_edit = allow_write
    files = FileActions(executor, workspace)
    if policy is None:
        policy = PermissionPolicy(create=allow_create, edit=allow_edit,
                                  delete=allow_delete, powershell=allow_powershell)

    @server.tool()
    def tspai_file_read(path: str, request_id: str, encoding: str = 'utf-8',
                        offset_bytes: int = 0, max_bytes: int = 16000) -> dict:
        """Read an absolute PC file in byte pages, using the approved owner session.

        encoding is utf-8 or base64 (use base64 for binary/other text encodings).
        Continue at next_offset_bytes with a NEW UUID. Reuse the SAME UUID and
        exact arguments only to retrieve a prior result after transport uncertainty.
        sha256 is full-file only when the entire file fits this read.
        """
        return files.read(path, request_id, encoding, offset_bytes, max_bytes)

    @server.tool()
    def tspai_file_write(path: str, content: str, request_id: str,
                         encoding: str = 'utf-8', mode: str = 'create',
                         expected_sha256: str | None = None) -> dict:
        """Write an absolute PC file, at most 256000 decoded bytes.

        Default create fails if the file exists. replace requires the previous
        full-file lowercase SHA256. encoding is utf-8 or base64. Parent must exist.
        Replacement uses atomic rename, which can change file metadata/permissions;
        it does not lock other apps. Runs as owner, not a sandbox.
        Reuse SAME UUID/arguments after uncertainty; never force a new-ID retry
        for outcome_unknown. No automatic backup or side-effect rollback.
        """
        permission = 'create' if mode == 'create' else 'edit'
        return policy.authorize(permission, lambda: files.write(
            path, content, request_id, encoding, mode, expected_sha256))

    @server.tool()
    def tspai_file_delete(path: str, request_id: str,
                          expected_sha256: str | None = None) -> dict:
        """Delete one regular file after matching its SHA256, or an EMPTY folder.

        Disabled by default; requires independent local startup authorization.
        No recursive deletion. This is NOT a sandbox against enabled PowerShell.
        """
        return policy.authorize('delete', lambda: files.delete(path, request_id, expected_sha256))

    @server.tool()
    def tspai_file_list(path: str, request_id: str, offset: int = 0,
                        limit: int = 100) -> dict:
        """List an absolute PC directory without recursion, at most 200 entries.

        Filesystem ordering can change between pages. Each new page needs a new
        UUID; same-ID replay returns the saved page. Requires the approved session.
        """
        return files.list(path, request_id, offset, limit)

    @server.tool()
    def tspai_powershell_probe(operation: str) -> dict:
        """Compatibility: read Windows date only; other probes are denied."""
        if operation != 'get_date':
            raise PermissionError('only get_date is supported by this probe')
        result = policy.authorize('powershell', lambda: executor.execute(
            'Get-Date -Format o', str(uuid.uuid4())))
        return {'ok': result['ok'], 'operation_id': result['request_id'],
                'route': 'powershell_local_authorized', 'error': None,
                'result': dict(result, operation=operation)}

    @server.tool()
    def tspai_powershell_execute(script: str, request_id: str, timeout_seconds: int = 30,
                                 working_directory: str | None = None) -> dict:
        """Run PowerShell in the locally approved Windows session.

        Supply a new canonical UUID request_id for each intended operation.
        On transport uncertainty query again with the SAME ID and exact arguments.
        outcome_unknown requires inspection, never a new ID to force a retry.
        Returns stdout, stderr, exit_code. Arbitrary script executes as the owner.
        """
        return policy.authorize('powershell', lambda: executor.execute(
            script, request_id, timeout_seconds, working_directory))

    @server.tool()
    def tspai_powershell_session_status() -> dict:
        """Read the active local PowerShell session's remaining lifetime."""
        active = policy.snapshot()
        return dict(executor.status(), server_version=VERSION,
                    capabilities=['file_read', 'file_list'] +
                    (['file_create'] if active['create'] else []) +
                    (['file_edit'] if active['edit'] else []) +
                    (['file_delete'] if active['delete'] else []) +
                    (['powershell'] if active['powershell'] else []) +
                    (['file_transfer_plus1'] if plus1_enabled else []),
                    approval='session', filesystem_sandbox=False)
    return server


async def run_cancellable_stdio(server):
    """Reuse SDK framing without leaving a reader on global buffered stdin."""
    # A cancelled read may finish only when the client closes its pipe. Its
    # private unbuffered handle must not lock sys.stdin during Python shutdown.
    source = io.TextIOWrapper(io.FileIO(os.dup(sys.stdin.fileno()), 'rb'),
                              encoding='utf-8', errors='replace')

    async def lines():
        while True:
            line = await anyio.to_thread.run_sync(source.readline, abandon_on_cancel=True)
            if not line:
                return
            yield line

    async with stdio_server(stdin=lines()) as (read_stream, write_stream):
        await server._mcp_server.run(
            read_stream, write_stream, server._mcp_server.create_initialization_options())


def main():
    parser = argparse.ArgumentParser(description='TSPAI MCP public preparation candidate')
    parser.add_argument('--check', action='store_true')
    parser.add_argument('--language', choices=('en', 'ja'), default='en',
                        help='Language of the local startup interface')
    parser.add_argument('--workspace', type=Path)
    parser.add_argument('--data-dir', type=Path)
    parser.add_argument('--enable-plus1', action='store_true',
                        help='Enable opt-in file transfer after first authenticated start')
    parser.add_argument('--session-seconds', type=int, default=3600)
    parser.add_argument('--enable-write', action='store_true', help='legacy: enable create and edit')
    parser.add_argument('--enable-create', action='store_true')
    parser.add_argument('--enable-edit', action='store_true')
    parser.add_argument('--enable-delete', action='store_true')
    parser.add_argument('--enable-powershell', action='store_true')
    args = parser.parse_args()
    ja = args.language == 'ja'
    if ja:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    if args.check:
        import importlib.metadata
        print('MCP SDK:', importlib.metadata.version('mcp'))
        print('TSPAI MCP', VERSION,
              '読み込み確認済み。認証・接続はこのチェックの対象外です。' if ja else
              'imports OK; authentication and transport not tested')
        return
    if os.name != 'nt':
        parser.error('Windowsデスクトップで実行してください。' if ja else 'Windows desktop required')
    if args.workspace is None or not args.workspace.is_absolute():
        parser.error('--workspace には既存フォルダーの絶対パスを指定してください。' if ja else '--workspace must be an existing absolute directory')
    if not 1 <= args.session_seconds <= 43200:
        parser.error('--session-seconds には1～43200秒（12時間）を指定してください。' if ja else '--session-seconds must be 1..43200 (12 hours)')
    try:
        workspace = args.workspace.resolve(strict=True)
    except FileNotFoundError:
        parser.error('作業フォルダーが見つかりません。' if ja else 'Workspace directory was not found')
    if not workspace.is_dir():
        parser.error('--workspace にはフォルダーを指定してください。' if ja else '--workspace must be a directory')
    base = args.data_dir or Path(os.environ['LOCALAPPDATA']) / 'TSPAI-MCP-Open'
    if not base.is_absolute():
        parser.error('--data-dir には絶対パスを指定してください。' if ja else '--data-dir must be absolute')
    base = base.resolve()
    if base.is_relative_to(workspace) or workspace.is_relative_to(base):
        parser.error('作業フォルダーと非公開の記録フォルダーを分けてください。' if ja else 'workspace and private audit directory must be separate')
    base.mkdir(parents=True, exist_ok=True)
    shell = Path(os.environ['SystemRoot']) / 'System32/WindowsPowerShell/v1.0/powershell.exe'
    server = FastMCP(f'TSPAI MCP Ver. {VERSION}', instructions=(
        'Windows Hello authorizes a time-limited session; there is no per-operation approval. '
        'File tools are limited to the locally configured workspace. PowerShell, if enabled, '
        'runs as the owner and is not sandboxed. Writes and PowerShell are disabled by default. '
        'Reuse the same request_id and exact arguments after transport uncertainty. '
        'Never rerun an outcome_unknown operation with a new ID without inspecting effects.'))
    selected, first_start = startup_permissions(base, {})
    # After first successful start, local owner chooses each session's permissions.
    try:
        selected = validate_selection(choose_permissions(first_start, selected, language=args.language))
    except PermissionError as error:
        print(error, file=sys.stderr)
        return 1
    allow_create = selected['create']
    allow_edit = selected['edit']
    allow_delete = selected['delete']
    allow_powershell = selected['powershell']
    gate = SessionGate()
    policy = PermissionPolicy(audit_db=base / 'permissions.sqlite3',
                              create=allow_create, edit=allow_edit,
                              delete=allow_delete,
                              powershell=allow_powershell)
    plus1_enabled = args.enable_plus1 and not first_start
    attach(server, gate, workspace=workspace, policy=policy, plus1_enabled=plus1_enabled)
    if plus1_enabled:
        attach_plus1(server, gate, base / 'plus1', language=args.language)
    with start_blocking_portal(name='tspai-stdio') as portal:
        transport = portal.start_task_soon(run_cancellable_stdio, server)
        try:
            authenticate(args.session_seconds, allow_create, allow_edit,
                         allow_delete, allow_powershell, first_start, plus1_enabled, language=args.language)
            gate.executor = PowerShellExecutor(base, shell, cwd=workspace,
                                              session_seconds=args.session_seconds)
            gate.authentication = 'verified'
            report_active_permissions(policy, args.session_seconds, language=args.language)
            if first_start:
                (base / 'first_start_verified').write_text('verified\\n', encoding='utf-8')
        except BaseException:
            gate.authentication = 'denied'
            print('ローカル認証が承認されなかったため、起動を停止しました。' if ja else
                  'Local authentication denied; server stopped.', file=sys.stderr)
            transport.cancel()
            return 1
        transport.result()
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
