from queue import Empty, Full, Queue
from threading import Lock
from typing import Any


MAX_PENDING_EVENTS = 100

_subscribers: set[Queue] = set()
_subscribers_lock = Lock()


def subscribe() -> Queue:
    subscriber = Queue(maxsize=MAX_PENDING_EVENTS)

    with _subscribers_lock:
        _subscribers.add(subscriber)

    return subscriber


def unsubscribe(subscriber: Queue) -> None:
    with _subscribers_lock:
        _subscribers.discard(subscriber)


def publish(event: dict[str, Any]) -> None:
    with _subscribers_lock:
        subscribers = list(_subscribers)

    for subscriber in subscribers:
        try:
            subscriber.put_nowait(event.copy())
        except Full:
            try:
                subscriber.get_nowait()
            except Empty:
                pass

            try:
                subscriber.put_nowait(event.copy())
            except Full:
                pass
