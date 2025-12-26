import httpx
from typing import Dict, Any, Optional
from .base import BaseAIProvider, AIResponse
from .prompts import SYSTEM_PROMPT, build_analysis_prompt


class OpenAIProvider(BaseAIProvider):
    """OpenAI Provider"""
    
    DEFAULT_BASE_URL = "https://api.openai.com/v1"
    DEFAULT_MODEL = "gpt-3.5-turbo"
    
    def __init__(
        self, 
        api_key: str, 
        base_url: Optional[str] = None,
        model: Optional[str] = None
    ):
        super().__init__(api_key, base_url or self.DEFAULT_BASE_URL)
        self._model = model or self.DEFAULT_MODEL
    
    @property
    def model_name(self) -> str:
        return self._model
    
    async def generate(self, prompt: str) -> str:
        """生成文本"""
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{self.base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": self._model,
                    "messages": [
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": prompt}
                    ],
                    "temperature": 0.7,
                    "max_tokens": 1000
                }
            )
            response.raise_for_status()
            data = response.json()
            
            return data["choices"][0]["message"]["content"]
    
    async def analyze_post(self, input_data: Dict[str, Any]) -> AIResponse:
        """分析单篇笔记"""
        prompt = build_analysis_prompt(input_data)
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{self.base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": self._model,
                    "messages": [
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": prompt}
                    ],
                    "temperature": 0.7,
                    "max_tokens": 1000
                }
            )
            response.raise_for_status()
            data = response.json()
            
            raw_response = data["choices"][0]["message"]["content"]
            parsed = self._parse_structured_response(raw_response)
            
            tokens_used = None
            if "usage" in data:
                tokens_used = {
                    "prompt_tokens": data["usage"].get("prompt_tokens", 0),
                    "completion_tokens": data["usage"].get("completion_tokens", 0),
                    "total_tokens": data["usage"].get("total_tokens", 0)
                }
            
            return AIResponse(
                summary=parsed.get("summary", ""),
                strengths=parsed.get("strengths", []),
                weaknesses=parsed.get("weaknesses", []),
                suggestions=parsed.get("suggestions", []),
                raw_response=raw_response,
                model_name=self._model,
                tokens_used=tokens_used
            )
