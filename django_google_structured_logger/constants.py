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

DEFAULT_SENSITIVE_HEADERS = [
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
]
