"""
Custom Middleware for AIRA Application.

This module provides custom FastAPI middleware for:
- Global exception handling and error responses
- Request/response logging with timing information
"""

import time
from fastapi import Request, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from app.logging_config import logger
from app.core.exceptions import AIRAException


class ErrorHandlingMiddleware(BaseHTTPMiddleware):
    """
    Middleware for handling exceptions globally.

    Catches all exceptions raised during request processing and converts them
    to appropriate JSON responses. AIRA-specific exceptions (AIRAException and subclasses)
    are handled with their configured status codes and messages. All other exceptions
    are caught and returned as 500 Internal Server Errors with generic messages.
    """

    async def dispatch(self, request: Request, call_next):
        """
        Process request and handle any exceptions.

        Args:
            request: The incoming HTTP request
            call_next: Function to call the next middleware/route handler

        Returns:
            JSONResponse: Error response if exception occurred, otherwise the normal response
        """
        try:
            response = await call_next(request)
            return response
        except AIRAException as exc:
            logger.error(f"AIRA Exception: {exc.message}")
            return JSONResponse(
                status_code=exc.status_code,
                content={
                    "error": exc.__class__.__name__,
                    "message": exc.message
                }
            )
        except Exception as exc:
            logger.error(f"Unexpected error: {str(exc)}", exc_info=True)
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={
                    "error": "InternalServerError",
                    "message": "An unexpected error occurred"
                }
            )


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware for logging HTTP requests and responses.

    Logs the method, path, status code, and processing time for each request.
    Useful for monitoring application performance and debugging issues.
    """

    async def dispatch(self, request: Request, call_next):
        """
        Process request and log timing information.

        Args:
            request: The incoming HTTP request
            call_next: Function to call the next middleware/route handler

        Returns:
            Response: The HTTP response from downstream handlers
        """
        start_time = time.time()

        logger.info(f"Request: {request.method} {request.url.path}")

        response = await call_next(request)

        process_time = time.time() - start_time
        logger.info(
            f"Response: {request.method} {request.url.path} "
            f"Status: {response.status_code} "
            f"Duration: {process_time:.3f}s"
        )

        return response
