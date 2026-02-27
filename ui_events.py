# -*- coding: utf-8 -*-
import pygame
from datetime import datetime

from model import AppConfig, AppState
from themes import next_theme
from config import apply_theme_to_config
from ui_draw import set_picker_from_color, apply_picker_to_active_color
from win32_window import (
    get_window_rect, get_cursor_pos, set_window_pos, set_window_shape, toggle_always_on_top
)


def compute_hover_states(cfg: AppConfig, state: AppState, rects: dict, mouse_pos: tuple[int, int]) -> dict:
    hover = {}
    if state.show_settings_modal:
        hover["save"] = rects["btn_save"].collidepoint(mouse_pos)
        hover["cancel"] = rects["btn_cancel"].collidepoint(mouse_pos)
    elif state.show_advanced_modal:
        if not state.show_buffer_dropdown:
            hover["adv_save"] = rects["adv_save"].collidepoint(mouse_pos)
            hover["adv_cancel"] = rects["adv_cancel"].collidepoint(mouse_pos)
            hover["buf_arrow"] = rects["btn_buf_arrow"].collidepoint(mouse_pos)
            hover["adv_top"] = rects["btn_adv_top"].collidepoint(mouse_pos)
            hover["adv_header"] = rects["btn_adv_header"].collidepoint(mouse_pos)
            hover["adv_cpu"] = rects["btn_adv_cpu"].collidepoint(mouse_pos)
            hover["adv_round"] = rects["btn_adv_round"].collidepoint(mouse_pos)
            hover["adv_status"] = rects["btn_adv_status"].collidepoint(mouse_pos)
            hover["adv_crypto"] = rects["btn_adv_crypto"].collidepoint(mouse_pos)
    elif state.show_color_modal:
        hover["c_save"] = rects["c_save"].collidepoint(mouse_pos)
        hover["c_cancel"] = rects["c_cancel"].collidepoint(mouse_pos)
        hover["c_theme"] = rects["c_theme"].collidepoint(mouse_pos)
    else:
        if cfg.show_controls:
            hover["minus"] = rects["minus"].collidepoint(mouse_pos)
            hover["plus"] = rects["plus"].collidepoint(mouse_pos)
            hover["time_display"] = rects["time_display"].collidepoint(mouse_pos)
        else:
            hover["overlay"] = rects["overlay"].collidepoint(mouse_pos)
        hover["menu"] = rects["menu"].collidepoint(mouse_pos)
    return hover


def update_cursor(cfg: AppConfig, state: AppState, rects: dict, hover: dict, mouse_pos: tuple[int, int]) -> None:
    cursor = pygame.SYSTEM_CURSOR_ARROW
    any_modal_open = state.show_settings_modal or state.show_color_modal or state.show_advanced_modal

    if state.show_settings_modal:
        if hover.get("save") or hover.get("cancel"):
            cursor = pygame.SYSTEM_CURSOR_HAND
        elif rects["inp_host"].collidepoint(mouse_pos) or rects["inp_port"].collidepoint(mouse_pos) or rects["inp_outport"].collidepoint(mouse_pos):
            cursor = pygame.SYSTEM_CURSOR_IBEAM

    elif state.show_advanced_modal:
        if state.show_buffer_dropdown:
            if rects["dd_opt_1"].collidepoint(mouse_pos) or rects["dd_opt_2"].collidepoint(mouse_pos) or rects["dd_opt_3"].collidepoint(mouse_pos):
                cursor = pygame.SYSTEM_CURSOR_HAND
        else:
            if (hover.get("adv_save") or hover.get("adv_cancel") or hover.get("buf_arrow") or
                hover.get("adv_top") or hover.get("adv_header") or hover.get("adv_cpu") or
                hover.get("adv_round") or hover.get("adv_status") or hover.get("adv_crypto")):
                cursor = pygame.SYSTEM_CURSOR_HAND
            elif rects["inp_lerp"].collidepoint(mouse_pos) or rects["inp_buff"].collidepoint(mouse_pos) or rects["inp_width"].collidepoint(mouse_pos):
                cursor = pygame.SYSTEM_CURSOR_IBEAM

    elif state.show_color_modal:
        if (hover.get("c_save") or hover.get("c_cancel") or hover.get("c_theme") or
            rects["c_bid"].collidepoint(mouse_pos) or rects["c_ask"].collidepoint(mouse_pos) or
            rects["c_bg"].collidepoint(mouse_pos) or rects["c_grid"].collidepoint(mouse_pos) or
            rects["c_btn"].collidepoint(mouse_pos) or rects["c_txt"].collidepoint(mouse_pos)):
            cursor = pygame.SYSTEM_CURSOR_HAND
        if rects["p_box"].collidepoint(mouse_pos) or rects["p_bar"].collidepoint(mouse_pos):
            cursor = pygame.SYSTEM_CURSOR_CROSSHAIR

    else:
        if rects["resize"].collidepoint(mouse_pos) or state.resize_active:
            cursor = pygame.SYSTEM_CURSOR_SIZENWSE
        elif hover.get("menu") or hover.get("minus") or hover.get("plus") or hover.get("overlay"):
            cursor = pygame.SYSTEM_CURSOR_HAND
        elif hover.get("time_display") and cfg.show_controls:
            cursor = pygame.SYSTEM_CURSOR_IBEAM
        elif state.show_menu and rects["menu_drop"].collidepoint(mouse_pos):
            cursor = pygame.SYSTEM_CURSOR_HAND

    pygame.mouse.set_cursor(cursor)


def _apply_settings_modal(cfg: AppConfig, state: AppState) -> None:
    cfg.host = state.input_host_str
    try:
        cfg.port_in = int(state.input_port_str)
    except Exception:
        cfg.port_in = 55011
    try:
        cfg.port_out = int(state.input_outport_str)
    except Exception:
        cfg.port_out = 55012
    state.request_save()


def _apply_advanced(cfg: AppConfig, state: AppState) -> None:
    try:
        val = float(state.input_lerp_str)
        if 1.0 <= val <= 100.0:
            cfg.lerp_factor = val / 100.0
    except Exception:
        pass

    try:
        val = int(state.input_buffer_str)
        if val > 64:
            cfg.buffer_size = val
    except Exception:
        pass

    try:
        val = int(state.input_width_str)
        if 10 <= val <= 100:
            cfg.bar_width_percent = val
    except Exception:
        pass

    cfg.is_always_on_top = state.temp_adv_always_on_top
    cfg.show_header = state.temp_adv_show_header
    cfg.show_cpu_usage = state.temp_adv_show_cpu
    cfg.rounded_corners = state.temp_adv_rounded
    cfg.show_status_indicator = state.temp_adv_show_status
    cfg.crypto_mode = state.temp_adv_crypto

    state.request_save()


def handle_events(cfg: AppConfig, state: AppState, rects: dict,
                 input_server, output_server, screen_ref: dict) -> None:
    """
    screen_ref ist dict mit: {"screen": pygame.Surface}
    damit wir bei Resize die Referenz aktualisieren koennen, ohne globale Variablen.
    """
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            state.request_save()
            state.running = False
            return

        if event.type == pygame.KEYDOWN:
            if state.editing_time_window:
                if event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                    try:
                        val = int(state.input_time_str)
                        if val > 0:
                            cfg.time_window_seconds = val
                            state.request_save()
                    except Exception:
                        pass
                    state.editing_time_window = False
                elif event.key == pygame.K_ESCAPE:
                    state.editing_time_window = False
                elif event.key == pygame.K_BACKSPACE:
                    state.input_time_str = state.input_time_str[:-1]
                else:
                    if event.unicode.isdigit() and len(state.input_time_str) < 4:
                        state.input_time_str += event.unicode

            elif state.show_settings_modal:
                if event.key == pygame.K_ESCAPE:
                    state.show_settings_modal = False
                elif event.key == pygame.K_TAB:
                    state.active_input_idx = (state.active_input_idx + 1) % 3
                elif event.key == pygame.K_RETURN:
                    _apply_settings_modal(cfg, state)
                    input_server.restart()
                    output_server.restart()
                    state.show_settings_modal = False
                elif event.key == pygame.K_BACKSPACE:
                    if state.active_input_idx == 0:
                        state.input_host_str = state.input_host_str[:-1]
                    elif state.active_input_idx == 1:
                        state.input_port_str = state.input_port_str[:-1]
                    else:
                        state.input_outport_str = state.input_outport_str[:-1]
                else:
                    if state.active_input_idx == 0:
                        state.input_host_str += event.unicode
                    elif state.active_input_idx == 1:
                        if event.unicode.isdigit():
                            state.input_port_str += event.unicode
                    else:
                        if event.unicode.isdigit():
                            state.input_outport_str += event.unicode

            elif state.show_advanced_modal:
                if event.key == pygame.K_ESCAPE:
                    state.show_advanced_modal = False
                    state.show_buffer_dropdown = False
                elif event.key == pygame.K_TAB:
                    state.active_adv_input_idx = (state.active_adv_input_idx + 1) % 3
                elif event.key == pygame.K_RETURN:
                    _apply_advanced(cfg, state)
                    if state.hwnd:
                        toggle_always_on_top(state.hwnd, cfg.is_always_on_top)
                        set_window_shape(state.hwnd, cfg.window_w, cfg.window_h, cfg.rounded_corners)
                    state.show_advanced_modal = False
                    state.show_buffer_dropdown = False
                elif event.key == pygame.K_BACKSPACE:
                    if state.active_adv_input_idx == 0:
                        state.input_lerp_str = state.input_lerp_str[:-1]
                    elif state.active_adv_input_idx == 1:
                        state.input_buffer_str = state.input_buffer_str[:-1]
                    else:
                        state.input_width_str = state.input_width_str[:-1]
                else:
                    if state.active_adv_input_idx in (0, 1, 2) and event.unicode.isdigit():
                        if state.active_adv_input_idx == 0:
                            state.input_lerp_str += event.unicode
                        elif state.active_adv_input_idx == 1:
                            state.input_buffer_str += event.unicode
                        elif state.active_adv_input_idx == 2:
                            if len(state.input_width_str) < 3:
                                state.input_width_str += event.unicode

            elif state.show_color_modal:
                if event.key == pygame.K_ESCAPE:
                    state.show_color_modal = False

        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            # Click-out save for time edit
            if state.editing_time_window and not rects["time_display"].collidepoint(event.pos):
                try:
                    val = int(state.input_time_str)
                    if val > 0:
                        cfg.time_window_seconds = val
                        state.request_save()
                except Exception:
                    pass
                state.editing_time_window = False

            if state.show_settings_modal:
                if rects["inp_host"].collidepoint(event.pos):
                    state.active_input_idx = 0
                elif rects["inp_port"].collidepoint(event.pos):
                    state.active_input_idx = 1
                elif rects["inp_outport"].collidepoint(event.pos):
                    state.active_input_idx = 2
                elif rects["btn_save"].collidepoint(event.pos):
                    _apply_settings_modal(cfg, state)
                    input_server.restart()
                    output_server.restart()
                    state.show_settings_modal = False
                elif rects["btn_cancel"].collidepoint(event.pos):
                    state.show_settings_modal = False

            elif state.show_advanced_modal:
                if state.show_buffer_dropdown:
                    if rects["dd_opt_1"].collidepoint(event.pos):
                        state.input_buffer_str = "2048"
                    elif rects["dd_opt_2"].collidepoint(event.pos):
                        state.input_buffer_str = "4096"
                    elif rects["dd_opt_3"].collidepoint(event.pos):
                        state.input_buffer_str = "8192"
                    state.show_buffer_dropdown = False
                else:
                    if rects["btn_buf_arrow"].collidepoint(event.pos):
                        state.show_buffer_dropdown = True
                    elif rects["inp_lerp"].collidepoint(event.pos):
                        state.active_adv_input_idx = 0
                    elif rects["inp_buff"].collidepoint(event.pos):
                        state.active_adv_input_idx = 1
                    elif rects["inp_width"].collidepoint(event.pos):
                        state.active_adv_input_idx = 2

                    elif rects["btn_adv_top"].collidepoint(event.pos):
                        state.temp_adv_always_on_top = not state.temp_adv_always_on_top
                    elif rects["btn_adv_header"].collidepoint(event.pos):
                        state.temp_adv_show_header = not state.temp_adv_show_header
                    elif rects["btn_adv_cpu"].collidepoint(event.pos):
                        state.temp_adv_show_cpu = not state.temp_adv_show_cpu
                    elif rects["btn_adv_round"].collidepoint(event.pos):
                        state.temp_adv_rounded = not state.temp_adv_rounded
                    elif rects["btn_adv_status"].collidepoint(event.pos):
                        state.temp_adv_show_status = not state.temp_adv_show_status
                    elif rects["btn_adv_crypto"].collidepoint(event.pos):
                        state.temp_adv_crypto = not state.temp_adv_crypto

                    elif rects["adv_save"].collidepoint(event.pos):
                        _apply_advanced(cfg, state)
                        if state.hwnd:
                            toggle_always_on_top(state.hwnd, cfg.is_always_on_top)
                            set_window_shape(state.hwnd, cfg.window_w, cfg.window_h, cfg.rounded_corners)
                        state.show_advanced_modal = False
                    elif rects["adv_cancel"].collidepoint(event.pos):
                        state.show_advanced_modal = False

            elif state.show_color_modal:
                if rects["p_box"].collidepoint(event.pos):
                    state.dragging_sv_box = True
                elif rects["p_bar"].collidepoint(event.pos):
                    state.dragging_hue_bar = True
                elif rects["c_bid"].collidepoint(event.pos):
                    state.color_edit_mode = "BID"; set_picker_from_color(state, state.temp_color_bid)
                elif rects["c_ask"].collidepoint(event.pos):
                    state.color_edit_mode = "ASK"; set_picker_from_color(state, state.temp_color_ask)
                elif rects["c_bg"].collidepoint(event.pos):
                    state.color_edit_mode = "BG"; set_picker_from_color(state, state.temp_color_bg)
                elif rects["c_grid"].collidepoint(event.pos):
                    state.color_edit_mode = "GRID"; set_picker_from_color(state, state.temp_color_grid)
                elif rects["c_btn"].collidepoint(event.pos):
                    state.color_edit_mode = "BTN"; set_picker_from_color(state, state.temp_color_btn)
                elif rects["c_txt"].collidepoint(event.pos):
                    state.color_edit_mode = "TEXT"; set_picker_from_color(state, state.temp_color_text)
                elif rects["c_theme"].collidepoint(event.pos):
                    cfg.theme_name = next_theme(cfg.theme_name)
                    apply_theme_to_config(cfg, cfg.theme_name)
                    # refresh temp colors from current cfg colors
                    state.temp_color_bid = cfg.color_bid
                    state.temp_color_ask = cfg.color_ask
                    state.temp_color_bg = cfg.color_bg
                    state.temp_color_grid = cfg.color_grid
                    state.temp_color_text = cfg.color_text
                    state.temp_color_btn = cfg.color_btn
                    # keep picker in current mode
                    mode_to_rgb = {
                        "BID": state.temp_color_bid, "ASK": state.temp_color_ask, "BG": state.temp_color_bg,
                        "GRID": state.temp_color_grid, "BTN": state.temp_color_btn, "TEXT": state.temp_color_text
                    }
                    set_picker_from_color(state, mode_to_rgb.get(state.color_edit_mode, state.temp_color_bid))
                    state.request_save()
                elif rects["c_save"].collidepoint(event.pos):
                    cfg.color_bid = state.temp_color_bid
                    cfg.color_ask = state.temp_color_ask
                    cfg.color_bg = state.temp_color_bg
                    cfg.color_grid = state.temp_color_grid
                    cfg.color_text = state.temp_color_text
                    cfg.color_btn = state.temp_color_btn
                    state.request_save()
                    state.show_color_modal = False
                elif rects["c_cancel"].collidepoint(event.pos):
                    state.show_color_modal = False

            elif state.show_menu:
                if rects["menu_drop"].collidepoint(event.pos):
                    rel_y = event.pos[1] - rects["menu_drop"].y
                    item_idx = rel_y // cfg.menu_item_height

                    if item_idx == 0:
                        cfg.show_controls = not cfg.show_controls
                        state.update_menu_first_line(cfg.show_controls)
                        state.request_save()
                    elif item_idx == 1:
                        state.show_settings_modal = True
                        state.input_host_str = cfg.host
                        state.input_port_str = str(cfg.port_in)
                        state.input_outport_str = str(cfg.port_out)
                        state.active_input_idx = 0
                        state.show_menu = False
                    elif item_idx == 2:
                        state.show_color_modal = True
                        state.temp_color_bid = cfg.color_bid
                        state.temp_color_ask = cfg.color_ask
                        state.temp_color_bg = cfg.color_bg
                        state.temp_color_grid = cfg.color_grid
                        state.temp_color_text = cfg.color_text
                        state.temp_color_btn = cfg.color_btn
                        state.color_edit_mode = "BID"
                        set_picker_from_color(state, state.temp_color_bid)
                        state.show_menu = False
                    elif item_idx == 3:
                        state.show_advanced_modal = True
                        state.input_lerp_str = str(int(cfg.lerp_factor * 100))
                        state.input_buffer_str = str(cfg.buffer_size)
                        state.input_width_str = str(cfg.bar_width_percent)
                        state.active_adv_input_idx = 0

                        state.temp_adv_always_on_top = cfg.is_always_on_top
                        state.temp_adv_show_header = cfg.show_header
                        state.temp_adv_show_cpu = cfg.show_cpu_usage
                        state.temp_adv_rounded = cfg.rounded_corners
                        state.temp_adv_show_status = cfg.show_status_indicator
                        state.temp_adv_crypto = cfg.crypto_mode

                        state.show_menu = False
                    elif item_idx == 4:
                        input_server.restart()
                        state.cont_bid = state.cont_ask = 0.0
                        state.last_raw_bid = state.last_raw_ask = 0.0
                        state.history.clear()
                        state.latest_time_str = "Refreshed..."
                        state.action_start_time = None
                        state.action_running = False
                        state.show_menu = False
                    elif item_idx == 5:
                        state.request_save()
                        state.running = False
                elif not rects["menu"].collidepoint(event.pos):
                    state.show_menu = False

            else:
                # normal clicks
                if rects["menu"].collidepoint(event.pos):
                    state.show_menu = not state.show_menu
                elif cfg.show_controls:
                    if rects["minus"].collidepoint(event.pos):
                        if cfg.time_window_seconds > 1:
                            cfg.time_window_seconds -= 1
                            state.request_save()
                    elif rects["plus"].collidepoint(event.pos):
                        cfg.time_window_seconds += 1
                        state.request_save()
                    elif rects["time_display"].collidepoint(event.pos):
                        state.editing_time_window = True
                        state.input_time_str = str(cfg.time_window_seconds)
                else:
                    if rects["overlay"].collidepoint(event.pos):
                        state.action_running = not state.action_running
                        if state.action_running:
                            state.action_ref_bid = state.cont_bid
                            state.action_ref_ask = state.cont_ask
                            state.action_start_time = datetime.now()
                        else:
                            state.action_start_time = None
                            state.current_bid_vol = 0
                            state.current_ask_vol = 0

                # Resize handle
                if rects["resize"].collidepoint(event.pos):
                    state.resize_active = True
                    if state.hwnd:
                        x, y, w, h = get_window_rect(state.hwnd)
                        state.resize_anchor_left = x
                        state.resize_anchor_top = y
                        state.resize_corner_dx = w - event.pos[0]
                        state.resize_corner_dy = h - event.pos[1]
                else:
                    # Drag window (only if no modal)
                    if not (state.show_settings_modal or state.show_advanced_modal or state.show_color_modal or state.editing_time_window):
                        state.drag_active = True
                        state.drag_offset_x = event.pos[0]
                        state.drag_offset_y = event.pos[1]

        elif event.type == pygame.MOUSEBUTTONUP:
            was_resizing = state.resize_active
            was_dragging = state.drag_active

            if state.resize_active and state.hwnd:
                x, y, w, h = get_window_rect(state.hwnd)
                cfg.window_w = w
                cfg.window_h = h
                screen_ref["screen"] = pygame.display.set_mode((cfg.window_w, cfg.window_h), pygame.NOFRAME | pygame.DOUBLEBUF)
                state.request_save()
                set_window_shape(state.hwnd, cfg.window_w, cfg.window_h, cfg.rounded_corners)
                if cfg.is_always_on_top:
                    toggle_always_on_top(state.hwnd, True)

            state.drag_active = False
            state.resize_active = False
            state.dragging_sv_box = False
            state.dragging_hue_bar = False

            if was_resizing or was_dragging:
                state.request_save()

        elif event.type == pygame.MOUSEMOTION:
            any_modal_open = state.show_settings_modal or state.show_color_modal or state.show_advanced_modal

            if state.show_color_modal:
                updated = False
                if state.dragging_hue_bar:
                    rel_y = max(0, min(cfg.picker_box_size, event.pos[1] - rects["p_bar"].y))
                    state.picker_hue = (rel_y / cfg.picker_box_size) * 360
                    updated = True
                if state.dragging_sv_box:
                    rel_x = max(0, min(cfg.picker_box_size, event.pos[0] - rects["p_box"].x))
                    rel_y = max(0, min(cfg.picker_box_size, event.pos[1] - rects["p_box"].y))
                    state.picker_sat = rel_x / cfg.picker_box_size
                    state.picker_val = 1.0 - (rel_y / cfg.picker_box_size)
                    updated = True
                if updated:
                    apply_picker_to_active_color(state)

            elif state.resize_active and not any_modal_open and state.hwnd:
                pt_x, pt_y = get_cursor_pos()
                new_w = max(cfg.min_w, (pt_x - state.resize_anchor_left) + state.resize_corner_dx)
                new_h = max(cfg.min_h, (pt_y - state.resize_anchor_top) + state.resize_corner_dy)

                now_t = state.now_sec()
                if (new_w != cfg.window_w or new_h != cfg.window_h) and (now_t - state.last_resize_apply) > state.resize_interval:
                    cfg.window_w = int(new_w)
                    cfg.window_h = int(new_h)
                    screen_ref["screen"] = pygame.display.set_mode((cfg.window_w, cfg.window_h), pygame.NOFRAME | pygame.DOUBLEBUF)
                    set_window_shape(state.hwnd, cfg.window_w, cfg.window_h, cfg.rounded_corners)
                    state.last_resize_apply = now_t

            elif state.drag_active and not any_modal_open and state.hwnd:
                pt_x, pt_y = get_cursor_pos()
                new_x = pt_x - state.drag_offset_x
                new_y = pt_y - state.drag_offset_y
                cfg.window_x = new_x
                cfg.window_y = new_y
                set_window_pos(state.hwnd, new_x, new_y)
