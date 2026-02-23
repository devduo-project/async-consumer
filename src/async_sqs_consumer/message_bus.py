"""Message Bus for dispatching incoming SQS messages to handlers."""

import logging
from collections import defaultdict

from ._types import MessageHandler
from .event import Event


class MessageBus:
    """Dispatches incoming SQS messages to registered handlers by event_type.

    Unlike CommandBus (one handler per command type), MessageBus supports
    multiple handlers per event_type for fan-out within the consumer process.

    Handlers receive typed Event dataclass instances (not raw dicts).
    """

    def __init__(self, logger: logging.Logger) -> None:
        self.logger = logger
        self._handlers: dict[str, list[MessageHandler]] = defaultdict(list)
        self._event_classes: dict[str, type[Event]] = {}

    def register(self, event_type: str, event_class: type[Event], handler: MessageHandler) -> None:
        """Register a handler for an event type."""
        self._event_classes[event_type] = event_class
        self._handlers[event_type].append(handler)
        self.logger.debug(
            f"Registered message handler for event: {event_type}",
            extra={"event_type": event_type, "handler": handler.__name__},
        )

    async def dispatch(self, event_type: str, data: dict) -> None:
        """Dispatch a message to all handlers registered for the event type.

        Deserializes data dict into the registered Event dataclass
        before passing to handlers.
        """
        handlers = self._handlers.get(event_type, [])
        if not handlers:
            self.logger.warning(
                f"No handlers registered for event type: {event_type}",
                extra={"event_type": event_type},
            )
            return

        event_class = self._event_classes[event_type]
        event = event_class(**data)

        self.logger.info(
            f"Dispatching event {event_type} to {len(handlers)} handler(s)",
            extra={"event_type": event_type, "handler_count": len(handlers)},
        )

        for handler in handlers:
            try:
                await handler(event)
            except Exception:
                self.logger.error(
                    f"Handler {handler.__name__} failed for event {event_type}",
                    extra={"event_type": event_type, "handler": handler.__name__},
                    exc_info=True,
                )
                raise

    def get_registered_event_types(self) -> list[str]:
        """Get list of all registered event types."""
        return list(self._handlers.keys())
