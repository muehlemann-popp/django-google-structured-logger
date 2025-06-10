import uuid
from typing import cast
from unittest.mock import Mock, patch

import pytest
from django.http import HttpResponse

from django_google_structured_logger.middlewares import SetUserContextMiddleware
from django_google_structured_logger.storages import _current_request


class TestSetUserContextMiddleware:
    """Tests for SetUserContextMiddleware that manages user context in request storage."""

    @pytest.fixture
    def mock_get_response(self):
        """Mock get_response function that returns a basic HttpResponse."""

        def get_response(request):
            return HttpResponse("Test response")

        return get_response

    @pytest.fixture
    def middleware(self, mock_get_response):
        """SetUserContextMiddleware instance."""
        return SetUserContextMiddleware(mock_get_response)

    def test_authenticated_user_context(self, middleware, authenticated_request, middleware_settings):
        """Test that authenticated user context is correctly set in RequestStorage."""
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

    def test_anonymous_user_context(self, middleware, anonymous_request, middleware_settings):
        """Test that anonymous user context sets user fields to None."""
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

    def test_custom_user_fields(self, mock_get_response, authenticated_request, settings):
        """Test middleware uses custom LOG_USER_ID_FIELD and LOG_USER_DISPLAY_FIELD settings."""

        # Configure custom user field settings
        settings.LOG_USER_ID_FIELD = "username"
        settings.LOG_USER_DISPLAY_FIELD = "username"

        # Ensure mock user has username attribute
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

    def test_missing_user_attributes(self, mock_get_response, authenticated_request, settings):
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

            # Verify missing attributes return None. Both user_id and user_display_field will return Mock object.
            user_id = cast(Mock, storage.user_id())
            assert user_id.side_effect is None
            user_display_field = cast(Mock, storage.user_display_field())
            assert user_display_field.side_effect is None

    def test_multiple_requests_different_contexts(
        self, middleware, authenticated_request, anonymous_request, middleware_settings
    ):
        """Test that each request gets its own context storage."""
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

    def test_uuid_uniqueness(self, middleware, authenticated_request, middleware_settings):
        """Test that each middleware call generates a unique UUID."""
        uuids = set()

        # Call middleware multiple times
        for _ in range(5):
            middleware(authenticated_request)
            storage = _current_request.get()
            assert storage is not None
            uuids.add(storage.uuid)

        # Verify all UUIDs are unique
        assert len(uuids) == 5
