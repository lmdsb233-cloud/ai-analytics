import pandas as pd
from sqlalchemy import select
from app.tasks.celery_app import celery_app
from app.db.session import create_thread_session_maker
from app.models.dataset import Dataset, DatasetStatus
from app.models.post import Post
from app.analysis.processor import DataProcessor
import asyncio


def run_async_in_thread(coro_func, *args, **kwargs):
    """在后台线程中运行异步代码，使用独立的数据库会话"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    session_maker, thread_engine = create_thread_session_maker()
    try:
        async def wrapper():
            async with session_maker() as db:
                return await coro_func(db, *args, **kwargs)
        return loop.run_until_complete(wrapper())
    except Exception as e:
        print(f"[run_async_in_thread] Error: {e}")
        import traceback
        traceback.print_exc()
        raise
    finally:
        loop.run_until_complete(thread_engine.dispose())
        loop.close()


def run_async(coro):
    """在同步环境中运行异步代码"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(coro)
    except Exception as e:
        print(f"[run_async] Error: {e}")
        import traceback
        traceback.print_exc()
        raise
    finally:
        loop.close()


async def _parse_dataset_impl(db, dataset_id: str):
    """解析数据集的实际实现"""
    result = await db.execute(select(Dataset).where(Dataset.id == dataset_id))
    dataset = result.scalar_one_or_none()

    if not dataset:
        return {"error": "数据集不存在"}

    try:
        dataset.status = DatasetStatus.PROCESSING
        await db.commit()

        df = pd.read_excel(dataset.file_path)

        processor = DataProcessor(df)
        validation = processor.validate()

        if not validation['valid']:
            dataset.status = DatasetStatus.FAILED
            dataset.error_message = '; '.join(validation['errors'])
            await db.commit()
            return {"error": validation['errors']}

        processor.process()
        records = processor.to_records()

        for record in records:
            post = Post(
                dataset_id=dataset.id,
                data_id=str(record.get('data_id', '')),
                publish_time=record.get('publish_time'),
                publish_link=record.get('publish_link'),
                content_type=record.get('content_type'),
                post_type=record.get('post_type'),
                source=record.get('source'),
                style_info=record.get('style_info'),
                read_7d=record.get('read_7d'),
                interact_7d=record.get('interact_7d'),
                visit_7d=record.get('visit_7d'),
                want_7d=record.get('want_7d'),
                read_14d=record.get('read_14d'),
                interact_14d=record.get('interact_14d'),
                visit_14d=record.get('visit_14d'),
                want_14d=record.get('want_14d')
            )
            db.add(post)

        dataset.status = DatasetStatus.COMPLETED
        dataset.row_count = len(records)
        await db.commit()

        return {
            "success": True,
            "row_count": len(records),
            "warnings": validation.get('warnings', [])
        }

    except Exception as e:
        dataset.status = DatasetStatus.FAILED
        dataset.error_message = str(e)
        await db.commit()
        return {"error": str(e)}


async def _parse_dataset(dataset_id: str):
    """解析数据集（使用共享会话，用于Celery）"""
    async with async_session_maker() as db:
        return await _parse_dataset_impl(db, dataset_id)


@celery_app.task(bind=True, name="parse_dataset")
def parse_dataset_task(self, dataset_id: str):
    """Celery任务: 解析数据集"""
    return run_async(_parse_dataset(dataset_id))
