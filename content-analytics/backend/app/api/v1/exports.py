import uuid
import os
from threading import Thread
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.db.session import get_db
from app.models.user import User
from app.models.analysis import Analysis, AnalysisStatus
from app.models.export import Export, ExportStatus, ExportFormat
from app.schemas.common import ResponseModel
from app.api.deps import get_current_user
from app.tasks.export_tasks import run_export_task
from app.tasks.celery_app import is_celery_available

router = APIRouter()


@router.post("/{analysis_id}/export", response_model=ResponseModel)
async def create_export(
    analysis_id: uuid.UUID,
    format: str = "excel",
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # 验证分析任务存在
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
            detail="分析任务尚未完成"
        )
    
    # 验证导出格式
    try:
        export_format = ExportFormat(format)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="不支持的导出格式"
        )
    
    # 创建导出记录
    export = Export(
        analysis_id=analysis_id,
        user_id=current_user.id,
        format=export_format,
        status=ExportStatus.PENDING
    )
    db.add(export)
    await db.commit()
    await db.refresh(export)
    
    # 触发异步导出任务
    if is_celery_available():
        run_export_task.delay(str(export.id))
        print(f"[exports] Celery task triggered for export {export.id}")
    else:
        # Celery未运行时使用后台线程处理
        print(f"[exports] Celery not available, using background thread for export {export.id}")
        from app.tasks.export_tasks import _run_export, run_async as export_run_async
        def run_export_thread(export_id):
            try:
                export_run_async(_run_export(export_id, use_thread_session=True))
                print(f"[exports] Background export completed for {export_id}")
            except Exception as ex:
                print(f"[exports] Background export failed for {export_id}: {ex}")
        Thread(target=run_export_thread, args=(str(export.id),), daemon=True).start()
    
    return ResponseModel(message="导出任务已创建", data={"export_id": str(export.id)})


@router.get("/{export_id}/download")
async def download_export(
    export_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    result = await db.execute(
        select(Export).where(
            Export.id == export_id,
            Export.user_id == current_user.id
        )
    )
    export = result.scalar_one_or_none()
    
    if not export:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="导出记录不存在"
        )
    
    if export.status != ExportStatus.COMPLETED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="导出任务尚未完成"
        )
    
    if not export.file_path or not os.path.exists(export.file_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="导出文件不存在"
        )

    format_value = getattr(export.format, "value", export.format)
    ext_map = {
        "excel": "xlsx",
        "json": "json",
        "pdf": "pdf",
    }
    filename = f"analysis_report.{ext_map.get(format_value, format_value)}"
    
    return FileResponse(
        path=export.file_path,
        filename=filename,
        media_type="application/octet-stream"
    )


@router.get("", response_model=ResponseModel)
async def list_exports(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取用户的导出记录列表"""
    result = await db.execute(
        select(Export)
        .options(selectinload(Export.analysis))
        .where(Export.user_id == current_user.id)
        .order_by(Export.created_at.desc())
        .limit(50)
    )
    exports = result.scalars().all()
    
    export_list = []
    for exp in exports:
        format_value = getattr(exp.format, "value", exp.format)
        status_value = getattr(exp.status, "value", exp.status)
        export_list.append({
            "id": str(exp.id),
            "analysis_id": str(exp.analysis_id),
            "analysis_name": exp.analysis.name if exp.analysis else "未知",
            "format": format_value,
            "status": status_value,
            "error_message": exp.error_message,
            "created_at": exp.created_at.isoformat(),
            "completed_at": exp.completed_at.isoformat() if exp.completed_at else None
        })
    
    return ResponseModel(data=export_list)


@router.get("/{export_id}/status", response_model=ResponseModel)
async def get_export_status(
    export_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取导出任务状态"""
    result = await db.execute(
        select(Export).where(
            Export.id == export_id,
            Export.user_id == current_user.id
        )
    )
    export = result.scalar_one_or_none()
    
    if not export:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="导出记录不存在"
        )
    
    return ResponseModel(data={
        "id": str(export.id),
        "status": getattr(export.status, "value", export.status),
        "error_message": export.error_message,
        "completed_at": export.completed_at.isoformat() if export.completed_at else None
    })
