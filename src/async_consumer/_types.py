"""Shared type aliases."""

from collections.abc import Callable, Coroutine
from typing import Any

from .event import Event

MessageHandler = Callable[[Event], Coroutine[Any, Any, None]]
