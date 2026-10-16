import threading


_lock = threading.Lock()
_shutdown_callback = None


def set_shutdown_callback(callback):
    global _shutdown_callback

    with _lock:
        _shutdown_callback = callback


def request_shutdown():
    with _lock:
        callback = _shutdown_callback
    if callback is not None:
        callback()
