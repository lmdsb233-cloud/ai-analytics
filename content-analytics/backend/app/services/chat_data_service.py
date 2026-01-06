from typing import Dict, Any, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc, asc
from sqlalchemy.orm import selectinload
from uuid import UUID

from app.models.analysis import Analysis, AnalysisResult, AIOutput
from app.models.post import Post
from app.models.dataset import Dataset


class ChatDataService:
    """对话数据查询服务"""
    
    def __init__(self, db: AsyncSession, user_id: UUID):
        self.db = db
        self.user_id = user_id
    
    async def get_analysis_summary(self, analysis_id: UUID) -> Dict[str, Any]:
        """获取分析任务的摘要统计"""
        # 验证权限
        analysis_result = await self.db.execute(
            select(Analysis).where(
                Analysis.id == analysis_id,
                Analysis.user_id == self.user_id
            )
        )
        analysis = analysis_result.scalar_one_or_none()
        if not analysis:
            raise ValueError("分析任务不存在或无权限")
        
        # 统计表现分布
        performance_stats = await self.db.execute(
            select(
                AnalysisResult.performance,
                func.count(AnalysisResult.id).label("count")
            )
            .where(AnalysisResult.analysis_id == analysis_id)
            .group_by(AnalysisResult.performance)
        )
        
        performance_dist = {
            row.performance: row.count 
            for row in performance_stats
            if row.performance
        }
        
        # 获取总数
        total_result = await self.db.execute(
            select(func.count(AnalysisResult.id))
            .where(AnalysisResult.analysis_id == analysis_id)
        )
        total = total_result.scalar_one()
        
        # 获取数据集信息
        dataset_result = await self.db.execute(
            select(Dataset).where(Dataset.id == analysis.dataset_id)
        )
        dataset = dataset_result.scalar_one_or_none()
        
        return {
            "analysis_id": str(analysis_id),
            "analysis_name": analysis.name,
            "dataset_name": dataset.name if dataset else None,
            "total_posts": total,
            "performance_distribution": performance_dist,
            "created_at": analysis.created_at.isoformat() if analysis.created_at else None,
            "status": getattr(analysis.status, "value", analysis.status) if analysis.status else None
        }
    
    async def get_analysis_result_context(self, analysis_result_id: UUID) -> Dict[str, Any]:
        """获取分析结果的完整上下文（用于建议修改对话）
        
        包含：
        - AI输出的建议内容
        - 笔记的基本信息和指标
        - 分析结果数据
        """
        # 查询分析结果，包含关联数据
        result = await self.db.execute(
            select(AnalysisResult)
            .options(
                selectinload(AnalysisResult.ai_output),
                selectinload(AnalysisResult.post),
                selectinload(AnalysisResult.analysis).selectinload(Analysis.dataset)
            )
            .where(AnalysisResult.id == analysis_result_id)
        )
        analysis_result = result.scalar_one_or_none()
        
        if not analysis_result:
            raise ValueError("分析结果不存在")
        
        # 验证权限
        if analysis_result.analysis.user_id != self.user_id:
            raise ValueError("无权访问此分析结果")
        
        post = analysis_result.post
        ai_output = analysis_result.ai_output
        analysis = analysis_result.analysis
        dataset = analysis.dataset
        
        # 构建上下文数据
        context = {
            "analysis_result_id": str(analysis_result_id),
            "post_info": {
                "post_id": str(post.id),
                "data_id": post.data_id,
                "publish_link": post.publish_link,
                "publish_time": post.publish_time.isoformat() if post.publish_time else None,
                "content_type": post.content_type,
                "post_type": post.post_type,
                "style_info": post.style_info,
                "content_title": post.content_title,
                "content_text": post.content_text[:500] if post.content_text else None,  # 限制长度
                "metrics": {
                    "read_7d": post.read_7d,
                    "interact_7d": post.interact_7d,
                    "visit_7d": post.visit_7d,
                    "want_7d": post.want_7d,
                    "read_14d": post.read_14d,
                    "interact_14d": post.interact_14d,
                    "visit_14d": post.visit_14d,
                    "want_14d": post.want_14d,
                }
            },
            "analysis_result": {
                "performance": analysis_result.performance,
                "result_data": analysis_result.result_data,
            },
            "current_ai_output": {
                "summary": ai_output.summary if ai_output else None,
                "strengths": ai_output.strengths if ai_output else [],
                "weaknesses": ai_output.weaknesses if ai_output else [],
                "suggestions": ai_output.suggestions if ai_output else [],
                "model_name": ai_output.model_name if ai_output else None,
                "created_at": ai_output.created_at.isoformat() if ai_output and ai_output.created_at else None,
            },
            "analysis_info": {
                "analysis_id": str(analysis.id),
                "analysis_name": analysis.name,
                "dataset_name": dataset.name,
            }
        }
        
        return context


