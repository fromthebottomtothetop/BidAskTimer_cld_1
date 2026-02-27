# -*- coding: utf-8 -*-
import pygame
from model import AppConfig, AppState


def calculate_layout(cfg: AppConfig, state: AppState) -> dict:
    w, h = cfg.window_w, cfg.window_h
    r = {}
    center_x = w // 2
    bottom_y = h - 50

    r["minus"] = pygame.Rect(center_x - 50, bottom_y + 4, 30, 22)
    r["plus"] = pygame.Rect(center_x + 20, bottom_y + 4, 30, 22)
    r["time_display"] = pygame.Rect(center_x - 20, bottom_y, 40, 30)

    r["overlay"] = pygame.Rect(center_x - 37, bottom_y, 76, 30)
    r["resize"] = pygame.Rect(w - 20, h - 20, 20, 20)
    r["menu"] = pygame.Rect(w - 35, 10, 30, 30)

    menu_h = len(state.menu_items) * cfg.menu_item_height
    menu_x = (w - cfg.menu_width) // 2
    if menu_x < 0:
        menu_x = 0
    r["menu_drop"] = pygame.Rect(menu_x, 45, cfg.menu_width, menu_h)

    # Connection modal
    modal_w, modal_h = 180, 250
    m_rect = pygame.Rect((w - modal_w) // 2, (h - modal_h) // 2, modal_w, modal_h)
    r["modal"] = m_rect
    r["inp_host"] = pygame.Rect(m_rect.x + 20, m_rect.y + 40, modal_w - 40, 30)
    r["inp_port"] = pygame.Rect(m_rect.x + 20, m_rect.y + 100, modal_w - 40, 30)
    r["inp_outport"] = pygame.Rect(m_rect.x + 20, m_rect.y + 160, modal_w - 40, 30)
    r["btn_save"] = pygame.Rect(m_rect.x + 20, m_rect.bottom - 50, (modal_w - 50) // 2, 30)
    r["btn_cancel"] = pygame.Rect(m_rect.x + 20 + (modal_w - 50) // 2 + 10, m_rect.bottom - 50, (modal_w - 50) // 2, 30)

    # Advanced modal
    adv_w, adv_h = 260, 390
    adv_rect = pygame.Rect((w - adv_w) // 2, (h - adv_h) // 2, adv_w, adv_h)
    r["adv_modal"] = adv_rect

    btn_w = 110
    r["btn_adv_top"] = pygame.Rect(adv_rect.x + 15, adv_rect.y + 45, btn_w, 30)
    r["btn_adv_header"] = pygame.Rect(adv_rect.right - 15 - btn_w, adv_rect.y + 45, btn_w, 30)
    r["btn_adv_cpu"] = pygame.Rect(adv_rect.x + 15, adv_rect.y + 85, btn_w, 30)
    r["btn_adv_round"] = pygame.Rect(adv_rect.right - 15 - btn_w, adv_rect.y + 85, btn_w, 30)

    r["btn_adv_status"] = pygame.Rect(adv_rect.x + 15, adv_rect.y + 125, btn_w, 30)
    r["btn_adv_crypto"] = pygame.Rect(adv_rect.right - 15 - btn_w, adv_rect.y + 125, btn_w, 30)

    r["inp_lerp"] = pygame.Rect(adv_rect.x + 20, adv_rect.y + 180, adv_w - 40, 30)
    r["inp_buff"] = pygame.Rect(adv_rect.x + 20, adv_rect.y + 240, adv_w - 40 - 35, 30)
    r["btn_buf_arrow"] = pygame.Rect(r["inp_buff"].right + 5, r["inp_buff"].y, 30, 30)
    r["inp_width"] = pygame.Rect(adv_rect.x + 20, adv_rect.y + 300, adv_w - 40, 30)

    r["dd_container"] = pygame.Rect(r["inp_buff"].x, r["inp_buff"].bottom + 1, r["inp_buff"].width + 35, 100)
    r["dd_opt_1"] = pygame.Rect(r["dd_container"].x, r["dd_container"].y, r["dd_container"].width, 33)
    r["dd_opt_2"] = pygame.Rect(r["dd_container"].x, r["dd_container"].y + 33, r["dd_container"].width, 33)
    r["dd_opt_3"] = pygame.Rect(r["dd_container"].x, r["dd_container"].y + 66, r["dd_container"].width, 33)

    r["adv_save"] = pygame.Rect(adv_rect.x + 20, adv_rect.bottom - 45, (adv_w - 50) // 2, 30)
    r["adv_cancel"] = pygame.Rect(adv_rect.x + 20 + (adv_w - 50) // 2 + 10, adv_rect.bottom - 45, (adv_w - 50) // 2, 30)

    # Color modal
    cm_w, cm_h = 230, 405
    cm_rect = pygame.Rect((w - cm_w) // 2, (h - cm_h) // 2, cm_w, cm_h)
    r["col_modal"] = cm_rect

    col_btn_w = 95
    col_btn_h = 28
    base_y = cm_rect.y + 35
    gap_y = 33

    r["c_bid"] = pygame.Rect(cm_rect.x + 15, base_y, col_btn_w, col_btn_h)
    r["c_ask"] = pygame.Rect(cm_rect.right - 15 - col_btn_w, base_y, col_btn_w, col_btn_h)
    r["c_bg"] = pygame.Rect(cm_rect.x + 15, base_y + gap_y, col_btn_w, col_btn_h)
    r["c_grid"] = pygame.Rect(cm_rect.right - 15 - col_btn_w, base_y + gap_y, col_btn_w, col_btn_h)
    r["c_btn"] = pygame.Rect(cm_rect.x + 15, base_y + gap_y * 2, col_btn_w, col_btn_h)
    r["c_txt"] = pygame.Rect(cm_rect.right - 15 - col_btn_w, base_y + gap_y * 2, col_btn_w, col_btn_h)
    r["c_theme"] = pygame.Rect(cm_rect.centerx - 60, base_y + gap_y * 3 + 2, 120, col_btn_h)

    picker_area_y = base_y + gap_y * 4 + 10
    total_picker_width = cfg.picker_box_size + 20 + cfg.picker_bar_width
    picker_start_x = cm_rect.centerx - (total_picker_width // 2)

    r["p_box"] = pygame.Rect(picker_start_x, picker_area_y, cfg.picker_box_size, cfg.picker_box_size)
    r["p_bar"] = pygame.Rect(r["p_box"].right + 20, picker_area_y, cfg.picker_bar_width, cfg.picker_box_size)

    btn_bottom_w = 80
    r["c_save"] = pygame.Rect(cm_rect.centerx - btn_bottom_w - 5, cm_rect.bottom - 35, btn_bottom_w, 25)
    r["c_cancel"] = pygame.Rect(cm_rect.centerx + 5, cm_rect.bottom - 35, btn_bottom_w, 25)

    return r

