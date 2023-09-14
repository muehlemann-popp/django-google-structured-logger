from pythonjsonlogger import jsonlogger  # type: ignore

from .storages import RequestStorage, get_current_request


class GoogleFormatter(jsonlogger.JsonFormatter):
    google_source_location_field = "logging.googleapis.com/sourceLocation"
    google_operation_field = "logging.googleapis.com/operation"
    google_labels_field = "logging.googleapis.com/labels"

    def add_fields(self, log_record: dict, record, message_dict: dict):
        """Set Google default fields

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
        current_request: RequestStorage | None = get_current_request()

        log_record["severity"] = record.levelname

        log_record[self.google_labels_field] = {
            "request_user_id": current_request.user_id() if current_request else None,
            "request_user_email": current_request.user_email()
            if current_request
            else None,
            **log_record.pop(self.google_labels_field, {}),
            **log_record.pop("labels", {}),
        }
        self.stringify_values(log_record[self.google_labels_field])

        log_record[self.google_operation_field] = {
            "id": current_request.uuid if current_request else None,
            "last": log_record.get("last_operation", False),
            **log_record.pop(self.google_operation_field, {}),
            **log_record.pop("operation", {}),
        }
        log_record[self.google_source_location_field] = {
            "file": record.pathname,
            "line": record.lineno,
            "function": record.funcName,
            "logger": record.name,
        }

    @staticmethod
    def stringify_values(dict_to_convert: dict):
        for key in dict_to_convert:
            dict_to_convert[key] = str(dict_to_convert[key])
