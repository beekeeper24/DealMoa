from fastapi import APIRouter

from app.api.v1.routes import health
from app.modules.products.router import router as products_router

api_router = APIRouter()
api_router.include_router(health.router, tags=["health"])
api_router.include_router(products_router)
