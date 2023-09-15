from contextvars import ContextVar
from dataclasses import dataclass
from typing import Callable, Optional


@dataclass(frozen=True)
class RequestStorage:
    uuid: str
    user_id: Callable[[], Optional[int]] = lambda: None
    user_display_field: Callable[[], Optional[str]] = lambda: None


_current_request: ContextVar[Optional[RequestStorage]] = ContextVar(
    "_current_request", default=None
)


def get_current_request() -> Optional[RequestStorage]:
    return _current_request.get()
