# -*- coding: utf-8 -*-
import ctypes

user32 = ctypes.windll.user32
gdi32 = ctypes.windll.gdi32

# DPI awareness (best effort)
def set_dpi_awareness() -> None:
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(1)
    except Exception:
        try:
            ctypes.windll.user32.SetProcessDPIAware()
        except Exception:
            pass


class POINT(ctypes.Structure):
    _fields_ = [("x", ctypes.c_long), ("y", ctypes.c_long)]


class RECT(ctypes.Structure):
    _fields_ = [
        ("left", ctypes.c_long), ("top", ctypes.c_long),
        ("right", ctypes.c_long), ("bottom", ctypes.c_long)
    ]


def init_win32_prototypes() -> None:
    user32.SetWindowPos.restype = ctypes.c_bool
    user32.SetWindowPos.argtypes = [
        ctypes.c_void_p, ctypes.c_void_p,
        ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int,
        ctypes.c_uint
    ]

    user32.GetWindowRect.restype = ctypes.c_bool
    user32.GetWindowRect.argtypes = [ctypes.c_void_p, ctypes.POINTER(RECT)]

    user32.GetCursorPos.restype = ctypes.c_bool
    user32.GetCursorPos.argtypes = [ctypes.POINTER(POINT)]

    user32.SetWindowRgn.argtypes = [ctypes.c_void_p, ctypes.c_void_p, ctypes.c_bool]

    # WindowLong
    user32.GetWindowLongW.restype = ctypes.c_long
    user32.GetWindowLongW.argtypes = [ctypes.c_void_p, ctypes.c_int]
    user32.SetWindowLongW.restype = ctypes.c_long
    user32.SetWindowLongW.argtypes = [ctypes.c_void_p, ctypes.c_int, ctypes.c_long]

    # Regions
    gdi32.CreateRoundRectRgn.restype = ctypes.c_void_p
    gdi32.CreateRoundRectRgn.argtypes = [
        ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int,
        ctypes.c_int, ctypes.c_int
    ]

    gdi32.CreateRectRgn.restype = ctypes.c_void_p
    gdi32.CreateRectRgn.argtypes = [ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int]


def get_window_rect(hwnd: int) -> tuple[int, int, int, int]:
    rect = RECT()
    ok = user32.GetWindowRect(ctypes.c_void_p(hwnd), ctypes.byref(rect))
    if not ok:
        return (0, 0, 0, 0)
    x = rect.left
    y = rect.top
    w = rect.right - rect.left
    h = rect.bottom - rect.top
    return (x, y, w, h)


def set_window_pos(hwnd: int, x: int, y: int) -> None:
    # SWP_NOSIZE = 0x0001
    user32.SetWindowPos(ctypes.c_void_p(hwnd), 0, int(x), int(y), 0, 0, 0x0001)


def toggle_always_on_top(hwnd: int, enabled: bool) -> None:
    # SWP_NOMOVE|SWP_NOSIZE = 0x0002|0x0001
    z = ctypes.c_void_p(-1) if enabled else ctypes.c_void_p(-2)
    user32.SetWindowPos(ctypes.c_void_p(hwnd), z, 0, 0, 0, 0, 0x0002 | 0x0001)


def set_window_shape(hwnd: int, w: int, h: int, rounded: bool, radius: int = 18) -> None:
    try:
        if rounded:
            region = gdi32.CreateRoundRectRgn(0, 0, int(w), int(h), int(radius), int(radius))
        else:
            region = gdi32.CreateRectRgn(0, 0, int(w), int(h))
        user32.SetWindowRgn(ctypes.c_void_p(hwnd), region, True)
    except Exception:
        pass


def apply_window_hack(hwnd: int, x: int, y: int, w: int, h: int, rounded: bool) -> None:
    try:
        GWL_EXSTYLE = -20
        style = user32.GetWindowLongW(ctypes.c_void_p(hwnd), GWL_EXSTYLE)
        # original: style = style & ~0x00000080 | 0x00040000
        style = (style & ~0x00000080) | 0x00040000
        user32.SetWindowLongW(ctypes.c_void_p(hwnd), GWL_EXSTYLE, style)
        # SWP_NOSIZE|SWP_SHOWWINDOW = 0x0001|0x0020
        user32.SetWindowPos(ctypes.c_void_p(hwnd), 0, int(x), int(y), 0, 0, 0x0001 | 0x0020)
        set_window_shape(hwnd, w, h, rounded)
    except Exception:
        pass


def get_cursor_pos() -> tuple[int, int]:
    pt = POINT()
    ok = user32.GetCursorPos(ctypes.byref(pt))
    if not ok:
        return (0, 0)
    return (pt.x, pt.y)