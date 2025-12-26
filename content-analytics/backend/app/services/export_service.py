import os
import uuid
from datetime import datetime
from typing import List, Dict, Any
import pandas as pd
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.models.analysis import Analysis, AnalysisResult, AIOutput
from app.models.export import Export, ExportStatus, ExportFormat
from app.core.config import settings


class ExportService:
    """导出服务"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def create_export(
        self, 
        analysis_id: uuid.UUID, 
        user_id: uuid.UUID,
        format: ExportFormat = ExportFormat.EXCEL
    ) -> Export:
        """创建导出任务"""
        export = Export(
            analysis_id=analysis_id,
            user_id=user_id,
            format=format,
            status=ExportStatus.PENDING
        )
        self.db.add(export)
        await self.db.commit()
        await self.db.refresh(export)
        return export
    
    async def generate_excel_report(self, export_id: uuid.UUID) -> str:
        """生成Excel报告"""
        # 获取导出记录
        result = await self.db.execute(
            select(Export).where(Export.id == export_id)
        )
        export = result.scalar_one_or_none()
        
        if not export:
            raise ValueError("导出记录不存在")
        
        try:
            export.status = ExportStatus.PROCESSING
            await self.db.commit()
            
            # 获取分析结果
            result = await self.db.execute(
                select(AnalysisResult)
                .options(
                    selectinload(AnalysisResult.post),
                    selectinload(AnalysisResult.ai_output)
                )
                .where(AnalysisResult.analysis_id == export.analysis_id)
            )
            analysis_results = result.scalars().all()
            
            # 构建数据
            data = []
            for ar in analysis_results:
                row = {
                    '笔记ID': ar.post.data_id if ar.post else '',
                    '内容形式': ar.post.content_type if ar.post else '',
                    '发文类型': ar.post.post_type if ar.post else '',
                    '7天阅读': ar.post.read_7d if ar.post else None,
                    '7天互动': ar.post.interact_7d if ar.post else None,
                    '整体表现': ar.performance,
                    '问题指标': '、'.join(ar.result_data.get('problem_metrics', [])) if ar.result_data else '',
                    '亮点指标': '、'.join(ar.result_data.get('highlight_metrics', [])) if ar.result_data else '',
                }
                
                if ar.ai_output:
                    row['AI总结'] = ar.ai_output.summary or ''
                    row['优点'] = '；'.join(ar.ai_output.strengths or [])
                    row['问题'] = '；'.join(ar.ai_output.weaknesses or [])
                    row['优化建议'] = '；'.join(ar.ai_output.suggestions or [])
                
                data.append(row)
            
            # 生成Excel
            df = pd.DataFrame(data)
            
            export_dir = os.path.join(settings.UPLOAD_DIR, 'exports')
            os.makedirs(export_dir, exist_ok=True)
            
            filename = f"analysis_report_{export.id}_{datetime.now().strftime('%Y%m%d%H%M%S')}.xlsx"
            file_path = os.path.join(export_dir, filename)
            
            df.to_excel(file_path, index=False, engine='openpyxl')
            
            # 更新状态
            export.file_path = file_path
            export.status = ExportStatus.COMPLETED
            export.completed_at = datetime.utcnow()
            await self.db.commit()
            
            return file_path
            
        except Exception as e:
            export.status = ExportStatus.FAILED
            export.error_message = str(e)
            await self.db.commit()
            raise
