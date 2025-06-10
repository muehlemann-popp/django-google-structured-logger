import json
import logging
import uuid
from unittest.mock import Mock

import pytest
from django.contrib.auth import get_user_model
from django.core.handlers.wsgi import WSGIRequest
from django.test import Client, RequestFactory

from django_google_structured_logger.middlewares import LogRequestAndResponseMiddleware
from django_google_structured_logger.storages import RequestStorage, _current_request

User = get_user_model()


@pytest.fixture
def request_factory() -> RequestFactory:
    """Django request factory for creating mock requests."""
    return RequestFactory()


@pytest.fixture
def client() -> Client:
    """Django test client."""
    return Client()


@pytest.fixture
def mock_user() -> Mock:
    """Mock authenticated user."""
    user = Mock()
    user.id = 1
    user.email = "test@example.com"
    user.username = "testuser"
    user.is_authenticated = True
    user.is_anonymous = False
    return user


@pytest.fixture
def anonymous_user() -> Mock:
    """Mock anonymous user."""
    user = Mock()
    user.id = None
    user.email = None
    user.username = None
    user.is_authenticated = False
    user.is_anonymous = True
    return user


@pytest.fixture
def authenticated_request(request_factory: RequestFactory, mock_user: Mock) -> WSGIRequest:
    """HTTP request with authenticated user."""
    request = request_factory.get("/test/")
    request.user = mock_user
    return request


@pytest.fixture
def anonymous_request(request_factory: RequestFactory, anonymous_user: Mock) -> WSGIRequest:
    """HTTP request with anonymous user."""
    request = request_factory.get("/test/")
    request.user = anonymous_user
    return request


@pytest.fixture
def post_request_with_data(request_factory: RequestFactory, mock_user: Mock) -> WSGIRequest:
    """POST request with JSON data."""
    data = {"username": "test", "password": "secret123", "email": "test@example.com"}
    request = request_factory.post("/api/login/", data=data, content_type="application/json")
    request.user = mock_user
    return request


@pytest.fixture
def request_with_sensitive_headers(request_factory: RequestFactory, mock_user: Mock) -> WSGIRequest:
    """Request with sensitive headers."""
    request = request_factory.get(
        "/api/users/",
        HTTP_AUTHORIZATION="Bearer secret-token",
        HTTP_X_API_KEY="api-key-123",
        HTTP_COOKIE="sessionid=abc123",
    )
    request.user = mock_user
    return request


@pytest.fixture
def mock_request_storage():
    """Mock request storage for context testing."""
    storage = RequestStorage(uuid=str(uuid.uuid4()), user_id=lambda: 1, user_display_field=lambda: "test@example.com")
    _current_request.set(storage)
    yield storage
    _current_request.set(None)


@pytest.fixture
def mock_google_cloud_settings(settings):
    """Mock Google Cloud Project settings."""
    settings.GOOGLE_CLOUD_PROJECT = "test-project-123"
    return settings


@pytest.fixture
def middleware_settings(settings):
    """Configure middleware settings for testing."""
    settings.LOG_MIDDLEWARE_ENABLED = True
    settings.LOG_MAX_STR_LEN = 50
    settings.LOG_MAX_LIST_LEN = 5
    settings.LOG_MAX_DEPTH = 3
    settings.LOG_MASK_STYLE = "partial"
    settings.LOG_USER_ID_FIELD = "id"
    settings.LOG_USER_DISPLAY_FIELD = "email"
    settings.LOG_EXCLUDED_ENDPOINTS = ["/health/", "/metrics/"]
    return settings


@pytest.fixture
def mock_response() -> Mock:
    """Mock HTTP response."""
    response = Mock()
    response.status_code = 200
    response.content = b'{"success": true}'
    response.data = {"success": True}
    response.headers = {"Content-Type": "application/json"}
    return response


@pytest.fixture(autouse=True)
def clear_context():
    """Clear context vars before each test."""
    _current_request.set(None)
    yield
    _current_request.set(None)


@pytest.fixture
def error_response() -> Mock:
    """
    Mock HttpResponse object with error status code for testing logging of unsuccessful responses.
    """
    response = Mock(spec=LogRequestAndResponseMiddleware)
    response.status_code = 500
    error_data = {"error": "Internal Server Error", "status": "failed"}
    response.content = json.dumps(error_data).encode("utf-8")
    response.data = error_data
    response.headers = {"Content-Type": "application/json"}
    return response


@pytest.fixture
def request_to_ignored_endpoint(request_factory: RequestFactory) -> WSGIRequest:
    """
    A request to an endpoint that should be ignored according to the LOG_EXCLUDED_ENDPOINTS settings.
    """
    return request_factory.get("/health/")


@pytest.fixture
def request_with_long_data(request_factory: RequestFactory) -> WSGIRequest:
    """
    A request containing a body with a very long string, a long list, and a deeply nested dictionary to test the data reduction mechanism.
    """
    long_string = "a" * 300
    long_list = list(range(20))
    deep_dict = {"a": {"b": {"c": {"d": {"e": "f"}}}}}
    data = {"long_str": long_string, "long_list": long_list, "deep_dict": deep_dict}
    return request_factory.post("/long-data/", data=json.dumps(data), content_type="application/json")


@pytest.fixture
def response_with_long_data() -> Mock:
    """
    A response containing a body with a very long string, a long list, and a deeply nested dictionary to test the data reduction mechanism.
    """
    response = Mock(spec=LogRequestAndResponseMiddleware)
    long_string = "a" * 300
    long_list = list(range(20))
    deep_dict = {"a": {"b": {"c": {"d": {"e": "f"}}}}}
    data = {"long_str": long_string, "long_list": long_list, "deep_dict": deep_dict}

    response.status_code = 200
    response.data = data
    response.content = json.dumps(data).encode("utf-8")
    response.headers = {"Content-Type": "application/json"}
    return response


@pytest.fixture
def mock_graphene_info(mock_user: Mock) -> Mock:
    """
    Mock of the `info` object passed to Graphene resolvers.
    Contains a context with a user object.
    """
    info = Mock()
    info.context.user = mock_user
    return info


@pytest.fixture
def log_record_with_trace() -> logging.LogRecord:
    """
    A `logging.LogRecord` instance with OpenTelemetry tracing attributes for testing GoogleCloudFormatter.
    """
    record = logging.LogRecord(
        name="test_logger",
        level=logging.INFO,
        pathname="/app/tests.py",
        lineno=10,
        msg="Test message with trace",
        args=(),
        exc_info=None,
    )
    record.otelTraceID = "a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4"
    record.otelSpanID = "a1b2c3d4e5f6a1b2"
    record.otelTraceSampled = True
    return record
