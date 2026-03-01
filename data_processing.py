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
    if not hasattr(state, 'bid_baseline_history'):
        state.bid_baseline_history = collections.deque()
    if not hasattr(state, 'ask_baseline_history'):
        state.ask_baseline_history = collections.deque()
    if not hasattr(state, 'bid_multiplier'):
        state.bid_multiplier = 1.0
    if not hasattr(state, 'ask_multiplier'):
        state.ask_multiplier = 1.0
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

            # Mode-Feld explizit lesen
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

            # BUG FIX 1: Flag=1 gilt jetzt fuer BEIDE Modi (Candle UND Tape).
            # Vorher: "if not state.tape_mode and new_bar_flag == 1"
            # Problem: Im Tape-Mode wurde Flag=1 ignoriert. Der eps_reset-
            # Fallback funktioniert nur wenn der neue Bar-Wert kleiner ist als
            # der alte. Mit Queue-Drain wird das "Reset-auf-0"-Paket jedoch
            # uebersprungen - Python sieht direkt den schon akkumulierten
            # neuen Wert (z.B. 600) der groesser ist als der alte (z.B. 20).
            # eps_reset greift nicht -> diff wird falsch berechnet.
            # Flag=1 loest das zuverlaessig fuer beide Modi.
            if new_bar_flag == 1:
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

    state.current_bid_vol = target_bid
    state.current_ask_vol = target_ask

    fps = max(getattr(cfg, 'fps', 60), 1)
    decay = 0.97 ** (1.0 / fps)

    now_dt        = datetime.now()
    factor        = max(int(getattr(cfg, "mult_baseline_factor", 6)), 1)
    baseline_secs = max(cfg.time_window_seconds * factor, 30)

    def _update_mult(history, cur_vol):
        if not history or (now_dt - history[-1][0]).total_seconds() > 0.5:
            history.append((now_dt, cur_vol))
        while history and (now_dt - history[0][0]).total_seconds() > baseline_secs:
            history.popleft()
        if len(history) >= 10:
            avg = sum(v for _, v in history) / len(history)
            return (cur_vol / avg) if avg > 0.1 else 1.0
        return 1.0

    state.bid_multiplier = _update_mult(state.bid_baseline_history, state.current_bid_vol)
    state.ask_multiplier = _update_mult(state.ask_baseline_history, state.current_ask_vol)


def build_payload(cfg: AppConfig, state: AppState) -> str:
    return (f"{state.latest_time_str};"
            f"{format_price(state.latest_price)};"
            f"{format_number(cfg, state.current_bid_vol)};"
            f"{format_number(cfg, state.current_ask_vol)}\n")
