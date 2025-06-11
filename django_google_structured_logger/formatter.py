from logging import LogRecord
from typing import Dict, Optional

from django.conf import settings
from pythonjsonlogger import jsonlogger

from .storages import RequestStorage, get_current_request


class StandardJSONFormatter(jsonlogger.JsonFormatter):
    """
    A standard JSON log formatter. It creates a base set of fields, including
    severity, source_location, labels, operation, and http_request/http_response.
    """

    def add_fields(self, log_record: Dict, record: LogRecord, message_dict: Dict):
        """Set standard fields for JSON logging."""
        super().add_fields(log_record, record, message_dict)

        current_request: Optional[RequestStorage] = get_current_request()

        log_record["severity"] = record.levelname
        self._set_source_location(log_record, record)
        self._set_labels(log_record, current_request)
        self._set_operation(log_record, current_request)
        self._set_http_context(log_record)

    def _set_source_location(self, log_record: Dict, record):
        """Set the source location in the log record under the `source_location` key."""
        log_record["source_location"] = {
            "file": record.pathname,
            "line": record.lineno,
            "function": record.funcName,
            "logger_name": record.name,
        }

    def _set_labels(self, log_record: Dict, current_request: Optional[RequestStorage]):
        """Set the labels in the log record under the `labels` key."""
        labels = {
            "user_id": current_request.user_id() if current_request is not None else None,
            "user_display_field": current_request.user_display_field() if current_request is not None else None,
            **log_record.pop("labels", {}),
        }
        self.stringify_values(labels)
        log_record["labels"] = labels

    def _set_operation(self, log_record: Dict, current_request: Optional[RequestStorage]):
        """Set the operation details in the log record under the `operation` key."""
        operation = {
            "id": getattr(current_request, "uuid", None),
            **log_record.pop("operation", {}),
        }
        if "first_operation" in log_record:
            operation["first"] = log_record.pop("first_operation")
        if "last_operation" in log_record:
            operation["last"] = log_record.pop("last_operation")
        log_record["operation"] = operation

    def _set_http_context(self, log_record: Dict):
        """Move request and response data to `http_request` and `http_response` keys."""
        if "request" in log_record:
            log_record["http_request"] = log_record.pop("request")
        if "response" in log_record:
            log_record["http_response"] = log_record.pop("response")

    @staticmethod
    def stringify_values(dict_to_convert: Dict):
        for key in dict_to_convert:
            dict_to_convert[key] = str(dict_to_convert[key])


class GoogleCloudFormatter(StandardJSONFormatter):
    """
    A log formatter for Google Cloud Logging. It inherits from StandardJSONFormatter and maps the standard fields to
    Google Cloud's specific field names.
    """

    google_source_location_field = "logging.googleapis.com/sourceLocation"
    google_operation_field = "logging.googleapis.com/operation"
    google_labels_field = "logging.googleapis.com/labels"
    google_trace_field = "logging.googleapis.com/trace"

    def add_fields(self, log_record: Dict, record: LogRecord, message_dict: Dict):
        """
        Set Google default fields by extending the standard formatter. It populates
        standard fields first, then remaps them to Google-specific keys.
        """
        super().add_fields(log_record, record, message_dict)

        if "source_location" in log_record:
            log_record[self.google_source_location_field] = log_record.pop("source_location")

        if "operation" in log_record:
            log_record[self.google_operation_field] = log_record.pop("operation")

        if "labels" in log_record:
            log_record[self.google_labels_field] = log_record.pop("labels")

        self._set_trace_correlation(log_record, record)

    def _set_trace_correlation(self, log_record: Dict, record: LogRecord):
        """Set the Google trace correlation fields in the log record."""
        trace_id = getattr(record, "otelTraceID", None)
        span_id = getattr(record, "otelSpanID", None)
        trace_sampled = getattr(record, "otelTraceSampled", None)

        project_id = getattr(settings, "GOOGLE_CLOUD_PROJECT", None)
        if trace_id is not None and project_id is not None:
            log_record[self.google_trace_field] = f"projects/{project_id}/traces/{trace_id}"
            if span_id is not None:
                log_record["spanId"] = span_id
            if trace_sampled is not None:
                log_record["traceSampled"] = bool(trace_sampled)
