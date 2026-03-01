# -*- coding: utf-8 -*-
import pygame
from model import AppConfig, AppState
from config import SCALE_FIXED


def calculate_layout(cfg: AppConfig, state: AppState) -> dict:
    w, h = cfg.window_w, cfg.window_h
    r = {}
    center_x = w // 2
    bottom_y  = h - 50

    fixed_mode = (getattr(cfg, "scale_mode", 0) == SCALE_FIXED)

    if fixed_mode:
        t_cx = w // 4
        r["minus"]        = pygame.Rect(t_cx - 35, bottom_y + 7, 21, 15)
        r["plus"]         = pygame.Rect(t_cx + 14, bottom_y + 7, 21, 15)
        r["time_display"] = pygame.Rect(t_cx - 14, bottom_y + 4, 28, 21)
        f_cx = (w * 3) // 4
        r["fix_minus"]   = pygame.Rect(f_cx - 35, bottom_y + 7, 21, 15)
        r["fix_plus"]    = pygame.Rect(f_cx + 14, bottom_y + 7, 21, 15)
        r["fix_display"] = pygame.Rect(f_cx - 20, bottom_y + 4, 41, 21)
    else:
        r["minus"]        = pygame.Rect(center_x - 35, bottom_y + 7, 21, 15)
        r["plus"]         = pygame.Rect(center_x + 14, bottom_y + 7, 21, 15)
        r["time_display"] = pygame.Rect(center_x - 14, bottom_y + 4, 28, 21)
        r["fix_minus"]   = pygame.Rect(-100, -100, 30, 22)
        r["fix_plus"]    = pygame.Rect(-100, -100, 30, 22)
        r["fix_display"] = pygame.Rect(-100, -100, 58, 30)

    r["overlay"]  = pygame.Rect(center_x - 37, bottom_y, 76, 30)
    r["resize"]   = pygame.Rect(w - 20, h - 20, 20, 20)
    r["menu"]     = pygame.Rect(w - 35, 10, 30, 30)

    menu_h = len(state.menu_items) * cfg.menu_item_height
    menu_x = max(0, (w - cfg.menu_width) // 2)
    r["menu_drop"] = pygame.Rect(menu_x, 45, cfg.menu_width, menu_h)

    modal_w, modal_h = 180, 250
    m_rect = pygame.Rect((w - modal_w) // 2, (h - modal_h) // 2, modal_w, modal_h)
    r["modal"]       = m_rect
    r["inp_host"]    = pygame.Rect(m_rect.x + 20, m_rect.y +  40, modal_w - 40, 30)
    r["inp_port"]    = pygame.Rect(m_rect.x + 20, m_rect.y + 100, modal_w - 40, 30)
    r["inp_outport"] = pygame.Rect(m_rect.x + 20, m_rect.y + 160, modal_w - 40, 30)
    r["btn_save"]    = pygame.Rect(m_rect.x + 20, m_rect.bottom - 50, (modal_w - 50) // 2, 30)
    r["btn_cancel"]  = pygame.Rect(m_rect.x + 20 + (modal_w - 50) // 2 + 10,
                                   m_rect.bottom - 50, (modal_w - 50) // 2, 30)

    # ------------------------------------------------------------------
    # Advanced Modal — aufgeräumtes Layout mit gleichmässigem Abstand
    #
    # Vertikale Struktur (alle y-Werte relativ zu adv_rect.y):
    #   +10   Titel
    #   +40   Toggle-Buttons Reihe 1 (AlwaysOnTop / Header)
    #   +80   Toggle-Buttons Reihe 2 (Show CPU / Round Corners)
    #   +120  Toggle-Buttons Reihe 3 (Ampel+Stale / Crypto Mode)
    #   +160  Scale-Button (volle Breite)
    #   +210  Fixed Max label (+18 = +228 effektiv) / Input bei +228
    #   +278  Buffer Size label/input
    #   +338  Bar Width label/input
    #   +398  Mult Baseline / Mult Schwelle (nebeneinander)
    #   +450  Save / Cancel
    #   Gesamt: adv_h = 500
    # ------------------------------------------------------------------
    adv_w, adv_h = 260, 500
    adv_rect = pygame.Rect((w - adv_w) // 2, (h - adv_h) // 2, adv_w, adv_h)
    r["adv_modal"] = adv_rect

    btn_w    = 110
    full_btn = adv_w - 30

    # Toggle-Buttons (3 Reihen à 2 Buttons)
    r["btn_adv_top"]    = pygame.Rect(adv_rect.x + 15,             adv_rect.y + 40,  btn_w, 30)
    r["btn_adv_header"] = pygame.Rect(adv_rect.right - 15 - btn_w, adv_rect.y + 40,  btn_w, 30)
    r["btn_adv_cpu"]    = pygame.Rect(adv_rect.x + 15,             adv_rect.y + 80,  btn_w, 30)
    r["btn_adv_round"]  = pygame.Rect(adv_rect.right - 15 - btn_w, adv_rect.y + 80,  btn_w, 30)
    r["btn_adv_status"] = pygame.Rect(adv_rect.x + 15,             adv_rect.y + 120, btn_w, 30)
    r["btn_adv_crypto"] = pygame.Rect(adv_rect.right - 15 - btn_w, adv_rect.y + 120, btn_w, 30)

    # Scale-Button (volle Breite, 8px Abstand zur letzten Toggle-Reihe)
    r["btn_adv_scale"]  = pygame.Rect(adv_rect.x + 15, adv_rect.y + 160, full_btn, 30)

    # Fixed Max Input (label 18px über Input → label bei y+210, input bei y+228)
    r["inp_fixed_max"]  = pygame.Rect(adv_rect.x + 20, adv_rect.y + 228, adv_w - 40, 30)

    # Buffer Size (label bei y+278, input bei y+296)
    r["inp_buff"]       = pygame.Rect(adv_rect.x + 20, adv_rect.y + 296, adv_w - 40 - 35, 30)
    r["btn_buf_arrow"]  = pygame.Rect(r["inp_buff"].right + 5, r["inp_buff"].y, 30, 30)

    # Bar Width (label bei y+338, input bei y+356)
    r["inp_width"]      = pygame.Rect(adv_rect.x + 20, adv_rect.y + 356, adv_w - 40, 30)

    # Mult Baseline + Schwelle (label bei y+398, inputs bei y+416)
    _mult_input_w = (adv_w - 45) // 2
    r["inp_mult_base"]  = pygame.Rect(adv_rect.x + 20, adv_rect.y + 416, _mult_input_w, 30)
    r["inp_mult_thr"]   = pygame.Rect(adv_rect.x + 20 + _mult_input_w + 5, adv_rect.y + 416, _mult_input_w, 30)

    # Dropdown (direkt unter Buffer-Input)
    r["dd_container"]   = pygame.Rect(r["inp_buff"].x, r["inp_buff"].bottom + 1,
                                      r["inp_buff"].width + 35, 100)
    r["dd_opt_1"] = pygame.Rect(r["dd_container"].x, r["dd_container"].y,      r["dd_container"].width, 33)
    r["dd_opt_2"] = pygame.Rect(r["dd_container"].x, r["dd_container"].y + 33, r["dd_container"].width, 33)
    r["dd_opt_3"] = pygame.Rect(r["dd_container"].x, r["dd_container"].y + 66, r["dd_container"].width, 33)

    # Save / Cancel
    _sbtn_w = (adv_w - 50) // 2
    r["adv_save"]   = pygame.Rect(adv_rect.x + 20, adv_rect.bottom - 45, _sbtn_w, 30)
    r["adv_cancel"] = pygame.Rect(adv_rect.x + 20 + _sbtn_w + 10,
                                  adv_rect.bottom - 45, _sbtn_w, 30)

    # ------------------------------------------------------------------
    # Color Modal
    # ------------------------------------------------------------------
    cm_w, cm_h = 230, 405
    cm_rect = pygame.Rect((w - cm_w) // 2, (h - cm_h) // 2, cm_w, cm_h)
    r["col_modal"] = cm_rect
    col_btn_w = 95
    col_btn_h = 28
    base_y    = cm_rect.y + 35
    gap_y     = 33
    r["c_bid"]  = pygame.Rect(cm_rect.x + 15,                base_y,             col_btn_w, col_btn_h)
    r["c_ask"]  = pygame.Rect(cm_rect.right - 15 - col_btn_w, base_y,            col_btn_w, col_btn_h)
    r["c_bg"]   = pygame.Rect(cm_rect.x + 15,                base_y + gap_y,     col_btn_w, col_btn_h)
    r["c_grid"] = pygame.Rect(cm_rect.right - 15 - col_btn_w, base_y + gap_y,    col_btn_w, col_btn_h)
    r["c_btn"]  = pygame.Rect(cm_rect.x + 15,                base_y + gap_y * 2, col_btn_w, col_btn_h)
    r["c_txt"]  = pygame.Rect(cm_rect.right - 15 - col_btn_w, base_y + gap_y*2,  col_btn_w, col_btn_h)
    r["c_theme"]= pygame.Rect(cm_rect.centerx - 60, base_y + gap_y * 3 + 2, 120, col_btn_h)
    picker_area_y      = base_y + gap_y * 4 + 10
    total_picker_width = cfg.picker_box_size + 20 + cfg.picker_bar_width
    picker_start_x     = cm_rect.centerx - (total_picker_width // 2)
    r["p_box"] = pygame.Rect(picker_start_x, picker_area_y, cfg.picker_box_size, cfg.picker_box_size)
    r["p_bar"] = pygame.Rect(r["p_box"].right + 20, picker_area_y, cfg.picker_bar_width, cfg.picker_box_size)
    btn_bottom_w = 80
    r["c_save"]   = pygame.Rect(cm_rect.centerx - btn_bottom_w - 5, cm_rect.bottom - 35, btn_bottom_w, 25)
    r["c_cancel"] = pygame.Rect(cm_rect.centerx + 5,                cm_rect.bottom - 35, btn_bottom_w, 25)

    return r
