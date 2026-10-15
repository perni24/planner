import threading
import unittest
from queue import Full, ShutDown
from unittest.mock import Mock, patch

from services import event_service


def test_closing_subscribers_unblocks_pending_queue_reads():
    subscriber = event_service.subscribe()
    stopped = threading.Event()

    def read_event():
        try:
            subscriber.get(timeout=2)
        except ShutDown:
            stopped.set()

    thread = threading.Thread(target=read_event)
    thread.start()
    try:
        event_service.close_subscribers()
        assert stopped.wait(timeout=1)
        thread.join(timeout=1)
        assert not thread.is_alive()
        assert subscriber not in event_service._subscribers
    finally:
        event_service.close_subscribers()
        thread.join(timeout=3)


def test_publishing_during_subscriber_shutdown_does_not_raise():
    subscriber = Mock()
    subscriber.put_nowait.side_effect = ShutDown
    with patch.object(event_service, "_subscribers", {subscriber}):
        event_service.publish({"entity": "tasks", "action": "updated", "ids": [1]})


def test_unsubscribe_closes_queue_even_before_server_shutdown():
    subscriber = event_service.subscribe()
    event_service.unsubscribe(subscriber)
    assert subscriber not in event_service._subscribers
    try:
        subscriber.get_nowait()
    except ShutDown:
        pass
    else:
        raise AssertionError("Unsubscribed queues must not leave executor reads blocked")


def test_full_queue_can_be_closed_while_publishing():
    subscriber = Mock()
    subscriber.put_nowait.side_effect = [Full, ShutDown]
    subscriber.get_nowait.side_effect = ShutDown
    with patch.object(event_service, "_subscribers", {subscriber}):
        event_service.publish({"entity": "tasks", "action": "updated", "ids": [1]})


def test_new_subscribers_work_after_previous_server_stops():
    old = event_service.subscribe()
    event_service.close_subscribers()
    current = event_service.subscribe()
    try:
        event = {"entity": "projects", "action": "created", "ids": [2]}
        event_service.publish(event)
        assert current.get_nowait() == event
        try:
            old.get_nowait()
        except ShutDown:
            pass
        else:
            raise AssertionError("Previous subscriber queue must remain closed")
    finally:
        event_service.close_subscribers()


def load_tests(loader, tests, pattern):
    return unittest.TestSuite(
        unittest.FunctionTestCase(function)
        for name, function in globals().items()
        if name.startswith("test_") and callable(function)
    )


if __name__ == "__main__":
    unittest.main()
