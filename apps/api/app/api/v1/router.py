from fastapi import APIRouter

from app.api.v1.routes import health
from app.modules.auth.router import router as auth_router
from app.modules.products.router import offer_router
from app.modules.products.router import router as products_router
from app.modules.search.router import admin_router as admin_search_router
from app.modules.search.router import router as search_router

api_router = APIRouter()
api_router.include_router(health.router, tags=["health"])
api_router.include_router(auth_router)
api_router.include_router(products_router)
api_router.include_router(offer_router)
api_router.include_router(search_router)
api_router.include_router(admin_search_router)
