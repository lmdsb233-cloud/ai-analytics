import httpx
import json
from typing import Dict, Any, Optional, List, AsyncGenerator
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
    
    async def analyze_post(self, input_data: Dict[str, Any], image_data: Optional[tuple[str, str]] = None) -> AIResponse:
        """分析单篇笔记，支持图片多模态分析
        
        Args:
            input_data: 输入数据
            image_data: 可选的图片数据元组 (base64_data, mime_type)
        """
        prompt = build_analysis_prompt(input_data)
        
        # 多模态分析（有图片时使用qwen3-vl-plus）
        use_image = image_data is not None
        
        if use_image:
            base64_data, mime_type = image_data
            user_content = [
                {"type": "text", "text": prompt},
                {
                    "type": "image_url",
                    "image_url": {"url": f"data:{mime_type};base64,{base64_data}"}
                }
            ]
            model_to_use = "qwen3-vl-plus"
        else:
            user_content = prompt
            model_to_use = self._model
        
        import asyncio
        max_retries = 10  # 最多重试10次
        
        async with httpx.AsyncClient(timeout=90.0) as client:
            for attempt in range(max_retries):
                try:
                    if attempt == 0:
                        print(f"[iflow] {'Multimodal' if use_image else 'Text'} analysis with {model_to_use}")
                    else:
                        print(f"[iflow] Retry {attempt}/{max_retries-1}...")
                    
                    response = await client.post(
                        f"{self.base_url}/chat/completions",
                        headers={
                            "Authorization": f"Bearer {self.api_key}",
                            "Content-Type": "application/json"
                        },
                        json={
                            "model": model_to_use,
                            "messages": [
                                {"role": "system", "content": SYSTEM_PROMPT},
                                {"role": "user", "content": user_content}
                            ],
                            "temperature": 0.7,
                            "max_tokens": 1500,
                            "stream": False
                        }
                    )
                    
                    # 429速率限制或500服务器错误：等待后重试
                    if response.status_code in (429, 500, 502, 503):
                        wait_time = 5 + attempt * 2  # 递增等待时间
                        print(f"[iflow] Error {response.status_code}, waiting {wait_time}s...")
                        await asyncio.sleep(wait_time)
                        continue
                    
                    response.raise_for_status()
                    data = response.json()
                    break  # 成功
                except httpx.HTTPStatusError as e:
                    if e.response.status_code in (429, 500, 502, 503):
                        wait_time = 5 + attempt * 2
                        print(f"[iflow] Error {e.response.status_code}, waiting {wait_time}s...")
                        await asyncio.sleep(wait_time)
                        continue
                    raise
                except Exception as e:
                    if attempt < max_retries - 1:
                        print(f"[iflow] Error: {e}, retrying...")
                        await asyncio.sleep(3)
                        continue
                    raise
            else:
                raise Exception(f"Failed after {max_retries} retries")
            
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

    async def analyze_with_image(self, image_base64: str) -> AIResponse:
        """使用图片进行分析（多模态 AI）"""
        system_prompt = """你是一个专业的数据分析专家。
请从截图中提取所有数据指标，并分析表现。

请严格按照以下JSON格式输出：
{
    "summary": "一句话总结",
    "strengths": ["优点1", "优点2"],
    "weaknesses": ["问题1", "问题2"],
    "suggestions": ["建议1", "建议2", "建议3"]
}
"""

        messages = [
            {
                "role": "system",
                "content": system_prompt
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": "请分析这个数据截图，提取所有指标并分析表现"
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/png;base64,{image_base64}"
                        }
                    }
                ]
            }
        ]

        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{self.base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": self._model,
                    "messages": messages,
                    "temperature": 0.7,
                    "max_tokens": 2000,
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

    async def chat_stream(
        self, 
        messages: List[Dict[str, str]],
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2000
    ) -> AsyncGenerator[str, None]:
        """流式聊天接口"""
        # 准备消息列表
        chat_messages = []
        if system_prompt:
            chat_messages.append({"role": "system", "content": system_prompt})
        chat_messages.extend(messages)
        
        print(f"[iFlow] chat_stream: model={self._model}, messages={len(chat_messages)}")
        
        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                async with client.stream(
                    "POST",
                    f"{self.base_url}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": self._model,
                        "messages": chat_messages,
                        "stream": True,
                        "temperature": temperature,
                        "max_tokens": max_tokens
                    }
                ) as response:
                    print(f"[iFlow] Response status: {response.status_code}")
                    if response.status_code != 200:
                        body = await response.aread()
                        print(f"[iFlow] Error response: {body.decode()}")
                        return
                    
                    # 使用 aiter_bytes 替代 aiter_lines，手动处理行分割
                    # 这样可以避免在某些异步上下文中 aiter_lines 不工作的问题
                    buffer = ""
                    line_count = 0
                    async for chunk in response.aiter_bytes():
                        buffer += chunk.decode('utf-8')
                        
                        # 按行分割处理
                        while '\n' in buffer:
                            line, buffer = buffer.split('\n', 1)
                            line = line.strip()
                            if not line:
                                continue
                            
                            line_count += 1
                            if line_count <= 3:
                                print(f"[iFlow] Line {line_count}: {line[:100]}...")
                            
                            # 支持 "data: {...}" 和 "data:{...}" 两种格式
                            if line.startswith("data: "):
                                data_str = line[6:]
                            elif line.startswith("data:"):
                                data_str = line[5:]
                            else:
                                continue
                                
                            if data_str.strip() == "[DONE]":
                                print(f"[iFlow] Stream done, total lines: {line_count}")
                                return
                            if not data_str.strip():
                                continue
                            try:
                                data = json.loads(data_str)
                                if data.get("choices") and len(data["choices"]) > 0:
                                    delta = data["choices"][0].get("delta", {})
                                    content = delta.get("content", "")
                                    if content:
                                        yield content
                            except json.JSONDecodeError as e:
                                print(f"[iFlow] JSON decode error: {e}, data: {data_str[:50]}")
                                continue
                    
                    # 处理剩余的 buffer
                    if buffer.strip():
                        line = buffer.strip()
                        if line.startswith("data: "):
                            data_str = line[6:]
                        elif line.startswith("data:"):
                            data_str = line[5:]
                        else:
                            return
                        if data_str.strip() and data_str.strip() != "[DONE]":
                            try:
                                data = json.loads(data_str)
                                if data.get("choices") and len(data["choices"]) > 0:
                                    delta = data["choices"][0].get("delta", {})
                                    content = delta.get("content", "")
                                    if content:
                                        yield content
                            except json.JSONDecodeError:
                                pass
                                
        except Exception as e:
            print(f"[iFlow] chat_stream error: {e}")
            import traceback
            traceback.print_exc()

    async def chat(
        self,
        messages: List[Dict[str, str]],
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2000
    ) -> str:
        """非流式聊天接口"""
        chat_messages = []
        if system_prompt:
            chat_messages.append({"role": "system", "content": system_prompt})
        chat_messages.extend(messages)
        
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                f"{self.base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": self._model,
                    "messages": chat_messages,
                    "temperature": temperature,
                    "max_tokens": max_tokens,
                    "stream": False
                }
            )
            response.raise_for_status()
            data = response.json()
            return data["choices"][0]["message"]["content"]
