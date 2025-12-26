from celery import Celery
from app.core.config import settings

celery_app = Celery(
    "content_analytics",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=[
        "app.tasks.dataset_tasks",
        "app.tasks.analysis_tasks",
        "app.tasks.ai_tasks",
        "app.tasks.export_tasks"
    ]
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Asia/Shanghai",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=3600,  # 1小时超时
    worker_prefetch_multiplier=1,
    task_acks_late=True,
)


# 缓存 Celery worker 可用性检查结果
_celery_available = None
_celery_check_time = 0


def is_celery_available() -> bool:
    """检查 Celery worker 是否可用"""
    global _celery_available, _celery_check_time
    import time
    
    # 缓存 30 秒
    now = time.time()
    if _celery_available is not None and (now - _celery_check_time) < 30:
        return _celery_available
    
    try:
        # 检查是否有活跃的 worker
        inspect = celery_app.control.inspect()
        active_workers = inspect.active_queues()
        _celery_available = active_workers is not None and len(active_workers) > 0
    except Exception:
        _celery_available = False
    
    _celery_check_time = now
    return _celery_available
