import pandas as pd
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from app.tasks.celery_app import celery_app
from app.db.session import async_session_maker, create_thread_session_maker
from app.models.dataset import Dataset
from app.models.post import Post
from app.models.analysis import Analysis, AnalysisStatus, AnalysisResult
from app.analysis.aggregator import AnalysisAggregator
import asyncio


def run_async(coro):
    """在同步环境中运行异步代码"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


async def _run_analysis(analysis_id: str, use_thread_session: bool = False):
    """执行分析"""
    if use_thread_session:
        session_maker, thread_engine = create_thread_session_maker()
    else:
        session_maker = async_session_maker
        thread_engine = None

    try:
        async with session_maker() as db:
            # 获取分析任务
            result = await db.execute(
                select(Analysis)
                .options(selectinload(Analysis.dataset))
                .where(Analysis.id == analysis_id)
            )
            analysis = result.scalar_one_or_none()

            if not analysis:
                return {"error": "分析任务不存在"}

            try:
                # 更新状态
                analysis.status = AnalysisStatus.ANALYZING
                await db.commit()

                # 获取所有笔记
                result = await db.execute(
                    select(Post).where(Post.dataset_id == analysis.dataset_id)
                )
                posts = result.scalars().all()

                if not posts:
                    analysis.status = AnalysisStatus.FAILED
                    analysis.error_message = "数据集中没有笔记数据"
                    await db.commit()
                    return {"error": "数据集中没有笔记数据"}

                # 构建DataFrame
                data = []
                posts_by_index = []
                for post in posts:
                    posts_by_index.append(post)
                    data.append({
                        'data_id': post.data_id,
                        'content_type': post.content_type,
                        'post_type': post.post_type,
                        'style_info': post.style_info,
                        'read_7d': post.read_7d,
                        'interact_7d': post.interact_7d,
                        'visit_7d': post.visit_7d,
                        'want_7d': post.want_7d,
                        'read_14d': post.read_14d,
                        'interact_14d': post.interact_14d,
                        'visit_14d': post.visit_14d,
                        'want_14d': post.want_14d
                    })

                df = pd.DataFrame(data)

                # 执行分析
                aggregator = AnalysisAggregator(df)
                aggregator.prepare()
                analysis_results = aggregator.analyze_all()

                # 保存分析结果
                total = len(analysis_results)
                for idx, result_data in enumerate(analysis_results):
                    post = None
                    row_index = result_data.get('row_index')
                    if isinstance(row_index, int) and 0 <= row_index < len(posts_by_index):
                        post = posts_by_index[row_index]
                    if not post:
                        data_id = result_data.get('data_id')
                        if data_id:
                            post = next((p for p in posts_by_index if p.data_id == data_id), None)

                    if post:
                        analysis_result = AnalysisResult(
                            analysis_id=analysis.id,
                            post_id=post.id,
                            performance=result_data.get('performance'),
                            result_data=result_data
                        )
                        db.add(analysis_result)

                    # 更新进度
                    progress = int((idx + 1) / total * 100)
                    analysis.progress = f"{progress}%"
                    await db.commit()

                # 完成
                analysis.status = AnalysisStatus.COMPLETED
                analysis.progress = "100%"
                from datetime import datetime
                analysis.completed_at = datetime.utcnow()
                await db.commit()

                return {"success": True, "analyzed_count": total}

            except Exception as e:
                analysis.status = AnalysisStatus.FAILED
                analysis.error_message = str(e)
                await db.commit()
                return {"error": str(e)}
    finally:
        if thread_engine:
            await thread_engine.dispose()


@celery_app.task(bind=True, name="run_analysis")
def run_analysis_task(self, analysis_id: str):
    """Celery任务: 执行数据分析"""
    return run_async(_run_analysis(analysis_id, use_thread_session=True))
