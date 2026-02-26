"""Base event class for event pattern."""

from dataclasses import asdict, dataclass


@dataclass
class Event:
    """Base class for all events."""

    def to_dict(self) -> dict:
        """Convert event to dictionary."""
        return asdict(self)
