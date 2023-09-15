import json
import logging
import uuid
from typing import Any

from django.http import HttpResponse

from . import settings
from .middlewares import LogRequestAndResponseMiddleware
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


class GrapheneLogRequestAndResponseMiddleware(LogRequestAndResponseMiddleware):
    def resolve(self, next, root, info, **args):
        if not settings.LOG_MIDDLEWARE_ENABLED:
            return next(root, info, **args)

        # Graphene middleware doesn't give access to the raw request/response
        # Instead, the `info` argument provides a `context` attribute which usually contains the request
        request = info.context

        self.process_request(request)

        # Since there's no direct access to the response,
        # we can't process the response in the same way.
        # But we can capture the result of the GraphQL execution.
        result = next(root, info, **args)
        # Here, `result` is the data returned from your GraphQL resolvers.
        # We're wrapping it in a Django HttpResponse to use the existing process_response function.
        fake_response = HttpResponse(content=json.dumps(result))
        self.process_response(request, fake_response)

        return result
