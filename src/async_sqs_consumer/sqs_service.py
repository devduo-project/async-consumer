"""SQS messaging service — abstract interface and aioboto3 implementation."""

import json
from abc import ABC, abstractmethod

import aioboto3


class AbstractSqsService(ABC):
    """Abstract interface for SQS operations."""

    @abstractmethod
    async def send_message(
        self,
        queue_url: str,
        message: dict,
        message_attributes: dict | None = None,
    ) -> str:
        """Send a message to an SQS queue.

        Returns the MessageId.
        """

    @abstractmethod
    async def receive_messages(
        self,
        queue_url: str,
        max_messages: int = 10,
        wait_time_seconds: int = 20,
        visibility_timeout: int = 30,
    ) -> list[dict]:
        """Receive messages from an SQS queue using long-polling."""

    @abstractmethod
    async def delete_message(self, queue_url: str, receipt_handle: str) -> None:
        """Delete a processed message from the queue."""


class SqsService(AbstractSqsService):
    """SQS messaging service using aioboto3."""

    def __init__(
        self,
        endpoint_url: str,
        region: str,
        access_key: str,
        secret_key: str,
    ) -> None:
        self._endpoint_url = endpoint_url
        self._session = aioboto3.Session(
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            region_name=region,
        )

    def _client(self):
        return self._session.client("sqs", endpoint_url=self._endpoint_url)

    async def send_message(
        self,
        queue_url: str,
        message: dict,
        message_attributes: dict | None = None,
    ) -> str:
        kwargs: dict = {
            "QueueUrl": queue_url,
            "MessageBody": json.dumps(message),
        }
        if message_attributes:
            kwargs["MessageAttributes"] = message_attributes

        async with self._client() as sqs:
            response = await sqs.send_message(**kwargs)
        return response["MessageId"]

    async def receive_messages(
        self,
        queue_url: str,
        max_messages: int = 10,
        wait_time_seconds: int = 20,
        visibility_timeout: int = 30,
    ) -> list[dict]:
        async with self._client() as sqs:
            response = await sqs.receive_message(
                QueueUrl=queue_url,
                MaxNumberOfMessages=max_messages,
                WaitTimeSeconds=wait_time_seconds,
                VisibilityTimeout=visibility_timeout,
                MessageAttributeNames=["All"],
            )
        return response.get("Messages", [])

    async def delete_message(self, queue_url: str, receipt_handle: str) -> None:
        async with self._client() as sqs:
            await sqs.delete_message(
                QueueUrl=queue_url,
                ReceiptHandle=receipt_handle,
            )
