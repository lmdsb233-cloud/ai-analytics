from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Dict, Any
import base64
import uuid
from pathlib import Path
import aiofiles
import httpx
import logging

from app.db.session import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.models.user_settings import UserSettings
from app.models.screenshot import ScreenshotAnalysis
from app.ai.factory import AIProviderFactory
from app.core.config import settings

router = APIRouter()

# 上传目录
UPLOAD_DIR = Path(settings.UPLOAD_DIR) / "screenshots"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


@router.post("/analyze")
async def analyze_screenshot(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    上传截图并使用 AI 分析
    """
    # 验证文件类型
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="只支持图片文件")

    result = await db.execute(
        select(UserSettings).where(UserSettings.user_id == current_user.id)
    )
    user_settings = result.scalar_one_or_none()
    if not user_settings:
        user_settings = UserSettings(user_id=current_user.id)
        db.add(user_settings)
        await db.commit()
        await db.refresh(user_settings)

    api_key = user_settings.get_api_key()
    if not api_key:
        raise HTTPException(
            status_code=400,
            detail=f"\u8bf7\u5148\u914d\u7f6e {user_settings.ai_provider} \u7684 API \u5bc6\u94a5"
        )
    # 生成唯一文件名
    file_extension = file.filename.split(".")[-1] if file.filename else "png"
    unique_filename = f"{uuid.uuid4()}.{file_extension}"
    file_path = UPLOAD_DIR / unique_filename

    try:
        # 保存文件
        async with aiofiles.open(file_path, "wb") as f:
            content = await file.read()
            if len(content) > settings.MAX_UPLOAD_SIZE:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"截图文件过大，请选择小于 {settings.MAX_UPLOAD_SIZE // (1024 * 1024)}MB 的图片"
                )
            await f.write(content)

        # 转换为 base64
        base64_image = base64.b64encode(content).decode("utf-8")

        # 获取用户的 AI Provider
        ai_provider = AIProviderFactory.create(
            provider_name=user_settings.ai_provider,
            api_key=api_key
        )

        # 检查是否支持图片分析
        if not hasattr(ai_provider, "analyze_with_image"):
            raise HTTPException(
                status_code=400,
                detail=f"当前 AI Provider ({user_settings.ai_provider}) 不支持图片分析，请使用 iFlow (Kimi)"
            )

        # 调用 AI 分析
        result = await ai_provider.analyze_with_image(base64_image)

        # 保存分析结果到数据库
        screenshot_analysis = ScreenshotAnalysis(
            user_id=current_user.id,
            image_path=str(file_path),
            summary=result.summary,
            strengths=result.strengths,
            weaknesses=result.weaknesses,
            suggestions=result.suggestions,
            model_name=result.model_name,
            tokens_used=result.tokens_used
        )

        db.add(screenshot_analysis)
        await db.commit()
        await db.refresh(screenshot_analysis)

        return {
            "success": True,
            "data": {
                "id": str(screenshot_analysis.id),
                "summary": result.summary,
                "strengths": result.strengths,
                "weaknesses": result.weaknesses,
                "suggestions": result.suggestions,
                "model_name": result.model_name,
                "tokens_used": result.tokens_used,
                "image_path": str(file_path),
                "created_at": screenshot_analysis.created_at.isoformat()
            }
        }

    except httpx.HTTPStatusError as e:
        if file_path.exists():
            file_path.unlink()
        status_code = e.response.status_code
        if status_code in (401, 403):
            detail = "AI 服务认证失败，请检查 API Key"
        elif status_code == 429:
            detail = "AI 服务请求过于频繁，请稍后重试"
        elif status_code >= 500:
            detail = "AI 服务器异常，请稍后重试"
        else:
            detail = f"AI 请求失败：{status_code}"
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=detail)
    except (httpx.TimeoutException, httpx.ConnectError):
        if file_path.exists():
            file_path.unlink()
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="AI 服务连接超时或无法连接，请检查网络"
        )
    except HTTPException:
        if file_path.exists():
            file_path.unlink()
        raise
    except ValueError as e:
        if file_path.exists():
            file_path.unlink()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        # 删除已保存的文件
        logging.exception("Screenshot analyze failed")
        if file_path.exists():
            file_path.unlink()
        raise HTTPException(status_code=500, detail=f"分析失败: {str(e)}")


@router.get("/history")
async def get_screenshot_history(
    skip: int = 0,
    limit: int = 20,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    获取截图分析历史记录
    """
    if skip < 0 or limit < 1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="分页参数不合法"
        )
    query = (
        select(ScreenshotAnalysis)
        .where(ScreenshotAnalysis.user_id == current_user.id)
        .order_by(ScreenshotAnalysis.created_at.desc())
        .offset(skip)
        .limit(limit)
    )

    result = await db.execute(query)
    analyses = result.scalars().all()

    return {
        "success": True,
        "data": [
            {
                "id": str(analysis.id),
                "image_path": analysis.image_path,
                "summary": analysis.summary,
                "model_name": analysis.model_name,
                "created_at": analysis.created_at.isoformat()
            }
            for analysis in analyses
        ],
        "total": len(analyses)
    }
