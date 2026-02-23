"""SNS messaging service — abstract interface and aioboto3 implementation."""

import json
from abc import ABC, abstractmethod

import aioboto3


class AbstractSnsService(ABC):
    """Abstract interface for SNS publish operations."""

    @abstractmethod
    async def publish(
        self,
        topic_arn: str,
        message: dict,
        message_attributes: dict | None = None,
    ) -> str:
        """Publish a message to an SNS topic.

        Returns the MessageId.
        """


class SnsService(AbstractSnsService):
    """SNS messaging service using aioboto3."""

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
        return self._session.client("sns", endpoint_url=self._endpoint_url)

    async def publish(
        self,
        topic_arn: str,
        message: dict,
        message_attributes: dict | None = None,
    ) -> str:
        kwargs: dict = {
            "TopicArn": topic_arn,
            "Message": json.dumps(message),
        }
        if message_attributes:
            kwargs["MessageAttributes"] = message_attributes

        async with self._client() as sns:
            response = await sns.publish(**kwargs)
        return response["MessageId"]
