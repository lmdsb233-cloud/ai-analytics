import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.db.session import get_db
from app.models.user import User
from app.models.post import Post
from app.models.dataset import Dataset
from app.models.analysis import AnalysisResult, AIOutput
from app.schemas.post import PostDetail
from app.schemas.analysis import AIOutputResponse
from app.schemas.common import ResponseModel
from app.api.deps import get_current_user

router = APIRouter()


@router.get("/{post_id}", response_model=ResponseModel[PostDetail])
async def get_post(
    post_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    result = await db.execute(
        select(Post)
        .options(selectinload(Post.dataset))
        .where(Post.id == post_id)
    )
    post = result.scalar_one_or_none()
    
    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="笔记不存在"
        )
    
    # 验证数据集属于当前用户
    if post.dataset.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权访问此笔记"
        )
    
    return ResponseModel(data=post)


@router.get("/{post_id}/ai-output", response_model=ResponseModel[AIOutputResponse])
async def get_post_ai_output(
    post_id: uuid.UUID,
    analysis_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # 查询分析结果
    result = await db.execute(
        select(AnalysisResult)
        .options(selectinload(AnalysisResult.ai_output))
        .where(
            AnalysisResult.post_id == post_id,
            AnalysisResult.analysis_id == analysis_id
        )
    )
    analysis_result = result.scalar_one_or_none()
    
    # 如果没有分析结果或AI输出，返回空数据而不是404
    if not analysis_result or not analysis_result.ai_output:
        return ResponseModel(data=None, message="暂无AI分析结果")
    
    return ResponseModel(data=analysis_result.ai_output)
