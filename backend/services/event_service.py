from queue import Empty, Full, Queue, ShutDown
from threading import Lock
from typing import Any

from services.operation_control import is_stopping


MAX_PENDING_EVENTS = 100

_subscribers: set[Queue] = set()
_subscribers_lock = Lock()


def subscribe() -> Queue:
    subscriber = Queue(maxsize=MAX_PENDING_EVENTS)

    with _subscribers_lock:
        if is_stopping():
            subscriber.shutdown(immediate=True)
        else:
            _subscribers.add(subscriber)

    return subscriber


def unsubscribe(subscriber: Queue) -> None:
    with _subscribers_lock:
        _subscribers.discard(subscriber)
    subscriber.shutdown(immediate=True)


def close_subscribers() -> None:
    """Sblocca le letture SSE prima della chiusura dell'event loop del server."""
    with _subscribers_lock:
        subscribers = list(_subscribers)
        _subscribers.clear()

    for subscriber in subscribers:
        subscriber.shutdown(immediate=True)


def publish(event: dict[str, Any]) -> None:
    with _subscribers_lock:
        subscribers = list(_subscribers)

    for subscriber in subscribers:
        try:
            subscriber.put_nowait(event.copy())
        except ShutDown:
            continue
        except Full:
            try:
                subscriber.get_nowait()
            except (Empty, ShutDown):
                pass

            try:
                subscriber.put_nowait(event.copy())
            except (Full, ShutDown):
                pass
