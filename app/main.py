import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.calendar_routes import router as calendar_router
from app.api.knowledge_routes import router as knowledge_router
from app.api.realtime_routes import router as realtime_router
from app.api.strategy_routes import router as strategy_router
from app.config.settings import get_settings

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger(__name__)


def create_app() -> FastAPI:
    """Application factory that builds and configures the FastAPI instance."""
    settings = get_settings()

    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        description="AI-powered Marketing Strategy Recommender for SMEs",
        docs_url="/docs",
        redoc_url="/redoc",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=False,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(strategy_router)
    app.include_router(knowledge_router)
    app.include_router(realtime_router)
    app.include_router(calendar_router)

    @app.get("/", tags=["Health"])
    async def root() -> dict:
        """Root endpoint — used by HF Spaces health checks."""
        return {
            "status": "healthy",
            "app": settings.APP_NAME,
            "version": settings.APP_VERSION,
        }

    @app.get("/health", tags=["Health"])
    async def health_check() -> dict:
        """Return basic health status."""
        return {
            "status": "healthy",
            "version": settings.APP_VERSION,
        }

    logger.info("Application initialized — %s v%s", settings.APP_NAME, settings.APP_VERSION)
    return app


app = create_app()
