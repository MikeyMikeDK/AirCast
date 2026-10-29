"""AirCast - AirPlay-modtager til Windows (spejl iPhone/iPad til PC'en).

Bruger UxPlay (engine\\bin\\uxplay.exe) som AirPlay-motor. I den færdige AirCast.exe ligger
motoren som engine.tar.xz og pakkes ud til %LOCALAPPDATA%\\AirCast første gang.
"""

import ctypes
import json
import os
import queue
import re
import subprocess
import sys
import threading
import tkinter as tk
from pathlib import Path
from tkinter import messagebox, ttk

import portable
import videowindow

DATA_DIR = Path(os.environ["APPDATA"]) / "AirCast"
SETTINGS_FILE = DATA_DIR / "settings.json"
if getattr(sys, "frozen", False):
    RESOURCES = Path(sys._MEIPASS)
    ENGINE = portable.unpack_engine(RESOURCES / "engine.tar.xz", Path(os.environ["LOCALAPPDATA"]) / "AirCast")
else:
    RESOURCES = Path(__file__).parent
    ENGINE = RESOURCES / "engine"
UXPLAY = ENGINE / "bin" / "uxplay.exe"

RESOLUTIONS = {
    "1280x720 (HD)": "1280x720@60",
    "1920x1080 (Full HD)": "1920x1080@60",
    "2560x1440 (2K)": "2560x1440@60",
    "3840x2160 (4K, H.265)": "3840x2160@60",
}

DEFAULT_SETTINGS = {
    "name": os.environ["COMPUTERNAME"],
    "resolution": "1920x1080 (Full HD)",
    "fullscreen": False,
    "audio": True,
    "low_latency": True,
    "use_pin": False,
    "pin": "1234",
}

CONNECT_RE = re.compile(r"connection request from (.+?) \((.+?)\) with deviceID")
FRAME_SIZE_RE = re.compile(r"video frame size (\d+)x(\d+)")
RESIZE_TRIES = 15  # videovinduet kan være op til 3 s om at dukke op efter første billede

BG = "#1e1f24"
PANEL = "#2a2c33"
FG = "#e8e8ec"
MUTED = "#9a9ca6"
ACCENT = "#3d8bfd"
GREEN = "#3ecf6e"
RED = "#e5534b"


def load_settings():
    if not SETTINGS_FILE.exists():
        return dict(DEFAULT_SETTINGS)
    return {**DEFAULT_SETTINGS, **json.loads(SETTINGS_FILE.read_text(encoding="utf-8"))}


def save_settings(settings):
    SETTINGS_FILE.parent.mkdir(parents=True, exist_ok=True)
    SETTINGS_FILE.write_text(json.dumps(settings, indent=2, ensure_ascii=False), encoding="utf-8")


def build_args(s):
    resolution = RESOLUTIONS[s["resolution"]]
    args = [str(UXPLAY), "-n", s["name"], "-nh", "-s", resolution, "-fps", "60", "-vs", "d3d12videosink"]
    if s["low_latency"]:
        # Vis hvert billede så snart det er afkodet i stedet for at vente på lydens tidsstempler
        args += ["-vsync", "no"]
    if resolution.startswith("3840"):
        args.append("-h265")
    if s["fullscreen"]:
        args.append("-fs")
    if not s["audio"]:
        args += ["-as", "0"]
    if s["use_pin"]:
        args.append("-pin" + s["pin"])
    return args


class Receiver:
    """Starter/stopper uxplay.exe og sender dens log-linjer til en kø."""

    def __init__(self, lines):
        self.lines = lines
        self.proc = None

    @property
    def running(self):
        return self.proc is not None and self.proc.poll() is None

    def start(self, args):
        env = dict(
            os.environ,
            PATH=f"{ENGINE / 'bin'};{os.environ['PATH']}",
            GST_PLUGIN_SYSTEM_PATH_1_0=str(ENGINE / "lib" / "gstreamer-1.0"),
            GST_PLUGIN_SCANNER_1_0=str(ENGINE / "libexec" / "gstreamer-1.0" / "gst-plugin-scanner.exe"),
            GST_REGISTRY_1_0=str(DATA_DIR / "gst-registry.bin"),
        )
        self.proc = subprocess.Popen(
            args,
            env=env,
            cwd=str(DATA_DIR),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            stdin=subprocess.DEVNULL,
            text=True,
            encoding="utf-8",
            errors="replace",
            creationflags=subprocess.CREATE_NO_WINDOW,
        )
        threading.Thread(target=self._pump, args=(self.proc,), daemon=True).start()

    def _pump(self, proc):
        for line in proc.stdout:
            self.lines.put(line.rstrip())
        self.lines.put(None)  # processen er slut

    def stop(self):
        self.proc.terminate()
        self.proc.wait()


class App:
    def __init__(self, root):
        self.root = root
        self.settings = load_settings()
        self.lines = queue.Queue()
        self.receiver = Receiver(self.lines)

        root.title("AirCast")
        root.iconbitmap(default=str(RESOURCES / "aircast.ico"))
        root.configure(bg=BG)
        root.resizable(False, True)
        root.minsize(460, 420)
        root.protocol("WM_DELETE_WINDOW", self.on_close)

        style = ttk.Style(root)
        style.theme_use("clam")
        style.configure(".", background=BG, foreground=FG, fieldbackground=PANEL)
        style.configure("TLabel", background=BG, foreground=FG, font=("Segoe UI", 10))
        style.configure("Muted.TLabel", foreground=MUTED, font=("Segoe UI", 9))
        style.configure("Title.TLabel", font=("Segoe UI Semibold", 18))
        style.configure("Status.TLabel", font=("Segoe UI Semibold", 12))
        style.configure("TCheckbutton", background=BG, foreground=FG, font=("Segoe UI", 10))
        style.map("TCheckbutton", background=[("active", BG)])
        style.configure("TEntry", foreground=FG, insertcolor=FG)
        style.configure("TCombobox", foreground=FG, arrowcolor=FG, background=PANEL)
        style.map("TCombobox", fieldbackground=[("readonly", PANEL)], foreground=[("readonly", FG)])
        style.configure("Accent.TButton", background=ACCENT, foreground="white",
                        font=("Segoe UI Semibold", 11), padding=(16, 8), borderwidth=0)
        style.map("Accent.TButton", background=[("active", "#5a9dfd")])

        frame = ttk.Frame(root, padding=20, style="TFrame")
        style.configure("TFrame", background=BG)
        frame.pack(fill="both", expand=True)

        ttk.Label(frame, text="AirCast", style="Title.TLabel").grid(row=0, column=0, columnspan=2, sticky="w")
        ttk.Label(frame, text="Spejl din iPhone eller iPad til denne computer",
                  style="Muted.TLabel").grid(row=1, column=0, columnspan=2, sticky="w", pady=(0, 14))

        self.status_dot = tk.Canvas(frame, width=14, height=14, bg=BG, highlightthickness=0)
        self.status_dot.grid(row=2, column=0, sticky="w")
        self.dot = self.status_dot.create_oval(2, 2, 12, 12, fill=RED, outline="")
        self.status = ttk.Label(frame, text="Stoppet", style="Status.TLabel")
        self.status.grid(row=2, column=0, columnspan=2, sticky="w", padx=(22, 0))
        self.device = ttk.Label(frame, text="", style="Muted.TLabel")
        self.device.grid(row=3, column=0, columnspan=2, sticky="w", pady=(2, 14))

        self.name_var = tk.StringVar(value=self.settings["name"])
        self.res_var = tk.StringVar(value=self.settings["resolution"])
        self.fs_var = tk.BooleanVar(value=self.settings["fullscreen"])
        self.audio_var = tk.BooleanVar(value=self.settings["audio"])
        self.low_latency_var = tk.BooleanVar(value=self.settings["low_latency"])
        self.pin_on_var = tk.BooleanVar(value=self.settings["use_pin"])
        self.pin_var = tk.StringVar(value=self.settings["pin"])

        ttk.Label(frame, text="Navn på modtager").grid(row=4, column=0, sticky="w", pady=4)
        ttk.Entry(frame, textvariable=self.name_var, width=28).grid(row=4, column=1, sticky="ew", pady=4)
        ttk.Label(frame, text="Opløsning").grid(row=5, column=0, sticky="w", pady=4)
        ttk.Combobox(frame, textvariable=self.res_var, values=list(RESOLUTIONS), state="readonly",
                     width=26).grid(row=5, column=1, sticky="ew", pady=4)
        ttk.Checkbutton(frame, text="Fuldskærm (Alt+Enter skifter)", variable=self.fs_var).grid(
            row=6, column=0, columnspan=2, sticky="w", pady=4)
        ttk.Checkbutton(frame, text="Afspil lyd på computeren", variable=self.audio_var).grid(
            row=7, column=0, columnspan=2, sticky="w", pady=4)
        ttk.Checkbutton(frame, text="Lav forsinkelse (lyd kan halte en smule efter)", variable=self.low_latency_var).grid(
            row=8, column=0, columnspan=2, sticky="w", pady=4)
        ttk.Checkbutton(frame, text="Kræv PIN-kode", variable=self.pin_on_var).grid(row=9, column=0, sticky="w", pady=4)
        ttk.Entry(frame, textvariable=self.pin_var, width=8).grid(row=9, column=1, sticky="w", pady=4)

        self.button = ttk.Button(frame, text="Start", style="Accent.TButton", command=self.toggle)
        self.button.grid(row=10, column=0, columnspan=2, sticky="ew", pady=(16, 10))

        ttk.Label(frame, text="På iPhone/iPad: Kontrolcenter → Skærmspejling → vælg navnet ovenfor",
                  style="Muted.TLabel").grid(row=11, column=0, columnspan=2, sticky="w")

        self.log = tk.Text(frame, height=8, bg=PANEL, fg=MUTED, relief="flat", font=("Consolas", 8),
                           state="disabled", wrap="none")
        self.log.grid(row=12, column=0, columnspan=2, sticky="nsew", pady=(10, 0))
        frame.columnconfigure(1, weight=1)
        frame.rowconfigure(12, weight=1)

        if not UXPLAY.exists():
            messagebox.showerror("AirCast", f"Kan ikke finde AirPlay-motoren:\n{UXPLAY}")
            root.destroy()
            return

        self.start()
        self.poll()

    def collect_settings(self):
        pin = self.pin_var.get().strip()
        if self.pin_on_var.get() and not re.fullmatch(r"\d{4}", pin):
            raise ValueError("PIN-koden skal være 4 cifre.")
        name = self.name_var.get().strip()
        if not name:
            raise ValueError("Modtageren skal have et navn.")
        return {
            "name": name,
            "resolution": self.res_var.get(),
            "fullscreen": self.fs_var.get(),
            "audio": self.audio_var.get(),
            "low_latency": self.low_latency_var.get(),
            "use_pin": self.pin_on_var.get(),
            "pin": pin,
        }

    def toggle(self):
        if self.receiver.running:
            self.receiver.stop()
        else:
            self.start()

    def start(self):
        try:
            self.settings = self.collect_settings()
        except ValueError as e:
            messagebox.showerror("AirCast", str(e))
            return
        save_settings(self.settings)
        self.append_log("> " + " ".join(build_args(self.settings)[1:]))
        self.receiver.start(build_args(self.settings))
        self.set_status(True)

    def set_status(self, running):
        self.status_dot.itemconfigure(self.dot, fill=GREEN if running else RED)
        if running:
            pin = f"  ·  PIN {self.settings['pin']}" if self.settings["use_pin"] else ""
            self.status.configure(text=f"Klar som \"{self.settings['name']}\"{pin}")
            self.device.configure(text="Venter på iPhone/iPad …")
            self.button.configure(text="Stop")
        else:
            self.status.configure(text="Stoppet")
            self.device.configure(text="")
            self.button.configure(text="Start")

    def poll(self):
        while not self.lines.empty():
            line = self.lines.get()
            if line is None:
                self.set_status(False)
                continue
            self.append_log(line)
            m = CONNECT_RE.search(line)
            if m:
                self.device.configure(text=f"Forbundet: {m.group(1)} ({m.group(2)})")
            m = FRAME_SIZE_RE.search(line)
            if m:
                self.fit_video_window(int(m.group(1)), int(m.group(2)), RESIZE_TRIES)
        self.root.after(100, self.poll)

    def fit_video_window(self, width, height, tries_left):
        if not self.receiver.running:
            return
        hwnd = videowindow.find_window(self.receiver.proc.pid)
        if hwnd:
            videowindow.fit_to_video(hwnd, width, height)
        elif tries_left > 1:
            self.root.after(200, self.fit_video_window, width, height, tries_left - 1)

    def append_log(self, line):
        self.log.configure(state="normal")
        self.log.insert("end", line + "\n")
        self.log.delete("1.0", "end-500l")
        self.log.see("end")
        self.log.configure(state="disabled")

    def on_close(self):
        if self.receiver.running:
            self.receiver.stop()
        self.root.destroy()


if __name__ == "__main__":
    # Rigtige pixelkoordinater, så videovinduet kan måles og flyttes præcist
    ctypes.windll.shcore.SetProcessDpiAwareness(2)
    root = tk.Tk()
    App(root)
    root.mainloop()
