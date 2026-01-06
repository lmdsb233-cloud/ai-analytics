import uuid
from typing import List
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.db.session import get_db
from app.models.user import User
from app.models.post import Post
from app.models.dataset import Dataset
from app.models.analysis import Analysis, AnalysisResult, AIOutput, AIOutputHistory
from app.schemas.post import PostDetail
from app.schemas.analysis import (
    AIOutputResponse,
    AIOutputUpdate,
    AIOutputHistoryResponse,
    AIOutputRollbackRequest,
)
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
        .order_by(AnalysisResult.created_at.desc())
    )
    analysis_result = result.scalars().first()
    
    # 如果没有分析结果或AI输出，返回空数据而不是404
    if not analysis_result or not analysis_result.ai_output:
        return ResponseModel(data=None, message="暂无AI分析结果")
    
    return ResponseModel(data=analysis_result.ai_output)


@router.get("/{post_id}/analysis-result-id", response_model=ResponseModel[dict])
async def get_post_analysis_result_id(
    post_id: uuid.UUID,
    analysis_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取笔记的分析结果ID（用于创建对话）"""
    # 查询分析结果 - 使用 first() 避免多行错误
    result = await db.execute(
        select(AnalysisResult)
        .join(AnalysisResult.analysis)
        .where(
            AnalysisResult.post_id == post_id,
            AnalysisResult.analysis_id == analysis_id,
            Analysis.user_id == current_user.id
        )
        .order_by(AnalysisResult.created_at.desc())
        .limit(1)
    )
    analysis_result = result.scalars().first()
    
    if not analysis_result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="分析结果不存在"
        )
    
    return ResponseModel(data={"analysis_result_id": str(analysis_result.id)})



@router.put("/{post_id}/ai-output", response_model=ResponseModel[AIOutputResponse])
async def update_post_ai_output(
    post_id: uuid.UUID,
    analysis_id: uuid.UUID,
    update_data: AIOutputUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """更新笔记的 AI 分析结果"""
    # 查询分析结果并验证权限 - 使用 first() 避免多行错误
    result = await db.execute(
        select(AnalysisResult)
        .options(selectinload(AnalysisResult.ai_output))
        .join(AnalysisResult.analysis)
        .where(
            AnalysisResult.post_id == post_id,
            AnalysisResult.analysis_id == analysis_id,
            Analysis.user_id == current_user.id
        )
        .order_by(AnalysisResult.created_at.desc())
        .limit(1)
    )
    analysis_result = result.scalars().first()
    
    if not analysis_result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="分析结果不存在或无权限"
        )
    
    ai_output = analysis_result.ai_output
    if not ai_output:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="AI 输出不存在，请先生成 AI 分析"
        )

    # 检查是否有实际变化
    has_changes = False
    if update_data.summary is not None and update_data.summary != ai_output.summary:
        has_changes = True
    if update_data.strengths is not None and update_data.strengths != ai_output.strengths:
        has_changes = True
    if update_data.weaknesses is not None and update_data.weaknesses != ai_output.weaknesses:
        has_changes = True
    if update_data.suggestions is not None and update_data.suggestions != ai_output.suggestions:
        has_changes = True

    if not has_changes:
        return ResponseModel(data=ai_output, message="未检测到修改")

    # 保存修改前快照
    history = AIOutputHistory(
        ai_output_id=ai_output.id,
        analysis_result_id=analysis_result.id,
        user_id=current_user.id,
        action="update",
        summary=ai_output.summary,
        strengths=ai_output.strengths,
        weaknesses=ai_output.weaknesses,
        suggestions=ai_output.suggestions,
        model_name=ai_output.model_name,
        raw_response=ai_output.raw_response,
        tokens_used=ai_output.tokens_used
    )
    db.add(history)

    # 更新字段（只更新提供的字段）
    if update_data.summary is not None:
        ai_output.summary = update_data.summary
    if update_data.strengths is not None:
        ai_output.strengths = update_data.strengths
    if update_data.weaknesses is not None:
        ai_output.weaknesses = update_data.weaknesses
    if update_data.suggestions is not None:
        ai_output.suggestions = update_data.suggestions
    
    # 标记为用户修改
    if ai_output.model_name and "(用户修改)" not in ai_output.model_name:
        ai_output.model_name = f"{ai_output.model_name} (用户修改)"
    
    await db.commit()
    await db.refresh(ai_output)
    
    return ResponseModel(data=ai_output, message="AI 分析结果已更新")


@router.get("/{post_id}/ai-output/history", response_model=ResponseModel[List[AIOutputHistoryResponse]])
async def get_post_ai_output_history(
    post_id: uuid.UUID,
    analysis_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取 AI 输出的修改历史"""
    result = await db.execute(
        select(AnalysisResult)
        .options(selectinload(AnalysisResult.ai_output))
        .join(AnalysisResult.analysis)
        .where(
            AnalysisResult.post_id == post_id,
            AnalysisResult.analysis_id == analysis_id,
            Analysis.user_id == current_user.id
        )
        .order_by(AnalysisResult.created_at.desc())
        .limit(1)
    )
    analysis_result = result.scalars().first()
    if not analysis_result or not analysis_result.ai_output:
        return ResponseModel(data=[])

    history_result = await db.execute(
        select(AIOutputHistory)
        .where(
            AIOutputHistory.ai_output_id == analysis_result.ai_output.id,
            AIOutputHistory.user_id == current_user.id
        )
        .order_by(AIOutputHistory.created_at.desc())
    )
    histories = history_result.scalars().all()
    return ResponseModel(data=histories)


@router.post("/{post_id}/ai-output/rollback", response_model=ResponseModel[AIOutputResponse])
async def rollback_post_ai_output(
    post_id: uuid.UUID,
    analysis_id: uuid.UUID,
    rollback_data: AIOutputRollbackRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """回退 AI 输出到指定历史版本"""
    result = await db.execute(
        select(AnalysisResult)
        .options(selectinload(AnalysisResult.ai_output))
        .join(AnalysisResult.analysis)
        .where(
            AnalysisResult.post_id == post_id,
            AnalysisResult.analysis_id == analysis_id,
            Analysis.user_id == current_user.id
        )
        .order_by(AnalysisResult.created_at.desc())
        .limit(1)
    )
    analysis_result = result.scalars().first()
    if not analysis_result or not analysis_result.ai_output:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="AI 输出不存在，请先生成 AI 分析"
        )

    ai_output = analysis_result.ai_output
    history_result = await db.execute(
        select(AIOutputHistory)
        .where(
            AIOutputHistory.id == rollback_data.history_id,
            AIOutputHistory.ai_output_id == ai_output.id,
            AIOutputHistory.user_id == current_user.id
        )
        .limit(1)
    )
    history = history_result.scalars().first()
    if not history:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="历史记录不存在或无权限"
        )

    # 回退前保存当前快照
    rollback_snapshot = AIOutputHistory(
        ai_output_id=ai_output.id,
        analysis_result_id=analysis_result.id,
        user_id=current_user.id,
        action="rollback",
        summary=ai_output.summary,
        strengths=ai_output.strengths,
        weaknesses=ai_output.weaknesses,
        suggestions=ai_output.suggestions,
        model_name=ai_output.model_name,
        raw_response=ai_output.raw_response,
        tokens_used=ai_output.tokens_used
    )
    db.add(rollback_snapshot)

    ai_output.summary = history.summary
    ai_output.strengths = history.strengths
    ai_output.weaknesses = history.weaknesses
    ai_output.suggestions = history.suggestions
    ai_output.model_name = history.model_name
    ai_output.raw_response = history.raw_response
    ai_output.tokens_used = history.tokens_used

    await db.commit()
    await db.refresh(ai_output)

    return ResponseModel(data=ai_output, message="已回退到历史版本")


@router.get("/{post_id}/analysis-result", response_model=ResponseModel[dict])
async def get_post_analysis_result(
    post_id: uuid.UUID,
    analysis_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取笔记的完整分析结果（包含 AI 输出）"""
    result = await db.execute(
        select(AnalysisResult)
        .options(selectinload(AnalysisResult.ai_output))
        .join(AnalysisResult.analysis)
        .where(
            AnalysisResult.post_id == post_id,
            AnalysisResult.analysis_id == analysis_id,
            Analysis.user_id == current_user.id
        )
        .order_by(AnalysisResult.created_at.desc())
        .limit(1)
    )
    analysis_result = result.scalars().first()
    
    if not analysis_result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="分析结果不存在"
        )
    
    ai_output = analysis_result.ai_output
    
    return ResponseModel(data={
        "analysis_result_id": str(analysis_result.id),
        "performance": analysis_result.performance,
        "result_data": analysis_result.result_data,
        "ai_output": {
            "id": str(ai_output.id) if ai_output else None,
            "summary": ai_output.summary if ai_output else None,
            "strengths": ai_output.strengths if ai_output else [],
            "weaknesses": ai_output.weaknesses if ai_output else [],
            "suggestions": ai_output.suggestions if ai_output else [],
            "model_name": ai_output.model_name if ai_output else None,
        } if ai_output else None
    })
