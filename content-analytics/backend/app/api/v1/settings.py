from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.session import get_db
from app.models.user import User
from app.models.user_settings import UserSettings
from app.schemas.settings import SettingsUpdate, SettingsResponse
from app.schemas.common import ResponseModel
from app.api.deps import get_current_user

router = APIRouter()


@router.get("", response_model=ResponseModel[SettingsResponse])
async def get_settings(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取当前用户设置"""
    result = await db.execute(
        select(UserSettings).where(UserSettings.user_id == current_user.id)
    )
    settings = result.scalar_one_or_none()
    
    if not settings:
        # 创建默认设置
        settings = UserSettings(
            user_id=current_user.id,
            ai_provider="deepseek"
        )
        db.add(settings)
        await db.commit()
        await db.refresh(settings)
    
    return ResponseModel(data=SettingsResponse(
        id=settings.id,
        user_id=settings.user_id,
        ai_provider=settings.ai_provider,
        has_deepseek_key=bool(settings.deepseek_api_key),
        has_openai_key=bool(settings.openai_api_key),
        has_iflow_key=bool(settings.iflow_api_key),
        iflow_model=settings.iflow_model,
        created_at=settings.created_at,
        updated_at=settings.updated_at
    ))


@router.put("", response_model=ResponseModel[SettingsResponse])
async def update_settings(
    settings_in: SettingsUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """更新用户设置"""
    result = await db.execute(
        select(UserSettings).where(UserSettings.user_id == current_user.id)
    )
    settings = result.scalar_one_or_none()
    
    if not settings:
        settings = UserSettings(user_id=current_user.id)
        db.add(settings)
    
    # 更新字段
    if settings_in.ai_provider is not None:
        settings.ai_provider = settings_in.ai_provider
    if settings_in.deepseek_api_key is not None:
        settings.deepseek_api_key = settings_in.deepseek_api_key
    if settings_in.openai_api_key is not None:
        settings.openai_api_key = settings_in.openai_api_key
    if settings_in.iflow_api_key is not None:
        settings.iflow_api_key = settings_in.iflow_api_key
    if settings_in.iflow_model is not None:
        settings.iflow_model = settings_in.iflow_model
    
    await db.commit()
    await db.refresh(settings)
    
    return ResponseModel(
        data=SettingsResponse(
            id=settings.id,
            user_id=settings.user_id,
            ai_provider=settings.ai_provider,
            has_deepseek_key=bool(settings.deepseek_api_key),
            has_openai_key=bool(settings.openai_api_key),
            has_iflow_key=bool(settings.iflow_api_key),
            iflow_model=settings.iflow_model,
            created_at=settings.created_at,
            updated_at=settings.updated_at
        ),
        message="设置已更新"
    )


@router.post("/test-api-key", response_model=ResponseModel)
async def test_api_key(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """测试API密钥是否有效"""
    result = await db.execute(
        select(UserSettings).where(UserSettings.user_id == current_user.id)
    )
    settings = result.scalar_one_or_none()
    
    if not settings:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="请先配置API密钥"
        )
    
    provider = settings.ai_provider
    api_key = None
    
    if provider == "deepseek":
        api_key = settings.deepseek_api_key
    elif provider == "openai":
        api_key = settings.openai_api_key
    elif provider == "iflow":
        api_key = settings.iflow_api_key
    
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"请先配置{provider}的API密钥"
        )
    
    # iFlow 真实连接测试
    if provider == "iflow":
        from app.ai.iflow import IFlowProvider
        result = await IFlowProvider.test_connection(
            api_key=api_key,
            model=settings.iflow_model
        )
        if result["success"]:
            return ResponseModel(message=result["message"])
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result["message"]
            )
    
    # 其他provider简单测试
    return ResponseModel(message=f"{provider} API密钥已配置")
