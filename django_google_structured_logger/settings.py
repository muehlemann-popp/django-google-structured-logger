from django.conf import settings

from django_google_structured_logger.constants import DEFAULT_SENSITIVE_HEADERS, DEFAULT_SENSITIVE_KEYS

LOG_MAX_STR_LEN = getattr(settings, "LOG_MAX_STR_LEN", 200)
LOG_MAX_LIST_LEN = getattr(settings, "LOG_MAX_LIST_LEN", 10)
LOG_EXCLUDED_ENDPOINTS = getattr(settings, "LOG_EXCLUDED_ENDPOINTS", [])
LOG_SENSITIVE_KEYS = getattr(settings, "LOG_SENSITIVE_KEYS", DEFAULT_SENSITIVE_KEYS)
LOG_MASK_STYLE = getattr(settings, "LOG_MASK_STYLE", "partial")
LOG_MIDDLEWARE_ENABLED = getattr(settings, "LOG_MIDDLEWARE_ENABLED", True)
LOG_EXCLUDED_HEADERS = getattr(settings, "LOG_EXCLUDED_HEADERS", DEFAULT_SENSITIVE_HEADERS)
LOG_USER_ID_FIELD = getattr(settings, "LOG_USER_ID_FIELD", "id")
LOG_USER_DISPLAY_FIELD = getattr(settings, "LOG_USER_DISPLAY_FIELD", "email")
LOG_MAX_DEPTH = getattr(settings, "LOG_MAX_DEPTH", 4)
