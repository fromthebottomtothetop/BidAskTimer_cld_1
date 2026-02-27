# -*- coding: utf-8 -*-
import socket
import threading
import time
from typing import List, Optional

from model import AppConfig, AppState


class OutputServer:
    def __init__(self, cfg: AppConfig, state: AppState) -> None:
        self._cfg = cfg
        self._state = state
        self._sock: Optional[socket.socket] = None
        self._thread: Optional[threading.Thread] = None
        self._stop = threading.Event()

        self._clients: List[socket.socket] = []
        self._lock = threading.Lock()

        self._last_sent_payload: str | None = None
        self._last_send_time: float = 0.0

    def start(self) -> None:
        self.stop()
        self._stop.clear()
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def restart(self) -> None:
        self.start()

    def stop(self) -> None:
        self._stop.set()
        with self._lock:
            for c in list(self._clients):
                try:
                    c.shutdown(socket.SHUT_RDWR)
                    c.close()
                except Exception:
                    pass
            self._clients.clear()

        if self._sock:
            try:
                self._sock.close()
            except Exception:
                pass
        self._sock = None

    def _handle_client(self, conn: socket.socket) -> None:
        with self._lock:
            self._clients.append(conn)

        try:
            try:
                conn.sendall(f"HELLO;{self._cfg.indicator_name}\n".encode("utf-8"))
            except Exception:
                pass

            conn.settimeout(1.0)
            while not self._stop.is_set():
                try:
                    data = conn.recv(1)
                    if not data:
                        break
                except socket.timeout:
                    continue
                except OSError:
                    break
        finally:
            try:
                conn.close()
            except Exception:
                pass
            with self._lock:
                if conn in self._clients:
                    self._clients.remove(conn)

    def _run(self) -> None:
        self._sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            self._sock.bind((self._cfg.host, int(self._cfg.port_out)))
            self._sock.listen()
            print(f"[OUTPUT] TCP Server running on {self._cfg.host}:{self._cfg.port_out}")

            while not self._stop.is_set():
                try:
                    self._sock.settimeout(1.0)
                    conn, addr = self._sock.accept()
                    t = threading.Thread(target=self._handle_client, args=(conn,), daemon=True)
                    t.start()
                except socket.timeout:
                    continue
                except OSError:
                    break
        except Exception as e:
            print(f"[OUTPUT] Server Bind Error ({self._cfg.host}:{self._cfg.port_out}): {e}")
        finally:
            self.stop()

    def broadcast(self, payload_line: str) -> None:
        # FIX #4: Lock NUR fuer das Kopieren der Liste halten.
        # sendall() laeuft ausserhalb des Locks damit ein langsamer/blockender
        # Client nicht den gesamten Main-Thread einfriert.
        data = payload_line.encode("utf-8", errors="replace")
        with self._lock:
            clients_snapshot = list(self._clients)

        dead = []
        for c in clients_snapshot:
            try:
                c.sendall(data)
            except Exception:
                dead.append(c)

        if dead:
            with self._lock:
                for c in dead:
                    try:
                        c.close()
                    except Exception:
                        pass
                    if c in self._clients:
                        self._clients.remove(c)

    def maybe_broadcast(self, payload: str) -> None:
        t_now = time.time()
        if (payload != self._last_sent_payload) and \
                ((t_now - self._last_send_time) >= float(self._cfg.min_send_interval)):
            self._last_sent_payload = payload
            self._last_send_time = t_now
            if not self._stop.is_set():
                self.broadcast(payload)
