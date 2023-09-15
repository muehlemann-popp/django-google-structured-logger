from django.conf import settings

DEFAULT_SENSITIVE_KEYS = [
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

DEFAULT_SENSITIVE_HEADERS = (
    [
        "Authorization",  # Tokens and credentials
        "Cookie",  # User session identifiers
        "Set-Cookie",  # Server set session identifiers
        "X-API-Key",  # API keys
        "X-CSRFToken",  # CSRF tokens
        "Proxy-Authorization",  # Credentials for a proxy connection
        "If-None-Match",  # Can be used for cache fingerprinting
        "Server",  # Can reveal specifics about the server
        "WWW-Authenticate",  # Authentication method details
        "X-Correlation-ID",  # Correlation IDs for logging
        "X-Frame-Options",  # Security-related header
        "Strict-Transport-Security",  # Security-related header
        "X-XSS-Protection",  # Security-related header
        "X-Content-Type-Options",  # Security-related header
        "X-Download-Options",  # Security-related header
        "X-Permitted-Cross-Domain-Policies",  # Security-related header
    ],
)

LOG_MAX_STR_LEN = getattr(settings, "LOG_MAX_STR_LEN", 200)
LOG_MAX_LIST_LEN = getattr(settings, "LOG_MAX_LIST_LEN", 10)
LOG_EXCLUDED_ENDPOINTS = getattr(settings, "LOG_EXCLUDED_ENDPOINTS", [])
LOG_SENSITIVE_KEYS = getattr(settings, "LOG_SENSITIVE_KEYS", DEFAULT_SENSITIVE_KEYS)
LOG_MASK_STYLE = getattr(settings, "LOG_MASK_STYLE", "partially")
LOG_MIDDLEWARE_ENABLED = getattr(settings, "LOG_MIDDLEWARE_ENABLED", True)
LOG_EXCLUDED_HEADERS = getattr(
    settings, "LOG_EXCLUDED_HEADERS", DEFAULT_SENSITIVE_HEADERS
)
LOG_USER_ID_FIELD = getattr(settings, "LOG_USER_ID_FIELD", "id")
LOG_USER_DISPLAY_FIELD = getattr(settings, "LOG_USER_DISPLAY_FIELD", "email")
LOG_MAX_DEPTH = getattr(settings, "LOG_MAX_DEPTH", 4)
