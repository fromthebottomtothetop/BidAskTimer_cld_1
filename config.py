# -*- coding: utf-8 -*-
import json
import os
from typing import Tuple

from model import AppConfig, AppState
from themes import THEME_ORDER, get_theme

# Scale mode constants
SCALE_RELATIVE = 0   # groesster Balken = volle Hoehe (Original)
SCALE_ABSOLUTE = 1   # Bid+Ask Summe = 100%
SCALE_FIXED    = 3   # beide Balken gegen konfigurierbares festes Maximum


def get_app_folder(folder_name: str = "BidAskTimer_cld_1") -> str:
    appdata_dir = os.getenv("APPDATA")
    base = appdata_dir if appdata_dir else os.path.dirname(os.path.abspath(__file__))
    app_folder = os.path.join(base, folder_name)
    if not os.path.exists(app_folder):
        try:
            os.makedirs(app_folder, exist_ok=True)
            print(f"Ordner erstellt: {app_folder}")
        except OSError as e:
            print(f"Fehler beim Erstellen des Ordners: {e}")
            app_folder = os.path.dirname(os.path.abspath(__file__))
    return app_folder


def get_config_file(app_folder: str, filename: str = "config_BidAskTimer_cld_1.json") -> str:
    return os.path.join(app_folder, filename)


def apply_theme_to_config(cfg: AppConfig, theme_name: str) -> None:
    t = get_theme(theme_name)
    cfg.theme_name       = theme_name
    cfg.color_bg         = t.get("BG",           cfg.color_bg)
    cfg.color_grid       = t.get("GRID",          cfg.color_grid)
    cfg.color_text       = t.get("TEXT",          cfg.color_text)
    cfg.color_btn        = t.get("BTN",           cfg.color_btn)
    cfg.color_btn_hover  = t.get("BTN_HOVER",     cfg.color_btn_hover)
    cfg.color_menu       = t.get("MENU",          cfg.color_menu)
    cfg.color_menu_bg    = t.get("MENU_BG",       cfg.color_menu_bg)
    cfg.color_menu_hover = t.get("MENU_HOVER",    cfg.color_menu_hover)
    cfg.color_grip       = t.get("GRIP",          cfg.color_grip)
    cfg.color_header     = t.get("HEADER",        cfg.color_header)
    cfg.color_input_bg   = t.get("INPUT_BG",      cfg.color_input_bg)
    cfg.color_input_active = t.get("INPUT_ACTIVE",cfg.color_input_active)
    cfg.color_bid        = t.get("BID",           cfg.color_bid)
    cfg.color_ask        = t.get("ASK",           cfg.color_ask)


def load_config(config_file: str, cfg: AppConfig, state: AppState) -> None:
    if not os.path.exists(config_file):
        state.update_menu_first_line(cfg.show_controls)
        return

    try:
        with open(config_file, "r", encoding="utf-8") as f:
            c = json.load(f)
    except Exception as e:
        print(f"Error loading config: {e}")
        state.update_menu_first_line(cfg.show_controls)
        return

    cfg.time_window_seconds   = int(c.get("time_window_seconds",   cfg.time_window_seconds))
    cfg.is_always_on_top      = bool(c.get("is_always_on_top",     cfg.is_always_on_top))
    cfg.show_header           = bool(c.get("show_header",          cfg.show_header))
    cfg.show_cpu_usage        = bool(c.get("show_cpu_usage",       cfg.show_cpu_usage))
    cfg.rounded_corners       = bool(c.get("rounded_corners",      cfg.rounded_corners))
    cfg.show_status_indicator = bool(c.get("show_status_indicator",cfg.show_status_indicator))
    cfg.crypto_mode           = bool(c.get("crypto_mode",          cfg.crypto_mode))
    cfg.show_controls         = bool(c.get("show_controls",        cfg.show_controls))

    if "scale_mode" in c:
        cfg.scale_mode = int(c["scale_mode"])
        if cfg.scale_mode not in (SCALE_RELATIVE, SCALE_ABSOLUTE, SCALE_FIXED):
            cfg.scale_mode = SCALE_RELATIVE
    else:
        if c.get("absolute_scale", False):
            cfg.scale_mode = SCALE_ABSOLUTE
        else:
            cfg.scale_mode = SCALE_RELATIVE

    cfg.fixed_scale_max = float(c.get("fixed_scale_max", 500.0))
    if cfg.fixed_scale_max < 1:
        cfg.fixed_scale_max = 500.0
    cfg.mult_baseline_factor = int(c.get("mult_baseline_factor", 6))
    cfg.mult_threshold       = float(c.get("mult_threshold", 1.5))

    cfg.host     = c.get("host",         cfg.host)
    cfg.port_in  = int(c.get("port",     cfg.port_in))
    cfg.port_out = int(c.get("output_port", cfg.port_out))

    cfg.buffer_size       = int(c.get("buffer_size",         cfg.buffer_size))
    cfg.bar_width_percent = int(c.get("bar_width_percent",   cfg.bar_width_percent))

    cfg.window_x = int(c.get("window_x", cfg.window_x))
    cfg.window_y = int(c.get("window_y", cfg.window_y))
    cfg.window_w = int(c.get("window_w", cfg.window_w))
    cfg.window_h = int(c.get("window_h", cfg.window_h))

    theme = c.get("theme", cfg.theme_name)
    theme = theme if theme in THEME_ORDER else "dark"
    apply_theme_to_config(cfg, theme)

    if "color_bid"  in c: cfg.color_bid  = tuple(c["color_bid"])
    if "color_ask"  in c: cfg.color_ask  = tuple(c["color_ask"])
    if "color_bg"   in c: cfg.color_bg   = tuple(c["color_bg"])
    if "color_grid" in c: cfg.color_grid = tuple(c["color_grid"])
    if "color_text" in c: cfg.color_text = tuple(c["color_text"])
    if "color_btn"  in c: cfg.color_btn  = tuple(c["color_btn"])

    state.update_menu_first_line(cfg.show_controls)
    print("Config loaded.")


def save_config(config_file: str, cfg: AppConfig, window_pos: Tuple[int, int] | None = None) -> None:
    curr_x, curr_y = (cfg.window_x, cfg.window_y)
    if window_pos is not None:
        curr_x, curr_y = window_pos

    c = {
        "time_window_seconds":   cfg.time_window_seconds,
        "is_always_on_top":      cfg.is_always_on_top,
        "show_header":           cfg.show_header,
        "show_cpu_usage":        cfg.show_cpu_usage,
        "rounded_corners":       cfg.rounded_corners,
        "show_status_indicator": cfg.show_status_indicator,
        "crypto_mode":           cfg.crypto_mode,
        "theme":                 cfg.theme_name,
        "show_controls":         cfg.show_controls,
        "scale_mode":            getattr(cfg, "scale_mode",      SCALE_RELATIVE),
        "fixed_scale_max":       getattr(cfg, "fixed_scale_max", 500.0),
        "mult_baseline_factor":  getattr(cfg, "mult_baseline_factor", 6),
        "mult_threshold":        getattr(cfg, "mult_threshold", 1.5),

        "host":         cfg.host,
        "port":         cfg.port_in,
        "output_port":  cfg.port_out,

        "buffer_size":       cfg.buffer_size,
        "bar_width_percent": cfg.bar_width_percent,

        "color_bid":  cfg.color_bid,
        "color_ask":  cfg.color_ask,
        "color_bg":   cfg.color_bg,
        "color_grid": cfg.color_grid,
        "color_text": cfg.color_text,
        "color_btn":  cfg.color_btn,

        "window_x": curr_x,
        "window_y": curr_y,
        "window_w": cfg.window_w,
        "window_h": cfg.window_h,
    }

    try:
        with open(config_file, "w", encoding="utf-8") as f:
            json.dump(c, f)
    except Exception as e:
        print(f"Error saving config: {e}")
