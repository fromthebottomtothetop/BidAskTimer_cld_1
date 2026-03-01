# -*- coding: utf-8 -*-
import pygame
import time
from datetime import datetime

from model import AppConfig, AppState
from config import SCALE_RELATIVE, SCALE_ABSOLUTE, SCALE_FIXED


def create_hue_bar(w: int, h: int) -> pygame.Surface:
    surf = pygame.Surface((w, h))
    for y in range(h):
        hue = (y / h) * 360
        c = pygame.Color(0)
        c.hsva = (hue, 100, 100, 100)
        pygame.draw.line(surf, c, (0, y), (w, y))
    return surf


def create_sv_overlay(w: int, h: int) -> pygame.Surface:
    surf = pygame.Surface((w, h), pygame.SRCALPHA)
    for x in range(w):
        alpha = 255 - int((x / w) * 255)
        pygame.draw.line(surf, (255, 255, 255, alpha), (x, 0), (x, h))
    surf2 = pygame.Surface((w, h), pygame.SRCALPHA)
    for y in range(h):
        alpha = int((y / h) * 255)
        pygame.draw.line(surf2, (0, 0, 0, alpha), (0, y), (w, y))
    surf.blit(surf2, (0, 0))
    return surf


def rgb_to_hsv(rgb: tuple) -> tuple[float, float, float]:
    c = pygame.Color(*rgb)
    h, s, v, a = c.hsva
    return h, s / 100.0, v / 100.0


def hsv_to_rgb(h: float, s: float, v: float) -> tuple[int, int, int]:
    c = pygame.Color(0)
    c.hsva = (h % 360, min(100, s * 100), min(100, v * 100), 100)
    return (c.r, c.g, c.b)


def set_picker_from_color(state: AppState, rgb: tuple) -> None:
    state.picker_hue, state.picker_sat, state.picker_val = rgb_to_hsv(rgb)


def apply_picker_to_active_color(state: AppState) -> None:
    rgb = hsv_to_rgb(state.picker_hue, state.picker_sat, state.picker_val)
    if   state.color_edit_mode == "BID":  state.temp_color_bid  = rgb
    elif state.color_edit_mode == "ASK":  state.temp_color_ask  = rgb
    elif state.color_edit_mode == "BG":   state.temp_color_bg   = rgb
    elif state.color_edit_mode == "GRID": state.temp_color_grid = rgb
    elif state.color_edit_mode == "TEXT": state.temp_color_text = rgb
    elif state.color_edit_mode == "BTN":  state.temp_color_btn  = rgb


def format_number(cfg: AppConfig, val: float) -> str:
    if cfg.crypto_mode:
        return f"{val:.1f}"
    return f"{int(val)}"


def format_price(val: float) -> str:
    try:
        s = f"{float(val):.8f}"
        s = s.rstrip("0").rstrip(".")
        return s if s else "0"
    except Exception:
        return "0"


def get_quality_status(cfg: AppConfig, state: AppState, input_client_count: int) -> tuple:
    now = time.time()
    age = (now - state.last_rx_time) if state.last_rx_time > 0 else 999.0

    if input_client_count == 0 and age > (cfg.stale_sec * 1.5):
        return (220, 70, 70), f"{age:.1f}s"

    if age <= cfg.green_rx_sec:
        col = (70, 200, 90)
    elif age <= cfg.yellow_rx_sec:
        col = (230, 200, 70)
    else:
        col = (220, 70, 70)

    return col, f"{age:.1f}s"


def draw_button(screen, rect, text, font_std, cfg: AppConfig,
                hover=False, override_color=None, text_color=None):
    if override_color:
        color = override_color
        if hover:
            color = tuple(min(v + 30, 255) for v in color)
    else:
        color = cfg.color_btn_hover if hover else cfg.color_btn
    t_col = text_color if text_color else cfg.color_text
    pygame.draw.rect(screen, color, rect, border_radius=5)
    lbl = font_std.render(text, True, t_col)
    screen.blit(lbl, (rect.centerx - lbl.get_width() // 2,
                      rect.centery - lbl.get_height() // 2))


def draw_resize_grip(screen, w, h, cfg: AppConfig):
    for i in range(3):
        offset = i * 4
        pygame.draw.line(screen, cfg.color_grip,
                         (w - 7 - offset, h - 7), (w - 7, h - 7 - offset), 2)


def draw_menu_dots(screen, rect, cfg: AppConfig, hover=False):
    color = (150, 150, 150) if hover else cfg.color_menu
    cx, cy = rect.centerx, rect.centery
    for dy in (-8, 0, 8):
        pygame.draw.circle(screen, color, (cx, cy + dy), 2)


def draw_text_input(screen, rect, text, font_small, font_std, cfg: AppConfig,
                    active=False, label=""):
    if label:
        lbl = font_small.render(label, True, cfg.color_text)
        screen.blit(lbl, (rect.x, rect.y - 18))
    bg = cfg.color_input_active if active else cfg.color_input_bg
    pygame.draw.rect(screen, bg, rect, border_radius=4)
    pygame.draw.rect(screen, cfg.color_bid if active else (80, 80, 80), rect, 1, border_radius=4)
    txt_surf = font_std.render(text, True, cfg.color_text)
    old_clip = screen.get_clip()
    screen.set_clip(rect.inflate(-4, -4))
    screen.blit(txt_surf, (rect.x + 5, rect.y + (rect.height - txt_surf.get_height()) // 2))
    screen.set_clip(old_clip)


_SCALE_LABELS = {
    SCALE_RELATIVE: ("REL",  (120, 120, 60),  " Scale: RELATIVE  (100%)"),
    SCALE_ABSOLUTE: ("ABS",  (40,  100, 160), " Scale: ABSOLUTE  (50%)"),
    SCALE_FIXED:    ("FIX",  (60,  140, 80),  " Scale: FIXED     (value)"),
}


def _multiplier_color(mult: float) -> tuple:
    if mult < 1.5: return (110, 110, 110)
    if mult < 2.0: return (180, 160, 80)
    if mult < 3.0: return (220, 160, 40)
    if mult < 4.0: return (220, 110, 30)
    return (220, 60, 60)


def _compute_bar_heights(cfg: AppConfig, state: AppState, chart_height: int) -> tuple[int, int]:
    scale_mode = getattr(cfg, "scale_mode",      SCALE_RELATIVE)
    fixed_max  = max(getattr(cfg, "fixed_scale_max", 500.0), 1.0)

    bid = state.current_bid_vol
    ask = state.current_ask_vol

    if scale_mode == SCALE_FIXED:
        h_bid = int(bid / fixed_max * chart_height)
        h_ask = int(ask / fixed_max * chart_height)
    elif scale_mode == SCALE_ABSOLUTE:
        scale_ref = max(bid + ask, 10)
        pxv   = chart_height / scale_ref
        h_bid = int(bid * pxv)
        h_ask = int(ask * pxv)
    else:  # SCALE_RELATIVE
        scale_ref = max(bid, ask, 10)
        pxv   = chart_height / scale_ref
        h_bid = int(bid * pxv)
        h_ask = int(ask * pxv)

    return min(h_bid, chart_height), min(h_ask, chart_height)


def render_all(screen, rects, hover_states, cfg: AppConfig, state: AppState,
               font_big, font_std, font_small, font_micro, font_micro_bold,
               hue_bar_surface, sat_val_overlay,
               input_client_count: int):

    screen.fill(cfg.color_bg)

    chart_base_y = cfg.window_h - 90
    chart_top_y  = 60
    chart_height = chart_base_y - chart_top_y

    grid_margin = 26
    scale_mode  = getattr(cfg, "scale_mode", SCALE_RELATIVE)
    fixed_max   = getattr(cfg, "fixed_scale_max", 500.0)

    for p in [0.0, 0.25, 0.50, 0.75, 1.0]:
        y_pos = chart_base_y - int(chart_height * p)
        pygame.draw.line(screen, cfg.color_grid,
                         (grid_margin, y_pos), (cfg.window_w - grid_margin, y_pos), 1)
        if scale_mode == SCALE_FIXED:
            lbl_txt = f"{int(fixed_max * p)}"
        else:
            lbl_txt = f"{int(p * 100)}%"
        lbl = font_small.render(lbl_txt, True, cfg.color_grid)
        screen.blit(lbl, (grid_margin - 25, y_pos - 8))

    # ------------------------------------------------------------------
    # Status-Zeile oben links: CPU + Ampel
    # ------------------------------------------------------------------
    x_cursor = 5
    y_top    = 5

    if cfg.show_cpu_usage and state.current_cpu_str:
        cpu_surf = font_micro.render(state.current_cpu_str, True, (120, 120, 120))
        screen.blit(cpu_surf, (x_cursor, y_top))
        x_cursor += cpu_surf.get_width() + 10

    if cfg.show_status_indicator:
        dot_col, status_txt = get_quality_status(cfg, state, input_client_count)
        pygame.draw.circle(screen, dot_col, (x_cursor + 5, y_top + 5), 3)
        x_cursor += 14
        status_surf = font_micro.render(status_txt, True, (120, 120, 120))
        screen.blit(status_surf, (x_cursor, y_top))

    # Scale-Modus Label (FIX/REL/ABS) oben rechts wurde entfernt.

    # ------------------------------------------------------------------
    # Balken
    # ------------------------------------------------------------------
    h_bid, h_ask = _compute_bar_heights(cfg, state, chart_height)

    half_window      = cfg.window_w / 2
    actual_bar_width = int(half_window * (cfg.bar_width_percent / 100.0))
    left_center      = half_window / 2
    right_center     = half_window + (half_window / 2)

    r_bid = pygame.Rect(0, 0, actual_bar_width, max(h_bid, 1))
    r_bid.centerx = int(left_center) + 15
    r_bid.bottom  = chart_base_y
    pygame.draw.rect(screen, cfg.color_bid, r_bid,
                     border_top_left_radius=5, border_top_right_radius=5)

    r_ask = pygame.Rect(0, 0, actual_bar_width, max(h_ask, 1))
    r_ask.centerx = int(right_center) - 15
    r_ask.bottom  = chart_base_y
    pygame.draw.rect(screen, cfg.color_ask, r_ask,
                     border_top_left_radius=5, border_top_right_radius=5)

    if scale_mode == SCALE_FIXED:
        if state.current_bid_vol >= fixed_max:
            pygame.draw.line(screen, (220, 60, 60),
                             (r_bid.left, chart_top_y), (r_bid.right, chart_top_y), 2)
        if state.current_ask_vol >= fixed_max:
            pygame.draw.line(screen, (220, 60, 60),
                             (r_ask.left, chart_top_y), (r_ask.right, chart_top_y), 2)

    _thr      = getattr(cfg, "mult_threshold", 1.5)
    _bid_mult = getattr(state, "bid_multiplier", 1.0)
    _ask_mult = getattr(state, "ask_multiplier", 1.0)
    if _bid_mult >= _thr and h_bid > 20:
        ms = font_micro_bold.render(f"{_bid_mult:.1f}x", True, cfg.color_text)
        screen.blit(ms, (r_bid.centerx - ms.get_width() // 2, r_bid.y + 4))
    if _ask_mult >= _thr and h_ask > 20:
        ms = font_micro_bold.render(f"{_ask_mult:.1f}x", True, cfg.color_text)
        screen.blit(ms, (r_ask.centerx - ms.get_width() // 2, r_ask.y + 4))

    str_bid = format_number(cfg, state.current_bid_vol)
    if str_bid != state.cache_bid_val:
        state.cache_bid_val  = str_bid
        state.cache_bid_surf = font_big.render(str_bid, True, cfg.color_text)

    str_ask = format_number(cfg, state.current_ask_vol)
    if str_ask != state.cache_ask_val:
        state.cache_ask_val  = str_ask
        state.cache_ask_surf = font_big.render(str_ask, True, cfg.color_text)

    if state.cache_bid_surf:
        screen.blit(state.cache_bid_surf,
                    (r_bid.centerx - state.cache_bid_surf.get_width() // 2,
                     r_bid.y - state.cache_bid_surf.get_height() - cfg.text_gap))
    if state.cache_ask_surf:
        screen.blit(state.cache_ask_surf,
                    (r_ask.centerx - state.cache_ask_surf.get_width() // 2,
                     r_ask.y - state.cache_ask_surf.get_height() - cfg.text_gap))

    lbl_bid = font_std.render("BID", True, cfg.color_bid)
    screen.blit(lbl_bid, (r_bid.centerx - lbl_bid.get_width() // 2, cfg.window_h - 80))
    lbl_ask = font_std.render("ASK", True, cfg.color_ask)
    screen.blit(lbl_ask, (r_ask.centerx - lbl_ask.get_width() // 2, cfg.window_h - 80))

    if cfg.show_header:
        h_surf = font_std.render(
            f"BidAskTimer_cld_1 - {state.latest_time_str}", True, cfg.color_header)
        screen.blit(h_surf, (cfg.window_w // 2 - h_surf.get_width() // 2, 10))

    bottom_y = cfg.window_h - 50
    if cfg.show_controls:
        draw_button(screen, rects["minus"], "-", font_std, cfg, hover_states.get("minus", False))
        draw_button(screen, rects["plus"],  "+", font_std, cfg, hover_states.get("plus",  False))

        if state.editing_time_window:
            tb = rects["time_display"]
            pygame.draw.rect(screen, cfg.color_input_bg, tb, border_radius=4)
            pygame.draw.rect(screen, cfg.color_bid,      tb, 1, border_radius=4)
            inp_s = font_std.render(state.input_time_str, True, cfg.color_text)
            screen.blit(inp_s, (tb.centerx - inp_s.get_width() // 2,
                                tb.centery - inp_s.get_height() // 2))
        else:
            t_surf = font_std.render(f"{cfg.time_window_seconds}s", True, cfg.color_text)
            td = rects["time_display"]
            screen.blit(t_surf, (td.centerx - t_surf.get_width() // 2, td.centery - t_surf.get_height() // 2))
            if hover_states.get("time_display"):
                pygame.draw.rect(screen, (100, 100, 100), rects["time_display"], 1, border_radius=4)
    else:
        if state.action_running:
            draw_button(screen, rects["overlay"], "RESET", font_std, cfg,
                        hover_states.get("overlay", False))
            if state.action_start_time:
                delta   = datetime.now() - state.action_start_time
                tot_sec = int(delta.total_seconds())
                t_str   = f"{tot_sec // 60:02}:{tot_sec % 60:02}"
                t_lbl   = font_small.render(t_str, True, cfg.color_text)
                screen.blit(t_lbl, (cfg.window_w // 2 - t_lbl.get_width() // 2, bottom_y - 18))
        else:
            draw_button(screen, rects["overlay"], "START", font_std, cfg,
                        hover_states.get("overlay", False), override_color=(40, 140, 40))

    if getattr(cfg, "scale_mode", 0) == SCALE_FIXED and cfg.show_controls:
        draw_button(screen, rects["fix_minus"], "-", font_std, cfg,
                    hover_states.get("fix_minus", False))
        draw_button(screen, rects["fix_plus"],  "+", font_std, cfg,
                    hover_states.get("fix_plus",  False))
        fix_val  = int(getattr(cfg, "fixed_scale_max", 500))
        fix_surf = font_std.render(str(fix_val), True, cfg.color_text)
        fd = rects["fix_display"]
        screen.blit(fix_surf, (fd.centerx - fix_surf.get_width() // 2,
                               fd.centery - fix_surf.get_height() // 2))

    draw_resize_grip(screen, cfg.window_w, cfg.window_h, cfg)
    draw_menu_dots(screen, rects["menu"], cfg, hover_states.get("menu", False))

    if state.show_menu and not (state.show_settings_modal or
                                state.show_color_modal or
                                state.show_advanced_modal):
        pygame.draw.rect(screen, cfg.color_menu_bg,  rects["menu_drop"], border_radius=5)
        pygame.draw.rect(screen, (80, 80, 80), rects["menu_drop"], 1, border_radius=5)
        m_pos = pygame.mouse.get_pos()
        for i, item_text in enumerate(state.menu_items):
            item_rect = pygame.Rect(rects["menu_drop"].x,
                                    rects["menu_drop"].y + i * cfg.menu_item_height,
                                    cfg.menu_width, cfg.menu_item_height)
            if item_rect.collidepoint(m_pos):
                pygame.draw.rect(screen, cfg.color_menu_hover, item_rect, border_radius=3)
            t = font_small.render(item_text, True, cfg.color_text)
            screen.blit(t, (item_rect.x + 10, item_rect.centery - t.get_height() // 2))

    if state.show_settings_modal or state.show_color_modal or state.show_advanced_modal:
        s = pygame.Surface((cfg.window_w, cfg.window_h))
        s.set_alpha(150)
        s.fill((0, 0, 0))
        screen.blit(s, (0, 0))

    # ------------------------------------------------------------------
    # Settings modal
    # ------------------------------------------------------------------
    if state.show_settings_modal:
        mr = rects["modal"]
        pygame.draw.rect(screen, cfg.color_menu_bg, mr, border_radius=8)
        pygame.draw.rect(screen, cfg.color_grid,    mr, 2, border_radius=8)
        draw_text_input(screen, rects["inp_host"],    state.input_host_str,    font_small, font_std, cfg, state.active_input_idx == 0, "Server IP:")
        draw_text_input(screen, rects["inp_port"],    state.input_port_str,    font_small, font_std, cfg, state.active_input_idx == 1, "Input Port:")
        draw_text_input(screen, rects["inp_outport"], state.input_outport_str, font_small, font_std, cfg, state.active_input_idx == 2, "Output Port:")
        draw_button(screen, rects["btn_save"],   "Save",   font_std, cfg, hover_states.get("save",   False), override_color=(40, 100, 40))
        draw_button(screen, rects["btn_cancel"], "Cancel", font_std, cfg, hover_states.get("cancel", False), override_color=(100, 40, 40))

    # ------------------------------------------------------------------
    # Advanced modal
    # ------------------------------------------------------------------
    if state.show_advanced_modal:
        ar = rects["adv_modal"]
        pygame.draw.rect(screen, cfg.color_menu_bg, ar, border_radius=8)
        pygame.draw.rect(screen, cfg.color_grid,    ar, 2, border_radius=8)
        title = font_std.render("Advanced Settings", True, cfg.color_text)
        screen.blit(title, (ar.centerx - title.get_width() // 2, ar.y + 10))

        def gc(flag): return (40, 140, 40) if flag else (100, 40, 40)

        draw_button(screen, rects["btn_adv_top"],    "Always on Top", font_std, cfg, hover_states.get("adv_top"),    gc(state.temp_adv_always_on_top))
        draw_button(screen, rects["btn_adv_header"], "Header",        font_std, cfg, hover_states.get("adv_header"), gc(state.temp_adv_show_header))
        draw_button(screen, rects["btn_adv_cpu"],    "Show CPU",      font_std, cfg, hover_states.get("adv_cpu"),    gc(state.temp_adv_show_cpu))
        draw_button(screen, rects["btn_adv_round"],  "Round Corners", font_std, cfg, hover_states.get("adv_round"),  gc(state.temp_adv_rounded))
        draw_button(screen, rects["btn_adv_status"], "Ampel + Stale", font_std, cfg, hover_states.get("adv_status"), gc(state.temp_adv_show_status))
        draw_button(screen, rects["btn_adv_crypto"], "Crypto Mode",   font_std, cfg, hover_states.get("adv_crypto"), gc(state.temp_adv_crypto))

        cur_mode  = getattr(state, "temp_adv_scale_mode", SCALE_RELATIVE)
        _, cur_col, cur_lbl = _SCALE_LABELS[cur_mode]
        draw_button(screen, rects["btn_adv_scale"], cur_lbl, font_std, cfg,
                    hover_states.get("adv_scale"), cur_col)

        fmax_active = (state.active_adv_input_idx == 0)
        fmax_dim    = (cur_mode != SCALE_FIXED)
        fmax_label  = "Fixed Max (Kontrakte):" if not fmax_dim else "Fixed Scale Value:"
        draw_text_input(screen, rects["inp_fixed_max"],
                        state.input_fixed_max_str if not fmax_dim else f"({state.input_fixed_max_str})",
                        font_small, font_std, cfg,
                        active=fmax_active and not fmax_dim,
                        label=fmax_label)
        if fmax_dim:
            dim = pygame.Surface((rects["inp_fixed_max"].width, rects["inp_fixed_max"].height))
            dim.set_alpha(120)
            dim.fill((0, 0, 0))
            screen.blit(dim, rects["inp_fixed_max"].topleft)

        draw_text_input(screen, rects["inp_buff"],      state.input_buffer_str,    font_small, font_std, cfg, state.active_adv_input_idx == 1, "Buffer Size:")
        draw_text_input(screen, rects["inp_width"],     state.input_width_str,     font_small, font_std, cfg, state.active_adv_input_idx == 2, "Bar Width (%):")
        draw_text_input(screen, rects["inp_mult_base"], state.input_mult_base_str, font_small, font_std, cfg, state.active_adv_input_idx == 3, "Mult Flow Time:")
        draw_text_input(screen, rects["inp_mult_thr"],  state.input_mult_thr_str,  font_small, font_std, cfg, state.active_adv_input_idx == 4, "Trigger Value:")

        draw_button(screen, rects["btn_buf_arrow"], "?",      font_std, cfg, hover_states.get("buf_arrow"),  (70, 70, 70))
        draw_button(screen, rects["adv_save"],      "Save",   font_std, cfg, hover_states.get("adv_save"),   (40, 100, 40))
        draw_button(screen, rects["adv_cancel"],    "Cancel", font_std, cfg, hover_states.get("adv_cancel"), (100, 40, 40))

        if state.show_buffer_dropdown:
            dd = rects["dd_container"]
            pygame.draw.rect(screen, cfg.color_menu_bg, dd, border_radius=5)
            pygame.draw.rect(screen, cfg.color_grid,    dd, 1, border_radius=5)
            for val_str, rr in [("2048", rects["dd_opt_1"]),
                                 ("4096", rects["dd_opt_2"]),
                                 ("8192", rects["dd_opt_3"])]:
                if rr.collidepoint(pygame.mouse.get_pos()):
                    pygame.draw.rect(screen, cfg.color_menu_hover, rr)
                lbl = font_std.render(val_str, True, cfg.color_text)
                screen.blit(lbl, (rr.x + 10, rr.centery - lbl.get_height() // 2))

    # ------------------------------------------------------------------
    # Color modal
    # ------------------------------------------------------------------
    if state.show_color_modal:
        cr = rects["col_modal"]
        pygame.draw.rect(screen, cfg.color_menu_bg, cr, border_radius=8)
        pygame.draw.rect(screen, cfg.color_grid,    cr, 2, border_radius=8)
        title = font_std.render("Color Settings", True, cfg.color_text)
        screen.blit(title, (cr.centerx - title.get_width() // 2, cr.y + 10))

        def outline_if(mode):
            return 2 if state.color_edit_mode == mode else 0

        for key, mode, col in [
            ("c_bid",  "BID",  state.temp_color_bid),
            ("c_ask",  "ASK",  state.temp_color_ask),
            ("c_bg",   "BG",   state.temp_color_bg),
            ("c_grid", "GRID", state.temp_color_grid),
            ("c_btn",  "BTN",  state.temp_color_btn),
            ("c_txt",  "TEXT", state.temp_color_text),
        ]:
            label = mode[0] + mode[1:].lower() + " Color"
            draw_button(screen, rects[key], label, font_std, cfg,
                        False, override_color=col, text_color=(255, 255, 255))
            if outline_if(mode):
                pygame.draw.rect(screen, (255, 255, 255), rects[key], 2, border_radius=5)

        draw_button(screen, rects["c_theme"], f"Theme: {cfg.theme_name.title()}",
                    font_std, cfg, hover_states.get("c_theme", False))

        pbox = rects["p_box"]
        pbar = rects["p_bar"]
        pure = pygame.Color(0)
        pure.hsva = (state.picker_hue, 100, 100, 100)
        pygame.draw.rect(screen, pure, pbox)
        screen.blit(sat_val_overlay, pbox)
        cx = pbox.x + int(state.picker_sat * cfg.picker_box_size)
        cy = pbox.y + int((1.0 - state.picker_val) * cfg.picker_box_size)
        pygame.draw.circle(screen, (0, 0, 0),       (cx, cy), 6, 2)
        pygame.draw.circle(screen, (255, 255, 255), (cx, cy), 4, 2)
        pygame.draw.rect(screen, (100, 100, 100), pbox, 1)

        screen.blit(hue_bar_surface, pbar)
        pygame.draw.rect(screen, (100, 100, 100), pbar, 1)
        hy = pbar.y + int((state.picker_hue / 360.0) * cfg.picker_box_size)
        pygame.draw.rect(screen, (0, 0, 0),
                         (pbar.x - 2, hy - 3, cfg.picker_bar_width + 4, 6), 2)

        draw_button(screen, rects["c_save"],   "Save",   font_std, cfg, hover_states.get("c_save"),   (40, 100, 40))
        draw_button(screen, rects["c_cancel"], "Cancel", font_std, cfg, hover_states.get("c_cancel"), (100, 40, 40))
