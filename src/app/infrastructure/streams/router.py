from __future__ import annotations

import logging
from collections.abc import Awaitable, Callable

from src.app.domain.events.task_event import EventType, TaskEvent

logger = logging.getLogger(__name__)

EventHandler = Callable[[TaskEvent], Awaitable[None]]


class EventRouter:
    def __init__(self) -> None:
        self._handlers: dict[EventType, EventHandler] = {}

    def register(self, event_type: EventType, handler: EventHandler) -> None:
        self._handlers[event_type] = handler

    def get_handler(self, event_type: EventType) -> EventHandler | None:
        return self._handlers.get(event_type)

    async def dispatch(self, event: TaskEvent) -> None:
        handler = self.get_handler(event.type)
        if handler is None:
            logger.warning(
                "No handler registered for event type",
                extra={"type": event.type},
            )
            return
        await handler(event)
