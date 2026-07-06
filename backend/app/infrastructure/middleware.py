import logging
import time

from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

logger = logging.getLogger("finpulse")


class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()

        response = await call_next(request)

        process_time = (time.time() - start_time) * 1000
        formatted_time = f"{process_time:.2f}ms"

        logger.info(f"{request.method} {request.url.path} " f"status={response.status_code} " f"time={formatted_time}")

        return response


class ErrorHandlingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        try:
            return await call_next(request)
        except Exception as e:
            logger.exception(f"Unhandled error for {request.method} {request.url.path}: {e}")

            return JSONResponse(
                status_code=500,
                content={"detail": "Internal server error"},
            )
