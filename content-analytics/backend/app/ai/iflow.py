import httpx
from typing import Dict, Any, Optional
from .base import BaseAIProvider, AIResponse
from .prompts import SYSTEM_PROMPT, build_analysis_prompt


class IFlowProvider(BaseAIProvider):
    """iFlow AI Provider"""
    
    DEFAULT_BASE_URL = "https://apis.iflow.cn/v1"
    DEFAULT_MODEL = "kimi-k2-0905"
    
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
                    "max_tokens": 1000,
                    "stream": False
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
                    "max_tokens": 1000,
                    "stream": False
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
    
    @classmethod
    async def test_connection(cls, api_key: str, base_url: Optional[str] = None, model: Optional[str] = None) -> Dict[str, Any]:
        """测试API连接（真实请求）"""
        url = base_url or cls.DEFAULT_BASE_URL
        test_model = model or cls.DEFAULT_MODEL
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{url}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": test_model,
                        "messages": [{"role": "user", "content": "ping"}],
                        "max_tokens": 16,
                        "temperature": 0,
                        "stream": False
                    }
                )
                
                if response.status_code == 200:
                    data = response.json()
                    if "choices" in data and len(data["choices"]) > 0:
                        return {"success": True, "message": "iFlow API连接成功"}
                    else:
                        return {"success": False, "message": "响应格式异常"}
                elif response.status_code == 401:
                    return {"success": False, "message": "API密钥无效（401）"}
                elif response.status_code == 403:
                    return {"success": False, "message": "无权限访问（403）"}
                elif response.status_code == 429:
                    return {"success": False, "message": "请求过于频繁，请稍后重试（429）"}
                elif response.status_code >= 500:
                    return {"success": False, "message": f"iFlow服务器错误（{response.status_code}）"}
                else:
                    return {"success": False, "message": f"请求失败（{response.status_code}）"}
                    
        except httpx.TimeoutException:
            return {"success": False, "message": "连接超时，请检查网络"}
        except httpx.ConnectError:
            return {"success": False, "message": "无法连接到iFlow服务器"}
        except Exception as e:
            # 不暴露详细错误信息，避免泄露敏感数据
            return {"success": False, "message": "连接测试失败，请检查配置"}
