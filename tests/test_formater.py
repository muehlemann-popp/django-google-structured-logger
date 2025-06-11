import json
from logging import LogRecord

from django_google_structured_logger.formatter import GoogleCloudFormatter, StandardJSONFormatter
from django_google_structured_logger.storages import RequestStorage


class TestStandardJSONFormatter:
    def test_correct_log_structure_with_context(self, base_log_record: LogRecord, mock_request_storage: RequestStorage):
        """
        Tests that the formatter correctly structures log records and enriches them with data from the request context.
        """
        formatter = StandardJSONFormatter()
        # Add request as a direct attribute for the formatter to process
        base_log_record.request = {"method": "GET", "url": "/test"}
        formatted_log = formatter.format(base_log_record)
        log_dict = json.loads(formatted_log)

        # Check for standard fields
        assert log_dict["severity"] == "INFO"
        assert log_dict["message"] == "This is a test message"

        # Check for source location
        assert log_dict["source_location"] == {
            "file": "/app/tests.py",
            "line": 42,
            "function": "test_function",
            "logger_name": "test_logger",
        }

        # Check for labels from context
        assert log_dict["labels"] == {"user_id": "1", "user_display_field": "test@example.com"}

        # Check for operation from context
        assert log_dict["operation"]["id"] == mock_request_storage.uuid

        # Check for http_request
        assert log_dict["http_request"] == {"method": "GET", "url": "/test"}

    def test_works_without_request_context(self, base_log_record: LogRecord):
        """
        Ensures the formatter does not raise errors when get_current_request() returns None and that user-dependent
        fields are empty.
        """
        formatter = StandardJSONFormatter()
        formatted_log = formatter.format(base_log_record)
        log_dict = json.loads(formatted_log)

        # Check that formatter runs without error and basic fields are present
        assert log_dict["severity"] == "INFO"
        assert log_dict["message"] == "This is a test message"

        # Check that user-dependent fields are string 'None' due to stringify_values
        assert log_dict["labels"]["user_id"] == "None"
        assert log_dict["labels"]["user_display_field"] == "None"
        assert log_dict["operation"]["id"] is None


class TestGoogleCloudFormatter:
    def test_field_remapping_for_google_cloud(self, base_log_record: LogRecord, mock_request_storage: RequestStorage):
        """
        Verifies that standard fields (source_location, operation, labels) are renamed to Google-specific fields.
        """
        formatter = GoogleCloudFormatter()
        formatted_log = formatter.format(base_log_record)
        log_dict = json.loads(formatted_log)

        # Check for renamed keys
        assert "source_location" not in log_dict
        assert "operation" not in log_dict
        assert "labels" not in log_dict

        assert formatter.google_source_location_field in log_dict
        assert formatter.google_operation_field in log_dict
        assert formatter.google_labels_field in log_dict

        # Check content of renamed fields
        assert log_dict[formatter.google_operation_field]["id"] == mock_request_storage.uuid
        assert log_dict[formatter.google_labels_field]["user_id"] == "1"

    def test_trace_correlation(self, log_record_with_trace: LogRecord):
        """
        Verifies that if otelTraceID is present, the log is enriched with the logging.googleapis.com/trace field.
        """
        formatter = GoogleCloudFormatter()
        formatted_log = formatter.format(log_record_with_trace)
        log_dict = json.loads(formatted_log)

        assert hasattr(log_record_with_trace, "otelTraceID")
        assert hasattr(log_record_with_trace, "otelSpanID")
        expected_trace = f"projects/test-project-123/traces/{log_record_with_trace.otelTraceID}"
        assert log_dict[formatter.google_trace_field] == expected_trace
        assert log_dict["spanId"] == log_record_with_trace.otelSpanID
        assert log_dict["traceSampled"] is True

    def test_trace_correlation_without_project_id(self, log_record_with_trace: LogRecord, settings):
        """
        Verifies that the trace field is not added if GOOGLE_CLOUD_PROJECT is not set.
        """
        settings.GOOGLE_CLOUD_PROJECT = None
        formatter = GoogleCloudFormatter()
        formatted_log = formatter.format(log_record_with_trace)
        log_dict = json.loads(formatted_log)

        assert formatter.google_trace_field not in log_dict
        assert "spanId" not in log_dict
        assert "traceSampled" not in log_dict
