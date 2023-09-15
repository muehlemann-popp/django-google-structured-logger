## Django Google Structured Logger

**Django Google Structured Logger** is a Django middleware designed to capture and log details from incoming requests and outgoing responses. It offers features to mask sensitive data, set default fields for Google Cloud Logging, and structure logs in a detailed and organized manner.

## Contents
* [Features](#features)
* [Usage](#usage)
* [Key Components](#key-components)
* [Settings](#settings)
* [Conclusion](#conclusion)

### Features:

1. **Detailed Logging**: Logs both requests and responses with meticulous details.
2. **Sensitive Data Masking**: Masks sensitive information using customizable regex patterns.
3. **Google Cloud Logging Support**: Formats logs to match Google Cloud Logging standards.
4. **Configurable Settings**: Customize log behavior through Django settings.

### Usage:

1. Add `GoogleFormatter` to your Django's `LOGGING` setting.
   Example:
   ```python
   LOGGING = {
       "version": 1,
       "disable_existing_loggers": False,
       "formatters": {
           "json": {
               "()": "django_google_structured_logger.formatter.GoogleFormatter",
           },
       },
       "handlers": {
           "google-json-handler": {
               "class": "logging.StreamHandler",
               "formatter": "json",
           },
       },
       "root": {
           "handlers": ["google-json-handler"],
           "level": logging.INFO,
       }
   }
   ```
2. Add `SetRequestToLoggerMiddleware` to your Django's `MIDDLEWARE` setting.

    Example for Django middleware:
    ```python
    MIDDLEWARE = [
        ...
        # Ordering is important:
        "django_google_structured_logger.middlewares.SetUserContextMiddleware",  # Set user context to logger.
        "django_google_structured_logger.middlewares.LogRequestAndResponseMiddleware",  # Log request and response.
    ]
    ```
   Example for GRAPHENE middleware:
   ```python
    GRAPHENE = {
         "MIDDLEWARE": [
              ...
              # Ordering is important:
              "django_google_structured_logger.graphene_middlewares.GrapheneSetUserContextMiddleware",  # Set user context to logger.
              "django_google_structured_logger.graphene_middlewares.GrapheneLogRequestAndResponseMiddleware",  # Log request and response.
         ]
    }
   ```
3. Ensure your Django project has the necessary configurations in the `settings.py`.

### Key Components:

#### 1. middleware.py

- **SetRequestToLoggerMiddleware**: This class contains methods to process incoming requests and outgoing responses and then log them. It supports features like abridging lengthy data and masking sensitive information.

#### 2. formatter.py

- **GoogleFormatter**: Extends `jsonlogger.JsonFormatter` to format logs specifically for Google Cloud Logging. It sets default fields such as severity, labels, operation, and source location based on Google's logging standards.

#### 3. settings.py

- Provides a list of default sensitive keys for data masking.
- Allows customization of logging behavior with options to specify maximum string length, excluded endpoints, sensitive keys, and more.

### Settings:

These are the settings that can be customized for the middleware:

- `LOG_MAX_STR_LEN`: Maximum string length before data is abridged. Default is `200`.
- `LOG_MAX_LIST_LEN`: Maximum list length before data is abridged. Default is `10`.
- `LOG_EXCLUDED_ENDPOINTS`: List of endpoints to exclude from logging. Default is an `empty list`.
- `LOG_SENSITIVE_KEYS`: Regex patterns for keys which contain sensitive data. Defaults `DEFAULT_SENSITIVE_KEYS`.
- `LOG_MASK_STYLE`: Style for masking sensitive data. Default is `"partially"`.
- `LOG_MIDDLEWARE_ENABLED`: Enable or disable the logging middleware. Default is `True`.
- `LOG_EXCLUDED_HEADERS`: List of request headers to exclude from logging. Defaults `DEFAULT_SENSITIVE_HEADERS`.
- `LOG_USER_ID_FIELD`: Field name for user ID. Default is `"id"`.
- `LOG_USER_EMAIL_FIELD`: Field name for user email. Default is `"email"`.
- `LOG_MAX_DEPTH`: Maximum depth for data to be logged. Default is `4`.

Note:
- All settings are imported from `django_google_structured_logger.settings`.


### Other Notes:
- `extra` kwargs passed to logger, for example:
  ```python
  logger.info("some message", extra={"some_key": "some_data}
  ```
  will be logged as structured data in the `jsonPayload` field in Google Cloud Logging.
  Any data passed to extra kwargs will not be abridged or masked.
- `extra` kwargs passed to logger may override any default fields set by `GoogleFormatter`.


### Conclusion:

**SetRequestToLoggerMiddleware** is a comprehensive solution for those seeking enhanced logging capabilities in their Django projects, with particular attention to sensitive data protection and compatibility with Google Cloud Logging.

To get started, integrate the provided middleware, formatter, and settings into your Django project, customize as needed, and enjoy advanced logging capabilities!
