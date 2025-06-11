import uuid
from typing import Callable
from unittest.mock import Mock, patch

import pytest
from django.conf import LazySettings
from django.core.handlers.wsgi import WSGIRequest
from django.http import HttpResponse

from django_google_structured_logger.graphene_middlewares import GrapheneSetUserContextMiddleware
from django_google_structured_logger.middlewares import LogRequestAndResponseMiddleware, SetUserContextMiddleware
from django_google_structured_logger.storages import RequestStorage, _current_request


class TestSetUserContextMiddleware:
    """Tests for SetUserContextMiddleware that manages user context in request storage."""

    @pytest.fixture
    def mock_get_response(self) -> Callable[[WSGIRequest], HttpResponse]:
        """Mock get_response function that returns a basic HttpResponse."""

        def get_response(request: WSGIRequest) -> HttpResponse:
            return HttpResponse("Test response")

        return get_response

    @pytest.fixture
    def middleware(self, mock_get_response: Callable[[WSGIRequest], HttpResponse]) -> SetUserContextMiddleware:
        """SetUserContextMiddleware instance."""
        return SetUserContextMiddleware(mock_get_response)

    def test_authenticated_user_context(
        self,
        middleware: SetUserContextMiddleware,
        authenticated_request: WSGIRequest,
        middleware_settings: LazySettings,
    ):
        """Test that authenticated user context is correctly set in RequestStorage."""
        assert middleware_settings.LOG_MIDDLEWARE_ENABLED
        # Call middleware
        response = middleware(authenticated_request)

        # Get the current request storage
        storage = _current_request.get()

        # Verify storage was created
        assert storage is not None
        assert isinstance(storage.uuid, str)
        assert uuid.UUID(storage.uuid)  # Verify valid UUID format

        # Verify user data extraction
        assert storage.user_id() == 1  # mock_user.id
        assert storage.user_display_field() == "test@example.com"  # mock_user.email

        # Verify response is returned
        assert response.status_code == 200

    def test_anonymous_user_context(
        self, middleware: SetUserContextMiddleware, anonymous_request: WSGIRequest, middleware_settings: LazySettings
    ):
        """Test that anonymous user context sets user fields to None."""
        assert middleware_settings.LOG_MIDDLEWARE_ENABLED
        # Call middleware
        response = middleware(anonymous_request)

        # Get the current request storage
        storage = _current_request.get()

        # Verify storage was created
        assert storage is not None
        assert isinstance(storage.uuid, str)
        assert uuid.UUID(storage.uuid)  # Verify valid UUID format

        # Verify anonymous user data
        assert storage.user_id() is None
        assert storage.user_display_field() is None

        # Verify response is returned
        assert response.status_code == 200

    def test_custom_user_fields(
        self,
        mock_get_response: Callable[[WSGIRequest], HttpResponse],
        authenticated_request: WSGIRequest,
        settings: LazySettings,
    ):
        """Test middleware uses custom LOG_USER_ID_FIELD and LOG_USER_DISPLAY_FIELD settings."""

        # Configure custom user field settings
        settings.LOG_USER_ID_FIELD = "username"
        settings.LOG_USER_DISPLAY_FIELD = "username"

        # Ensure mock user has username attribute
        assert authenticated_request.user.is_authenticated
        assert hasattr(authenticated_request.user, "username")
        authenticated_request.user.username = "testuser"

        # Patch the settings in the middleware module and create new instance
        with (
            patch("django_google_structured_logger.middlewares.settings.LOG_USER_ID_FIELD", "username"),
            patch("django_google_structured_logger.middlewares.settings.LOG_USER_DISPLAY_FIELD", "username"),
        ):
            middleware = SetUserContextMiddleware(mock_get_response)
            response = middleware(authenticated_request)

        # Get the current request storage
        storage = _current_request.get()

        # Verify storage was created
        assert storage is not None
        assert isinstance(storage.uuid, str)

        # Verify custom field extraction
        assert storage.user_id() == "testuser"
        assert storage.user_display_field() == "testuser"

        # Verify response is returned
        assert response.status_code == 200

    def test_missing_user_attributes(
        self,
        mock_get_response: Callable[[WSGIRequest], HttpResponse],
        authenticated_request: WSGIRequest,
        settings: LazySettings,
    ):
        """Test middleware handles missing user attributes gracefully."""

        # Configure non-existent field
        settings.LOG_USER_ID_FIELD = "nonexistent_field"
        settings.LOG_USER_DISPLAY_FIELD = "another_missing_field"

        # Patch the settings in the middleware module and create new instance
        with (
            patch("django_google_structured_logger.middlewares.settings.LOG_USER_ID_FIELD", "nonexistent_field"),
            patch(
                "django_google_structured_logger.middlewares.settings.LOG_USER_DISPLAY_FIELD", "another_missing_field"
            ),
        ):
            middleware = SetUserContextMiddleware(mock_get_response)
            middleware(authenticated_request)

            # Get the current request storage
            storage = _current_request.get()

            # Verify storage was created
            assert storage is not None

            # Verify missing attributes return None
            assert storage.user_id() is None
            assert storage.user_display_field() is None

    def test_multiple_requests_different_contexts(
        self,
        middleware: SetUserContextMiddleware,
        authenticated_request: WSGIRequest,
        anonymous_request: WSGIRequest,
        middleware_settings: LazySettings,
    ):
        """Test that each request gets its own context storage."""
        assert middleware_settings.LOG_MIDDLEWARE_ENABLED
        # Process authenticated request
        middleware(authenticated_request)
        auth_storage = _current_request.get()
        assert auth_storage is not None
        auth_uuid = auth_storage.uuid
        auth_user_id = auth_storage.user_id()

        # Process anonymous request
        middleware(anonymous_request)
        anon_storage = _current_request.get()
        assert anon_storage is not None
        anon_uuid = anon_storage.uuid
        anon_user_id = anon_storage.user_id()

        # Verify different UUIDs and user contexts
        assert auth_uuid != anon_uuid
        assert auth_user_id == 1
        assert anon_user_id is None

    def test_uuid_uniqueness(
        self,
        middleware: SetUserContextMiddleware,
        authenticated_request: WSGIRequest,
        middleware_settings: LazySettings,
    ):
        """Test that each middleware call generates a unique UUID."""
        assert middleware_settings.LOG_MIDDLEWARE_ENABLED
        uuids = set()

        # Call middleware multiple times
        for _ in range(5):
            middleware(authenticated_request)
            storage = _current_request.get()
            assert storage is not None
            uuids.add(storage.uuid)

        # Verify all UUIDs are unique
        assert len(uuids) == 5


@patch("django_google_structured_logger.middlewares.logger")
class TestLogRequestAndResponseMiddleware:
    def test_basic_request_and_response_logging(
        self,
        mock_logger: Mock,
        authenticated_request: WSGIRequest,
        mock_response: HttpResponse,
        get_response_factory: Callable[[HttpResponse], Callable[[WSGIRequest], HttpResponse]],
    ):
        middleware = LogRequestAndResponseMiddleware(get_response_factory(mock_response))
        middleware(authenticated_request)

        assert mock_logger.info.call_count == 2
        request_log_call = mock_logger.info.call_args_list[0]
        response_log_call = mock_logger.info.call_args_list[1]

        assert "request" in request_log_call.kwargs["extra"]
        assert request_log_call.kwargs["extra"]["first_operation"] is True
        assert request_log_call.kwargs["extra"]["request"]["method"] == "GET"

        assert "response" in response_log_call.kwargs["extra"]
        assert response_log_call.kwargs["extra"]["last_operation"] is True
        assert response_log_call.kwargs["extra"]["response"]["status_code"] == 200

    def test_error_response_logging(
        self,
        mock_logger: Mock,
        authenticated_request: WSGIRequest,
        error_response: HttpResponse,
        get_response_factory: Callable[[HttpResponse], Callable[[WSGIRequest], HttpResponse]],
    ):
        middleware = LogRequestAndResponseMiddleware(get_response_factory(error_response))
        middleware(authenticated_request)

        mock_logger.info.assert_called_once()
        mock_logger.warning.assert_called_once()

        response_log_call = mock_logger.warning.call_args_list[0]
        assert "response" in response_log_call.kwargs["extra"]
        assert response_log_call.kwargs["extra"]["response"]["status_code"] == 500

    def test_ignored_endpoint_from_settings(
        self,
        mock_logger: Mock,
        request_to_ignored_endpoint: WSGIRequest,
        mock_response: HttpResponse,
        get_response_factory: Callable[[HttpResponse], Callable[[WSGIRequest], HttpResponse]],
    ):
        middleware = LogRequestAndResponseMiddleware(get_response_factory(mock_response))
        middleware(request_to_ignored_endpoint)
        mock_logger.info.assert_not_called()
        mock_logger.warning.assert_not_called()

    def test_excluded_headers(
        self,
        mock_logger: Mock,
        request_with_sensitive_headers: WSGIRequest,
        mock_response: HttpResponse,
        get_response_factory: Callable[[HttpResponse], Callable[[WSGIRequest], HttpResponse]],
    ):
        middleware = LogRequestAndResponseMiddleware(get_response_factory(mock_response))
        middleware(request_with_sensitive_headers)

        mock_logger.info.assert_called()
        request_log_call = mock_logger.info.call_args_list[0]
        logged_headers = request_log_call.kwargs["extra"]["request"]["headers"]

        # All sensitive headers are excluded, making the header dict empty, which is then set to None.
        assert logged_headers is None

    @patch("django_google_structured_logger.middlewares.settings.LOG_MASK_STYLE", "partial")
    def test_partial_masking_of_sensitive_data(
        self,
        mock_logger: Mock,
        post_request_with_data: WSGIRequest,
        mock_response: HttpResponse,
        get_response_factory: Callable[[HttpResponse], Callable[[WSGIRequest], HttpResponse]],
    ):
        middleware = LogRequestAndResponseMiddleware(get_response_factory(mock_response))
        middleware(post_request_with_data)

        request_log_call = mock_logger.info.call_args_list[0]
        logged_body = request_log_call.kwargs["extra"]["request"]["body"]
        assert logged_body["password"] == "se.....MASKED.....23"

    @patch("django_google_structured_logger.middlewares.settings.LOG_MASK_STYLE", "complete")
    def test_complete_masking_of_sensitive_data(
        self,
        mock_logger: Mock,
        post_request_with_data: WSGIRequest,
        mock_response: HttpResponse,
        get_response_factory: Callable[[HttpResponse], Callable[[WSGIRequest], HttpResponse]],
    ):
        middleware = LogRequestAndResponseMiddleware(get_response_factory(mock_response))
        middleware(post_request_with_data)

        request_log_call = mock_logger.info.call_args_list[0]
        logged_body = request_log_call.kwargs["extra"]["request"]["body"]
        assert logged_body["password"] == "...FULL_MASKED..."

    @patch("django_google_structured_logger.middlewares.settings.LOG_MAX_STR_LEN", 50)
    def test_abridging_long_strings(
        self,
        mock_logger: Mock,
        request_with_long_data: WSGIRequest,
        response_with_long_data: HttpResponse,
        get_response_factory: Callable[[HttpResponse], Callable[[WSGIRequest], HttpResponse]],
    ):
        middleware = LogRequestAndResponseMiddleware(get_response_factory(response_with_long_data))
        middleware(request_with_long_data)

        request_body = mock_logger.info.call_args_list[0].kwargs["extra"]["request"]["body"]
        response_data = mock_logger.info.call_args_list[1].kwargs["extra"]["response"]["data"]

        assert request_body["long_str"].endswith("..SHORTENED")
        assert len(request_body["long_str"]) == 50 + len("..SHORTENED")
        assert response_data["long_str"].endswith("..SHORTENED")
        assert len(response_data["long_str"]) == 50 + len("..SHORTENED")

    @patch("django_google_structured_logger.middlewares.settings.LOG_MAX_LIST_LEN", 5)
    def test_abridging_long_lists(
        self,
        mock_logger: Mock,
        request_with_long_data: WSGIRequest,
        response_with_long_data: HttpResponse,
        get_response_factory: Callable[[HttpResponse], Callable[[WSGIRequest], HttpResponse]],
    ):
        middleware = LogRequestAndResponseMiddleware(get_response_factory(response_with_long_data))
        middleware(request_with_long_data)

        request_body = mock_logger.info.call_args_list[0].kwargs["extra"]["request"]["body"]
        response_data = mock_logger.info.call_args_list[1].kwargs["extra"]["response"]["data"]

        assert len(request_body["long_list"]) == 5
        assert len(response_data["long_list"]) == 5

    @patch("django_google_structured_logger.middlewares.settings.LOG_MAX_DEPTH", 3)
    def test_abridging_deeply_nested_data(
        self,
        mock_logger: Mock,
        request_with_long_data: WSGIRequest,
        response_with_long_data: HttpResponse,
        get_response_factory: Callable[[HttpResponse], Callable[[WSGIRequest], HttpResponse]],
    ):
        middleware = LogRequestAndResponseMiddleware(get_response_factory(response_with_long_data))
        middleware(request_with_long_data)

        request_body = mock_logger.info.call_args_list[0].kwargs["extra"]["request"]["body"]
        response_data = mock_logger.info.call_args_list[1].kwargs["extra"]["response"]["data"]

        assert request_body["deep_dict"]["a"]["b"]["c"] == "..DEPTH EXCEEDED"
        assert response_data["deep_dict"]["a"]["b"]["c"] == "..DEPTH EXCEEDED"

    @patch("django_google_structured_logger.middlewares.settings.LOG_MIDDLEWARE_ENABLED", False)
    def test_middleware_is_disabled(
        self,
        mock_logger: Mock,
        authenticated_request: WSGIRequest,
        mock_response: HttpResponse,
        get_response_factory: Callable[[HttpResponse], Callable[[WSGIRequest], HttpResponse]],
    ):
        middleware = LogRequestAndResponseMiddleware(get_response_factory(mock_response))
        middleware(authenticated_request)

        mock_logger.info.assert_not_called()
        mock_logger.warning.assert_not_called()
        mock_logger.exception.assert_not_called()


class TestGrapheneSetUserContextMiddleware:
    """Tests for GrapheneSetUserContextMiddleware."""

    def test_sets_context_if_not_exists(self, mock_graphene_info: Mock, mock_user: Mock):
        """
        Verify that the middleware correctly creates a RequestStorage and extracts user data from info.context.user
        when no context is present.
        """
        middleware = GrapheneSetUserContextMiddleware()
        next_middleware = Mock()

        # Ensure context is initially empty
        assert _current_request.get() is None

        middleware.resolve(next_middleware, None, mock_graphene_info)

        storage = _current_request.get()
        assert storage is not None
        assert isinstance(storage, RequestStorage)
        assert isinstance(storage.uuid, str)
        assert uuid.UUID(storage.uuid)  # Ensures it's a valid UUID

        # Verify user data is extracted correctly
        assert storage.user_id() == mock_user.id
        assert storage.user_display_field() == mock_user.email
        next_middleware.assert_called_once()

    def test_updates_existing_context(
        self, mock_request_storage: RequestStorage, mock_graphene_info: Mock, mock_user: Mock
    ):
        """
        Verify that if RequestStorage already exists (e.g., created by Django middleware), it is correctly updated
        rather than replaced.
        """
        assert isinstance(mock_request_storage, RequestStorage)
        middleware = GrapheneSetUserContextMiddleware()
        next_middleware = Mock()

        # Get the initial storage and its UUID
        initial_storage = _current_request.get()
        assert initial_storage is not None
        initial_uuid = initial_storage.uuid

        middleware.resolve(next_middleware, None, mock_graphene_info)

        updated_storage = _current_request.get()
        assert updated_storage is not None

        # Verify the storage object was updated, not replaced
        assert updated_storage.uuid == initial_uuid

        # Verify user data has been updated from the Graphene context
        assert updated_storage.user_id() == mock_user.id
        assert updated_storage.user_display_field() == mock_user.email
        next_middleware.assert_called_once()
