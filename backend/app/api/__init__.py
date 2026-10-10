from fastapi import APIRouter

from app.api.routes import register

api_router = APIRouter()
register(api_router)

__all__ = ["api_router"]
