# async-sqs-consumer

Async SQS consumer with MessageBus dispatch for Python 3.12+.

## Installation

```bash
pip install "async-sqs-consumer @ git+https://github.com/org/async-sqs-consumer.git@v0.1.0"
```

## Usage

```python
from async_sqs_consumer import SqsConsumer, MessageBus, SqsService, Event

# Define your event
@dataclass
class OrderCreated(Event):
    order_id: str

# Create SQS service
sqs_service = SqsService(
    endpoint_url="https://sqs.eu-central-1.amazonaws.com",
    region="eu-central-1",
    access_key="...",
    secret_key="...",
)

# Build message bus
bus = MessageBus(logger=logging.getLogger("message_bus"))
bus.register("order.created", OrderCreated, handle_order_created)

# Start consumer
consumer = SqsConsumer(
    sqs_service=sqs_service,
    message_bus=bus,
    queue_configs=[{"name": "orders", "url": "https://..."}],
)
await consumer.start()
```
