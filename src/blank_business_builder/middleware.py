import uuid
import json
import time
import logging
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger("bbb_api")

class RequestIDMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # 1. Request ID middleware
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        request.state.request_id = request_id

        client_ip = getattr(request.client, "host", "unknown") if getattr(request, "client", None) is not None else "unknown"

        start_time = time.time()
        logger.info(json.dumps({
            "event": "request_started",
            "method": request.method,
            "url": str(request.url),
            "request_id": request_id,
            "client_ip": client_ip
        }))

        try:
            response = await call_next(request)

            process_time = time.time() - start_time
            response.headers["X-Request-ID"] = request_id

            logger.info(json.dumps({
                "event": "request_finished",
                "method": request.method,
                "url": str(request.url),
                "status_code": response.status_code,
                "request_id": request_id,
                "process_time": f"{process_time:.4f}s"
            }))

            return response
        except Exception as e:
            process_time = time.time() - start_time
            logger.error(json.dumps({
                "event": "request_failed",
                "method": request.method,
                "url": str(request.url),
                "request_id": request_id,
                "error": str(e),
                "process_time": f"{process_time:.4f}s"
            }))
            # Returning JSON response directly from middleware for uncaught exceptions
            # since Starlette's BaseHTTPMiddleware doesn't always cleanly pass exceptions to
            # app.exception_handler without swallowing them or crashing when streaming.
            import os
            import traceback
            from fastapi.responses import JSONResponse
            from fastapi import status

            debug_mode = os.getenv("DEBUG", "false").lower() == "true"
            response_content = {
                "error": "Internal Server Error",
                "request_id": request_id,
                "detail": str(e) if debug_mode else "An unexpected error occurred."
            }
            if debug_mode:
                response_content["traceback"] = traceback.format_exception(type(e), e, e.__traceback__)

            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content=response_content
            )
