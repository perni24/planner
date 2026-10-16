import threading
import time
from contextlib import contextmanager
from contextvars import ContextVar

from config import SHUTDOWN_OPERATION_GRACE_SECONDS


_deadline = ContextVar("operation_deadline", default=None)
_lock = threading.Lock()
_shutdown_at = None


def reset_operations():
    """Solo prima dell'avvio, quando non ci sono worker del precedente server."""
    global _shutdown_at
    with _lock:
        _shutdown_at = None


def request_stop():
    """La prima richiesta fissa la scadenza; le successive non la prolungano."""
    global _shutdown_at
    with _lock:
        if _shutdown_at is None:
            _shutdown_at = time.monotonic()


def is_stopping():
    with _lock:
        return _shutdown_at is not None


def operation_deadline(seconds):
    deadline = time.monotonic() + seconds
    inherited = _deadline.get()
    return min(deadline, inherited) if inherited is not None else deadline


@contextmanager
def operation_scope(seconds):
    token = _deadline.set(operation_deadline(seconds))
    try:
        check_operation()
        yield
    finally:
        _deadline.reset(token)


def cancellation_requested(deadline=None):
    now = time.monotonic()
    deadline = _deadline.get() if deadline is None else deadline
    with _lock:
        stopped = _shutdown_at is not None and now >= (
            _shutdown_at + SHUTDOWN_OPERATION_GRACE_SECONDS
        )
    return stopped or (deadline is not None and now >= deadline)


def check_operation(deadline=None):
    if cancellation_requested(deadline):
        if is_stopping():
            raise InterruptedError("Operation cancelled during application shutdown")
        raise TimeoutError("Database operation exceeded its time limit")
