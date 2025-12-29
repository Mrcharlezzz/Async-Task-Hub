import asyncio
from uuid import uuid4

import pytest
from redis.exceptions import ConnectionError, TimeoutError

from src.app.domain.events.task_event import EventType, TaskEvent
from src.app.domain.models.task_progress import TaskProgress
from src.app.domain.models.task_state import TaskState
from src.app.domain.models.task_status import TaskStatus
from src.app.infrastructure.streams.client import StreamsClient
from src.app.infrastructure.streams.consumer import StreamsConsumer
from src.app.infrastructure.streams.publisher import StreamsPublisher
from src.app.infrastructure.streams.router import EventRouter
from src.setup.stream_config import StreamSettings


@pytest.mark.asyncio
async def test_streams_consumer_dispatches_events() -> None:
    redis_url = StreamSettings().REDIS_URL
    if not redis_url:
        pytest.skip("REDIS_URL not set; skipping streams integration test.")

    stream_name = f"test:events:{uuid4().hex}"  # Unique stream per test avoids collisions.
    group = "test-group"
    consumer_name = f"test-consumer-{uuid4().hex}"
    task_id = uuid4().hex

    client = StreamsClient(redis_url)
    try:
        await client.redis.ping()
    except (ConnectionError, TimeoutError):
        await client.close()
        pytest.skip(f"Cannot reach Redis at {redis_url}; skipping streams integration test.")
    router = EventRouter()
    status_seen = asyncio.Event()
    result_seen = asyncio.Event()
    status_payload: dict[str, object] = {}
    result_payload: dict[str, object] = {}

    async def handle_status(event: TaskEvent) -> None:
        nonlocal status_payload
        status_payload = event.payload
        status_seen.set()

    async def handle_result(event: TaskEvent) -> None:
        nonlocal result_payload
        result_payload = event.payload
        result_seen.set()

    router.register(EventType.TASK_STATUS, handle_status)
    router.register(EventType.TASK_RESULT, handle_result)

    consumer = StreamsConsumer(
        client,
        stream=stream_name,
        group=group,
        consumer_name=consumer_name,
        router=router,
        block_ms=100,
        count=10,
        reclaim_pending=False,
        reclaim_idle_ms=1000,
    )
    publisher = StreamsPublisher(client, stream_name)

    try:
        await consumer.start()
        status = TaskStatus(
            state=TaskState.RUNNING,
            progress=TaskProgress(current=1, total=2, percentage=0.5),
        )
        await publisher.publish(
            [
                TaskEvent.status(task_id, status),
                TaskEvent.result(task_id, {"task_id": task_id, "data": {"value": 42}}),
            ]
        )

        await asyncio.wait_for(status_seen.wait(), timeout=2)
        await asyncio.wait_for(result_seen.wait(), timeout=2)

        assert status_payload["status"]["state"] == TaskState.RUNNING.value
        assert result_payload["result"]["data"]["value"] == 42
    finally:
        await consumer.stop()
        await client.redis.delete(stream_name)
        await client.close()
