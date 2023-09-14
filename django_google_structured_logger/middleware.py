import json
import logging
import re
import uuid
from copy import deepcopy
from typing import Any, OrderedDict

from django.http import HttpRequest, HttpResponse  # type: ignore

from . import settings
from .storages import RequestStorage, _current_request

logger = logging.getLogger(__name__)


class SetRequestToLoggerMiddleware:
    """Middleware for logging requests and responses with sensitive data masked."""

    def __init__(self, get_response):
        # One-time configuration and initialization.
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        # Early exit if logging middleware is disabled
        if not settings.LOG_MIDDLEWARE_ENABLED:
            return self.get_response(request)

        # Code to be executed for each request before
        # the view (and later middleware) are called.

        response = self.get_response(request)
        # Code to be executed for each request/response after
        # the view is called.
        self.process_request(request)
        self.process_response(request, response)
        return response

    def process_request(self, request):
        """
        Log necessary data from the incoming request.

        Example:
        Input: Django request object
        Output: Logs the necessary details of the request
        """
        if self._is_ignored(request):
            return request

        user_id = lambda: self._get_user_id(request)  # noqa
        user_email = lambda: self._get_user_email(request)  # noqa
        request_uuid = str(uuid.uuid4())

        try:
            _current_request.set(
                RequestStorage(
                    user_id=user_id, user_email=user_email, uuid=request_uuid
                )
            )

            request_data = self._get_request_data(request)
            request_method = request_data["request"]["method"]
            request_path = request_data["request"]["path"]

            logger.info(
                f"Request {request_method} {request_path}",
                extra=request_data,
            )
        except Exception as exc:
            logger.exception(exc)

    def process_response(self, request, response):
        """
        Log necessary data from the outgoing response.

        Example:
        Input: Django request object, Django response object
        Output: Logs the necessary details of the response
        """
        if self._is_ignored(request):
            return response

        try:
            response_data = self._abridge(getattr(response, "data", None))
            response_status_code = getattr(response, "status_code", "Unknown STATUS")
            response_headers = self._exclude_keys(
                getattr(response, "headers", None), settings.LOG_EXCLUDED_HEADERS
            )

            data = {
                "response": {
                    "headers": response_headers,
                    "data": response_data,
                    "status_code": response_status_code,
                },
                "last_operation": True,
            }

            log_message = (
                f"Response {request.method} {request.path} > {response_status_code}"
            )
            logger_method = (
                logger.info if 199 < response_status_code < 300 else logger.warning
            )
            logger_method(log_message, extra=data)

        except Exception as exc:
            logger.exception(exc)

        return response

    def _abridge(self, data: Any) -> Any:
        """
        Abridge data based on length settings.

        Example:
        Input: {"name": "Very long name..."}
        Output: {"name": "Very long...SHORTENED"}
        """
        max_str_len = settings.LOG_MAX_STR_LEN
        max_list_len = settings.LOG_MAX_LIST_LEN

        if isinstance(data, dict):
            data = {k: self._abridge(v) for k, v in data.items() if k != "meta"}
        elif isinstance(data, str) and max_str_len and len(data) > max_str_len:
            return f"{data[:max_str_len]}..SHORTENED"
        elif isinstance(data, list) and max_list_len:
            return [self._abridge(item) for item in data[:max_list_len]]
        return data

    @staticmethod
    def _empty_value_none(
        obj: dict | OrderedDict | str | None,
    ) -> dict | OrderedDict | str | None:
        """
        Returns None if the value is empty.

        Example:
        Input: ""
        Output: None
        """
        return obj if bool(obj) else None

    @staticmethod
    def _mask_sensitive_data(
        obj: Any,
    ) -> str | dict | None:
        """Mask sensitive data in a dictionary based on specified keys and masking style.

        Args:
            obj: Dictionary containing potential sensitive data.

        Returns:
            dict: A new dictionary with sensitive data masked.

        Example:
            Given:
            obj = {"password": "my_secret_pass"}

            Returns based on style:
            - complete: {"password": "*********MASKED*********"}
            - partial: {"password": "my_s*****MASKED*****pass"}
            - custom: {"password": "my...ss"}
        """
        if not isinstance(obj, dict):
            return obj

        data = deepcopy(obj)
        data_keys = list(map(str, data.keys()))

        sensitive_keys = settings.LOG_SENSITIVE_KEYS
        mask_style = settings.LOG_MASK_STYLE

        def get_mask_function(style):
            if style == "complete":
                return lambda value: "*********MASKED*********"
            elif style == "partial":
                return lambda value: f"{value[:4]}*****MASKED*****{value[-4:]}"
            elif style == "custom":
                custom_style = settings.LOG_MASK_CUSTOM_STYLE
                return lambda value: custom_style.format(data=value)
            else:
                return lambda value: value

        mask_func = get_mask_function(mask_style)

        def _mask(_sensitive_keys: list[str]):
            for sensitive_key in _sensitive_keys:
                r = re.compile(sensitive_key, flags=re.IGNORECASE)
                match_keys = filter(r.match, data_keys)
                for key in match_keys:
                    data[key] = mask_func(data[key])

        _mask(sensitive_keys)

        return data

    @staticmethod
    def _exclude_keys(
        obj: dict | OrderedDict | None, keys_to_exclude: list[str]
    ) -> dict | None:
        """
        Exclude specific keys from a dictionary.

        Example:
        Input: {"key1": "value1", "key2": "value2"}, ["key2"]
        Output: {"key1": "value1"}
        """
        if obj is None:
            return None
        keys_to_exclude_set = set(map(str.lower, keys_to_exclude))
        return {k: v for k, v in obj.items() if k.lower() not in keys_to_exclude_set}

    def _get_request_data(self, request) -> dict[str, Any]:
        """
        Extract necessary request data for logging.

        Example:
        Input: Django request object with GET method
        Output: {"request": {"method": "GET", ...}}
        """
        return {
            "request": {
                "body": self._get_request_body(request),
                "query_params": self._empty_value_none(getattr(request, "GET", None)),
                "content_type": self._empty_value_none(
                    getattr(request, "content_type", None)
                ),
                "method": self._empty_value_none(getattr(request, "method", None)),
                "path": self._empty_value_none(getattr(request, "path", None)),
                "headers": self._empty_value_none(
                    self._exclude_keys(
                        getattr(request, "headers", None), settings.LOG_EXCLUDED_HEADERS
                    )
                ),
            }
        }

    def _get_request_body(self, request) -> str | dict | None:
        """
        Extract request body and mask sensitive data.

        Example:
        Input: Django request object with JSON body {"key": "value" }
        Output: {"key": "value"}
        """
        content_type = getattr(request, "content_type", None)

        def decode_and_abridge(body_bytes):
            body_str = body_bytes.decode("UTF-8") if body_bytes else None
            try:
                return self._abridge(json.loads(body_str))
            except Exception:  # noqa
                return self._abridge(body_str)

        match content_type:
            case "multipart/form-data":
                return "The image was uploaded to the server"
            case "application/json":
                return self._mask_sensitive_data(
                    decode_and_abridge(getattr(request, "body", None))
                )
            case "text/plain":
                return self._mask_sensitive_data(
                    self._abridge(getattr(request, "body", None))
                )
            case _:
                return self._mask_sensitive_data(content_type)

    def _get_user_id(self, request) -> Any:
        """
        Extract user ID from the request.

        Example:
        Input: Django request object with user ID 123
        Output: 123
        """
        return self._empty_value_none(
            getattr(request.user, settings.LOG_USER_ID_FIELD, None)
        )

    def _get_user_email(self, request) -> Any:
        """
        Extract user email from the request.

        Example:
        Input: Django request object with user email "test@example.com"
        Output: "test@example.com"
        """
        return self._empty_value_none(
            getattr(request.user, settings.LOG_USER_EMAIL_FIELD, None)
        )

    @staticmethod
    def _is_ignored(request) -> bool:
        """
        Determine if the request should be ignored based on path.

        Example:
        Input: Django request object with the path "__ignore_me__"
        Output: True
        """
        default_ignored = request.path.startswith("__")
        user_ignored = request.path in settings.LOG_EXCLUDED_ENDPOINTS
        return default_ignored or user_ignored
