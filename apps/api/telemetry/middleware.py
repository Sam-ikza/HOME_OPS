import json
import logging
import time
import uuid

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

logger = logging.getLogger("homesense.telemetry")


class TelemetryMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        request_id = request.headers.get("x-request-id", str(uuid.uuid4()))
        request.state.request_id = request_id
        start = time.perf_counter()

        try:
            response = await call_next(request)
            latency_ms = round((time.perf_counter() - start) * 1000, 2)
            logger.info(
                json.dumps(
                    {
                        "request_id": request_id,
                        "method": request.method,
                        "path": request.url.path,
                        "status_code": response.status_code,
                        "latency_ms": latency_ms,
                        "model": getattr(request.state, "model_used", "unknown"),
                    }
                )
            )
            response.headers["x-request-id"] = request_id
            return response
        except Exception as exc:  # pragma: no cover - runtime telemetry
            latency_ms = round((time.perf_counter() - start) * 1000, 2)
            logger.exception(
                json.dumps(
                    {
                        "request_id": request_id,
                        "method": request.method,
                        "path": request.url.path,
                        "status_code": 500,
                        "latency_ms": latency_ms,
                        "error": str(exc),
                    }
                )
            )
            raise
