"""SQS Consumer — polls SQS queues and dispatches messages to MessageBus."""

import asyncio
import json
import logging

from .message_bus import MessageBus
from .sqs_service import AbstractSqsService

logger = logging.getLogger(__name__)


class SqsConsumer:
    """Long-polling SQS consumer that dispatches messages via MessageBus."""

    def __init__(
        self,
        sqs_service: AbstractSqsService,
        message_bus: MessageBus,
        queue_configs: list[dict],
    ) -> None:
        self._sqs_service = sqs_service
        self._message_bus = message_bus
        self._queue_configs = queue_configs
        self._running = False
        self._tasks: list[asyncio.Task] = []

    async def start(self) -> None:
        """Start polling all configured queues."""
        self._running = True
        logger.info(
            f"Starting SQS consumer for {len(self._queue_configs)} queue(s)",
            extra={"queues": [qc["name"] for qc in self._queue_configs]},
        )
        for qc in self._queue_configs:
            task = asyncio.create_task(self._poll_queue(qc))
            self._tasks.append(task)
        await asyncio.gather(*self._tasks, return_exceptions=True)

    async def stop(self) -> None:
        """Signal all polling loops to stop."""
        logger.info("Stopping SQS consumer...")
        self._running = False
        for task in self._tasks:
            task.cancel()
        await asyncio.gather(*self._tasks, return_exceptions=True)
        self._tasks.clear()
        logger.info("SQS consumer stopped")

    async def _poll_queue(self, queue_config: dict) -> None:
        """Continuously poll a single queue."""
        queue_url = queue_config["url"]
        queue_name = queue_config["name"]
        logger.info(f"Polling queue: {queue_name} ({queue_url})")

        while self._running:
            try:
                messages = await self._sqs_service.receive_messages(queue_url)
                for message in messages:
                    await self._process_message(queue_url, queue_name, message)
            except asyncio.CancelledError:
                break
            except Exception:
                logger.error(
                    f"Error polling queue {queue_name}",
                    extra={"queue": queue_name},
                    exc_info=True,
                )
                await asyncio.sleep(5)

    async def _process_message(self, queue_url: str, queue_name: str, message: dict) -> None:
        """Parse, dispatch, and acknowledge a single SQS message."""
        message_id = message.get("MessageId", "unknown")
        receipt_handle = message["ReceiptHandle"]

        try:
            body = json.loads(message["Body"])

            # Unwrap SNS envelope if present
            if body.get("Type") == "Notification":
                body = json.loads(body["Message"])

            event_type = body.get("event_type")
            data = body.get("data", {})

            if not event_type:
                logger.warning(
                    f"Message {message_id} missing event_type, skipping",
                    extra={"queue": queue_name, "message_id": message_id},
                )
                await self._sqs_service.delete_message(queue_url, receipt_handle)
                return

            logger.info(
                f"Processing message {message_id}: {event_type}",
                extra={
                    "queue": queue_name,
                    "message_id": message_id,
                    "event_type": event_type,
                },
            )

            await self._message_bus.dispatch(event_type, data)
            await self._sqs_service.delete_message(queue_url, receipt_handle)

            logger.info(
                f"Message {message_id} processed and deleted",
                extra={"queue": queue_name, "message_id": message_id},
            )

        except Exception:
            logger.error(
                f"Failed to process message {message_id}, leaving for retry",
                extra={"queue": queue_name, "message_id": message_id},
                exc_info=True,
            )
