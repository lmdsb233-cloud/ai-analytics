from sqlalchemy import select
from sqlalchemy.orm import selectinload
from app.tasks.celery_app import celery_app
from app.db.session import async_session_maker, create_thread_session_maker
from app.models.analysis import Analysis, AnalysisStatus, AnalysisResult, AIOutput
from app.models.post import Post
from app.models.user_settings import UserSettings
from app.ai.factory import get_ai_provider
from app.analysis.aggregator import AnalysisAggregator
import asyncio
import pandas as pd
import httpx
import base64


async def download_image_as_base64(url: str, timeout: float = 15.0) -> tuple[str, str] | None:
    """下载图片并转换为base64，返回 (base64_data, mime_type)
    
    注意：iflow API不支持webp格式，会自动转换为jpeg
    """
    if not url:
        return None
    try:
        from PIL import Image
        import io
        
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.get(url)
            response.raise_for_status()
            image_data = response.content
            
            # 检测图片格式
            content_type = response.headers.get('content-type', '').lower()
            is_webp = 'webp' in content_type or url.endswith('.webp') or '?x-oss-process' in url
            
            # webp格式需要转换为jpeg（iflow不支持webp多模态）
            if is_webp:
                print(f"[ai_tasks] Converting webp to jpeg...")
                img = Image.open(io.BytesIO(image_data))
                # 转换为RGB（去除alpha通道）
                if img.mode in ('RGBA', 'LA', 'P'):
                    img = img.convert('RGB')
                output = io.BytesIO()
                img.save(output, format='JPEG', quality=85)
                image_data = output.getvalue()
                mime_type = 'image/jpeg'
            elif 'png' in content_type or url.endswith('.png'):
                mime_type = 'image/png'
            elif 'gif' in content_type or url.endswith('.gif'):
                mime_type = 'image/gif'
            else:
                mime_type = 'image/jpeg'
            
            base64_data = base64.b64encode(image_data).decode('utf-8')
            return (base64_data, mime_type)
    except Exception as e:
        print(f"[ai_tasks] Failed to download/convert image {url[:50]}...: {e}")
        return None


def run_async(coro):
    """在同步环境中运行异步代码"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


async def _run_ai_analysis(analysis_id: str, use_thread_session: bool = False):
    """执行AI分析"""
    # 在后台线程中使用独立的数据库会话
    if use_thread_session:
        session_maker, thread_engine = create_thread_session_maker()
    else:
        session_maker = async_session_maker
        thread_engine = None
    
    try:
        async with session_maker() as db:
            # 获取分析任务和结果
            result = await db.execute(
                select(Analysis).where(Analysis.id == analysis_id)
            )
            analysis = result.scalar_one_or_none()
            
            if not analysis:
                return {"error": "分析任务不存在"}
            
            try:
                # 更新状态
                analysis.status = AnalysisStatus.AI_PROCESSING
                await db.commit()
                
                # 获取分析结果
                result = await db.execute(
                    select(AnalysisResult)
                    .options(selectinload(AnalysisResult.post))
                    .where(AnalysisResult.analysis_id == analysis_id)
                )
                analysis_results = result.scalars().all()
                
                if not analysis_results:
                    analysis.status = AnalysisStatus.FAILED
                    analysis.error_message = "没有分析结果"
                    await db.commit()
                    return {"error": "没有分析结果"}
                
                # 获取用户的AI配置
                settings_result = await db.execute(
                    select(UserSettings).where(UserSettings.user_id == analysis.user_id)
                )
                user_settings = settings_result.scalar_one_or_none()
                
                if not user_settings:
                    analysis.status = AnalysisStatus.FAILED
                    analysis.error_message = "请先在设置页面配置AI API密钥"
                    await db.commit()
                    return {"error": "未配置AI API密钥"}
                
                # 获取对应的API密钥
                provider_name = user_settings.ai_provider or "deepseek"
                api_key = None
                model = None
                if provider_name == "deepseek":
                    api_key = user_settings.deepseek_api_key
                elif provider_name == "openai":
                    api_key = user_settings.openai_api_key
                elif provider_name == "iflow":
                    api_key = user_settings.iflow_api_key
                    model = user_settings.iflow_model or "kimi-k2-0905"
                
                if not api_key:
                    analysis.status = AnalysisStatus.FAILED
                    analysis.error_message = f"请先在设置页面配置{provider_name}的API密钥"
                    await db.commit()
                    return {"error": f"未配置{provider_name} API密钥"}
                
                # 获取AI Provider（使用用户的配置）
                if provider_name == "iflow":
                    from app.ai.iflow import IFlowProvider
                    ai_provider = IFlowProvider(api_key=api_key, model=model)
                else:
                    ai_provider = get_ai_provider(provider_name, api_key)
                
                # 对每个分析结果调用AI
                total = len(analysis_results)
                processed = 0
                
                for ar in analysis_results:
                    # 检查是否已有AI输出
                    existing = await db.execute(
                        select(AIOutput).where(AIOutput.analysis_result_id == ar.id)
                    )
                    if existing.scalar_one_or_none():
                        processed += 1
                        continue
                    
                    # 构建AI输入
                    post = ar.post
                    input_data = {
                        'content_description': {
                            'content_type': post.content_type or '',
                            'post_type': post.post_type or '',
                            'style_info': post.style_info or '',
                            'content_title': post.content_title or '',
                            'content_text': post.content_text or '',
                            'cover_image': post.cover_image or '',
                            'image_urls': post.image_urls or []
                        },
                        'analysis_result': ar.result_data or {}
                    }
                    
                    # 下载封面图片用于多模态分析
                    image_data = None
                    if provider_name == "iflow" and post.cover_image:
                        print(f"[ai_tasks] Downloading cover image for post {post.data_id}...")
                        image_data = await download_image_as_base64(post.cover_image)
                    
                    # 调用AI（添加请求间隔避免限流）
                    try:
                        if provider_name == "iflow":
                            ai_response = await ai_provider.analyze_post(input_data, image_data=image_data)
                            # qwen3-vl-plus多模态模型限流严格，每次请求后等待3秒
                            if image_data:
                                await asyncio.sleep(3)
                        else:
                            ai_response = await ai_provider.analyze_post(input_data)
                        
                        # 保存AI输出
                        ai_output = AIOutput(
                            analysis_result_id=ar.id,
                            summary=ai_response.summary,
                            strengths=ai_response.strengths,
                            weaknesses=ai_response.weaknesses,
                            suggestions=ai_response.suggestions,
                            raw_response=ai_response.raw_response,
                            model_name=ai_response.model_name,
                            tokens_used=ai_response.tokens_used
                        )
                        db.add(ai_output)
                        
                    except Exception as e:
                        # 单个失败不影响整体
                        import traceback
                        print(f"AI分析失败 (result_id={ar.id}): {str(e)}")
                        print(f"详细错误: {traceback.format_exc()}")
                    
                    processed += 1
                    analysis.progress = f"{int(processed / total * 100)}%"
                    await db.commit()
                
                # 完成
                analysis.status = AnalysisStatus.COMPLETED
                analysis.progress = "100%"
                await db.commit()
                
                return {"success": True, "processed_count": processed}
                
            except Exception as e:
                analysis.status = AnalysisStatus.FAILED
                analysis.error_message = str(e)
                await db.commit()
                return {"error": str(e)}
    finally:
        # 清理后台线程创建的引擎
        if thread_engine:
            await thread_engine.dispose()


@celery_app.task(bind=True, name="run_ai_analysis")
def run_ai_analysis_task(self, analysis_id: str):
    """Celery任务: 执行AI分析"""
    return run_async(_run_ai_analysis(analysis_id, use_thread_session=True))
