import pytest
import uuid
from unittest.mock import Mock

from django.contrib.auth import get_user_model
from django.test import RequestFactory, Client
from django.http import HttpRequest

from django_google_structured_logger.storages import RequestStorage, _current_request


User = get_user_model()


@pytest.fixture
def request_factory():
    """Django request factory for creating mock requests."""
    return RequestFactory()


@pytest.fixture
def client():
    """Django test client."""
    return Client()


@pytest.fixture
def mock_user():
    """Mock authenticated user."""
    user = Mock()
    user.id = 1
    user.email = "test@example.com"
    user.username = "testuser"
    user.is_authenticated = True
    user.is_anonymous = False
    return user


@pytest.fixture
def anonymous_user():
    """Mock anonymous user."""
    user = Mock()
    user.id = None
    user.email = None
    user.username = None
    user.is_authenticated = False
    user.is_anonymous = True
    return user


@pytest.fixture
def authenticated_request(request_factory, mock_user):
    """HTTP request with authenticated user."""
    request = request_factory.get("/test/")
    request.user = mock_user
    return request


@pytest.fixture
def anonymous_request(request_factory, anonymous_user):
    """HTTP request with anonymous user."""
    request = request_factory.get("/test/")
    request.user = anonymous_user
    return request


@pytest.fixture
def post_request_with_data(request_factory, mock_user):
    """POST request with JSON data."""
    data = {"username": "test", "password": "secret123", "email": "test@example.com"}
    request = request_factory.post(
        "/api/login/",
        data=data,
        content_type="application/json"
    )
    request.user = mock_user
    return request


@pytest.fixture
def request_with_sensitive_headers(request_factory, mock_user):
    """Request with sensitive headers."""
    request = request_factory.get(
        "/api/users/",
        HTTP_AUTHORIZATION="Bearer secret-token",
        HTTP_X_API_KEY="api-key-123",
        HTTP_COOKIE="sessionid=abc123"
    )
    request.user = mock_user
    return request


@pytest.fixture
def mock_request_storage():
    """Mock request storage for context testing."""
    storage = RequestStorage(
        uuid=str(uuid.uuid4()),
        user_id=lambda: 1,
        user_display_field=lambda: "test@example.com"
    )
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
def mock_response():
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
