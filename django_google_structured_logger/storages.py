from contextvars import ContextVar
from dataclasses import dataclass
from typing import Callable


@dataclass(frozen=True)
class RequestStorage:
    user_id: Callable[[], int]
    user_email: Callable[[], str]
    uuid: str


_current_request: ContextVar[RequestStorage | None] = ContextVar(
    "_current_request", default=None
)


def get_current_request() -> RequestStorage | None:
    return _current_request.get()
