from fastapi import APIRouter
from .auth import router as auth_router
from .datasets import router as datasets_router
from .analyses import router as analyses_router
from .posts import router as posts_router
from .exports import router as exports_router
from .settings import router as settings_router
from .screenshots import router as screenshots_router

api_router = APIRouter()

api_router.include_router(auth_router, prefix="/auth", tags=["认证"])
api_router.include_router(datasets_router, prefix="/datasets", tags=["数据集"])
api_router.include_router(analyses_router, prefix="/analyses", tags=["分析"])
api_router.include_router(posts_router, prefix="/posts", tags=["笔记"])
api_router.include_router(exports_router, prefix="/exports", tags=["导出"])
api_router.include_router(settings_router, prefix="/settings", tags=["设置"])
api_router.include_router(screenshots_router, prefix="/screenshots", tags=["截图分析"])
