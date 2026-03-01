# -*- coding: utf-8 -*-
from __future__ import annotations

from dataclasses import dataclass, field
from collections import deque
import queue
import time


@dataclass
class AppConfig:
    # Network
    host: str = "127.0.0.1"
    port_in: int = 55011
    port_out: int = 55012
    indicator_name: str = "BidAskTimerCryptoTest"

    # Window
    window_w: int = 200
    window_h: int = 600
    min_w: int = 120
    min_h: int = 100
    window_x: int = 100
    window_y: int = 100

    # Behavior
    fps: int = 60
    buffer_size: int = 4096
    lerp_factor: float = 0.8
    bar_width_percent: int = 60
    time_window_seconds: int = 30

    is_always_on_top: bool = True
    show_header: bool = True
    show_cpu_usage: bool = True
    rounded_corners: bool = True
    show_controls: bool = True
    show_status_indicator: bool = True
    crypto_mode: bool = False

    # Status thresholds
    green_rx_sec: float = 0.25
    yellow_rx_sec: float = 1.0
    stale_sec: float = 2.0

    # Output throttling
    min_send_interval: float = 0.03

    # UI constants
    font_size_val: int = 30
    text_gap: int = 1
    menu_width: int = 220
    menu_item_height: int = 40

    # Color picker sizes
    picker_box_size: int = 150
    picker_bar_width: int = 30

    # Theme + colors (werden durch Theme gesetzt + optional überschrieben)
    theme_name: str = "atas dark"

    color_bid: tuple = (214, 39, 40)
    color_ask: tuple = (44, 160, 44)
    color_bg: tuple = (18, 18, 18)
    color_grid: tuple = (50, 50, 50)
    color_text: tuple = (220, 220, 220)
    color_btn: tuple = (50, 50, 50)
    color_btn_hover: tuple = (100, 100, 100)
    color_menu: tuple = (50, 50, 50)
    color_menu_bg: tuple = (40, 40, 40)
    color_menu_hover: tuple = (60, 60, 60)
    color_grip: tuple = (80, 80, 80)
    color_header: tuple = (100, 100, 100)
    color_input_bg: tuple = (30, 30, 30)
    color_input_active: tuple = (60, 60, 60)


@dataclass
class AppState:
    # Runtime queues/history
    data_queue: queue.Queue[str] = field(default_factory=queue.Queue)
    history: deque = field(default_factory=deque)

    # Continuous counters
    cont_bid: float = 0.0
    cont_ask: float = 0.0
    last_raw_bid: float = 0.0
    last_raw_ask: float = 0.0

    # Displayed volumes (smoothed)
    current_bid_vol: float = 0.0
    current_ask_vol: float = 0.0

    # Latest tick fields
    latest_time_str: str = "waiting..."
    latest_price: float = 0.0

    # Stopwatch mode
    action_running: bool = False
    action_start_time: object | None = None
    action_ref_bid: float = 0.0
    action_ref_ask: float = 0.0

    # Win32/pygame handles
    hwnd: int | None = None

    # UI toggles / menu
    running: bool = True
    show_menu: bool = False

    menu_items: list[str] = field(default_factory=lambda: [
        "Mode: Setup",
        "Connection Settings",
        "Color Settings",
        "Advanced Settings",
        "Refresh Connection",
        "Close"
    ])

    # Status indicator timestamps
    last_rx_time: float = 0.0
    last_change_bid_t: float = 0.0
    last_change_ask_t: float = 0.0
    last_change_price_t: float = 0.0
    last_stale_raw_bid: float | None = None
    last_stale_raw_ask: float | None = None
    last_stale_price: float | None = None

    # CPU text
    last_cpu_check: float = 0.0
    current_cpu_str: str = ""

    # Modals
    show_settings_modal: bool = False
    input_host_str: str = ""
    input_port_str: str = ""
    input_outport_str: str = ""
    active_input_idx: int = 0

    show_advanced_modal: bool = False
    input_lerp_str: str = ""
    input_buffer_str: str = ""
    input_width_str: str = ""
    active_adv_input_idx: int = 0
    show_buffer_dropdown: bool = False

    temp_adv_always_on_top: bool = False
    temp_adv_show_header: bool = False
    temp_adv_show_cpu: bool = False
    temp_adv_rounded: bool = False
    temp_adv_show_status: bool = False
    temp_adv_crypto: bool = False

    editing_time_window: bool = False
    input_time_str: str = ""

    show_color_modal: bool = False
    color_edit_mode: str = "BID"
    temp_color_bid: tuple = (214, 39, 40)
    temp_color_ask: tuple = (44, 160, 44)
    temp_color_bg: tuple = (18, 18, 18)
    temp_color_grid: tuple = (50, 50, 50)
    temp_color_text: tuple = (220, 220, 220)
    temp_color_btn: tuple = (50, 50, 50)

    picker_hue: float = 0.0
    picker_sat: float = 1.0
    picker_val: float = 1.0

    dragging_sv_box: bool = False
    dragging_hue_bar: bool = False

    # Resize / Drag
    resize_active: bool = False
    resize_anchor_left: int = 0
    resize_anchor_top: int = 0
    resize_corner_dx: int = 0
    resize_corner_dy: int = 0
    last_resize_apply: float = 0.0
    resize_interval: float = 0.016

    drag_active: bool = False
    drag_offset_x: int = 0
    drag_offset_y: int = 0

    # Render cache
    cache_bid_val: str = ""
    cache_ask_val: str = ""
    cache_bid_surf: object | None = None
    cache_ask_surf: object | None = None

    # Save request flag (damit wir zentral speichern)
    save_requested: bool = False

    def request_save(self) -> None:
        self.save_requested = True

    def update_menu_first_line(self, show_controls: bool) -> None:
        self.menu_items[0] = f"Mode: {'Flow' if show_controls else 'Stopwatch'}"

    def now_sec(self) -> float:
        return time.time()


