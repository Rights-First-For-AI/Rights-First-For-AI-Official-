"""Windows desktop UserConsentVerifier interop; never receives a PIN.

Uses the SDK ABI via Python ctypes, not the UWP-only request method.
No success fallback: unavailable/cancel/error/timeouts deny the operation.
"""
import ctypes as C
import os
import time
import uuid


def operation_iid():
    # WinRT parameterized interface UUID, IAsyncOperation<enum ...;i4>.
    signature = ('pinterface({9fc2b0bb-e446-44e2-aa61-9cab8f636af2};'
                 'enum(Windows.Security.Credentials.UI.UserConsentVerificationResult;i4))')
    return uuid.uuid5(uuid.UUID('11f47ad5-7b73-42c0-abae-878b1e16adee'), signature)


def verify(hwnd, message, pump, timeout=120):
    if os.name != 'nt' or not hwnd:
        raise RuntimeError('Windows desktop window required')
    P = C.c_void_p
    H = C.c_int32
    U = C.c_uint32
    G = C.c_ubyte * 16
    def guid(value):
        return G.from_buffer_copy(uuid.UUID(str(value)).bytes_le)
    def check(hr):
        if hr < 0:
            raise OSError('Windows Hello HRESULT 0x%08x' % (hr & 0xffffffff))
    def call(obj, slot, args, *values):
        table = C.cast(obj, C.POINTER(C.POINTER(P))).contents
        return C.WINFUNCTYPE(H, P, *args)(table[slot])(obj, *values)
    api = C.WinDLL('combase')
    api.RoInitialize.argtypes = [U]
    api.RoInitialize.restype = H
    api.RoUninitialize.argtypes = []
    api.RoUninitialize.restype = None
    api.WindowsCreateString.argtypes = [C.c_wchar_p, U, C.POINTER(P)]
    api.WindowsCreateString.restype = H
    api.WindowsDeleteString.argtypes = [P]
    api.RoGetActivationFactory.argtypes = [P, C.POINTER(G), C.POINTER(P)]
    api.RoGetActivationFactory.restype = H
    check(api.RoInitialize(0))
    strings, objects = [], []
    info = None
    try:
        def hstring(text):
            result = P()
            check(api.WindowsCreateString(text, len(text.encode('utf-16-le')) // 2, C.byref(result)))
            strings.append(result)
            return result
        factory = P()
        iid = guid('39e050c3-4e74-441a-8dc0-b81104df949c')
        check(api.RoGetActivationFactory(hstring('Windows.Security.Credentials.UI.UserConsentVerifier'),
                                         C.byref(iid), C.byref(factory)))
        objects.append(factory)
        operation = P()
        iid = guid(operation_iid())
        check(call(factory, 6, [P, P, C.POINTER(G), C.POINTER(P)], P(hwnd),
                   hstring(message), C.byref(iid), C.byref(operation)))
        objects.append(operation)
        info = P()
        iid = guid('00000036-0000-0000-c000-000000000046')
        check(call(operation, 0, [C.POINTER(G), C.POINTER(P)], C.byref(iid), C.byref(info)))
        objects.append(info)
        end = time.monotonic() + timeout
        while True:
            status = H()
            check(call(info, 7, [C.POINTER(H)], C.byref(status)))
            if status.value != 0:
                break
            if time.monotonic() >= end:
                call(info, 9, [])  # IAsyncInfo.Cancel
                raise TimeoutError('Windows Hello expired')
            pump()
            time.sleep(0.05)
        if status.value != 1:
            raise PermissionError('Windows Hello canceled or failed')
        result = H()
        check(call(operation, 8, [C.POINTER(H)], C.byref(result)))
        if result.value != 0:  # Verified only
            raise PermissionError('Windows Hello denied: %s' % result.value)
        return True
    finally:
        if info:
            call(info, 9, [])  # Cancel any outstanding prompt on window close/error.
            call(info, 10, [])  # IAsyncInfo.Close
        for obj in reversed(objects):
            call(obj, 2, [])
        for string in strings:
            api.WindowsDeleteString(string)
        api.RoUninitialize()

