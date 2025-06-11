## Django Google Structured Logger

[![PyPI version](https://badge.fury.io/py/django-google-structured-logger.svg)](https://badge.fury.io/py/django-google-structured-logger)
[![Python Versions](https://img.shields.io/pypi/pyversions/django-google-structured-logger)](https://pypi.org/project/django-google-structured-logger/)
[![Django Versions](https://img.shields.io/pypi/djversions/django-google-structured-logger)](https://pypi.org/project/django-google-structured-logger/)
[![codecov](https://codecov.io/gh/muehlemann-popp/django-google-structured-logger/graph/badge.svg?token=2X2RMRFOZO)](https://codecov.io/gh/muehlemann-popp/django-google-structured-logger)
![Mypy Checked](https://img.shields.io/badge/checked%20with-mypy-blue.svg)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![Taskfile](https://img.shields.io/badge/Task-Taskfile-blue?logo=data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSI1MDAiIGhlaWdodD0iNTAwIiB2aWV3Qm94PSIwIDAgMzc1IDM3NSI+PHBhdGggZmlsbD0iIzI5YmViMCIgZD0iTSAxODcuNTcwMzEyIDE5MC45MzM1OTQgTCAxODcuNTcwMzEyIDM3NSBMIDMwLjA3MDMxMiAyNzkuNTM1MTU2IEwgMzAuMDcwMzEyIDk1LjQ2NDg0NCBaIi8+PHBhdGggZmlsbD0iIzY5ZDJjOCIgZD0iTSAxODcuNTcwMzEyIDE5MC45MzM1OTQgTCAxODcuNTcwMzEyIDM3NSBMIDM0NS4wNzAzMTIgMjc5LjUzNTE1NiBMIDM0NS4wNzAzMTIgOTUuNDY0ODQ0IFoiLz48cGF0aCBmaWxsPSIjOTRkZmQ4IiBkPSJNIDE4Ny41NzAzMTIgMTkwLjkzMzU5NCBMIDMwLjA3MDMxMiA5NS40NjQ4NDQgTCAxODcuNTcwMzEyIDAgTCAzNDUuMDcwMzEyIDk1LjQ2NDg0NCBaIi8+PC9zdmc+)](https://taskfile.dev/)

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

#### Installation

You can install the package using pip:

```bash
pip install django-google-structured-logger
```

#### Configuration

1. Add a formatter to your Django's `LOGGING` setting.

   **For standard JSON logging:**
   ```python
    LOGGING = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "json": {
                "()": "django_google_structured_logger.formatter.StandardJSONFormatter",
            },
        },
        "handlers": {
            "console": {
                "level": "INFO",
                "class": "logging.StreamHandler",
            },
            "json-handler": {
                "class": "logging.StreamHandler",
                "formatter": "json",
            },
        },
        "root": {
            "handlers": [env.str("DJANGO_LOG_HANDLER", "json-handler")],
            "level": env.str("ROOT_LOG_LEVEL", "INFO"),
        },
        "loggers": {
            "()": {
                "handlers": [env.str("DJANGO_LOG_HANDLER", "json-handler")],
                "level": env.str("DJANGO_LOG_LEVEL", "INFO"),
            },
            "django": {
                "handlers": [env.str("DJANGO_LOG_HANDLER", "json-handler")],
                "level": env.str("DJANGO_LOG_LEVEL", "INFO"),
                "propagate": False,
            },
            "django.server": {
                "handlers": [env.str("DJANGO_LOG_HANDLER", "json-handler")],
                "level": env.str("DJANGO_SERVER_LEVEL", "ERROR"),
                "propagate": False,
            },
            "django.request": {
                "handlers": [env.str("DJANGO_LOG_HANDLER", "json-handler")],
                "level": env.str("DJANGO_REQUEST_LEVEL", "ERROR"),
                "propagate": False,
            },
        },
    }
   ```

   **For Google Cloud Logging integration:**
   ```python
    LOGGING = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "google": {
                "()": "django_google_structured_logger.formatter.GoogleCloudFormatter",
            },
        },
        "handlers": {
            "console": {
                "level": "INFO",
                "class": "logging.StreamHandler",
            },
            "google-json-handler": {
                "class": "logging.StreamHandler",
                "formatter": "google",
            },
        },
        "root": {
            "handlers": [env.str("DJANGO_LOG_HANDLER", "google-json-handler")],
            "level": env.str("ROOT_LOG_LEVEL", "INFO"),
        },
        "loggers": {
            "()": {
                "handlers": [env.str("DJANGO_LOG_HANDLER", "google-json-handler")],
                "level": env.str("DJANGO_LOG_LEVEL", "INFO"),
            },
            "django": {
                "handlers": [env.str("DJANGO_LOG_HANDLER", "google-json-handler")],
                "level": env.str("DJANGO_LOG_LEVEL", "INFO"),
                "propagate": False,
            },
            "django.server": {
                "handlers": [env.str("DJANGO_LOG_HANDLER", "google-json-handler")],
                "level": env.str("DJANGO_SERVER_LEVEL", "ERROR"),
                "propagate": False,
            },
            "django.request": {
                "handlers": [env.str("DJANGO_LOG_HANDLER", "google-json-handler")],
                "level": env.str("DJANGO_REQUEST_LEVEL", "ERROR"),
                "propagate": False,
            },
        },
    }
   ```

   Alternatively, you can configure the formatter class via Django settings:
   ```python
   # For standard JSON logging (default)
   LOG_FORMATTER_CLASS = "django_google_structured_logger.formatter.StandardJSONFormatter"
   
   # For Google Cloud Logging
   LOG_FORMATTER_CLASS = "django_google_structured_logger.formatter.GoogleCloudFormatter"
   ```

2. Add middleware to your Django's `MIDDLEWARE` setting.

    Django middleware:
    ```python
    MIDDLEWARE = [
        ...
        # Ordering is important:
        "django_google_structured_logger.middlewares.SetUserContextMiddleware",  # Set user context to logger.
        "django_google_structured_logger.middlewares.LogRequestAndResponseMiddleware",  # Log request and response.
    ]
    ```
   GRAPHENE middleware:
   ```python
    GRAPHENE = {
         "MIDDLEWARE": [
              ...
              "django_google_structured_logger.graphene_middlewares.GrapheneSetUserContextMiddleware",  # Set user context to logger.
         ]
    }
   ```
3. Ensure your Django project has the necessary configurations in the `settings.py`.

### Key Components:

#### 1. middlewares.py

- **SetUserContextMiddleware**: Sets user context information for logging throughout the request lifecycle.
- **LogRequestAndResponseMiddleware**: Processes incoming requests and outgoing responses and logs them. It supports features like abridging lengthy data and masking sensitive information.

#### 2. formatter.py

- **StandardJSONFormatter**: A universal JSON log formatter that creates structured logs with fields like severity, source_location, labels, operation, and http_request/http_response. Suitable for any logging system that accepts JSON format.
- **GoogleCloudFormatter**: Extends `StandardJSONFormatter` to format logs specifically for Google Cloud Logging. It remaps standard fields to Google Cloud's specific field names (e.g., `logging.googleapis.com/sourceLocation`) and adds trace correlation support.

#### 3. settings.py

- Provides a list of default sensitive keys for data masking.
- Allows customization of logging behavior with options to specify maximum string length, excluded endpoints, sensitive keys, and more.

### Settings:

These are the settings that can be customized for the middleware:

- `LOG_FORMATTER_CLASS`: Formatter class to use. Default is `"django_google_structured_logger.formatter.StandardJSONFormatter"`.
- `LOG_MAX_STR_LEN`: Maximum string length before data is abridged. Default is `200`.
- `LOG_MAX_LIST_LEN`: Maximum list length before data is abridged. Default is `10`.
- `LOG_EXCLUDED_ENDPOINTS`: List of endpoints to exclude from logging. Default is an `empty list`.
- `LOG_SENSITIVE_KEYS`: Regex patterns for keys which contain sensitive data. Defaults `DEFAULT_SENSITIVE_KEYS`.
- `LOG_MASK_STYLE`: Style for masking sensitive data. Default is `"partial"`.
- `LOG_MIDDLEWARE_ENABLED`: Enable or disable the logging middleware. Default is `True`.
- `LOG_EXCLUDED_HEADERS`: List of request headers to exclude from logging. Defaults `DEFAULT_SENSITIVE_HEADERS`.
- `LOG_USER_ID_FIELD`: Field name for user ID. Default is `"id"`.
- `LOG_USER_DISPLAY_FIELD`: Field name for user email. Default is `"email"`.
- `LOG_MAX_DEPTH`: Maximum depth for data to be logged. Default is `4`.

Note:
- All settings are imported from `django_google_structured_logger.constants`.


### Other Notes:
- `extra` kwargs passed to logger, for example:
  ```python
  logger.info("some message", extra={"some_key": "some_data}
  ```
  will be logged as structured data in the `jsonPayload` field in Google Cloud Logging.
  Any data passed to extra kwargs will not be abridged or masked.
- `extra` kwargs passed to logger may override any default fields set by the formatters.


### Conclusion:

**Django Google Structured Logger** is a comprehensive solution for those seeking enhanced logging capabilities in their Django projects, with particular attention to sensitive data protection and compatibility with Google Cloud Logging.

To get started, integrate the provided middleware, formatter, and settings into your Django project, customize as needed, and enjoy advanced logging capabilities!
