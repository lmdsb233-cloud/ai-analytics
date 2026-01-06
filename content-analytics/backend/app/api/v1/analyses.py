import uuid
from threading import Thread
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from typing import List, Optional

from app.db.session import get_db
from app.models.user import User
from app.models.dataset import Dataset
from app.models.analysis import Analysis, AnalysisStatus, AnalysisResult, AIOutput
from app.schemas.analysis import (
    AnalysisCreate,
    AnalysisResponse,
    AnalysisResultResponse,
    AnalysisDetailResponse
)
from app.schemas.common import ResponseModel
from app.api.deps import get_current_user
from app.tasks.analysis_tasks import run_analysis_task, _run_analysis, run_async
from app.tasks.ai_tasks import run_ai_analysis_task, _run_ai_analysis
from app.tasks.celery_app import is_celery_available

router = APIRouter()


def _resolve_ai_status(analysis: Analysis, total_results: int, ai_outputs: int) -> Optional[str]:
    if analysis.status == AnalysisStatus.AI_PROCESSING:
        return "processing"
    if analysis.status != AnalysisStatus.COMPLETED:
        return None
    if total_results == 0 or ai_outputs == 0:
        return "not_started"
    if ai_outputs < total_results:
        return "partial"
    return "completed"


async def _get_ai_counts(db: AsyncSession, analysis_ids: List[uuid.UUID]):
    if not analysis_ids:
        return {}, {}
    total_rows = await db.execute(
        select(
            AnalysisResult.analysis_id,
            func.count(AnalysisResult.id).label("total")
        )
        .where(AnalysisResult.analysis_id.in_(analysis_ids))
        .group_by(AnalysisResult.analysis_id)
    )
    total_map = {row.analysis_id: row.total for row in total_rows}
    ai_rows = await db.execute(
        select(
            AnalysisResult.analysis_id,
            func.count(AIOutput.id).label("ai_count")
        )
        .join(AIOutput, AIOutput.analysis_result_id == AnalysisResult.id, isouter=True)
        .where(AnalysisResult.analysis_id.in_(analysis_ids))
        .group_by(AnalysisResult.analysis_id)
    )
    ai_map = {row.analysis_id: row.ai_count for row in ai_rows}
    return total_map, ai_map


def _to_analysis_response(
    analysis: Analysis,
    total_map: dict,
    ai_map: dict
) -> AnalysisResponse:
    total = total_map.get(analysis.id, 0)
    ai_count = ai_map.get(analysis.id, 0)
    return AnalysisResponse(
        id=analysis.id,
        dataset_id=analysis.dataset_id,
        name=analysis.name,
        status=analysis.status,
        progress=analysis.progress,
        ai_status=_resolve_ai_status(analysis, total, ai_count),
        error_message=analysis.error_message,
        created_at=analysis.created_at,
        completed_at=analysis.completed_at
    )


@router.post("", response_model=ResponseModel[AnalysisResponse])
async def create_analysis(
    analysis_in: AnalysisCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # 验证数据集存在且属于当前用户
    result = await db.execute(
        select(Dataset).where(
            Dataset.id == analysis_in.dataset_id,
            Dataset.user_id == current_user.id
        )
    )
    dataset = result.scalar_one_or_none()
    
    if not dataset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="数据集不存在"
        )
    
    # 创建分析任务
    analysis = Analysis(
        dataset_id=analysis_in.dataset_id,
        user_id=current_user.id,
        name=analysis_in.name or f"分析-{datetime.now().strftime('%Y%m%d%H%M%S')}",
        config=analysis_in.config,
        status=AnalysisStatus.PENDING
    )
    db.add(analysis)
    await db.commit()
    await db.refresh(analysis)
    
    # 触发异步分析任务
    if is_celery_available():
        run_analysis_task.delay(str(analysis.id))
        print(f"[analyses] Celery task triggered for analysis {analysis.id}")
    else:
        # Celery未运行时，使用后台线程处理
        print(f"[analyses] Celery not available, using background thread for analysis {analysis.id}")
        def run_analysis_thread(analysis_id):
            try:
                run_async(_run_analysis(analysis_id, use_thread_session=True))
                print(f"[analyses] Background analysis completed for {analysis_id}")
            except Exception as ex:
                print(f"[analyses] Background analysis failed for {analysis_id}: {ex}")
        Thread(target=run_analysis_thread, args=(str(analysis.id),), daemon=True).start()
    
    return ResponseModel(data=analysis)


@router.get("", response_model=ResponseModel[List[AnalysisResponse]])
async def list_analyses(
    dataset_id: Optional[uuid.UUID] = None,
    page: int = 1,
    page_size: int = 20,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if page < 1 or page_size < 1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="分页参数不合法"
        )
    query = select(Analysis).where(Analysis.user_id == current_user.id)
    
    if dataset_id:
        query = query.where(Analysis.dataset_id == dataset_id)
    
    offset = (page - 1) * page_size
    result = await db.execute(
        query.order_by(Analysis.created_at.desc())
        .offset(offset)
        .limit(page_size)
    )
    analyses = result.scalars().all()
    analysis_ids = [a.id for a in analyses]
    total_map, ai_map = await _get_ai_counts(db, analysis_ids)
    response_data = [_to_analysis_response(a, total_map, ai_map) for a in analyses]
    return ResponseModel(data=response_data)


@router.get("/{analysis_id}", response_model=ResponseModel[AnalysisResponse])
async def get_analysis(
    analysis_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    result = await db.execute(
        select(Analysis).where(
            Analysis.id == analysis_id,
            Analysis.user_id == current_user.id
        )
    )
    analysis = result.scalar_one_or_none()
    
    if not analysis:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="分析任务不存在"
        )
    
    total_map, ai_map = await _get_ai_counts(db, [analysis.id])
    return ResponseModel(data=_to_analysis_response(analysis, total_map, ai_map))


@router.get("/{analysis_id}/results", response_model=ResponseModel[List[AnalysisResultResponse]])
async def get_analysis_results(
    analysis_id: uuid.UUID,
    performance: Optional[str] = None,
    page: int = 1,
    page_size: int = 50,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if page < 1 or page_size < 1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="分页参数不合法"
        )
    # 验证分析任务存在且属于当前用户
    result = await db.execute(
        select(Analysis).where(
            Analysis.id == analysis_id,
            Analysis.user_id == current_user.id
        )
    )
    analysis = result.scalar_one_or_none()
    
    if not analysis:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="分析任务不存在"
        )
    
    # 查询分析结果
    query = select(AnalysisResult).where(AnalysisResult.analysis_id == analysis_id)
    
    if performance:
        query = query.where(AnalysisResult.performance == performance)
    
    offset = (page - 1) * page_size
    from app.models.post import Post
    result = await db.execute(
        query.options(selectinload(AnalysisResult.post))
        .join(Post, AnalysisResult.post_id == Post.id)
        .order_by(Post.created_at.asc())  # 按原始数据集顺序排序
        .offset(offset)
        .limit(page_size)
    )
    results = result.scalars().all()
    
    # 构建响应
    response_data = []
    for r in results:
        response_data.append(AnalysisResultResponse(
            id=r.id,
            analysis_id=r.analysis_id,
            post_id=r.post_id,
            performance=r.performance,
            result_data=r.result_data,
            created_at=r.created_at,
            post_data_id=r.post.data_id if r.post else None,
            post_content_type=r.post.content_type if r.post else None,
            post_type=r.post.post_type if r.post else None
        ))
    
    return ResponseModel(data=response_data)


@router.post("/{analysis_id}/ai", response_model=ResponseModel)
async def trigger_ai_analysis(
    analysis_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    result = await db.execute(
        select(Analysis).where(
            Analysis.id == analysis_id,
            Analysis.user_id == current_user.id
        )
    )
    analysis = result.scalar_one_or_none()
    
    if not analysis:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="分析任务不存在"
        )
    
    if analysis.status != AnalysisStatus.COMPLETED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="分析任务尚未完成，无法触发AI分析"
        )
    
    # 更新状态，并重置进度，避免继承非AI阶段的100%
    analysis.status = AnalysisStatus.AI_PROCESSING
    analysis.progress = "0%"
    analysis.error_message = None
    await db.commit()
    
    # 触发AI分析异步任务
    if is_celery_available():
        run_ai_analysis_task.delay(str(analysis.id))
        print(f"[analyses] Celery AI task triggered for analysis {analysis.id}")
    else:
        # Celery未运行时，使用后台线程处理
        print(f"[analyses] Celery not available, using background thread for AI analysis {analysis.id}")
        from app.tasks.ai_tasks import run_async as ai_run_async
        def run_ai_thread(analysis_id):
            try:
                ai_run_async(_run_ai_analysis(analysis_id, use_thread_session=True))
                print(f"[analyses] Background AI analysis completed for {analysis_id}")
            except Exception as ex:
                import traceback
                print(f"[analyses] Background AI analysis failed for {analysis_id}: {ex}")
                traceback.print_exc()
        Thread(target=run_ai_thread, args=(str(analysis.id),), daemon=True).start()
    
    return ResponseModel(message="AI分析任务已触发")


@router.post("/{analysis_id}/stop", response_model=ResponseModel)
async def stop_analysis(
    analysis_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """停止分析任务"""
    result = await db.execute(
        select(Analysis).where(
            Analysis.id == analysis_id,
            Analysis.user_id == current_user.id
        )
    )
    analysis = result.scalar_one_or_none()
    
    if not analysis:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="分析任务不存在"
        )
    
    # 只能停止正在运行的任务
    if analysis.status not in [AnalysisStatus.ANALYZING, AnalysisStatus.AI_PROCESSING]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="只能停止正在运行的任务"
        )
    
    # 设置状态为失败（停止）
    analysis.status = AnalysisStatus.FAILED
    analysis.error_message = "用户手动停止"
    await db.commit()
    
    return ResponseModel(message="分析任务已停止")


@router.delete("/{analysis_id}", response_model=ResponseModel)
async def delete_analysis(
    analysis_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """删除分析任务"""
    result = await db.execute(
        select(Analysis).where(
            Analysis.id == analysis_id,
            Analysis.user_id == current_user.id
        )
    )
    analysis = result.scalar_one_or_none()
    
    if not analysis:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="分析任务不存在"
        )
    
    await db.delete(analysis)
    await db.commit()
    
    return ResponseModel(message="分析任务已删除")
