import json
import logging

from logging_config import JsonFormatter, request_id_var


def test_structured_logging_contains_correlation_without_traceback_body():
    token = request_id_var.set("req-123")
    try:
        record = logging.LogRecord("licenzpol", logging.INFO, __file__, 1, "event=%s", ("ok",), None)
        data = json.loads(JsonFormatter().format(record))
        assert data["request_id"] == "req-123"
        assert data["message"] == "event=ok"
        assert data["logger"] == "licenzpol"
    finally:
        request_id_var.reset(token)
