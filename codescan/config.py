"""
配置管理模块
~~~~~~~~~

处理软件配置、大模型API密钥等
"""

import os
import yaml
import json
from pathlib import Path
import logging
from typing import Dict, Any, Optional

# 默认配置
DEFAULT_CONFIG = {
    'models': {
        'default': {
            'provider': 'deepseek',
            'model': 'deepseek-chat',
            'api_key': '',
            'base_url': 'https://api.deepseek.com',
            'max_tokens': 8192
        },
        'deepseek': {
            'provider': 'deepseek',
            'model': 'deepseek-chat',
            'api_key': '',
            'base_url': 'https://api.deepseek.com',
            'max_tokens': 8192
        },
        'openai': {
            'provider': 'openai',
            'model': 'gpt-3.5-turbo',
            'api_key': '',
            'max_tokens': 8192
        },
        'anthropic': {
            'provider': 'anthropic',
            'model': 'claude-3-opus-20240229',
            'api_key': '',
            'max_tokens': 8192
        }
    },
    'scan': {
        'excluded_dirs': ['node_modules', 'venv', '__pycache__', '.git'],
        'excluded_files': ['.jpg', '.png', '.gif', '.mp4', '.zip', '.tar.gz'],
        'max_file_size_mb': 10,
        'timeout_seconds': 60
    },
    'vulndb': {
        'update_url': 'https://example.com/vulndb/latest.json',
        'auto_update': True,
        'update_interval_days': 7
    },
    'output': {
        'format': 'html',
        'detail_level': 'medium',  # low, medium, high
        'default_output_dir': '~/codescan_reports'
    }
}

class Config:
    """配置管理类"""
    
    def __init__(self):
        """初始化配置管理器"""
        self.config_dir = os.path.expanduser('~/.codescan')
        self.config_file = os.path.join(self.config_dir, 'config.yaml')
        self.vulndb_dir = os.path.join(self.config_dir, 'vulndb')
        self.env_file = os.path.join(self.config_dir, 'env.json')
        self.config = {}
        
        self._init_dirs()
        self._load_config()
        self._load_env_vars()
    
    def _init_dirs(self) -> None:
        """初始化配置目录"""
        os.makedirs(self.config_dir, exist_ok=True)
        os.makedirs(self.vulndb_dir, exist_ok=True)
    
    def _load_config(self) -> None:
        """加载配置文件，如果不存在则创建默认配置"""
        try:
            if not os.path.exists(self.config_file):
                self._create_default_config()
            
            with open(self.config_file, 'r', encoding='utf-8') as f:
                self.config = yaml.safe_load(f)
                
            # 确保配置文件包含所有必要项
            for section, values in DEFAULT_CONFIG.items():
                if section not in self.config:
                    self.config[section] = {}
                for key, value in values.items():
                    if key not in self.config[section]:
                        self.config[section][key] = value
                        
            # 更新配置文件以包含缺少的项
            self.save_config()
                
        except Exception as e:
            logging.error(f"加载配置文件出错: {e}")
            self.config = DEFAULT_CONFIG.copy()
    
    def _load_env_vars(self) -> None:
        """加载保存的环境变量"""
        try:
            if os.path.exists(self.env_file):
                with open(self.env_file, 'r') as f:
                    env_vars = json.load(f)
                    for key, value in env_vars.items():
                        os.environ[key] = value
                        logging.info(f"已设置环境变量: {key}")
        except Exception as e:
            logging.error(f"加载环境变量出错: {e}")
    
    def _create_default_config(self) -> None:
        """创建默认配置文件"""
        with open(self.config_file, 'w', encoding='utf-8') as f:
            yaml.dump(DEFAULT_CONFIG, f, default_flow_style=False, allow_unicode=True)
    
    def save_config(self) -> None:
        """保存配置到文件"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                yaml.dump(self.config, f, default_flow_style=False, allow_unicode=True)
        except Exception as e:
            logging.error(f"保存配置文件出错: {e}")
    
    def get(self, section: str, key: str, default: Any = None) -> Any:
        """获取配置项
        
        Args:
            section: 配置节
            key: 配置键
            default: 默认值
            
        Returns:
            配置值
        """
        try:
            return self.config[section][key]
        except KeyError:
            return default
    
    def set(self, section: str, key: str, value: Any) -> None:
        """设置配置项
        
        Args:
            section: 配置节
            key: 配置键
            value: 配置值
        """
        if section not in self.config:
            self.config[section] = {}
        
        self.config[section][key] = value
        self.save_config()
    
    def get_model_config(self, model_name: str = 'default') -> Dict[str, Any]:
        """获取指定大模型的配置
        
        Args:
            model_name: 模型名称
            
        Returns:
            模型配置字典
        """
        models = self.config.get('models', {})
        return models.get(model_name, models.get('default', {}))
    
    def add_model_config(self, name: str, provider: str, model: str, 
                         api_key: str, max_tokens: int = 8192) -> None:
        """添加新的模型配置
        
        Args:
            name: 配置名称
            provider: 提供商 (openai, custom等)
            model: 模型名称
            api_key: API密钥
            max_tokens: 最大token数
        """
        if 'models' not in self.config:
            self.config['models'] = {}
            
        self.config['models'][name] = {
            'provider': provider,
            'model': model,
            'api_key': api_key,
            'max_tokens': max_tokens
        }
        
        self.save_config()

# 全局配置实例
config = Config() 