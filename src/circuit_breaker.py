import hashlib
import json


def tool_call_fingerprint(tool_name: str, arguments: dict[str, object]) -> str:
    payload = {"tool_name": tool_name, "arguments": arguments}
    normalized = json.dumps(payload, sort_keys=True)
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()



def stop_reason(
    completed_iterations: int,
    previous_fingerprint: str | None,
    current_fingerprint: str,
) -> str | None:
    if completed_iterations >= 6:
        return "Reached the six-iteration limit."

    if current_fingerprint == previous_fingerprint:
        return "Detected a repeated tool call."

    return None