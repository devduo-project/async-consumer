# async-consumer

Async consumer with MessageBus dispatch for Python 3.12+.

## Installation

### pip
```bash
pip install "async-consumer @ git+https://github.com/devduo-project/async-consumer.git@v0.1.0"
```
### PDM
```bash
pdm add "async-consumer @ git+https://github.com/devduo-project/async-consumer.git@v0.1.0"
```

## Usage

```python
import asyncio
import logging
from dataclasses import dataclass

from async_consumer import SqsConsumer, MessageBus, SqsService, Event


# Define your event
@dataclass
class OrderCreated(Event):
    order_id: str


# Define your handler
async def handle_order_created(event: OrderCreated) -> None:
    print(f"Order created: {event.order_id}")


# Create SQS service
sqs_service = SqsService(
    endpoint_url="https://sqs.eu-central-1.amazonaws.com",
    region="eu-central-1",
    access_key="...",
    secret_key="...",
)

# Build message bus and register handlers.
# "order.created" is the event_type string from the SQS message JSON body:
# {"event_type": "order.created", "data": {"order_id": "123"}}
bus = MessageBus(logger=logging.getLogger("message_bus"))
bus.register("order.created", OrderCreated, handle_order_created)

# Start consumer
async def main() -> None:
    consumer = SqsConsumer(
        sqs_service=sqs_service,
        message_bus=bus,
        queue_configs=[{"name": "orders", "url": "https://..."}],
    )
    await consumer.start()


asyncio.run(main())
```
