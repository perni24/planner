import asyncio
import json
from queue import Empty

from starlette.responses import StreamingResponse
from starlette.routing import Route

from services.event_service import subscribe, unsubscribe


HEARTBEAT_INTERVAL_SECONDS = 30


async def stream_events(request):
    subscriber = subscribe()

    async def event_stream():
        try:
            while True:
                if await request.is_disconnected():
                    break

                try:
                    event = await asyncio.to_thread(
                        subscriber.get,
                        True,
                        HEARTBEAT_INTERVAL_SECONDS,
                    )
                except Empty:
                    yield ": heartbeat\n\n"
                    continue

                yield f"data: {json.dumps(event)}\n\n"
        finally:
            unsubscribe(subscriber)

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


routes = [
    Route("/events", endpoint=stream_events),
]
