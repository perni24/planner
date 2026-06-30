import os
import threading
import time


HEARTBEAT_INTERVAL_SECONDS = 10
HEARTBEAT_TIMEOUT_SECONDS = 60

_last_heartbeat = time.monotonic()
_lock = threading.Lock()
_monitor_started = False
_shutdown_callback = None


def register_heartbeat():
    global _last_heartbeat

    with _lock:
        _last_heartbeat = time.monotonic()


def set_shutdown_callback(callback):
    global _shutdown_callback

    _shutdown_callback = callback


def request_shutdown():
    if _shutdown_callback:
        _shutdown_callback()
        return

    os._exit(0)


def start_heartbeat_monitor(enabled):
    global _monitor_started

    if not enabled or _monitor_started:
        return

    register_heartbeat()
    _monitor_started = True

    monitor_thread = threading.Thread(target=_monitor_heartbeat, daemon=True)
    monitor_thread.start()


def _monitor_heartbeat():
    while True:
        time.sleep(HEARTBEAT_INTERVAL_SECONDS)

        with _lock:
            seconds_without_heartbeat = time.monotonic() - _last_heartbeat

        if seconds_without_heartbeat >= HEARTBEAT_TIMEOUT_SECONDS:
            request_shutdown()
            return
