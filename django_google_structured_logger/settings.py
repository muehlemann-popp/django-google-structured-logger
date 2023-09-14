from django.conf import settings  # type: ignore

DEFAULT_LOG_SENSITIVE_KEYS = [
    "^password$",
    ".*secret.*",
    ".*token.*",
    ".*key.*",
    ".*pass.*",
    ".*auth.*",
    "^Bearer.*",
    ".*ssn.*",  # Social Security Number (or equivalent in some countries)
    ".*credit.*card.*",  # Credit card numbers
    ".*cvv.*",  # CVV code for credit cards
    ".*dob.*",  # Date of Birth
    ".*pin.*",  # Personal Identification Numbers
    ".*salt.*",  # Salts used in cryptography
    ".*encrypt.*",  # Encryption keys or related values
    ".*api.*",  # API keys
    ".*jwt.*",  # JSON Web Tokens
    ".*session.*id.*",  # Session Identifiers
    "^Authorization$",  # Authorization headers
    ".*user.*name.*",  # Usernames (can sometimes be used in combination with other data for malicious purposes)
    ".*address.*",  # Physical or email addresses
    ".*phone.*",  # Phone numbers
    "^otp.*",  # One-Time Passwords or related values
]
LOG_MAX_STR_LEN = getattr(settings, "LOG_MAX_STR_LEN", 200)
LOG_MAX_LIST_LEN = getattr(settings, "LOG_MAX_LIST_LEN", 10)
LOG_EXCLUDED_ENDPOINTS = getattr(settings, "LOG_EXCLUDED_ENDPOINTS", [])
LOG_SENSITIVE_KEYS = getattr(settings, "LOG_SENSITIVE_KEYS", DEFAULT_LOG_SENSITIVE_KEYS)
LOG_MASK_STYLE = getattr(settings, "LOG_MASK_STYLE", "partially")
LOG_MASK_CUSTOM_STYLE = getattr(settings, "LOG_MASK_CUSTOM_STYLE", "{data}")
LOG_MIDDLEWARE_ENABLED = getattr(settings, "LOG_MIDDLEWARE_ENABLED", True)
LOG_EXCLUDED_HEADERS = getattr(settings, "LOG_EXCLUDED_HEADERS", ["Authorization"])
LOG_USER_ID_FIELD = getattr(settings, "LOG_USER_ID_FIELD", "id")
LOG_USER_EMAIL_FIELD = getattr(settings, "LOG_USER_EMAIL_FIELD", "email")
