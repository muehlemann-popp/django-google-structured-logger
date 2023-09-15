from typing import Dict, Optional

from pythonjsonlogger import jsonlogger

from .storages import RequestStorage, get_current_request


class GoogleFormatter(jsonlogger.JsonFormatter):
    google_source_location_field = "logging.googleapis.com/sourceLocation"
    google_operation_field = "logging.googleapis.com/operation"
    google_labels_field = "logging.googleapis.com/labels"

    def add_fields(self, log_record: Dict, record, message_dict: Dict):
        """
        Set Google default fields.

        List of Google supported fields:
        https://cloud.google.com/logging/docs/reference/v2/rest/v2/LogEntry

        List of associated JSON fields:
        https://cloud.google.com/logging/docs/structured-logging#default-parsers

        This method sets these fields if present:
         - severity
         - labels
         - operation
         - sourceLocation
        """
        super().add_fields(log_record, record, message_dict)

        current_request: Optional[RequestStorage] = get_current_request()

        log_record["severity"] = record.levelname

        # Update each specialized field
        self._set_labels(log_record, current_request)
        self._set_operation(log_record, current_request)
        self._set_source_location(log_record, record)

    def _set_labels(self, log_record: Dict, current_request: Optional[RequestStorage]):
        """Set the Google labels in the log record."""
        labels = {
            "user_id": getattr(current_request, "user_id", None),
            "user_display_field": getattr(current_request, "user_display_field", None),
            **log_record.get(self.google_labels_field, {}),
            **log_record.pop("labels", {}),
        }
        self.stringify_values(labels)
        log_record[self.google_labels_field] = labels

    def _set_operation(
        self, log_record: Dict, current_request: Optional[RequestStorage]
    ):
        """Set the Google operation details in the log record."""
        operation = {
            "id": getattr(current_request, "uuid", None),
            **{
                k: v
                for k, v in log_record.items()
                if k in ["first_operation", "last_operation"] and v
            },
            **log_record.get(self.google_operation_field, {}),
            **log_record.pop("operation", {}),
        }
        log_record[self.google_operation_field] = operation

    def _set_source_location(self, log_record: Dict, record):
        """Set the Google source location in the log record."""
        log_record[self.google_source_location_field] = {
            "file": record.pathname,
            "line": record.lineno,
            "function": record.funcName,
            "logger_name": record.name,
        }

    @staticmethod
    def stringify_values(dict_to_convert: Dict):
        for key in dict_to_convert:
            dict_to_convert[key] = str(dict_to_convert[key])
