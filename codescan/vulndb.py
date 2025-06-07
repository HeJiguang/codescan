"""
漏洞库模块
~~~~~~~~~

管理和更新漏洞库
"""

import os
import json
import logging
import requests
import time
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from pathlib import Path
import json

logger = logging.getLogger(__name__)

class VulnerabilityDB:
    """漏洞库类，管理已知漏洞模式"""
    
    def __init__(self):
        """初始化漏洞库"""
        self.config_dir = os.path.expanduser('~/.codescan')
        self.vulndb_dir = os.path.join(self.config_dir, 'vulndb')
        self.vulndb_file = os.path.join(self.vulndb_dir, 'vulndb.json')
        self.last_update_file = os.path.join(self.vulndb_dir, 'last_update.json')
        self.patterns = {}
        
        self._ensure_dirs()
        self._load_patterns()
        
        # 检查是否需要自动更新
        from .config import config
        vulndb_config = config.config.get('vulndb', {})
        if vulndb_config.get('auto_update', False):
            if self._should_update():
                logger.info("自动更新漏洞库")
                self.update()
    
    def _ensure_dirs(self) -> None:
        """确保必要的目录存在"""
        os.makedirs(self.vulndb_dir, exist_ok=True)
    
    def _create_default_db(self) -> None:
        """创建默认的漏洞数据库"""
        self.patterns = {
            "common": [
                {
                    "id": "common-1",
                    "name": "硬编码密钥",
                    "pattern": "password|secret|token|api_key|apikey",
                    "description": "检测代码中的硬编码密钥",
                    "severity": "high",
                    "languages": ["*"]
                },
                {
                    "id": "common-2",
                    "name": "潜在的SQL注入",
                    "pattern": "execute|query|select.*from.*where",
                    "description": "检测潜在的SQL注入漏洞",
                    "severity": "critical",
                    "languages": ["*"]
                },
                {
                    "id": "common-3",
                    "name": "未处理的异常",
                    "pattern": "try|catch|except",
                    "description": "检测未适当处理的异常",
                    "severity": "medium",
                    "languages": ["*"]
                }
            ],
            "python": [
                {
                    "id": "python-1",
                    "name": "不安全的pickle使用",
                    "pattern": "pickle\\.loads|pickle\\.load",
                    "description": "检测不安全的pickle使用",
                    "severity": "high",
                    "languages": ["python"]
                },
                {
                    "id": "python-2",
                    "name": "os.system命令注入",
                    "pattern": "os\\.system|subprocess\\.call|eval\\(",
                    "description": "检测潜在的命令注入",
                    "severity": "critical",
                    "languages": ["python"]
                }
            ],
            "javascript": [
                {
                    "id": "javascript-1",
                    "name": "不安全的eval使用",
                    "pattern": "eval\\(|setTimeout\\(.*\\)|setInterval\\(.*\\)",
                    "description": "检测不安全的eval使用",
                    "severity": "high",
                    "languages": ["javascript"]
                },
                {
                    "id": "javascript-2",
                    "name": "XSS漏洞",
                    "pattern": "innerHTML|document\\.write|\\$\\(.*\\)\\.html\\(",
                    "description": "检测潜在的XSS漏洞",
                    "severity": "critical",
                    "languages": ["javascript"]
                }
            ],
            "java": [
                {
                    "id": "java-1",
                    "name": "不安全的反序列化",
                    "pattern": "ObjectInputStream|readObject",
                    "description": "检测不安全的反序列化操作",
                    "severity": "high",
                    "languages": ["java"]
                }
            ]
        }
        
        # 保存默认漏洞库
        self._save_patterns()
    
    def _load_patterns(self) -> None:
        """加载漏洞模式"""
        try:
            if os.path.exists(self.vulndb_file):
                with open(self.vulndb_file, 'r', encoding='utf-8') as f:
                    self.patterns = json.load(f)
                    logger.info(f"从文件加载了 {sum(len(patterns) for patterns in self.patterns.values())} 个漏洞模式")
            else:
                logger.info("漏洞库文件不存在，创建默认漏洞库")
                self._create_default_db()
        except Exception as e:
            logger.error(f"加载漏洞库失败: {str(e)}")
            self._create_default_db()
    
    def _save_patterns(self) -> None:
        """保存漏洞模式到文件"""
        try:
            with open(self.vulndb_file, 'w', encoding='utf-8') as f:
                json.dump(self.patterns, f, ensure_ascii=False, indent=2)
                
            # 更新最后更新时间
            with open(self.last_update_file, 'w', encoding='utf-8') as f:
                json.dump({
                    "last_update": datetime.now().timestamp()
                }, f)
                
            logger.info("漏洞库已保存")
        except Exception as e:
            logger.error(f"保存漏洞库失败: {str(e)}")
    
    def get_patterns_for_language(self, language: str) -> List[Dict[str, Any]]:
        """获取指定语言的漏洞模式"""
        # 添加通用模式
        patterns = self.patterns.get("common", [])[:]
        
        # 添加特定语言的模式
        language_patterns = self.patterns.get(language.lower(), [])
        patterns.extend(language_patterns)
        
        return patterns
    
    def _should_update(self) -> bool:
        """检查是否应该更新漏洞库"""
        # 获取配置的更新间隔
        from .config import config
        vulndb_config = config.config.get('vulndb', {})
        update_interval_days = vulndb_config.get('update_interval_days', 7)
        
        try:
            # 如果最后更新记录不存在，则应该更新
            if not os.path.exists(self.last_update_file):
                return True
                
            # 读取最后更新时间
            with open(self.last_update_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                last_update = data.get("last_update", 0)
                
            # 检查是否超过更新间隔
            now = datetime.now().timestamp()
            if now - last_update > update_interval_days * 24 * 3600:
                return True
                
        except Exception as e:
            logger.error(f"检查更新时间出错: {str(e)}")
            return True
            
        return False
    
    def update(self) -> bool:
        """更新漏洞库
        
        Returns:
            更新是否成功
        """
        from .config import config
        vulndb_config = config.config.get('vulndb', {})
        update_url = vulndb_config.get('update_url', '')
        
        if not update_url:
            logger.warning("漏洞库更新URL未配置")
            return False
        
        try:
            logger.info(f"从 {update_url} 更新漏洞库")
            
            # 发送请求获取更新
            response = requests.get(update_url, timeout=30)
            if response.status_code != 200:
                logger.error(f"更新漏洞库失败，HTTP状态码: {response.status_code}")
                return False
                
            # 解析响应数据
            try:
                new_patterns = response.json()
                
                # 简单验证数据结构
                if not isinstance(new_patterns, dict):
                    logger.error("更新的漏洞库数据格式无效")
                    return False
                
                # 更新漏洞模式
                self.patterns = new_patterns
                
                # 保存更新后的漏洞库
                self._save_patterns()
                
                logger.info("漏洞库更新成功")
                return True
                
            except json.JSONDecodeError:
                logger.error("解析漏洞库更新数据失败")
                return False
                
        except requests.exceptions.RequestException as e:
            logger.error(f"请求漏洞库更新失败: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"更新漏洞库时出错: {str(e)}")
            return False
    
    def import_semgrep_rules(self, directory: str) -> bool:
        """导入Semgrep规则
        
        Args:
            directory: Semgrep规则目录
            
        Returns:
            导入是否成功
        """
        try:
            from .semgrep_converter import convert_semgrep_rules_dir
            
            # 转换规则
            logger.info(f"从目录 {directory} 导入Semgrep规则")
            new_rules = convert_semgrep_rules_dir(directory)
            
            # 合并规则
            rules_count = self._merge_rules(new_rules)
            
            # 保存更新的规则
            self._save_patterns()
            
            logger.info(f"成功导入 {rules_count} 条Semgrep规则")
            return True
            
        except Exception as e:
            logger.error(f"导入Semgrep规则时出错: {str(e)}")
            return False
            
    def import_semgrep_from_url(self, url: str) -> bool:
        """从URL导入Semgrep规则
        
        Args:
            url: Semgrep规则URL
            
        Returns:
            导入是否成功
        """
        try:
            from .semgrep_converter import download_semgrep_rules
            
            # 下载并转换规则
            logger.info(f"从URL {url} 导入Semgrep规则")
            new_rules = download_semgrep_rules(url)
            
            # 合并规则
            rules_count = self._merge_rules(new_rules)
            
            # 保存更新的规则
            self._save_patterns()
            
            logger.info(f"成功从URL导入 {rules_count} 条规则")
            return True
            
        except Exception as e:
            logger.error(f"从URL导入Semgrep规则时出错: {str(e)}")
            return False
    
    def import_json_rules(self, rules_data: Dict[str, List[Dict[str, Any]]]) -> bool:
        """导入JSON格式的规则
        
        Args:
            rules_data: JSON规则数据
            
        Returns:
            导入是否成功
        """
        try:
            # 合并规则
            rules_count = self._merge_rules(rules_data)
            
            # 保存更新的规则
            self._save_patterns()
            
            logger.info(f"成功导入 {rules_count} 条JSON规则")
            return True
            
        except Exception as e:
            logger.error(f"导入JSON规则时出错: {str(e)}")
            return False
    
    def _merge_rules(self, new_rules: Dict[str, List[Dict[str, Any]]]) -> int:
        """合并新规则到现有规则库
        
        Args:
            new_rules: 新规则字典
            
        Returns:
            添加的规则数量
        """
        total_added = 0
        
        try:
            # 遍历新规则
            for lang, rules in new_rules.items():
                if lang not in self.patterns:
                    self.patterns[lang] = []
                    
                # 现有规则ID集合
                existing_ids = {rule.get('id', ''): i for i, rule in enumerate(self.patterns[lang])}
                
                # 处理每条规则
                for rule in rules:
                    rule_id = rule.get('id', '')
                    
                    # 如果ID为空，生成一个唯一ID
                    if not rule_id:
                        rule_id = f"{lang}-{len(self.patterns[lang]) + total_added + 1:04d}"
                        rule['id'] = rule_id
                    
                    # 检查规则是否已存在
                    if rule_id in existing_ids:
                        # 更新现有规则
                        index = existing_ids[rule_id]
                        # 如果新规则的模式非空且不同于旧规则，才进行更新
                        if rule.get('pattern') and rule.get('pattern') != self.patterns[lang][index].get('pattern'):
                            self.patterns[lang][index] = rule
                            # 我们不计算更新的规则
                    else:
                        # 添加新规则
                        self.patterns[lang].append(rule)
                        total_added += 1
                
                # 如果列表为空删除该语言条目
                if not self.patterns[lang]:
                    del self.patterns[lang]
            
            # 保存更新后的规则库
            if total_added > 0:
                self._save_patterns()
                
            return total_added
                
        except Exception as e:
            logger.error(f"合并规则时出错: {str(e)}")
            return 0
    
    def import_github_rules(self, repo_url: str, branch: str = "develop", languages: List[str] = None) -> Tuple[bool, int]:
        """从GitHub仓库导入Semgrep规则
        
        Args:
            repo_url: GitHub仓库URL
            branch: 分支名
            languages: 要导入的语言列表，如果为None则导入所有语言
            
        Returns:
            是否成功和导入的规则数量
        """
        try:
            # 导入转换器模块
            from .semgrep_converter import import_from_github
            
            # 导入规则
            logger.info(f"从GitHub {repo_url} 导入Semgrep规则")
            new_rules, rule_count = import_from_github(repo_url, branch, languages)
            
            if rule_count > 0:
                # 合并规则
                merged_count = self._merge_rules(new_rules)
                logger.info(f"成功导入 {merged_count} 条规则")
                return True, merged_count
            else:
                logger.warning("从GitHub导入规则失败：未找到有效规则")
                return False, 0
                
        except Exception as e:
            logger.error(f"从GitHub导入规则出错: {str(e)}")
            return False, 0 