from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List, AsyncGenerator
from dataclasses import dataclass


@dataclass
class AIResponse:
    """AI响应数据类"""
    summary: str
    strengths: list
    weaknesses: list
    suggestions: list
    raw_response: str
    model_name: str
    tokens_used: Optional[Dict[str, int]] = None


class BaseAIProvider(ABC):
    """AI Provider基类"""
    
    def __init__(self, api_key: str, base_url: Optional[str] = None):
        self.api_key = api_key
        self.base_url = base_url
    
    @property
    @abstractmethod
    def model_name(self) -> str:
        """模型名称"""
        pass
    
    @abstractmethod
    async def generate(self, prompt: str) -> str:
        """生成文本"""
        pass
    
    @abstractmethod
    async def analyze_post(self, input_data: Dict[str, Any]) -> AIResponse:
        """分析单篇笔记"""
        pass
    
    async def chat_stream(
        self, 
        messages: List[Dict[str, str]],
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2000
    ) -> AsyncGenerator[str, None]:
        """流式聊天接口（默认实现，子类可覆盖）
        
        Args:
            messages: 消息列表，格式 [{"role": "user", "content": "..."}, ...]
            system_prompt: 系统提示词
            temperature: 温度参数
            max_tokens: 最大token数
        
        Yields:
            字符串片段（token）
        """
        # 默认实现：调用非流式接口并逐字符返回
        # 子类应该覆盖此方法以实现真正的流式响应
        full_response = await self.chat(messages, system_prompt, temperature, max_tokens)
        for char in full_response:
            yield char
    
    async def chat(
        self,
        messages: List[Dict[str, str]],
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2000
    ) -> str:
        """非流式聊天接口（默认实现，子类可覆盖）"""
        # 默认实现：使用generate方法
        # 子类应该覆盖此方法
        if messages:
            user_message = messages[-1].get("content", "")
            return await self.generate(user_message)
        return ""
    
    def _parse_structured_response(self, response: str) -> Dict[str, Any]:
        """解析结构化响应"""
        import json
        import re
        
        # 尝试直接解析JSON
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            pass
        
        # 尝试从markdown代码块中提取JSON
        json_match = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', response)
        if json_match:
            try:
                return json.loads(json_match.group(1))
            except json.JSONDecodeError:
                pass
        
        # 解析失败，返回默认结构
        return {
            'summary': response[:200] if len(response) > 200 else response,
            'strengths': [],
            'weaknesses': [],
            'suggestions': []
        }
