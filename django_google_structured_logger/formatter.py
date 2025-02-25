from typing import Dict, Optional

from django.conf import settings
from pythonjsonlogger import jsonlogger

from .storages import RequestStorage, get_current_request


class GoogleFormatter(jsonlogger.JsonFormatter):
    google_source_location_field = "logging.googleapis.com/sourceLocation"
    google_operation_field = "logging.googleapis.com/operation"
    google_labels_field = "logging.googleapis.com/labels"
    google_trace_field = "logging.googleapis.com/trace"

    def add_fields(self, log_record: Dict, record, message_dict: Dict):
        """
        Set Google default fields.

        List of Google supported fields:
        https://cloud.google.com/logging/docs/reference/v2/rest/v2/LogEntry

        List of associated JSON fields:
        https://cloud.google.com/logging/docs/structured-logging#default-parsers

        Traces and metrics:
        https://cloud.google.com/trace/docs/setup/python-ot

        This method sets these fields if present:
         - severity
         - labels
         - operation
         - sourceLocation
         - trace (string) - REST resource name of trace
         - spanId (string) - Trace span ID
         - traceSampled (boolean) - W3C trace-context sampling decision
        """
        super().add_fields(log_record, record, message_dict)

        current_request: Optional[RequestStorage] = get_current_request()

        log_record["severity"] = record.levelname

        # Update specialized fields
        self._set_trace_correlation(log_record, record)
        self._set_labels(log_record, current_request)
        self._set_operation(log_record, current_request)
        self._set_source_location(log_record, record)

    def _set_labels(self, log_record: Dict, current_request: Optional[RequestStorage]):
        """Set the Google labels in the log record."""
        labels = {
            "user_id": current_request.user_id() if current_request else None,
            "user_display_field": current_request.user_display_field() if current_request else None,
            **log_record.get(self.google_labels_field, {}),
            **log_record.pop("labels", {}),
        }
        self.stringify_values(labels)
        log_record[self.google_labels_field] = labels

    def _set_operation(self, log_record: Dict, current_request: Optional[RequestStorage]):
        """Set the Google operation details in the log record."""
        operation = {
            "id": getattr(current_request, "uuid", None),
            **log_record.get(self.google_operation_field, {}),
            **log_record.pop("operation", {}),
        }

        if "first_operation" in log_record:
            operation["first"] = log_record.pop("first_operation")
        if "last_operation" in log_record:
            operation["last"] = log_record.pop("last_operation")

        log_record[self.google_operation_field] = operation

    def _set_source_location(self, log_record: Dict, record):
        """Set the Google source location in the log record."""
        log_record[self.google_source_location_field] = {
            "file": record.pathname,
            "line": record.lineno,
            "function": record.funcName,
            "logger_name": record.name,
        }

    def _set_trace_correlation(self, log_record: Dict, record):
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

    @staticmethod
    def stringify_values(dict_to_convert: Dict):
        for key in dict_to_convert:
            dict_to_convert[key] = str(dict_to_convert[key])
