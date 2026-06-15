from .bql_executor import execute
from .bql_error_contract import ok_envelope, error_envelope

def run_query_contract(query_text, memory_root, max_results=50, include_trace=False):
    try:
        result = execute(query_text, memory_root=memory_root, max_results=max_results)
        if result.get("status") == "WARN_V03G2_SEED_NOT_FOUND":
            raise RuntimeError("BQL_SEED_NOT_FOUND")
        return ok_envelope(query_text, result)
    except Exception as exc:
        return error_envelope(query_text, exc, include_trace=include_trace)
