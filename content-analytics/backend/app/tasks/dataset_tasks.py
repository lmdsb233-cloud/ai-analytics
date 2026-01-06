import pandas as pd
from sqlalchemy import select
from urllib.parse import urlparse
from app.tasks.celery_app import celery_app
from app.db.session import async_session_maker, create_thread_session_maker
from app.models.dataset import Dataset, DatasetStatus
from app.models.post import Post
from app.models.analysis import Analysis, AnalysisStatus, AnalysisResult
from app.analysis.processor import DataProcessor
from app.crawlers.poizon_fetcher import fetch_poizon_meta
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

        def _normalize_url(url: str) -> str:
            if not url:
                return ""
            url = str(url).strip()
            if not url:
                return ""
            if not url.startswith(("http://", "https://")):
                return f"https://{url}"
            return url

        def _is_poizon(url: str) -> bool:
            try:
                host = urlparse(url).netloc.lower()
            except Exception:
                return False
            return "poizon.com" in host or "dewu.com" in host

        def _should_fetch(source: str | None, url: str) -> bool:
            if not url or not _is_poizon(url):
                return False
            if not source:
                return True
            source_text = str(source).lower()
            if "得物" in source_text or "poizon" in source_text or "dewu" in source_text:
                return True
            return False

        total_records = len(records)
        for idx, record in enumerate(records):
            # 更新进度
            dataset.progress = f"{idx+1}/{total_records}"
            if idx % 5 == 0:  # 每5条提交一次进度
                await db.commit()
            
            print(f"[dataset] Processing record {idx+1}/{total_records}")
            content_title = record.get('content_title')
            content_text = None
            cover_image = None
            image_urls = None

            publish_link = record.get('publish_link')
            if publish_link:
                publish_link = _normalize_url(publish_link)
            if publish_link:
                try:
                    if _should_fetch(record.get('source'), publish_link):
                        print(f"[dataset] Fetching poizon link: {publish_link[:50]}...")
                        meta = await fetch_poizon_meta(publish_link, timeout=20, use_playwright_fallback=True)
                        # 得物链接：优先使用抓取的标题和描述（比Excel中的更准确）
                        if meta.get("title"):
                            content_title = meta.get("title")
                        if meta.get("description"):
                            content_text = meta.get("description")
                        cover_image = meta.get("image") or cover_image
                        image_urls = meta.get("image_urls") or image_urls
                except Exception as e:
                    print(f"[dataset] fetch link failed ({publish_link}): {e}")
            # 外链抓取失败时仅跳过本条，继续入库

            post = Post(
                dataset_id=dataset.id,
                data_id=str(record.get('data_id', '')),
                publish_time=record.get('publish_time'),
                publish_link=publish_link or record.get('publish_link'),
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
                want_14d=record.get('want_14d'),
                content_title=content_title,
                content_text=content_text,
                cover_image=cover_image,
                image_urls=image_urls
            )
            db.add(post)

        dataset.status = DatasetStatus.COMPLETED
        dataset.row_count = len(records)
        await db.commit()
        
        # 自动创建分析任务
        print(f"[dataset] Auto-creating analysis for dataset {dataset.id}...")
        analysis = Analysis(
            dataset_id=dataset.id,
            user_id=dataset.user_id,
            name=f"{dataset.name}的分析",
            status=AnalysisStatus.ANALYZING
        )
        db.add(analysis)
        await db.commit()
        await db.refresh(analysis)
        
        # 获取所有posts并创建分析结果
        posts_result = await db.execute(
            select(Post).where(Post.dataset_id == dataset.id)
        )
        posts = posts_result.scalars().all()
        
        # 构建DataFrame用于初始化聚合器
        from app.analysis.aggregator import AnalysisAggregator
        
        posts_data = []
        for post in posts:
            posts_data.append({
                'data_id': post.data_id,
                'publish_time': post.publish_time,
                'content_type': post.content_type,
                'post_type': post.post_type,
                'read_7d': post.read_7d or 0,
                'interact_7d': post.interact_7d or 0,
                'visit_7d': post.visit_7d or 0,
                'want_7d': post.want_7d or 0,
                'read_14d': post.read_14d or 0,
                'interact_14d': post.interact_14d or 0,
                'visit_14d': post.visit_14d or 0,
                'want_14d': post.want_14d or 0
            })
        
        df = pd.DataFrame(posts_data)
        aggregator = AnalysisAggregator(df).prepare()
        
        total_posts = len(posts)
        for idx, post in enumerate(posts):
            # 获取对应的DataFrame行
            row = df[df['data_id'] == post.data_id].iloc[0] if not df[df['data_id'] == post.data_id].empty else None
            if row is None:
                continue
            result_data = aggregator.analyze_single_post(row)
            
            analysis_result = AnalysisResult(
                analysis_id=analysis.id,
                post_id=post.id,
                performance=result_data.get('performance'),
                result_data=result_data
            )
            db.add(analysis_result)
            
            if idx % 10 == 0:
                analysis.progress = f"{int((idx+1)/total_posts*100)}%"
                await db.commit()
        
        analysis.status = AnalysisStatus.COMPLETED
        analysis.progress = "100%"
        await db.commit()
        print(f"[dataset] Analysis {analysis.id} created and completed")

        return {
            "success": True,
            "row_count": len(records),
            "analysis_id": str(analysis.id),
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

