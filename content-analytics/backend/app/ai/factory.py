from typing import Optional
from .base import BaseAIProvider
from .deepseek import DeepSeekProvider
from .openai import OpenAIProvider
from .iflow import IFlowProvider
from app.core.config import settings


class AIProviderFactory:
    """AI Provider工厂"""
    
    _providers = {
        'deepseek': DeepSeekProvider,
        'openai': OpenAIProvider,
        'iflow': IFlowProvider
    }
    
    @classmethod
    def register(cls, name: str, provider_class: type):
        """注册新的Provider"""
        cls._providers[name] = provider_class
    
    @classmethod
    def create(cls, provider_name: Optional[str] = None, api_key: Optional[str] = None) -> BaseAIProvider:
        """创建Provider实例
        
        Args:
            provider_name: AI服务商名称 (deepseek/openai)
            api_key: 用户提供的API密钥，如果不提供则使用系统配置
        """
        name = provider_name or settings.AI_PROVIDER
        
        if name not in cls._providers:
            raise ValueError(f"不支持的AI Provider: {name}")
        
        provider_class = cls._providers[name]
        
        if name == 'deepseek':
            key = api_key or settings.DEEPSEEK_API_KEY
            if not key:
                raise ValueError("未配置DEEPSEEK_API_KEY")
            return provider_class(
                api_key=key,
                base_url=settings.DEEPSEEK_BASE_URL
            )
        elif name == 'openai':
            key = api_key or settings.OPENAI_API_KEY
            if not key:
                raise ValueError("未配置OPENAI_API_KEY")
            return provider_class(
                api_key=key
            )
        elif name == 'iflow':
            key = api_key or getattr(settings, 'IFLOW_API_KEY', None)
            if not key:
                raise ValueError("未配置IFLOW_API_KEY")
            return provider_class(
                api_key=key,
                base_url=getattr(settings, 'IFLOW_BASE_URL', None)
            )
        else:
            raise ValueError(f"未配置 {name} Provider的初始化逻辑")


def get_ai_provider(provider_name: Optional[str] = None, api_key: Optional[str] = None) -> BaseAIProvider:
    """获取AI Provider实例
    
    Args:
        provider_name: AI服务商名称
        api_key: 用户提供的API密钥
    """
    return AIProviderFactory.create(provider_name, api_key)
