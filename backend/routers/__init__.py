from .competitors import router as competitors_router
from .dashboard import router as dashboard_router
from .alerts import router as alerts_router
from .scraping import router as scraping_router

__all__ = ["competitors_router", "dashboard_router", "alerts_router", "scraping_router"]
