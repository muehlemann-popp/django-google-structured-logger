import json
import logging
import re
import uuid
from copy import deepcopy
from typing import Any, Dict, List, Optional, Union

from django.http import HttpRequest, HttpResponse

from . import settings
from .storages import RequestStorage, _current_request

logger = logging.getLogger(__name__)


class SetUserContextMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        _current_request.set(
            RequestStorage(
                uuid=str(uuid.uuid4()),
                user_id=lambda: self._get_user_attribute(
                    request.user, settings.LOG_USER_ID_FIELD
                ),
                user_display_field=lambda: self._get_user_attribute(
                    request.user, settings.LOG_USER_DISPLAY_FIELD
                ),
            )
        )
        return self.get_response(request)

    @staticmethod
    def _get_user_attribute(user, attribute) -> Any:
        return getattr(user, attribute, None)


class LogRequestAndResponseMiddleware:
    """Middleware for logging requests and responses with sensitive data masked."""

    def __init__(self, get_response):
        self.get_response = get_response
        self.log_excluded_headers_set = set(
            map(str.lower, settings.LOG_EXCLUDED_HEADERS)
        )

    def __call__(self, request: HttpRequest) -> HttpResponse:
        if not settings.LOG_MIDDLEWARE_ENABLED:
            return self.get_response(request)

        self.process_request(request)
        response = self.get_response(request)
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

        try:
            path = self._empty_value_none(getattr(request, "path", None))
            method = self._empty_value_none(getattr(request, "method", None))
            content_type = self._empty_value_none(
                getattr(request, "content_type", None)
            )
            request_body = self._empty_value_none(getattr(request, "body", None))
            request_data = {
                "request": {
                    "body": self._get_request_body(content_type, request_body),
                    "query_params": self._empty_value_none(
                        getattr(request, "GET", None)
                    ),
                    "content_type": content_type,
                    "method": method,
                    "path": path,
                    "headers": self._empty_value_none(
                        self._exclude_keys(getattr(request, "headers", None))
                    ),
                },
                "first_operation": True,
            }

            logger.info(
                f"Request {method} {path}",
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
            if response_data is None:
                response_content = self._abridge(getattr(response, "content", None))
                content_type = self._empty_value_none(
                    getattr(request, "content_type", None)
                )
                response_data = (
                    self._get_request_body(content_type, response_content),
                )
            response_status_code = getattr(response, "status_code", 0)
            response_headers = self._exclude_keys(getattr(response, "headers", None))

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

    def _abridge(self, data: Any, current_depth: int = 0) -> Any:
        """
        Abridge data based on length settings and depth.

        Example:
        Input: {"name": "Very long name..."}
        Output: {"name": "Very long...SHORTENED"}
        """
        max_str_len = settings.LOG_MAX_STR_LEN
        max_list_len = settings.LOG_MAX_LIST_LEN
        max_depth = settings.LOG_MAX_DEPTH

        # Check for the depth threshold
        if current_depth > max_depth:
            return "..DEPTH EXCEEDED"

        if isinstance(data, dict):
            data = {
                k: self._abridge(v, current_depth + 1)
                for k, v in data.items()
                if k != "meta"
            }
        elif isinstance(data, str) and max_str_len and len(data) > max_str_len:
            return "{value}..SHORTENED".format(value=data[:max_str_len])
        elif isinstance(data, list) and max_list_len:
            return [
                self._abridge(item, current_depth + 1) for item in data[:max_list_len]
            ]
        return data

    @staticmethod
    def _empty_value_none(obj: Union[Dict, str, None]) -> Union[Dict, str, None]:
        """
        Returns None if the value is empty.

        Example:
        Input: ""
        Output: None
        """
        return obj if bool(obj) else None

    @staticmethod
    def _mask_sensitive_data(obj: Any) -> Union[str, Dict, None]:
        """Mask sensitive data in a dictionary based on specified keys and masking style.

        Args:
            obj: Dictionary containing potential sensitive data.

        Returns:
            dict: A new dictionary with sensitive data masked.

        Example:
            Given:
            obj = {"password": "my_secret_pass"}

            Returns based on style:
            - complete: {"password": "...FULL_MASKED..."}
            - partial: {"password": "my_s...MASKED...pass"}
        """
        if not isinstance(obj, dict):
            return obj

        data = deepcopy(obj)
        data_keys = list(map(str, data.keys()))

        sensitive_keys = settings.LOG_SENSITIVE_KEYS
        mask_style = settings.LOG_MASK_STYLE

        def get_mask_function(style):
            def complete_mask(value):
                return "...FULL_MASKED..."

            def partial_mask(value):
                length = len(value)
                if length <= 4:
                    return complete_mask(value)
                slice_value = min(4, length // 4)
                return "{prefix_value}...MASKED...{suffix_value}".format(
                    prefix_value=value[:slice_value], suffix_value=value[-slice_value:]
                )

            mask_styles = {
                "complete": complete_mask,
                "partial": partial_mask,
            }
            _mask_style = mask_styles.get(style)
            if _mask_style is None:
                logger.warning(
                    f"Invalid mask style {style}. Using default style 'partial'."
                )
                _mask_style = partial_mask
            return _mask_style

        mask_func = get_mask_function(mask_style)

        def _mask(_sensitive_keys: List[str]):
            for sensitive_key in _sensitive_keys:
                r = re.compile(sensitive_key, flags=re.IGNORECASE)
                match_keys = filter(r.match, data_keys)
                for key in match_keys:
                    data[key] = mask_func(data[key])

        _mask(sensitive_keys)

        return data

    def _exclude_keys(self, obj: Optional[Dict]) -> Optional[Dict]:
        """
        Exclude specific keys from a dictionary.

        Example:
        Input: {"key1": "value1", "key2": "value2"}, ["key2"]
        Output: {"key1": "value1"}
        """
        if obj is None:
            return None
        return {
            k: v
            for k, v in obj.items()
            if k.lower() not in self.log_excluded_headers_set
        }

    def _get_request_body(self, content_type, request_body) -> Union[str, Dict, None]:
        """
        Extract request body and mask sensitive data.

        Example:
        Input: Django request object with JSON body {"key": "value" }
        Output: {"key": "value"}
        """

        def decode_and_abridge(body_bytes):
            body_str = body_bytes.decode("UTF-8") if body_bytes else None
            try:
                return self._abridge(json.loads(body_str))
            except Exception:  # noqa
                return self._abridge(body_str)

        # Using traditional conditional checks instead of `match` for Python < 3.10 compatibility
        if content_type == "multipart/form-data":
            return "The image was uploaded to the server"
        elif content_type == "application/json":
            return self._mask_sensitive_data(decode_and_abridge(request_body))
        elif content_type == "text/plain":
            return self._mask_sensitive_data(self._abridge(request_body))
        else:
            return self._mask_sensitive_data(content_type)

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
