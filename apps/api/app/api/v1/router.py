from fastapi import APIRouter

from app.api.v1.routes import health
from app.modules.admin.router import router as admin_router
from app.modules.ai_assistant.router import router as ai_assistant_router
from app.modules.auth.router import router as auth_router
from app.modules.crawlers.router import admin_router as admin_crawler_run_logs_router
from app.modules.discussions.router import admin_router as admin_discussions_router
from app.modules.discussions.router import router as discussions_router
from app.modules.evidence.router import admin_router as admin_evidence_router
from app.modules.evidence.router import router as evidence_router
from app.modules.favorites.router import router as favorites_router
from app.modules.notifications.router import router as notifications_router
from app.modules.products.router import offer_router
from app.modules.products.router import router as products_router
from app.modules.reports.router import admin_router as admin_reports_router
from app.modules.reports.router import router as reports_router
from app.modules.search.router import admin_router as admin_search_router
from app.modules.search.router import router as search_router
from app.modules.submissions.router import admin_router as admin_submissions_router
from app.modules.submissions.router import me_router as me_submissions_router
from app.modules.submissions.router import router as submissions_router

api_router = APIRouter()
api_router.include_router(health.router, tags=["health"])
api_router.include_router(ai_assistant_router)
api_router.include_router(auth_router)
api_router.include_router(favorites_router)
api_router.include_router(notifications_router)
api_router.include_router(admin_router)
api_router.include_router(reports_router)
api_router.include_router(admin_reports_router)
api_router.include_router(submissions_router)
api_router.include_router(me_submissions_router)
api_router.include_router(admin_submissions_router)
api_router.include_router(products_router)
api_router.include_router(discussions_router)
api_router.include_router(evidence_router)
api_router.include_router(offer_router)
api_router.include_router(search_router)
api_router.include_router(admin_search_router)
api_router.include_router(admin_evidence_router)
api_router.include_router(admin_discussions_router)
api_router.include_router(admin_crawler_run_logs_router)
