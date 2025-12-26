import pandas as pd
from typing import List, Dict, Any, Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.post import Post
from app.models.analysis import Analysis, AnalysisResult
from app.analysis.aggregator import AnalysisAggregator


class AnalysisService:
    """分析服务"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def get_posts_dataframe(self, dataset_id: UUID) -> pd.DataFrame:
        """获取数据集的所有笔记并转为DataFrame"""
        result = await self.db.execute(
            select(Post).where(Post.dataset_id == dataset_id)
        )
        posts = result.scalars().all()
        
        data = []
        for post in posts:
            data.append({
                'id': str(post.id),
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
        
        return pd.DataFrame(data)
    
    async def run_analysis(self, analysis: Analysis) -> List[AnalysisResult]:
        """执行分析"""
        # 获取数据
        df = await self.get_posts_dataframe(analysis.dataset_id)
        
        if df.empty:
            return []
        
        # 创建ID映射
        post_id_map = dict(zip(df['data_id'], df['id']))
        
        # 执行分析
        aggregator = AnalysisAggregator(df)
        aggregator.prepare()
        results = aggregator.analyze_all()
        
        # 保存结果
        analysis_results = []
        for result_data in results:
            data_id = result_data.get('data_id')
            post_id = post_id_map.get(data_id)
            
            if post_id:
                ar = AnalysisResult(
                    analysis_id=analysis.id,
                    post_id=post_id,
                    performance=result_data.get('performance'),
                    result_data=result_data
                )
                self.db.add(ar)
                analysis_results.append(ar)
        
        await self.db.commit()
        return analysis_results
    
    def get_ai_input(self, post: Post, result_data: Dict[str, Any]) -> Dict[str, Any]:
        """构建AI输入数据"""
        return {
            'content_description': {
                'content_type': post.content_type or '',
                'post_type': post.post_type or '',
                'style_info': post.style_info or ''
            },
            'analysis_result': {
                'performance': result_data.get('performance', ''),
                'problem_metrics': result_data.get('problem_metrics', []),
                'highlight_metrics': result_data.get('highlight_metrics', []),
                'compare_to_avg': result_data.get('compare_to_avg', {})
            }
        }
