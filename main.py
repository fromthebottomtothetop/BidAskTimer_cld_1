# -*- coding: utf-8 -*-
import sys
import time
import atexit
import ctypes

import pygame
import psutil

from model import AppConfig, AppState
from config import get_app_folder, get_config_file, load_config, save_config, apply_theme_to_config
from win32_window import set_dpi_awareness, init_win32_prototypes, apply_window_hack, toggle_always_on_top, get_window_rect
from net_input import InputServer
from net_output import OutputServer
from ui_layout import calculate_layout
from ui_draw import create_hue_bar, create_sv_overlay, render_all
from ui_events import compute_hover_states, update_cursor, handle_events
from data_processing import process_incoming_data, trim_history, compute_target, smooth_volumes, build_payload


def clamp_window_to_screen(cfg: AppConfig) -> None:
    """
    Checks if the window position is within the visible virtual screen area.
    Supports multi-monitor setups (including monitors left/above the primary).
    Resets position to (100, 100) if the window would be off-screen.
    """
    try:
        user32 = ctypes.windll.user32
        # Virtual screen bounds (all monitors combined)
        virt_x      = user32.GetSystemMetrics(76)   # SM_XVIRTUALSCREEN
        virt_y      = user32.GetSystemMetrics(77)   # SM_YVIRTUALSCREEN
        virt_w      = user32.GetSystemMetrics(78)   # SM_CXVIRTUALSCREEN
        virt_h      = user32.GetSystemMetrics(79)   # SM_CYVIRTUALSCREEN
        virt_right  = virt_x + virt_w
        virt_bottom = virt_y + virt_h

        margin = 50  # at least 50px must be visible

        win_right  = cfg.window_x + cfg.window_w
        win_bottom = cfg.window_y + cfg.window_h

        off_screen = (
            win_right  < virt_x + margin or
            cfg.window_x > virt_right  - margin or
            win_bottom < virt_y + margin or
            cfg.window_y > virt_bottom - margin
        )

        if off_screen:
            print(f"[WARN] Window position ({cfg.window_x}, {cfg.window_y}) is off-screen - "
                  f"resetting to (100, 100). "
                  f"Virtual screen: ({virt_x},{virt_y}) {virt_w}x{virt_h}")
            cfg.window_x = 100
            cfg.window_y = 100

    except Exception as e:
        print(f"[WARN] Could not validate window position: {e}")
        cfg.window_x = 100
        cfg.window_y = 100


def main():
    # Win32 init
    set_dpi_awareness()
    init_win32_prototypes()

    cfg = AppConfig()
    state = AppState()

    # Config path
    app_folder = get_app_folder("BidAskTimer_cld_1")
    config_file = get_config_file(app_folder, "config_BidAskTimer_cld_1.json")
    print(f"Config: {config_file}")

    # Load config + apply theme
    load_config(config_file, cfg, state)
    apply_theme_to_config(cfg, cfg.theme_name)

    # FIX: validate window position before creating the window
    clamp_window_to_screen(cfg)

    # Pygame init
    pygame.init()

    hue_bar_surface = create_hue_bar(cfg.picker_bar_width, cfg.picker_box_size)
    sat_val_overlay = create_sv_overlay(cfg.picker_box_size, cfg.picker_box_size)

    screen = pygame.display.set_mode((cfg.window_w, cfg.window_h), pygame.NOFRAME | pygame.DOUBLEBUF)
    pygame.display.set_caption("BidAskTimer_cld_1")
    clock = pygame.time.Clock()

    font_big = pygame.font.SysFont("Consolas", cfg.font_size_val, bold=True)
    font_std = pygame.font.SysFont("Segoe UI", 16)
    font_small = pygame.font.SysFont("Segoe UI", 12)
    font_micro = pygame.font.SysFont("Consolas", 12)

    # hwnd + window hack
    state.hwnd = pygame.display.get_wm_info().get("window", None)
    if state.hwnd:
        apply_window_hack(state.hwnd, cfg.window_x, cfg.window_y, cfg.window_w, cfg.window_h, cfg.rounded_corners)
        if cfg.is_always_on_top:
            toggle_always_on_top(state.hwnd, True)

    # Servers
    input_server = InputServer(cfg, state)
    output_server = OutputServer(cfg, state)
    input_server.start()
    output_server.start()

    # CPU monitor
    current_process = psutil.Process()
    cpu_check_interval = 1.0

    def on_exit():
        try:
            if state.hwnd:
                x, y, w, h = get_window_rect(state.hwnd)
                cfg.window_x, cfg.window_y = x, y
                cfg.window_w, cfg.window_h = w, h
                save_config(config_file, cfg, (x, y))
            else:
                save_config(config_file, cfg, (cfg.window_x, cfg.window_y))
        except Exception:
            pass
        try:
            input_server.stop()
        except Exception:
            pass
        try:
            output_server.stop()
        except Exception:
            pass

    atexit.register(on_exit)

    # Main loop
    layout_dirty = True
    rects = calculate_layout(cfg, state)

    screen_ref = {"screen": screen}
    frame_count = 0

    while state.running:
        if layout_dirty:
            rects = calculate_layout(cfg, state)
            layout_dirty = False

        # CPU
        if cfg.show_cpu_usage:
            now_t = time.time()
            if now_t - state.last_cpu_check > cpu_check_interval:
                try:
                    raw_pct = current_process.cpu_percent()
                    count = psutil.cpu_count() or 1
                    real_pct = raw_pct / count
                    state.current_cpu_str = f"CPU: {real_pct:.1f}%"
                except Exception:
                    state.current_cpu_str = "CPU: --"
                state.last_cpu_check = now_t
        else:
            state.current_cpu_str = ""

        # Data
        process_incoming_data(cfg, state)
        trim_history(cfg, state)
        target_bid, target_ask = compute_target(cfg, state)
        smooth_volumes(cfg, state, target_bid, target_ask)

        payload = build_payload(cfg, state)
        output_server.maybe_broadcast(payload)

        # Hover / cursor
        mouse_pos = pygame.mouse.get_pos()
        hover_states = compute_hover_states(cfg, state, rects, mouse_pos)
        update_cursor(cfg, state, rects, hover_states, mouse_pos)

        # Events (may recreate screen)
        handle_events(cfg, state, rects, input_server, output_server, screen_ref)
        screen = screen_ref["screen"]

        # If screen recreated, update hwnd + shape
        new_hwnd = pygame.display.get_wm_info().get("window", None)
        if new_hwnd and new_hwnd != state.hwnd:
            state.hwnd = new_hwnd

        # If user requested save, do it with current window pos
        if state.save_requested:
            state.save_requested = False
            try:
                if state.hwnd:
                    x, y, w, h = get_window_rect(state.hwnd)
                    cfg.window_x, cfg.window_y = x, y
                    cfg.window_w, cfg.window_h = w, h
                    save_config(config_file, cfg, (x, y))
                else:
                    save_config(config_file, cfg, (cfg.window_x, cfg.window_y))
            except Exception:
                pass
            layout_dirty = True

        # Draw
        render_all(
            screen, rects, hover_states, cfg, state,
            font_big, font_std, font_small, font_micro,
            hue_bar_surface, sat_val_overlay,
            input_server.client_count()
        )
        pygame.display.flip()

        frame_count += 1
        if frame_count % 60 == 0 and cfg.is_always_on_top and state.hwnd:
            toggle_always_on_top(state.hwnd, True)

        clock.tick(cfg.fps)

    # Shutdown
    input_server.stop()
    output_server.stop()
    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()