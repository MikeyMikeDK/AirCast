"""Sørger for at Windows Firewall lukker iPhone/iPad ind til AirPlay-motoren.

Uden en tilladelse kan enheden ikke finde PC'en. Har Windows tidligere spurgt, mens netværket var
"Offentligt", har den typisk lavet en blokerings-regel, som altid vinder over en tilladelse."""

import ctypes
import subprocess
from ctypes import wintypes
from pathlib import Path

RULE_NAME = "AirCast"
SEE_MASK_NOCLOSEPROCESS = 0x40
SW_HIDE = 0
INFINITE = 0xFFFFFFFF


class SHELLEXECUTEINFOW(ctypes.Structure):
    _fields_ = [("cbSize", wintypes.DWORD), ("fMask", wintypes.ULONG), ("hwnd", wintypes.HWND),
                ("lpVerb", wintypes.LPCWSTR), ("lpFile", wintypes.LPCWSTR), ("lpParameters", wintypes.LPCWSTR),
                ("lpDirectory", wintypes.LPCWSTR), ("nShow", ctypes.c_int), ("hInstApp", wintypes.HINSTANCE),
                ("lpIDList", ctypes.c_void_p), ("lpClass", wintypes.LPCWSTR), ("hkeyClass", wintypes.HKEY),
                ("dwHotKey", wintypes.DWORD), ("hIconOrMonitor", wintypes.HANDLE), ("hProcess", wintypes.HANDLE)]


def is_allowed(program: Path) -> bool:
    """True når AirCasts egen tilladelses-regel findes for netop denne uxplay.exe."""
    result = subprocess.run(["netsh", "advfirewall", "firewall", "show", "rule", f"name={RULE_NAME}", "verbose"],
                            capture_output=True, text=True, encoding="oem", errors="replace",
                            creationflags=subprocess.CREATE_NO_WINDOW)
    return str(program).lower() in result.stdout.lower()


def run_elevated(program: str, parameters: str, verb: str = "runas") -> int | None:
    """Kører program med administrator-rettigheder (UAC), venter og returnerer exit-koden.
    None hvis brugeren afviste UAC."""
    info = SHELLEXECUTEINFOW(cbSize=ctypes.sizeof(SHELLEXECUTEINFOW), fMask=SEE_MASK_NOCLOSEPROCESS,
                             lpVerb=verb, lpFile=program, lpParameters=parameters, nShow=SW_HIDE)
    if not ctypes.windll.shell32.ShellExecuteExW(ctypes.byref(info)):
        return None
    kernel32 = ctypes.windll.kernel32
    kernel32.WaitForSingleObject(info.hProcess, INFINITE)
    code = wintypes.DWORD()
    kernel32.GetExitCodeProcess(info.hProcess, ctypes.byref(code))
    kernel32.CloseHandle(info.hProcess)
    return code.value


def allow(program: Path) -> bool:
    """Fjerner alle regler for programmet (også Windows' egne blokeringer) og tillader det på alle netværk.
    Viser UAC-dialogen. Returnerer True hvis det lykkedes."""
    commands = (f'netsh advfirewall firewall delete rule name=all program="{program}"'
                f' & netsh advfirewall firewall delete rule name={RULE_NAME}'
                f' & netsh advfirewall firewall add rule name={RULE_NAME} dir=in action=allow'
                f' program="{program}" enable=yes profile=any')
    return run_elevated("cmd.exe", f"/c {commands}") == 0
