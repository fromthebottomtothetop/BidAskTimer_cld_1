# -*- coding: utf-8 -*-
import time
from datetime import datetime

from model import AppConfig, AppState
from ui_draw import format_number, format_price


def process_incoming_data(cfg: AppConfig, state: AppState) -> None:
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
                state.latest_time_str = parts[0].split(".")[0] if len(parts[0]) > 0 else "Time Error"
                state.latest_price = float(parts[1].replace(",", "."))
                raw_bid = float(parts[4].replace(",", "."))
                raw_ask = float(parts[5].replace(",", "."))
            except ValueError:
                continue

            now_sec = time.time()
            state.last_rx_time = now_sec

            if state.last_stale_raw_bid is None:
                state.last_stale_raw_bid = raw_bid
                state.last_stale_raw_ask = raw_ask
                state.last_stale_price = state.latest_price
                state.last_change_bid_t = now_sec
                state.last_change_ask_t = now_sec
                state.last_change_price_t = now_sec
            else:
                if raw_bid != state.last_stale_raw_bid:
                    state.last_change_bid_t = now_sec
                    state.last_stale_raw_bid = raw_bid
                if raw_ask != state.last_stale_raw_ask:
                    state.last_change_ask_t = now_sec
                    state.last_stale_raw_ask = raw_ask
                if state.latest_price != state.last_stale_price:
                    state.last_change_price_t = now_sec
                    state.last_stale_price = state.latest_price

            new_bar_flag = 0
            if len(parts) >= 7:
                try:
                    new_bar_flag = int(parts[6])
                except Exception:
                    new_bar_flag = 0

            if state.last_raw_bid == 0 and state.last_raw_ask == 0:
                state.last_raw_bid = raw_bid
                state.last_raw_ask = raw_ask
                continue

            eps_reset = 0.000001 if cfg.crypto_mode else 0.5

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


def smooth_volumes(cfg: AppConfig, state: AppState, target_bid: float, target_ask: float) -> None:
    if abs(target_bid - state.current_bid_vol) > 0.01:
        state.current_bid_vol += (target_bid - state.current_bid_vol) * cfg.lerp_factor
    else:
        state.current_bid_vol = target_bid

    if abs(target_ask - state.current_ask_vol) > 0.01:
        state.current_ask_vol += (target_ask - state.current_ask_vol) * cfg.lerp_factor
    else:
        state.current_ask_vol = target_ask


def build_payload(cfg: AppConfig, state: AppState) -> str:
    disp_bid = format_number(cfg, state.current_bid_vol)
    disp_ask = format_number(cfg, state.current_ask_vol)
    disp_price = format_price(state.latest_price)
    return f"{state.latest_time_str};{disp_price};{disp_bid};{disp_ask}\n"

