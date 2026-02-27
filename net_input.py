# -*- coding: utf-8 -*-
import socket
import threading
import time
from typing import List, Optional

from model import AppConfig, AppState


class InputServer:
    def __init__(self, cfg: AppConfig, state: AppState) -> None:
        self._cfg = cfg
        self._state = state
        self._sock: Optional[socket.socket] = None
        self._thread: Optional[threading.Thread] = None
        self._stop = threading.Event()
        self._clients: List[socket.socket] = []
        self._lock = threading.Lock()

    def client_count(self) -> int:
        with self._lock:
            return len(self._clients)

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

    def _flush_queue(self) -> None:
        # FIX #1: Alle alten Daten aus der Queue entfernen wenn eine neue
        # Verbindung aufgebaut wird. Verhindert dass Python nach einem
        # ATAS-Neustart kurz falsche Werte anzeigt weil noch alte
        # Basis-Werte in der Queue lagen.
        flushed = 0
        while True:
            try:
                self._state.data_queue.get_nowait()
                flushed += 1
            except Exception:
                break
        if flushed > 0:
            print(f"[INPUT] Queue geflusht: {flushed} alte Eintraege verworfen.")

        # Auch den Akkumulierungs-State zuruecksetzen damit diff-Berechnung
        # nicht auf alten raw-Werten aufsetzt.
        self._state.last_raw_bid = 0
        self._state.last_raw_ask = 0
        self._state.cont_bid     = 0.0
        self._state.cont_ask     = 0.0
        self._state.history.clear()

    def _handle_client(self, conn: socket.socket) -> None:
        # Queue leeren bevor wir die ersten Daten der neuen Verbindung
        # verarbeiten.
        self._flush_queue()

        with self._lock:
            self._clients.append(conn)

        try:
            buffer = ""
            conn.settimeout(1.0)
            while not self._stop.is_set():
                try:
                    data = conn.recv(int(self._cfg.buffer_size))
                except socket.timeout:
                    continue
                except OSError:
                    break
                if not data:
                    break

                buffer += data.decode("utf-8", errors="replace")
                while "\n" in buffer:
                    line, buffer = buffer.split("\n", 1)
                    if line.strip():
                        self._state.data_queue.put(line.strip())
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
            self._sock.bind((self._cfg.host, int(self._cfg.port_in)))
            self._sock.listen()
            print(f"[INPUT] TCP Server running on {self._cfg.host}:{self._cfg.port_in}")

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
            print(f"[INPUT] Server Bind Error ({self._cfg.host}:{self._cfg.port_in}): {e}")
            self._state.data_queue.put("Error Bind;;;;;0;0;0")
        finally:
            self.stop()
