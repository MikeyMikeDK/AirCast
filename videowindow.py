"""Finder UxPlays videovindue og tilpasser det til billedets format (stående/liggende)."""

import ctypes
from ctypes import wintypes

user32 = ctypes.windll.user32
user32.MonitorFromWindow.restype = wintypes.HMONITOR
user32.MonitorFromWindow.argtypes = [wintypes.HWND, wintypes.DWORD]
user32.GetMonitorInfoW.argtypes = [wintypes.HMONITOR, ctypes.c_void_p]
user32.SetWindowPos.argtypes = [wintypes.HWND, wintypes.HWND, ctypes.c_int, ctypes.c_int,
                                ctypes.c_int, ctypes.c_int, wintypes.UINT]

MONITOR_DEFAULTTONEAREST = 2
SWP_NOZORDER = 0x0004
SWP_NOACTIVATE = 0x0010
SCREEN_FRACTION = 0.9  # videovinduet må fylde højst 90 % af skærmens arbejdsområde

EnumWindowsProc = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)


class MONITORINFO(ctypes.Structure):
    _fields_ = [("cbSize", wintypes.DWORD), ("rcMonitor", wintypes.RECT),
                ("rcWork", wintypes.RECT), ("dwFlags", wintypes.DWORD)]


def find_window(pid):
    """Returnerer det synlige topvindue, som processen `pid` ejer, eller None."""
    found = []

    def callback(hwnd, _):
        owner = wintypes.DWORD()
        user32.GetWindowThreadProcessId(hwnd, ctypes.byref(owner))
        if owner.value == pid and user32.IsWindowVisible(hwnd):
            found.append(hwnd)
            return False
        return True

    user32.EnumWindows(EnumWindowsProc(callback), 0)
    return found[0] if found else None


def _rect(hwnd, getter):
    r = wintypes.RECT()
    getter(hwnd, ctypes.byref(r))
    return r


def fit_to_video(hwnd, video_w, video_h):
    """Giver vinduets videoflade samme format som videoen, centreret hvor vinduet er nu.
    Gør intet i fuldskærm."""
    info = MONITORINFO(cbSize=ctypes.sizeof(MONITORINFO))
    user32.GetMonitorInfoW(user32.MonitorFromWindow(hwnd, MONITOR_DEFAULTTONEAREST), ctypes.byref(info))
    mon, work = info.rcMonitor, info.rcWork
    win = _rect(hwnd, user32.GetWindowRect)
    client = _rect(hwnd, user32.GetClientRect)

    if (win.left, win.top, win.right, win.bottom) == (mon.left, mon.top, mon.right, mon.bottom):
        return

    border_w = (win.right - win.left) - client.right
    border_h = (win.bottom - win.top) - client.bottom
    work_w, work_h = work.right - work.left, work.bottom - work.top
    scale = min((work_w * SCREEN_FRACTION - border_w) / video_w, (work_h * SCREEN_FRACTION - border_h) / video_h)
    new_w = round(video_w * scale) + border_w
    new_h = round(video_h * scale) + border_h

    center_x, center_y = (win.left + win.right) // 2, (win.top + win.bottom) // 2
    x = min(max(center_x - new_w // 2, work.left), work.right - new_w)
    y = min(max(center_y - new_h // 2, work.top), work.bottom - new_h)
    user32.SetWindowPos(hwnd, None, x, y, new_w, new_h, SWP_NOZORDER | SWP_NOACTIVATE)
