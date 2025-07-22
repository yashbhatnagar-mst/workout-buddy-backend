from typing import Any

def api_response(message: str, status: int, data: Any = None) -> dict:
    return {
        "message": message,
        "status": status,
        "success": status < 400,
        "data": data
    }