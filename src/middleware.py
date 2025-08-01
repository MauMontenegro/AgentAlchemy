import time
import uuid
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
import logging

from .exceptions import AgentAlchemyException, create_http_exception

logger = logging.getLogger(__name__)

class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware for request/response logging and timing"""
    
    async def dispatch(self, request: Request, call_next):
        # Generate request ID
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id
        
        # Log request
        start_time = time.time()
        logger.info(f"[{request_id}] {request.method} {request.url}")
        
        try:
            response = await call_next(request)
            process_time = time.time() - start_time
            
            # Add headers
            response.headers["X-Request-ID"] = request_id
            response.headers["X-Process-Time"] = str(process_time)
            
            logger.info(f"[{request_id}] Completed in {process_time:.3f}s - Status: {response.status_code}")
            return response
            
        except Exception as exc:
            process_time = time.time() - start_time
            logger.error(f"[{request_id}] Error after {process_time:.3f}s: {str(exc)}")
            raise

class ExceptionHandlerMiddleware(BaseHTTPMiddleware):
    """Global exception handler middleware"""
    
    async def dispatch(self, request: Request, call_next):
        try:
            return await call_next(request)
        except AgentAlchemyException as exc:
            logger.error(f"AgentAlchemy error: {exc.message}", extra={"details": exc.details})
            http_exc = create_http_exception(exc)
            return JSONResponse(
                status_code=http_exc.status_code,
                content={"detail": http_exc.detail, "request_id": getattr(request.state, "request_id", None)}
            )
        except Exception as exc:
            logger.error(f"Unhandled error: {str(exc)}", exc_info=True)
            return JSONResponse(
                status_code=500,
                content={"detail": "Internal server error", "request_id": getattr(request.state, "request_id", None)}
            )