from typing import Any
from fastapi.responses import JSONResponse


def api_response(message: str, status: int = 200, data: Any = None, success: bool = True):
    return JSONResponse(
        status_code=status,
        content={
            "message": message,
            "status": status,
            "success": success,
            "data": data,
        },
    )
