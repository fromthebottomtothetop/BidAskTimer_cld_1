# -*- coding: utf-8 -*-
import collections
import time
from datetime import datetime

from model import AppConfig, AppState
from ui_draw import format_number, format_price

MODE_CANDLE = 0
MODE_TAPE   = 1


def _init_state_extras(state: AppState) -> None:
    if not hasattr(state, 'tape_mode'):
        state.tape_mode = False
    if not hasattr(state, 'vol_baseline_history'):
        state.vol_baseline_history = collections.deque()
    if not hasattr(state, 'vol_multiplier'):
        state.vol_multiplier = 1.0
    if not hasattr(state, 'input_fixed_max_str'):
        state.input_fixed_max_str = "500"


def process_incoming_data(cfg: AppConfig, state: AppState) -> None:
    _init_state_extras(state)

    try:
        while True:
            try:
                line = state.data_queue.get_nowait()
            except Exception:
                break

            parts = line.strip().split(";")
            if len(parts) < 6:
                continue

            try:
                state.latest_time_str = parts[0].split(".")[0] if parts[0] else "Time Error"
                state.latest_price    = float(parts[1].replace(",", "."))
                raw_bid = float(parts[4].replace(",", "."))
                raw_ask = float(parts[5].replace(",", "."))
            except ValueError:
                continue

            now_sec = time.time()
            state.last_rx_time = now_sec

            # Stale detection
            if state.last_stale_raw_bid is None:
                state.last_stale_raw_bid  = raw_bid
                state.last_stale_raw_ask  = raw_ask
                state.last_stale_price    = state.latest_price
                state.last_change_bid_t   = now_sec
                state.last_change_ask_t   = now_sec
                state.last_change_price_t = now_sec
            else:
                if raw_bid != state.last_stale_raw_bid:
                    state.last_change_bid_t  = now_sec
                    state.last_stale_raw_bid = raw_bid
                if raw_ask != state.last_stale_raw_ask:
                    state.last_change_ask_t  = now_sec
                    state.last_stale_raw_ask = raw_ask
                if state.latest_price != state.last_stale_price:
                    state.last_change_price_t = now_sec
                    state.last_stale_price    = state.latest_price

            # KRITISCH 1: Mode-Feld explizit lesen
            new_bar_flag = 0
            if len(parts) >= 7:
                try: new_bar_flag = int(parts[6])
                except Exception: new_bar_flag = 0

            incoming_mode = MODE_CANDLE
            if len(parts) >= 8:
                try: incoming_mode = int(parts[7])
                except Exception: incoming_mode = MODE_CANDLE

            current_mode_int = MODE_TAPE if state.tape_mode else MODE_CANDLE
            if incoming_mode != current_mode_int:
                state.tape_mode    = (incoming_mode == MODE_TAPE)
                state.last_raw_bid = 0
                state.last_raw_ask = 0
                state.cont_bid     = 0.0
                state.cont_ask     = 0.0
                state.history.clear()
                continue

            if state.last_raw_bid == 0 and state.last_raw_ask == 0:
                state.last_raw_bid = raw_bid
                state.last_raw_ask = raw_ask
                continue

            eps_reset = 0.000001 if cfg.crypto_mode else 0.5

            if not state.tape_mode and new_bar_flag == 1:
                diff_bid = max(0.0, raw_bid)
                diff_ask = max(0.0, raw_ask)
            else:
                if raw_bid < (state.last_raw_bid - eps_reset):
                    diff_bid = max(0.0, raw_bid)
                else:
                    diff_bid = max(0.0, raw_bid - state.last_raw_bid)

                if raw_ask < (state.last_raw_ask - eps_reset):
                    diff_ask = max(0.0, raw_ask)
                else:
                    diff_ask = max(0.0, raw_ask - state.last_raw_ask)

            state.cont_bid += diff_bid
            state.cont_ask += diff_ask
            state.last_raw_bid = raw_bid
            state.last_raw_ask = raw_ask

            now_dt = datetime.now()
            if not state.history or (now_dt - state.history[-1][0]).total_seconds() > 0.03:
                state.history.append((now_dt, state.cont_bid, state.cont_ask))

    except Exception as e:
        print(f"Data Error: {e}")


def trim_history(cfg: AppConfig, state: AppState) -> None:
    now = datetime.now()
    while state.history and (now - state.history[0][0]).total_seconds() > cfg.time_window_seconds:
        state.history.popleft()


def compute_target(cfg: AppConfig, state: AppState) -> tuple[float, float]:
    if cfg.show_controls:
        if state.history:
            target_bid = state.cont_bid - state.history[0][1]
            target_ask = state.cont_ask - state.history[0][2]
        else:
            target_bid, target_ask = 0.0, 0.0
    else:
        if state.action_running:
            target_bid = state.cont_bid - state.action_ref_bid
            target_ask = state.cont_ask - state.action_ref_ask
        else:
            target_bid, target_ask = 0.0, 0.0
    return target_bid, target_ask


def smooth_volumes(cfg: AppConfig, state: AppState,
                   target_bid: float, target_ask: float) -> None:
    _init_state_extras(state)

    if abs(target_bid - state.current_bid_vol) > 0.01:
        state.current_bid_vol += (target_bid - state.current_bid_vol) * cfg.lerp_factor
    else:
        state.current_bid_vol = target_bid

    if abs(target_ask - state.current_ask_vol) > 0.01:
        state.current_ask_vol += (target_ask - state.current_ask_vol) * cfg.lerp_factor
    else:
        state.current_ask_vol = target_ask

    # Single-Mode Peak-Tracking mit langsamem Decay
    fps = max(getattr(cfg, 'fps', 60), 1)
    decay = 0.97 ** (1.0 / fps)

    # KRITISCH 3: Vol-Multiplier (aktuell vs. rollender Durchschnitt)
    now_dt       = datetime.now()
    current_total = state.current_bid_vol + state.current_ask_vol

    if (not state.vol_baseline_history or
            (now_dt - state.vol_baseline_history[-1][0]).total_seconds() > 0.5):
        state.vol_baseline_history.append((now_dt, current_total))

    baseline_secs = max(cfg.time_window_seconds * 6, 60)
    while (state.vol_baseline_history and
           (now_dt - state.vol_baseline_history[0][0]).total_seconds() > baseline_secs):
        state.vol_baseline_history.popleft()

    if len(state.vol_baseline_history) >= 10:
        avg = sum(v for _, v in state.vol_baseline_history) / len(state.vol_baseline_history)
        state.vol_multiplier = (current_total / avg) if avg > 0.1 else 1.0
    else:
        state.vol_multiplier = 1.0


def build_payload(cfg: AppConfig, state: AppState) -> str:
    return (f"{state.latest_time_str};"
            f"{format_price(state.latest_price)};"
            f"{format_number(cfg, state.current_bid_vol)};"
            f"{format_number(cfg, state.current_ask_vol)}\n")
