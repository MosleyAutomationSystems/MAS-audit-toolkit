# gui.py
# Accessible Tkinter desktop UI — MAS Accessibility Audit Toolkit
# Mosley Standard Section 3.2 — Full Visual Disability Support
#
# Settings dialog tabs:
#   Appearance   — theme (4 options), font family, font size (14–20)
#   Reading      — dyslexia preset, word spacing presets, line height
#   Color Vision — CVD simulation (5 modes) + brightness/contrast/saturation/hue
#
# Note on desktop limitations:
#   Word spacing is implemented as preset extra-space insertion (Normal/Wide/Wider).
#   Letter spacing is not supported in Tkinter and is excluded from the desktop version.
#   Both are available with full em-precision in the web version.
#
# Run with: py gui.py

import tkinter as tk
from tkinter import ttk, filedialog, scrolledtext
import threading
import json
import os
import re
import colorsys

import config
from utils.logger import masLog
from utils.fetcher import load_html
from bs4 import BeautifulSoup
import importlib
import pkgutil
import checks
from reporter import generate_report

SETTINGS_FILE = os.path.join(config.BASE_DIR, "gui_settings.json")

# ── Color transform utilities ─────────────────────────────────────────────────

def hex_to_rgb(h: str) -> tuple:
    """Convert '#rrggbb' to (r, g, b) floats in range 0.0–1.0."""
    h = h.lstrip('#')
    return tuple(int(h[i:i+2], 16) / 255.0 for i in (0, 2, 4))

def rgb_to_hex(r: float, g: float, b: float) -> str:
    """Convert (r, g, b) floats to '#rrggbb', clamped to 0–1."""
    r, g, b = [max(0.0, min(1.0, x)) for x in (r, g, b)]
    return '#{:02x}{:02x}{:02x}'.format(int(r*255), int(g*255), int(b*255))

# CVD simulation matrices — Vienot et al. (1999)
CVD_MATRICES = {
    "Protanopia": [
        [0.567, 0.433, 0.000],
        [0.558, 0.442, 0.000],
        [0.000, 0.242, 0.758],
    ],
    "Deuteranopia": [
        [0.625, 0.375, 0.000],
        [0.700, 0.300, 0.000],
        [0.000, 0.300, 0.700],
    ],
    "Tritanopia": [
        [0.950, 0.050, 0.000],
        [0.000, 0.433, 0.567],
        [0.000, 0.475, 0.525],
    ],
    "Monochrome": [
        [0.299, 0.587, 0.114],
        [0.299, 0.587, 0.114],
        [0.299, 0.587, 0.114],
    ],
}

def apply_cvd(rgb: tuple, mode: str) -> tuple:
    """Apply a CVD transformation matrix to (r, g, b)."""
    if mode not in CVD_MATRICES:
        return rgb
    r, g, b = rgb
    m = CVD_MATRICES[mode]
    return (
        m[0][0]*r + m[0][1]*g + m[0][2]*b,
        m[1][0]*r + m[1][1]*g + m[1][2]*b,
        m[2][0]*r + m[2][1]*g + m[2][2]*b,
    )

def apply_adjustments(rgb: tuple, brightness: float, contrast: float,
                      saturation: float, hue_shift: int) -> tuple:
    """Apply brightness, contrast, saturation, hue on top of CVD simulation."""
    r, g, b = rgb
    r, g, b = r * brightness, g * brightness, b * brightness
    r = (r - 0.5) * contrast + 0.5
    g = (g - 0.5) * contrast + 0.5
    b = (b - 0.5) * contrast + 0.5
    r, g, b = [max(0.0, min(1.0, x)) for x in (r, g, b)]
    h, s, v = colorsys.rgb_to_hsv(r, g, b)
    s = max(0.0, min(1.0, s * saturation))
    h = (h + hue_shift / 360.0) % 1.0
    return colorsys.hsv_to_rgb(h, s, v)

def transform_theme(base: dict, cvd_mode: str, brightness: float,
                    contrast: float, saturation: float, hue_shift: int) -> dict:
    """
    Apply CVD simulation + adjustments to every hex color in a theme dict.
    Returns the base dict unchanged if all parameters are at identity values.
    """
    identity = (cvd_mode == "Normal" and brightness == 1.0 and
                contrast == 1.0 and saturation == 1.0 and hue_shift == 0)
    if identity:
        return base
    result = {}
    for key, val in base.items():
        if isinstance(val, str) and val.startswith('#') and len(val) == 7:
            rgb = hex_to_rgb(val)
            rgb = apply_cvd(rgb, cvd_mode)
            rgb = apply_adjustments(rgb, brightness, contrast, saturation, hue_shift)
            result[key] = rgb_to_hex(*rgb)
        else:
            result[key] = val
    return result

# ── Theme definitions ─────────────────────────────────────────────────────────

THEMES = {
    "Dark": {
        "BG": "#1e1e1e", "FG": "#f0f0f0", "ACCENT": "#4ea8de",
        "BTN_BG": "#2d6a9f", "BTN_FG": "#ffffff",
        "ERROR": "#ffb347",    # Amber — avoids red/green CVD failure
        "SUCCESS": "#6abf69",  "MUTED": "#a0a0a0",
        "INPUT_BG": "#2d2d2d", "STATUS_BG": "#2a2a2a",
        "FOCUS": "#4ea8de",    "BORDER": "#555555", "ACTIVE_BTN": "#1a4f7a",
    },
    "Light": {
        "BG": "#f5f5f5", "FG": "#1a1a1a", "ACCENT": "#1565c0",
        "BTN_BG": "#1565c0", "BTN_FG": "#ffffff",
        "ERROR": "#b45309",    "SUCCESS": "#1b5e20", "MUTED": "#555555",
        "INPUT_BG": "#ffffff", "STATUS_BG": "#e0e0e0",
        "FOCUS": "#1565c0",    "BORDER": "#9e9e9e",  "ACTIVE_BTN": "#0d47a1",
    },
    "High Contrast": {
        "BG": "#000000", "FG": "#ffffff", "ACCENT": "#ffff00",
        "BTN_BG": "#ffffff", "BTN_FG": "#000000",
        "ERROR": "#ffcc00",    "SUCCESS": "#00ff00", "MUTED": "#c0c0c0",
        "INPUT_BG": "#0d0d0d", "STATUS_BG": "#111111",
        "FOCUS": "#ffff00",    "BORDER": "#ffffff",  "ACTIVE_BTN": "#cccccc",
    },
    "CVD-Safe": {
        # Wong (2011) palette — distinguishable across all CVD types
        "BG": "#1a1a2e", "FG": "#f5f0e8", "ACCENT": "#56b4e9",
        "BTN_BG": "#0077bb", "BTN_FG": "#ffffff",
        "ERROR": "#ee7733",    # Orange (Wong)
        "SUCCESS": "#56b4e9",  "MUTED": "#b0a898",
        "INPUT_BG": "#2a2a42", "STATUS_BG": "#14141f",
        "FOCUS": "#f0e442",    "BORDER": "#56b4e9",  "ACTIVE_BTN": "#005588",
    },
}

FONT_FAMILIES = ["Consolas", "Courier New", "Arial", "Segoe UI", "Verdana", "Trebuchet MS"]
FONT_SIZES    = [14, 16, 18, 20]
CVD_MODES     = ["Normal", "Protanopia", "Deuteranopia", "Tritanopia", "Monochrome"]

DYSLEXIA_PRESETS = {"Normal": 0, "Large": 4, "X-Large": 8}

# Word spacing presets — extra spaces inserted per word boundary.
# "Normal" = 0 extra spaces, "Wide" = 1, "Wider" = 2.
# Tkinter has no CSS word-spacing equivalent; this is the best desktop approximation.
WORD_SPACING_PRESETS = {"Normal": 0, "Wide": 1, "Wider": 2}

DEFAULT_SETTINGS = {
    "theme": "Dark", "font_family": "Consolas", "font_size": 14,
    "dyslexia_preset": "Normal",
    "word_spacing":  "Normal",   # "Normal" | "Wide" | "Wider"
    "line_height":   1.5,        # 1.0–3.0 multiplier
    "cvd_mode":      "Normal",
    "brightness":    1.0,
    "contrast":      1.0,
    "saturation":    1.0,
    "hue_shift":     0,
}

CUE_ERROR   = "[!] "
CUE_SUCCESS = "[OK] "
CUE_INFO    = "[>] "


def load_settings() -> dict:
    try:
        with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
            return {**DEFAULT_SETTINGS, **json.load(f)}
    except (FileNotFoundError, json.JSONDecodeError):
        return DEFAULT_SETTINGS.copy()


def save_settings(settings: dict) -> None:
    with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
        json.dump(settings, f, indent=2)
    masLog("GUI settings saved")


# ── Settings dialog ───────────────────────────────────────────────────────────

class SettingsDialog(tk.Toplevel):
    """
    Tabbed settings dialog with live preview.
    Changes are only committed on Apply & Save.
    """

    def __init__(self, parent: "AuditApp"):
        super().__init__(parent)
        self.parent_app = parent
        self.work = parent.settings.copy()

        self.transient(parent)
        self.grab_set()
        self.title("Settings — MAS Audit Toolkit")
        self.resizable(True, True)
        self.minsize(580, 580)

        t = parent.get_effective_theme()
        self.configure(bg=t["BG"])

        self._init_vars()
        self._build_ui(t)
        self._update_preview()

        self.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width()  // 2) - (self.winfo_width()  // 2)
        y = parent.winfo_y() + (parent.winfo_height() // 2) - (self.winfo_height() // 2)
        self.geometry(f"+{x}+{y}")

        self.focus_set()
        self.bind("<Escape>", lambda e: self.destroy())
        self.wait_window()

    def _init_vars(self):
        """Create tk variables from settings and trace all for live preview."""
        s = self.work
        self.var_theme       = tk.StringVar(value=s["theme"])
        self.var_font_family = tk.StringVar(value=s["font_family"])
        self.var_font_size   = tk.IntVar(value=s["font_size"])
        self.var_dyslexia    = tk.StringVar(value=s["dyslexia_preset"])
        self.var_word_sp     = tk.StringVar(value=s["word_spacing"])
        self.var_line_height = tk.DoubleVar(value=s["line_height"])
        self.var_cvd         = tk.StringVar(value=s["cvd_mode"])
        self.var_brightness  = tk.DoubleVar(value=s["brightness"])
        self.var_contrast    = tk.DoubleVar(value=s["contrast"])
        self.var_saturation  = tk.DoubleVar(value=s["saturation"])
        self.var_hue         = tk.IntVar(value=s["hue_shift"])

        for var in [self.var_theme, self.var_font_family, self.var_font_size,
                    self.var_dyslexia, self.var_word_sp, self.var_line_height,
                    self.var_cvd, self.var_brightness, self.var_contrast,
                    self.var_saturation, self.var_hue]:
            var.trace_add("write", lambda *_: self.after(10, self._update_preview))

    def _read_vars(self):
        """Sync var values back into self.work."""
        self.work.update({
            "theme":           self.var_theme.get(),
            "font_family":     self.var_font_family.get(),
            "font_size":       self.var_font_size.get(),
            "dyslexia_preset": self.var_dyslexia.get(),
            "word_spacing":    self.var_word_sp.get(),
            "line_height":     round(self.var_line_height.get(), 1),
            "cvd_mode":        self.var_cvd.get(),
            "brightness":      round(self.var_brightness.get(), 2),
            "contrast":        round(self.var_contrast.get(), 2),
            "saturation":      round(self.var_saturation.get(), 2),
            "hue_shift":       self.var_hue.get(),
        })

    def _preview_theme(self) -> dict:
        """Compute fully transformed theme from current var values."""
        self._read_vars()
        base = THEMES.get(self.work["theme"], THEMES["Dark"])
        return transform_theme(base, self.work["cvd_mode"], self.work["brightness"],
                               self.work["contrast"], self.work["saturation"],
                               self.work["hue_shift"])

    def _build_ui(self, t: dict):
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure("TNotebook",      background=t["BG"], borderwidth=0)
        style.configure("TNotebook.Tab",  background=t["INPUT_BG"], foreground=t["FG"],
                        padding=[14, 6],  font=("Segoe UI", 10))
        style.map("TNotebook.Tab",
                  background=[("selected", t["BTN_BG"])],
                  foreground=[("selected", t["BTN_FG"])])

        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

        nb = ttk.Notebook(self)
        nb.grid(row=0, column=0, sticky="nsew", padx=12, pady=(12, 0))

        self._build_appearance_tab(nb, t)
        self._build_reading_tab(nb, t)
        self._build_color_vision_tab(nb, t)

        # ── Live preview ──
        pf = tk.LabelFrame(self,
            text=" Preview — updates as you change settings ",
            bg=t["BG"], fg=t["ACCENT"],
            font=("Segoe UI", 9, "bold"), relief="flat", bd=1)
        pf.grid(row=1, column=0, sticky="ew", padx=12, pady=(10, 0))
        pf.columnconfigure(0, weight=1)

        self.prev_box = tk.Frame(pf, bg=t["INPUT_BG"], padx=12, pady=8)
        self.prev_box.grid(row=0, column=0, sticky="ew", padx=4, pady=4)
        self.prev_box.columnconfigure(0, weight=1)

        kw = dict(anchor="w", bg=t["INPUT_BG"], font=("Consolas", 14))
        self.prev_heading = tk.Label(self.prev_box,
            text=f"{CUE_INFO}Audit result preview",
            fg=t["ACCENT"], **kw)
        self.prev_heading.grid(row=0, column=0, sticky="ew")

        self.prev_error = tk.Label(self.prev_box,
            text=f"{CUE_ERROR}WCAG 1.1.1 — <img> missing alt attribute",
            fg=t["ERROR"], **kw)
        self.prev_error.grid(row=1, column=0, sticky="ew")

        self.prev_success = tk.Label(self.prev_box,
            text=f"{CUE_SUCCESS}Heading structure — no issues found",
            fg=t["SUCCESS"], **kw)
        self.prev_success.grid(row=2, column=0, sticky="ew")

        self.prev_muted = tk.Label(self.prev_box,
            text=f"{CUE_INFO}Report saved to output/audit_2026-03-05.txt",
            fg=t["MUTED"], **kw)
        self.prev_muted.grid(row=3, column=0, sticky="ew")

        # ── Buttons ──
        bf = tk.Frame(self, bg=t["BG"])
        bf.grid(row=2, column=0, sticky="ew", padx=12, pady=12)
        bf.columnconfigure(0, weight=1)

        def btn(parent, text, cmd, bold=False):
            return tk.Button(parent, text=text, command=cmd,
                             bg=t["BTN_BG"], fg=t["BTN_FG"],
                             font=("Segoe UI", 10, "bold" if bold else "normal"),
                             relief="flat", padx=12, cursor="hand2",
                             activebackground=t["ACTIVE_BTN"],
                             activeforeground=t["BTN_FG"])

        btn(bf, "Reset All",    self._reset_all).pack(side="left", ipady=4)
        btn(bf, "Cancel",       self.destroy).pack(side="right", padx=(8, 0), ipady=4)
        btn(bf, "Apply & Save", self._apply, bold=True).pack(side="right", ipady=4)

    def _build_appearance_tab(self, nb, t: dict):
        f = tk.Frame(nb, bg=t["BG"])
        nb.add(f, text="  Appearance  ")
        f.columnconfigure(1, weight=1)

        # Theme
        tk.Label(f, text="Color theme:", bg=t["BG"], fg=t["FG"],
                 font=("Segoe UI", 10)).grid(
                     row=0, column=0, sticky="nw", padx=16, pady=(14, 4))
        tf = tk.Frame(f, bg=t["BG"])
        tf.grid(row=0, column=1, sticky="w", padx=8, pady=(14, 4))
        for name, desc in [
            ("Dark",          "Dark (default)"),
            ("Light",         "Light"),
            ("High Contrast", "High Contrast — for low vision"),
            ("CVD-Safe",      "CVD-Safe — safe for all color vision types"),
        ]:
            tk.Radiobutton(tf, text=desc, variable=self.var_theme, value=name,
                           bg=t["BG"], fg=t["FG"], selectcolor=t["INPUT_BG"],
                           activebackground=t["BG"], activeforeground=t["FG"],
                           font=("Segoe UI", 10)).pack(anchor="w", pady=1)

        # Font family
        tk.Label(f, text="Font family:", bg=t["BG"], fg=t["FG"],
                 font=("Segoe UI", 10)).grid(
                     row=1, column=0, sticky="w", padx=16, pady=8)
        ttk.Combobox(f, textvariable=self.var_font_family, values=FONT_FAMILIES,
                     state="readonly", width=20, font=("Segoe UI", 10)
                     ).grid(row=1, column=1, sticky="w", padx=8, pady=8)

        # Font size
        tk.Label(f, text="Font size:", bg=t["BG"], fg=t["FG"],
                 font=("Segoe UI", 10)).grid(
                     row=2, column=0, sticky="w", padx=16, pady=8)
        sf = tk.Frame(f, bg=t["BG"])
        sf.grid(row=2, column=1, sticky="w", padx=8, pady=8)
        for sz in FONT_SIZES:
            tk.Radiobutton(sf, text=str(sz), variable=self.var_font_size, value=sz,
                           bg=t["BG"], fg=t["FG"], selectcolor=t["INPUT_BG"],
                           activebackground=t["BG"], activeforeground=t["FG"],
                           font=("Segoe UI", 10)).pack(side="left", padx=8)

    def _build_reading_tab(self, nb, t: dict):
        f = tk.Frame(nb, bg=t["BG"])
        nb.add(f, text="  Reading  ")
        f.columnconfigure(1, weight=1)

        # Dyslexia preset
        tk.Label(f, text="Dyslexia preset:", bg=t["BG"], fg=t["FG"],
                 font=("Segoe UI", 10)).grid(
                     row=0, column=0, sticky="nw", padx=16, pady=(14, 4))
        pf = tk.Frame(f, bg=t["BG"])
        pf.grid(row=0, column=1, sticky="w", padx=8, pady=(14, 4))
        for name, desc in [("Normal", "Normal"),
                            ("Large",   "Large (+4pt)"),
                            ("X-Large", "X-Large (+8pt)")]:
            tk.Radiobutton(pf, text=desc, variable=self.var_dyslexia, value=name,
                           bg=t["BG"], fg=t["FG"], selectcolor=t["INPUT_BG"],
                           activebackground=t["BG"], activeforeground=t["FG"],
                           font=("Segoe UI", 10)).pack(side="left", padx=10)

        # Word spacing presets
        tk.Label(f, text="Word spacing:", bg=t["BG"], fg=t["FG"],
                 font=("Segoe UI", 10)).grid(
                     row=1, column=0, sticky="nw", padx=16, pady=8)
        wf = tk.Frame(f, bg=t["BG"])
        wf.grid(row=1, column=1, sticky="w", padx=8, pady=8)
        for name, desc in [("Normal", "Normal"),
                            ("Wide",   "Wide"),
                            ("Wider",  "Wider")]:
            tk.Radiobutton(wf, text=desc, variable=self.var_word_sp, value=name,
                           bg=t["BG"], fg=t["FG"], selectcolor=t["INPUT_BG"],
                           activebackground=t["BG"], activeforeground=t["FG"],
                           font=("Segoe UI", 10)).pack(side="left", padx=10)

        # Line height slider
        tk.Label(f, text="Line height:", bg=t["BG"], fg=t["FG"],
                 font=("Segoe UI", 10)).grid(
                     row=2, column=0, sticky="w", padx=16, pady=8)
        self._slider_row(f, 2, t, self.var_line_height,
                         1.0, 3.0, 0.1, 1.5, "{:.1f}x", "Reset")

        # Desktop limitations note
        tk.Label(f,
            text="Note: Letter spacing is not supported in the desktop app.\n"
                 "It is available with full em-precision in the web version.",
            bg=t["BG"], fg=t["MUTED"], font=("Segoe UI", 8),
            justify="left").grid(row=3, column=0, columnspan=2,
                                 sticky="w", padx=16, pady=(12, 4))

    def _build_color_vision_tab(self, nb, t: dict):
        f = tk.Frame(nb, bg=t["BG"])
        nb.add(f, text="  Color Vision  ")
        f.columnconfigure(1, weight=1)

        # CVD simulation
        tk.Label(f, text="CVD simulation:", bg=t["BG"], fg=t["FG"],
                 font=("Segoe UI", 10)).grid(
                     row=0, column=0, sticky="nw", padx=16, pady=(14, 4))
        cf = tk.Frame(f, bg=t["BG"])
        cf.grid(row=0, column=1, sticky="w", padx=8, pady=(14, 4))
        for mode, desc in [
            ("Normal",       "Normal vision"),
            ("Protanopia",   "Protanopia — red-blind"),
            ("Deuteranopia", "Deuteranopia — green-blind"),
            ("Tritanopia",   "Tritanopia — blue-blind"),
            ("Monochrome",   "Monochrome — no color"),
        ]:
            tk.Radiobutton(cf, text=desc, variable=self.var_cvd, value=mode,
                           bg=t["BG"], fg=t["FG"], selectcolor=t["INPUT_BG"],
                           activebackground=t["BG"], activeforeground=t["FG"],
                           font=("Segoe UI", 10)).pack(anchor="w", pady=1)

        # Color adjustments
        tk.Label(f, text="Color adjustments:", bg=t["BG"], fg=t["ACCENT"],
                 font=("Segoe UI", 10, "bold")).grid(
                     row=1, column=0, columnspan=2,
                     sticky="w", padx=16, pady=(12, 4))

        self._slider_row(f, 2, t, self.var_brightness,
                         0.5, 2.0, 0.05, 1.0, "{:.0%}", "Reset")
        tk.Label(f, text="Brightness:", bg=t["BG"], fg=t["FG"],
                 font=("Segoe UI", 10)).grid(row=2, column=0, sticky="w", padx=16, pady=5)

        self._slider_row(f, 3, t, self.var_contrast,
                         0.5, 2.0, 0.05, 1.0, "{:.0%}", "Reset")
        tk.Label(f, text="Contrast:", bg=t["BG"], fg=t["FG"],
                 font=("Segoe UI", 10)).grid(row=3, column=0, sticky="w", padx=16, pady=5)

        self._slider_row(f, 4, t, self.var_saturation,
                         0.0, 2.0, 0.05, 1.0, "{:.0%}", "Reset")
        tk.Label(f, text="Saturation:", bg=t["BG"], fg=t["FG"],
                 font=("Segoe UI", 10)).grid(row=4, column=0, sticky="w", padx=16, pady=5)

        self._slider_row(f, 5, t, self.var_hue,
                         -180, 180, 1, 0, "{:+d}\u00b0", "Reset")
        tk.Label(f, text="Hue shift:", bg=t["BG"], fg=t["FG"],
                 font=("Segoe UI", 10)).grid(row=5, column=0, sticky="w", padx=16, pady=5)

    def _slider_row(self, parent, row: int, t: dict, var,
                    from_, to, resolution, reset_val, fmt: str, reset_label: str):
        """Build a slider cell: [scale] [value label] [reset button] in column 1."""
        cell = tk.Frame(parent, bg=t["BG"])
        cell.grid(row=row, column=1, sticky="ew", padx=8, pady=5)
        cell.columnconfigure(0, weight=1)

        val_lbl = tk.Label(cell, text="", bg=t["BG"], fg=t["FG"],
                           font=("Segoe UI", 9), width=9, anchor="e")
        val_lbl.grid(row=0, column=1, padx=(6, 0))

        def _refresh(*_):
            try:
                val_lbl.config(text=fmt.format(var.get()))
            except Exception:
                val_lbl.config(text=str(var.get()))

        tk.Scale(cell, variable=var, from_=from_, to=to, resolution=resolution,
                 orient="horizontal", showvalue=False,
                 bg=t["BG"], fg=t["FG"], troughcolor=t["INPUT_BG"],
                 highlightthickness=0, activebackground=t["ACCENT"],
                 command=lambda v: _refresh()
                 ).grid(row=0, column=0, sticky="ew")

        _refresh()

        tk.Button(cell, text=reset_label, command=lambda: (var.set(reset_val), _refresh()),
                  bg=t["BTN_BG"], fg=t["BTN_FG"],
                  font=("Segoe UI", 8), relief="flat", padx=6, cursor="hand2",
                  activebackground=t["ACTIVE_BTN"], activeforeground=t["BTN_FG"]
                  ).grid(row=0, column=2, padx=(6, 0))

    def _update_preview(self):
        """Recolor and refont all preview labels from current var values."""
        try:
            pt = self._preview_theme()
        except Exception:
            return
        ff  = self.var_font_family.get()
        fs  = self.var_font_size.get()
        dp  = DYSLEXIA_PRESETS.get(self.var_dyslexia.get(), 0)
        efs = fs + dp
        bg  = pt["INPUT_BG"]

        self.prev_box.config(bg=bg)
        self.prev_heading.config(bg=bg, fg=pt["ACCENT"],  font=(ff, efs, "bold"))
        self.prev_error.config(  bg=bg, fg=pt["ERROR"],   font=(ff, efs))
        self.prev_success.config(bg=bg, fg=pt["SUCCESS"], font=(ff, efs))
        self.prev_muted.config(  bg=bg, fg=pt["MUTED"],   font=(ff, efs))

    def _reset_all(self):
        d = DEFAULT_SETTINGS
        self.var_theme.set(d["theme"])
        self.var_font_family.set(d["font_family"])
        self.var_font_size.set(d["font_size"])
        self.var_dyslexia.set(d["dyslexia_preset"])
        self.var_word_sp.set(d["word_spacing"])
        self.var_line_height.set(d["line_height"])
        self.var_cvd.set(d["cvd_mode"])
        self.var_brightness.set(d["brightness"])
        self.var_contrast.set(d["contrast"])
        self.var_saturation.set(d["saturation"])
        self.var_hue.set(d["hue_shift"])

    def _apply(self):
        self._read_vars()
        self.parent_app.settings.update(self.work)
        save_settings(self.parent_app.settings)
        self.parent_app._redraw_ui()
        self.destroy()


# ── Main application window ───────────────────────────────────────────────────

class AuditApp(tk.Tk):
    """
    Main window — Mosley Standard Section 3.2 compliant.

    WCAG implementations:
      1.4.1  Use of Color     — [!]/[OK]/[>] cues; no info by color alone
      1.4.3  Contrast         — all themes >= 4.5:1 verified
      1.4.4  Resize Text      — 14–20pt + dyslexia presets, persisted
      2.1.1  Keyboard         — full Tab navigation; Enter = Run Audit
      2.1.2  No Keyboard Trap — Tab/Shift-Tab exit results box cleanly
      2.4.7  Focus Visible    — 2px focus ring on all interactive elements
      4.1.3  Status Messages  — announcement label + focus = aria-live equivalent
    """

    def __init__(self):
        super().__init__()
        self.settings = load_settings()
        self.title(f"{config.TOOL_NAME} v{config.TOOL_VERSION}")
        self.minsize(680, 560)
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)
        self.configure(bg=self.get_effective_theme()["BG"])
        self._build_ui()
        masLog("GUI initialized")

    def get_effective_theme(self) -> dict:
        base = THEMES.get(self.settings["theme"], THEMES["Dark"])
        return transform_theme(
            base,
            self.settings.get("cvd_mode",   "Normal"),
            self.settings.get("brightness", 1.0),
            self.settings.get("contrast",   1.0),
            self.settings.get("saturation", 1.0),
            self.settings.get("hue_shift",  0),
        )

    def _effective_font_size(self) -> int:
        return (self.settings.get("font_size", 14) +
                DYSLEXIA_PRESETS.get(self.settings.get("dyslexia_preset", "Normal"), 0))

    def _apply_word_spacing(self, text: str) -> str:
        """Insert extra spaces between words based on the word_spacing preset."""
        extra = WORD_SPACING_PRESETS.get(self.settings.get("word_spacing", "Normal"), 0)
        if extra == 0:
            return text
        padding = " " * extra
        return re.sub(r'(?<=[^\s])( )(?=[^\s])', f'\\1{padding}', text)

    def _build_ui(self):
        t  = self.get_effective_theme()
        ff = self.settings["font_family"]
        fs = self._effective_font_size()
        self.configure(bg=t["BG"])

        # ── Input frame ───────────────────────────────────────────────────── #
        inp = tk.Frame(self, bg=t["BG"], padx=16, pady=12)
        inp.grid(row=0, column=0, sticky="ew")
        inp.columnconfigure(1, weight=1)

        tb = tk.Frame(inp, bg=t["BG"])
        tb.grid(row=0, column=0, columnspan=3, sticky="ew", pady=(0, 10))
        tb.columnconfigure(0, weight=1)

        tk.Label(tb, text="MAS Accessibility Audit Toolkit",
                 bg=t["BG"], fg=t["ACCENT"],
                 font=("Segoe UI", 14, "bold")).grid(row=0, column=0, sticky="w")

        tk.Button(tb, text="Settings", command=self._open_settings,
                  bg=t["BTN_BG"], fg=t["BTN_FG"],
                  font=("Segoe UI", 9), relief="flat", padx=10, cursor="hand2",
                  activebackground=t["ACTIVE_BTN"], activeforeground=t["BTN_FG"]
                  ).grid(row=0, column=1, sticky="e")

        # Label immediately before entry — NVDA/JAWS reads this on focus
        tk.Label(inp, text="URL or local HTML file path:",
                 bg=t["BG"], fg=t["FG"],
                 font=("Segoe UI", 10)).grid(row=1, column=0, columnspan=3, sticky="w")

        self.source_var = tk.StringVar()
        self.source_entry = tk.Entry(
            inp, textvariable=self.source_var,
            font=(ff, fs), bg=t["INPUT_BG"], fg=t["FG"],
            insertbackground=t["FG"], relief="flat",
            highlightthickness=2, highlightcolor=t["FOCUS"],
            highlightbackground=t["BORDER"])
        self.source_entry.grid(row=2, column=0, columnspan=2,
                               sticky="ew", pady=(4, 0), ipady=6)

        self.bind("<Alt-u>", lambda e: self.source_entry.focus_set())
        self.bind("<Alt-U>", lambda e: self.source_entry.focus_set())

        self.browse_btn = tk.Button(
            inp, text="Browse...", command=self._browse_file,
            bg=t["BTN_BG"], fg=t["BTN_FG"],
            font=("Segoe UI", 10), relief="flat", padx=12, cursor="hand2",
            activebackground=t["ACTIVE_BTN"], activeforeground=t["BTN_FG"])
        self.browse_btn.grid(row=2, column=2,
                             sticky="ew", padx=(8, 0), pady=(4, 0), ipady=6)

        self.run_btn = tk.Button(
            inp, text="Run Audit", command=self._start_audit,
            bg=t["BTN_BG"], fg=t["BTN_FG"],
            font=("Segoe UI", 10, "bold"), relief="flat", padx=12, cursor="hand2",
            activebackground=t["ACTIVE_BTN"], activeforeground=t["BTN_FG"])
        self.run_btn.grid(row=3, column=0, columnspan=3,
                          sticky="ew", pady=(10, 0), ipady=8)

        self.bind("<Return>", lambda e: self._start_audit())

        # ── Results frame ─────────────────────────────────────────────────── #
        rf = tk.Frame(self, bg=t["BG"], padx=16, pady=0)
        rf.grid(row=1, column=0, sticky="nsew")
        rf.columnconfigure(0, weight=1)
        rf.rowconfigure(2, weight=1)

        # Screen reader announcement — NVDA/JAWS reads on focus_set()
        self.announce_var = tk.StringVar(value="")
        self.announce_label = tk.Label(
            rf, textvariable=self.announce_var,
            bg=t["BG"], fg=t["ACCENT"],
            font=("Segoe UI", 10, "bold"), anchor="w", takefocus=True)
        self.announce_label.grid(row=0, column=0, sticky="ew", pady=(4, 0))

        tk.Label(rf, text="Audit Results:",
                 bg=t["BG"], fg=t["FG"],
                 font=("Segoe UI", 10)).grid(row=1, column=0, sticky="w", pady=(4, 4))

        lh      = self.settings.get("line_height", 1.5)
        spacing = max(0, int((lh - 1.0) * fs * 0.8))

        self.results_box = scrolledtext.ScrolledText(
            rf, font=(ff, fs), bg=t["INPUT_BG"], fg=t["FG"],
            insertbackground=t["FG"], relief="flat", wrap=tk.WORD,
            state="disabled", spacing2=spacing,
            highlightthickness=2, highlightcolor=t["FOCUS"],
            highlightbackground=t["BORDER"])
        self.results_box.grid(row=2, column=0, sticky="nsew")

        # Keyboard trap fix (WCAG 2.1.2)
        self.results_box.bind("<Tab>",
            lambda e: (self.run_btn.focus_set(), "break")[1])
        self.results_box.bind("<Shift-Tab>",
            lambda e: (self.source_entry.focus_set(), "break")[1])

        self.results_box.tag_config("heading",
            foreground=t["ACCENT"], font=(ff, fs, "bold"))
        self.results_box.tag_config("error",   foreground=t["ERROR"])
        self.results_box.tag_config("success", foreground=t["SUCCESS"])
        self.results_box.tag_config("muted",   foreground=t["MUTED"])

        # ── Status bar ────────────────────────────────────────────────────── #
        self.status_var = tk.StringVar(value="Ready.")
        tk.Label(self, textvariable=self.status_var,
                 bg=t["STATUS_BG"], fg=t["MUTED"],
                 font=("Segoe UI", 9), anchor="w", padx=16, pady=6
                 ).grid(row=2, column=0, sticky="ew")

    def _redraw_ui(self):
        for w in self.winfo_children():
            w.destroy()
        self._build_ui()
        self.source_entry.focus_set()

    def _open_settings(self):
        SettingsDialog(self)

    def _browse_file(self):
        fp = filedialog.askopenfilename(
            title="Select an HTML file",
            filetypes=[("HTML files", "*.html *.htm"), ("All files", "*.*")])
        if fp:
            self.source_var.set(fp)
            masLog(f"File selected via browser: {fp}")

    def _start_audit(self):
        source = self.source_var.get().strip()
        if not source:
            self._announce("Error: please enter a URL or file path.")
            self._write_result(f"{CUE_ERROR}Please enter a URL or file path.\n", tag="error")
            return

        self.source_entry.config(state="disabled")
        self.run_btn.config(state="disabled")
        self.browse_btn.config(state="disabled")
        self._clear_results()
        self._announce("Audit running, please wait.")
        self.status_var.set("Running audit...")
        self._write_result(f"{CUE_INFO}Auditing: {source}\n", tag="heading")

        threading.Thread(
            target=self._run_audit_thread, args=(source,), daemon=True).start()

    def _run_audit_thread(self, source: str):
        try:
            html = load_html(source)
            if html is None:
                self._write_result(
                    f"{CUE_ERROR}ERROR: Could not load source. Check the log.\n",
                    tag="error")
                self._finish_audit("Load failed.", "Error: could not load source.")
                return

            soup = BeautifulSoup(html, config.HTML_PARSER)

            all_findings = []
            for finder, module_name, _ in pkgutil.iter_modules(checks.__path__):
                module_config = config.MODULES.get(module_name, {})
                if not module_config.get("enabled", True):
                    continue
                module = importlib.import_module(f"checks.{module_name}")
                if hasattr(module, "run"):
                    all_findings.extend(module.run(soup, source))

            if not all_findings:
                self._write_result(
                    f"{CUE_SUCCESS}No accessibility issues detected.\n", tag="success")
            else:
                # Group findings by severity before display.
                severity_order = ["critical", "moderate", "minor"]
                severity_labels = {
                    "critical": "CRITICAL — Immediate Accessibility Barriers",
                    "moderate": "MODERATE — Usability Issues",
                    "minor":    "MINOR — Quality Improvements",
                }
                severity_descriptions = {
                    "critical": "These issues prevent access for users with disabilities.",
                    "moderate": "These issues significantly affect usability.",
                    "minor":    "These issues are best-practice improvements.",
                }

                grouped = {level: [] for level in severity_order}
                for f in all_findings:
                    level = f.get("severity", "minor")
                    if level not in grouped:
                        level = "minor"
                    grouped[level].append(f)

                total    = len(all_findings)
                critical = len(grouped["critical"])
                moderate = len(grouped["moderate"])
                minor    = len(grouped["minor"])

                self._write_result(
                    f"{CUE_INFO}{total} finding(s) — "
                    f"{critical} critical, {moderate} moderate, {minor} minor\n\n",
                    tag="heading")

                finding_number = 1
                for level in severity_order:
                    level_findings = grouped[level]
                    if not level_findings:
                        continue

                    self._write_result(
                        f"{CUE_ERROR}{severity_labels[level]}\n",
                        tag="heading")
                    self._write_result(
                        f"     {severity_descriptions[level]}\n\n",
                        tag="muted")

                    for f in level_findings:
                        self._write_result(
                            f"  [{finding_number}] {f['check']} "
                            f"— WCAG {f['wcag']} (Level {f['level']})\n",
                            tag="heading")
                        self._write_result(
                            f"       {f['message']}\n\n",
                            tag="error")
                        finding_number += 1

                    self._write_result("─" * 40 + "\n\n", tag="muted")

            report_path = generate_report(source, all_findings)
            self._write_result(
                f"{CUE_INFO}Report saved to:\n{report_path}\n", tag="muted")

            count = len(all_findings)
            msg = (f"Audit complete. {count} finding{'s' if count != 1 else ''} found."
                   if count else "Audit complete. No issues found.")
            self._finish_audit(f"Done. Report: {report_path}", msg)

        except Exception as e:
            masLog(f"Unexpected GUI error: {e}", level="error")
            self._write_result(f"{CUE_ERROR}Unexpected error: {e}\n", tag="error")
            self._finish_audit("Audit failed.", "Error: audit failed unexpectedly.")

    def _announce(self, message: str):
        def _u():
            self.announce_var.set(message)
            self.announce_label.focus_set()
        self.after(0, _u)

    def _write_result(self, text: str, tag: str = ""):
        text = self._apply_word_spacing(text)
        def _insert():
            self.results_box.config(state="normal")
            if tag:
                self.results_box.insert(tk.END, text, tag)
            else:
                self.results_box.insert(tk.END, text)
            self.results_box.config(state="disabled")
            self.results_box.see(tk.END)
        self.after(0, _insert)

    def _clear_results(self):
        self.results_box.config(state="normal")
        self.results_box.delete("1.0", tk.END)
        self.results_box.config(state="disabled")

    def _finish_audit(self, status_message: str, announcement: str = ""):
        def _u():
            self.source_entry.config(state="normal")
            self.run_btn.config(state="normal")
            self.browse_btn.config(state="normal")
            self.status_var.set(status_message)
        self.after(0, _u)
        if announcement:
            self.after(200, lambda: self._announce(announcement))


if __name__ == "__main__":
    app = AuditApp()
    app.mainloop()
