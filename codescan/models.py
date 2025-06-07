"""
大语言模型处理模块
~~~~~~~~~

管理和调用不同的大语言模型API
"""

import os
import logging
import json
from typing import Dict, Any, Optional, List
from abc import ABC, abstractmethod

import openai
import requests

try:
    import anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False

from .config import config

logger = logging.getLogger(__name__)

class ModelHandler(ABC):
    """大语言模型处理基类"""
    
    @abstractmethod
    def analyze_code(self, prompt: str) -> str:
        """分析代码
        
        Args:
            prompt: 提示词
            
        Returns:
            分析结果
        """
        pass
    
    @abstractmethod
    def summarize_project(self, prompt: str) -> str:
        """总结项目
        
        Args:
            prompt: 提示词
            
        Returns:
            总结结果
        """
        pass

class OpenAIHandler(ModelHandler):
    """OpenAI模型处理器"""
    
    def __init__(self, api_key: str, model: str = "gpt-3.5-turbo", max_tokens: int = 8192, base_url: str = None, extra_body: Dict[str, Any] = None):
        """初始化OpenAI模型处理器
        
        Args:
            api_key: OpenAI API密钥
            model: 模型名称
            max_tokens: 最大token数
            base_url: API基础URL，用于支持DeepSeek、Qwen等兼容OpenAI接口的服务
            extra_body: 额外请求参数，用于支持Qwen等模型的特殊参数
        """
        self.api_key = api_key
        self.model = model
        self.max_tokens = max_tokens
        self.base_url = base_url
        self.extra_body = extra_body or {}
        
        # 创建客户端时传入base_url参数（如果有）
        client_args = {"api_key": api_key}
        if base_url:
            client_args["base_url"] = base_url
            
        self.client = openai.OpenAI(**client_args)
    
    def analyze_code(self, prompt: str) -> str:
        """使用OpenAI模型分析代码
        
        Args:
            prompt: 提示词
            
        Returns:
            分析结果
        """
        try:
            # 基本参数
            params = {
                "model": self.model,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.1,
                "max_tokens": self.max_tokens
            }
            
            # 添加额外参数
            if self.extra_body:
                # 支持OpenAI Chat API的extra_body参数
                if "extra_body" not in params:
                    params["extra_body"] = {}
                params["extra_body"].update(self.extra_body)
            
            response = self.client.chat.completions.create(**params)
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"OpenAI API调用出错: {str(e)}")
            raise
    
    def summarize_project(self, prompt: str) -> str:
        """使用OpenAI模型总结项目
        
        Args:
            prompt: 提示词
            
        Returns:
            总结结果
        """
        return self.analyze_code(prompt)

class AnthropicHandler(ModelHandler):
    """Anthropic Claude模型处理器"""
    
    def __init__(self, api_key: str, model: str = "claude-3-opus-20240229", max_tokens: int = 8192):
        """初始化Anthropic模型处理器
        
        Args:
            api_key: Anthropic API密钥
            model: 模型名称
            max_tokens: 最大token数
        """
        if not ANTHROPIC_AVAILABLE:
            raise ImportError("未安装anthropic库，请使用 pip install anthropic 进行安装")
            
        self.api_key = api_key
        self.model = model
        self.max_tokens = max_tokens
        self.client = anthropic.Anthropic(api_key=api_key)
    
    def analyze_code(self, prompt: str) -> str:
        """使用Anthropic Claude模型分析代码
        
        Args:
            prompt: 提示词
            
        Returns:
            分析结果
        """
        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                temperature=0.1,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            return response.content[0].text
        except Exception as e:
            logger.error(f"Anthropic API调用出错: {str(e)}")
            raise
    
    def summarize_project(self, prompt: str) -> str:
        """使用Anthropic Claude模型总结项目
        
        Args:
            prompt: 提示词
            
        Returns:
            总结结果
        """
        return self.analyze_code(prompt)

class CustomAPIHandler(ModelHandler):
    """自定义API模型处理器"""
    
    def __init__(self, api_url: str, api_key: str = None, headers: Dict[str, str] = None, 
                 params: Dict[str, Any] = None):
        """初始化自定义API模型处理器
        
        Args:
            api_url: API URL
            api_key: API密钥(可选)
            headers: 请求头(可选)
            params: 请求参数(可选)
        """
        self.api_url = api_url
        self.api_key = api_key
        self.headers = headers or {}
        self.params = params or {}
        
        if api_key and "Authorization" not in self.headers:
            self.headers["Authorization"] = f"Bearer {api_key}"
    
    def analyze_code(self, prompt: str) -> str:
        """使用自定义API分析代码
        
        Args:
            prompt: 提示词
            
        Returns:
            分析结果
        """
        try:
            data = {
                "prompt": prompt,
                **self.params
            }
            
            response = requests.post(
                self.api_url, 
                headers=self.headers,
                json=data
            )
            
            if response.status_code != 200:
                logger.error(f"自定义API调用失败: HTTP {response.status_code}")
                raise ValueError(f"API调用失败: HTTP {response.status_code}")
            
            result = response.json()
            
            if "response" in result:
                return result["response"]
            elif "output" in result:
                return result["output"]
            elif "result" in result:
                return result["result"]
            else:
                return str(result)
                
        except Exception as e:
            logger.error(f"自定义API调用出错: {str(e)}")
            raise
    
    def summarize_project(self, prompt: str) -> str:
        """使用自定义API总结项目
        
        Args:
            prompt: 提示词
            
        Returns:
            总结结果
        """
        return self.analyze_code(prompt)

def get_model_handler(model_name: str = "default") -> ModelHandler:
    """获取模型处理器
    
    Args:
        model_name: 模型配置名称
        
    Returns:
        模型处理器实例
    """
    model_config = config.get_model_config(model_name)
    provider = model_config.get("provider", "")
    
    if not provider:
        raise ValueError(f"无效的模型配置: {model_name}")
        
    api_key = model_config.get("api_key", "")
    model = model_config.get("model", "")
    max_tokens = int(model_config.get("max_tokens", 8192))
    
    if provider == "openai":
        base_url = model_config.get("base_url", None)
        extra_body = model_config.get("extra_body", None)
        return OpenAIHandler(api_key, model, max_tokens, base_url, extra_body)
    elif provider == "deepseek":
        # DeepSeek使用与OpenAI兼容的API接口
        base_url = model_config.get("base_url", "https://api.deepseek.com")
        extra_body = model_config.get("extra_body", None)
        return OpenAIHandler(api_key, model, max_tokens, base_url, extra_body)
    elif provider == "anthropic":
        return AnthropicHandler(api_key, model, max_tokens)
    elif provider == "custom":
        api_url = model_config.get("api_url", "")
        headers = model_config.get("headers", {})
        params = model_config.get("params", {})
        return CustomAPIHandler(api_url, api_key, headers, params)
    else:
        raise ValueError(f"不支持的模型提供商: {provider}")
        
def list_available_models() -> List[str]:
    """列出所有可用的模型配置
    
    Returns:
        模型配置名称列表
    """
    models = config.config.get("models", {})
    # 过滤出支持的模型（只保留provider为"openai"、"anthropic"、"deepseek"或"custom"的模型）
    supported_models = []
    for name, model_config in models.items():
        provider = model_config.get("provider", "")
        if provider in ["openai", "anthropic", "deepseek", "custom"]:
            supported_models.append(name)
    return supported_models 