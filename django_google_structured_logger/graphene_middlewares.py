import logging
import uuid
from typing import Any

from . import settings
from .storages import RequestStorage, _current_request

logger = logging.getLogger(__name__)


class GrapheneSetUserContextMiddleware:
    def resolve(self, next, root, info, **args):
        _current_request.set(
            RequestStorage(
                uuid=str(uuid.uuid4()),
                user_id=lambda: self._get_user_attribute(
                    info.context.user, settings.LOG_USER_ID_FIELD
                ),
                user_display_field=lambda: self._get_user_attribute(
                    info.context.user, settings.LOG_USER_DISPLAY_FIELD
                ),
            )
        )

        return next(root, info, **args)

    @staticmethod
    def _get_user_attribute(user, attribute) -> Any:
        return getattr(user, attribute, None)
