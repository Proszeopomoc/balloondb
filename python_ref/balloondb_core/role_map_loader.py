import json
from pathlib import Path

EXPECTED_LAYERS = [
    "INGESTION_LAYER",
    "CONTEXT_MEMORY_ARCHITECTURE",
    "QUERY_ENGINE_EXECUTION",
    "AGENT_CONTROL_CENTER"
]

def load_role_map(path: str) -> dict:
    p = Path(path)
    if not p.exists():
        return {"ok": False, "error": f"role map not found: {p}"}
    data = json.loads(p.read_text(encoding="utf-8-sig"))
    layers = data.get("layers", {})
    missing = [x for x in EXPECTED_LAYERS if x not in layers]
    return {
        "ok": not missing,
        "path": str(p),
        "map_id": data.get("map_id"),
        "missing_layers": missing,
        "layer_count": len(layers)
    }
