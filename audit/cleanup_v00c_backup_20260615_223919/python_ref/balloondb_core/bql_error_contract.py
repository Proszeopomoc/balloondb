import json

from .bql_time_filter import TimeFilterError

ERROR_CONTRACT_VERSION = "V03G6_BQL_TIME_FILTER"

def classify_error(exc):
    name = exc.__class__.__name__
    message = str(exc)
    lower = message.lower()

    if isinstance(exc, TimeFilterError):
        return {
            "status": "BQL_TIME_FILTER_PARSE_ERROR",
            "error_class": name,
            "message": message,
            "feature_version": ERROR_CONTRACT_VERSION,
            "retryable": False
        }

    if name == "ParseError":
        if "timestamp" in lower or "named window" in lower or "ts" in lower or "time filter" in lower:
            status = "BQL_TIME_FILTER_PARSE_ERROR"
        elif "unsafe token" in lower:
            status = "BQL_SAFETY_ERROR"
        else:
            status = "BQL_PARSE_ERROR"
        return {
            "status": status,
            "error_class": name,
            "message": message,
            "feature_version": ERROR_CONTRACT_VERSION,
            "retryable": False
        }

    if isinstance(exc, PermissionError):
        return {
            "status": "BQL_READONLY_SAFETY_ERROR",
            "error_class": name,
            "message": message,
            "feature_version": ERROR_CONTRACT_VERSION,
            "retryable": False
        }

    if isinstance(exc, ValueError):
        return {
            "status": "BQL_EXECUTION_ERROR",
            "error_class": name,
            "message": message,
            "feature_version": ERROR_CONTRACT_VERSION,
            "retryable": False
        }

    return {
        "status": "BQL_INTERNAL_ERROR",
        "error_class": name,
        "message": message,
        "feature_version": ERROR_CONTRACT_VERSION,
        "retryable": False
    }

def classify_bql_error(exc):
    return classify_error(exc)

def contract_error_response(exc, query=None):
    response = classify_error(exc)
    if query is not None:
        response["query"] = query
    return response

def error_json_line(exc, query=None):
    return json.dumps(contract_error_response(exc, query=query), ensure_ascii=False, sort_keys=True)
