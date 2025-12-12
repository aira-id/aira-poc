"""
AIRA Voice Bot Server - Main Application Entry Point.

This module creates and configures the FastAPI application for the AIRA voice bot server.
It sets up:
- CORS middleware for cross-origin requests
- Custom error handling and request logging middleware
- API routes for health checks and endpoints
- WebSocket routes for real-time ASR and TTS streaming
- Static file serving for web UI components
- Application lifecycle events (startup/shutdown)
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path
from app.config import settings
from app.logging_config import logger
from app.core.middleware import ErrorHandlingMiddleware, RequestLoggingMiddleware
from app.api.routes import health, index, websocket


def create_app() -> FastAPI:
    """
    Create and configure the FastAPI application.

    Sets up the complete AIRA application with all middleware, routes, and static files.
    The application includes:
    - CORS middleware configured from settings
    - Global error handling and request logging
    - API routes for various endpoints
    - WebSocket routes for ASR and TTS streaming
    - Static file serving for voice and chat UI

    Returns:
        FastAPI: Configured FastAPI application instance ready to serve
    """

    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        debug=settings.debug,
        docs_url="/docs",
        redoc_url="/redoc",
    )

    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=settings.cors_credentials,
        allow_methods=settings.cors_methods,
        allow_headers=settings.cors_headers,
    )

    # Add custom middleware
    app.add_middleware(ErrorHandlingMiddleware)
    app.add_middleware(RequestLoggingMiddleware)

    # Include routers (must be before static files to allow API routes to take precedence)
    app.include_router(health.router)
    app.include_router(websocket.router)

    # Mount static files for web-ui (after routers to prevent conflicts)
    web_ui_path = Path(__file__).parent / "web-ui"
    if web_ui_path.exists():
        # Mount voice assets if exists
        voice_path = web_ui_path / "voice"
        if voice_path.exists():
            app.mount("/voice", StaticFiles(directory=str(voice_path), html=True), name="voice_static")

        # Mount chat assets if exists
        chat_path = web_ui_path / "chat"
        if chat_path.exists():
            app.mount("/chat", StaticFiles(directory=str(chat_path), html=True), name="chat_static")
        
        # Mount index assets if exists
        voice_path = web_ui_path / "index"
        if voice_path.exists():
            app.mount("/", StaticFiles(directory=str(voice_path), html=True), name="speak_static")

    @app.on_event("startup")
    async def startup_event():
        """
        Run on application startup.

        Logs startup information and initializes services.
        Future: Will initialize ASR, LLM, and TTS services for the voice bot.
        """
        logger.info(f"Starting {settings.app_name} v{settings.app_version}")
        logger.info(f"Debug mode: {settings.debug}")
        logger.info(f"Log level: {settings.log_level}")

        # TODO: Initialize ASR, LLM, TTS services

    @app.on_event("shutdown")
    async def shutdown_event():
        """
        Run on application shutdown.

        Performs cleanup operations before the server stops.
        Future: Will cleanup ASR, LLM, and TTS resources to prevent memory leaks.
        """
        logger.info(f"Shutting down {settings.app_name}")

        # TODO: Cleanup ASR, LLM, TTS resources

    return app


app = create_app()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level=settings.log_level.lower(),
    )
