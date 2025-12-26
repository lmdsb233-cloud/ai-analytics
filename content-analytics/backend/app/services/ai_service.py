from typing import Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.factory import get_ai_provider
from app.ai.base import AIResponse
from app.models.analysis import AIOutput, AnalysisResult


class AIService:
    """AI服务"""
    
    def __init__(self, db: AsyncSession, provider_name: Optional[str] = None):
        self.db = db
        self.provider = get_ai_provider(provider_name)
    
    async def analyze_single(self, input_data: Dict[str, Any]) -> AIResponse:
        """分析单条数据"""
        return await self.provider.analyze_post(input_data)
    
    async def save_ai_output(
        self, 
        analysis_result_id, 
        ai_response: AIResponse
    ) -> AIOutput:
        """保存AI输出"""
        ai_output = AIOutput(
            analysis_result_id=analysis_result_id,
            summary=ai_response.summary,
            strengths=ai_response.strengths,
            weaknesses=ai_response.weaknesses,
            suggestions=ai_response.suggestions,
            raw_response=ai_response.raw_response,
            model_name=ai_response.model_name,
            tokens_used=ai_response.tokens_used
        )
        self.db.add(ai_output)
        await self.db.commit()
        await self.db.refresh(ai_output)
        return ai_output
