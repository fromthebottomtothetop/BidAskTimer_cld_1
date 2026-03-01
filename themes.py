# -*- coding: utf-8 -*-

THEME_DARK = {
    "BG": (18, 18, 18), "GRID": (50, 50, 50), "TEXT": (220, 220, 220),
    "BTN": (50, 50, 50), "BTN_HOVER": (100, 100, 100),
    "MENU": (50, 50, 50), "MENU_BG": (40, 40, 40), "MENU_HOVER": (60, 60, 60),
    "GRIP": (80, 80, 80), "HEADER": (100, 100, 100),
    "INPUT_BG": (30, 30, 30), "INPUT_ACTIVE": (60, 60, 60),
    "BID": (214, 39, 40), "ASK": (44, 160, 44)
}
THEME_LIGHT = {
    "BG": (240, 240, 240), "GRID": (180, 180, 180), "TEXT": (20, 20, 20),
    "BTN": (220, 220, 220), "BTN_HOVER": (180, 180, 180),
    "MENU": (160, 160, 160), "MENU_BG": (255, 255, 255), "MENU_HOVER": (230, 230, 230),
    "GRIP": (180, 180, 180), "HEADER": (100, 100, 100),
    "INPUT_BG": (255, 255, 255), "INPUT_ACTIVE": (240, 240, 255),
    "BID": (200, 30, 30), "ASK": (30, 150, 30)
}
THEME_ATAS_DARK = {
    "BG": (21, 27, 38), "GRID": (99, 99, 101), "TEXT": (220, 220, 200),
    "BTN": (45, 45, 48), "BTN_HOVER": (70, 70, 70),
    "MENU": (99, 99, 101), "MENU_BG": (30, 35, 45), "MENU_HOVER": (70, 70, 70),
    "GRIP": (99, 99, 101), "HEADER": (99, 99, 101),
    "INPUT_BG": (128, 128, 128), "INPUT_ACTIVE": (128, 128, 128),
    "BID": (242, 56, 90), "ASK": (8, 153, 129)
}
THEME_COZY = {
    "BG": (43, 35, 30), "GRID": (70, 60, 50), "TEXT": (230, 210, 190),
    "BTN": (70, 60, 55), "BTN_HOVER": (100, 90, 80),
    "MENU": (90, 80, 70), "MENU_BG": (55, 45, 40), "MENU_HOVER": (110, 100, 90),
    "GRIP": (100, 90, 80), "HEADER": (160, 140, 120),
    "INPUT_BG": (60, 50, 45), "INPUT_ACTIVE": (80, 70, 60),
    "BID": (180, 80, 80), "ASK": (100, 150, 100)
}
THEME_EVIL = {
    "BG": (5, 0, 0), "GRID": (60, 0, 0), "TEXT": (255, 20, 20),
    "BTN": (40, 0, 0), "BTN_HOVER": (80, 0, 0),
    "MENU": (100, 0, 0), "MENU_BG": (20, 0, 0), "MENU_HOVER": (50, 0, 0),
    "GRIP": (120, 0, 0), "HEADER": (200, 0, 0),
    "INPUT_BG": (30, 0, 0), "INPUT_ACTIVE": (60, 0, 0),
    "BID": (159, 28, 28), "ASK": (255, 132, 0)
}
THEME_OCEAN = {
    "BG": (10, 25, 47), "GRID": (23, 42, 69), "TEXT": (200, 230, 255),
    "BTN": (23, 42, 69), "BTN_HOVER": (50, 80, 110),
    "MENU": (23, 42, 69), "MENU_BG": (13, 30, 55), "MENU_HOVER": (30, 60, 90),
    "GRIP": (60, 90, 120), "HEADER": (100, 210, 255),
    "INPUT_BG": (20, 40, 70), "INPUT_ACTIVE": (40, 70, 100),
    "BID": (255, 136, 136), "ASK": (0, 200, 200)
}
THEME_FOREST = {
    "BG": (20, 30, 20), "GRID": (62, 86, 62), "TEXT": (200, 220, 200),
    "BTN": (40, 60, 40), "BTN_HOVER": (60, 90, 60),
    "MENU": (40, 60, 40), "MENU_BG": (25, 40, 25), "MENU_HOVER": (45, 70, 45),
    "GRIP": (80, 120, 80), "HEADER": (120, 180, 120),
    "INPUT_BG": (30, 50, 30), "INPUT_ACTIVE": (50, 80, 50),
    "BID": (255, 144, 144), "ASK": (90, 222, 153)
}

THEME_ORDER = ["dark", "light", "cozy", "evil", "ocean", "forest", "atas dark"]


def get_theme(theme_name: str) -> dict:
    t = (theme_name or "").strip().lower()
    if t == "light":     return THEME_LIGHT
    if t == "atas dark": return THEME_ATAS_DARK
    if t == "cozy":      return THEME_COZY
    if t == "evil":      return THEME_EVIL
    if t == "ocean":     return THEME_OCEAN
    if t == "forest":    return THEME_FOREST
    return THEME_DARK


def next_theme(current_name: str) -> str:
    try:
        idx = THEME_ORDER.index((current_name or "").strip().lower())
    except ValueError:
        idx = 0
    return THEME_ORDER[(idx + 1) % len(THEME_ORDER)]
