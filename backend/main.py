from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from database import init_db
from routers import competitors_router, dashboard_router, alerts_router, scraping_router
from services.scheduler import start_scheduler, stop_scheduler


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler for startup/shutdown events."""
    # Startup: Initialize database
    await init_db()
    # Start the scheduled scraping service
    await start_scheduler()
    yield
    # Shutdown: Stop the scheduler
    await stop_scheduler()


app = FastAPI(
    title="Competitive Intelligence Dashboard API",
    description="Backend API for monitoring competitor pricing across delivery platforms",
    version="1.0.0",
    lifespan=lifespan,
)

# Configure CORS to allow requests from the frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routers with /api/v1 prefix
app.include_router(competitors_router, prefix="/api/v1")
app.include_router(dashboard_router, prefix="/api/v1")
app.include_router(alerts_router, prefix="/api/v1")
app.include_router(scraping_router, prefix="/api/v1")


@app.get("/api/health")
async def health_check():
    """Health check endpoint to verify backend connectivity."""
    return {
        "status": "ok",
        "message": "Backend is connected"
    }


@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "name": "Competitive Intelligence Dashboard API",
        "version": "1.0.0",
        "docs": "/docs",
        "endpoints": {
            "health": "/api/health",
            "competitors": "/api/v1/competitors",
            "dashboard": "/api/v1/dashboard",
            "alerts": "/api/v1/alerts",
            "scraping": "/api/v1/scraping",
        }
    }
