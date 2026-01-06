import os
import uuid
import aiofiles
from threading import Thread
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import List

from app.db.session import get_db
from app.models.user import User
from app.models.dataset import Dataset, DatasetStatus
from app.schemas.dataset import DatasetResponse, DatasetList
from app.schemas.common import ResponseModel
from app.api.deps import get_current_user
from app.core.config import settings
from app.tasks.dataset_tasks import parse_dataset_task, _parse_dataset_impl, run_async_in_thread
from app.tasks.celery_app import is_celery_available

router = APIRouter()


@router.post("/upload", response_model=ResponseModel[DatasetResponse])
async def upload_dataset(
    file: UploadFile = File(...),
    name: str = Form(...),
    background_tasks: BackgroundTasks = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # 验证文件类型
    if not file.filename.endswith(('.xlsx', '.xls')):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="只支持Excel文件格式(.xlsx, .xls)"
        )
    
    # 准备保存文件
    upload_dir = os.path.join(settings.UPLOAD_DIR, str(current_user.id))
    os.makedirs(upload_dir, exist_ok=True)
    
    file_id = str(uuid.uuid4())
    file_ext = os.path.splitext(file.filename)[1]
    file_path = os.path.join(upload_dir, f"{file_id}{file_ext}")
    
    # 流式写入文件，避免内存占用过大
    total_size = 0
    async with aiofiles.open(file_path, 'wb') as out_file:
        while chunk := await file.read(1024 * 1024):  # 1MB chunks
            total_size += len(chunk)
            if total_size > settings.MAX_UPLOAD_SIZE:
                await out_file.close()
                os.remove(file_path)
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"文件大小超过限制({settings.MAX_UPLOAD_SIZE // 1024 // 1024}MB)"
                )
            await out_file.write(chunk)
    
    # 创建数据集记录
    dataset = Dataset(
        user_id=current_user.id,
        name=name,
        file_path=file_path,
        original_filename=file.filename,
        status=DatasetStatus.PENDING
    )
    db.add(dataset)
    await db.commit()
    await db.refresh(dataset)
    
    # 触发异步任务解析Excel
    if is_celery_available():
        parse_dataset_task.delay(str(dataset.id))
        print(f"[datasets] Celery task triggered for dataset {dataset.id}")
    else:
        # Celery未运行时，使用后台线程处理
        print(f"[datasets] Celery not available, using background thread for dataset {dataset.id}")
        def run_parse_task(dataset_id):
            try:
                run_async_in_thread(_parse_dataset_impl, dataset_id)
                print(f"[datasets] Background parse completed for {dataset_id}")
            except Exception as ex:
                print(f"[datasets] Background parse failed for {dataset_id}: {ex}")
        Thread(target=run_parse_task, args=(str(dataset.id),), daemon=True).start()
    
    return ResponseModel(data=dataset)


@router.get("", response_model=ResponseModel[DatasetList])
async def list_datasets(
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
    # 查询总数（使用COUNT优化，不加载所有记录）
    count_result = await db.execute(
        select(func.count(Dataset.id)).where(Dataset.user_id == current_user.id)
    )
    total = count_result.scalar() or 0
    
    # 分页查询
    offset = (page - 1) * page_size
    result = await db.execute(
        select(Dataset)
        .where(Dataset.user_id == current_user.id)
        .order_by(Dataset.created_at.desc())
        .offset(offset)
        .limit(page_size)
    )
    datasets = result.scalars().all()
    
    return ResponseModel(data=DatasetList(items=datasets, total=total))


@router.get("/{dataset_id}", response_model=ResponseModel[DatasetResponse])
async def get_dataset(
    dataset_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    result = await db.execute(
        select(Dataset).where(
            Dataset.id == dataset_id,
            Dataset.user_id == current_user.id
        )
    )
    dataset = result.scalar_one_or_none()
    
    if not dataset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="数据集不存在"
        )
    
    return ResponseModel(data=dataset)


@router.delete("/{dataset_id}", response_model=ResponseModel)
async def delete_dataset(
    dataset_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    result = await db.execute(
        select(Dataset).where(
            Dataset.id == dataset_id,
            Dataset.user_id == current_user.id
        )
    )
    dataset = result.scalar_one_or_none()
    
    if not dataset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="数据集不存在"
        )
    
    # 删除文件
    if os.path.exists(dataset.file_path):
        os.remove(dataset.file_path)
    
    await db.delete(dataset)
    await db.commit()
    
    return ResponseModel(message="删除成功")
