"""
代码扫描模块
~~~~~~~~~

处理文件和目录扫描，使用大语言模型进行漏洞分析
"""

import os
import re
import logging
import time
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from concurrent.futures import ThreadPoolExecutor, as_completed
import json

from .ai.schemas import AIFileIssue
from .ai.service import AIAnalysisService
from .config import config
from .utils import get_file_language, count_lines, is_binary_file, extract_file_info
from .vulndb import VulnerabilityDB

# 配置日志
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class VulnerabilityIssue:
    """漏洞问题类"""
    severity: str  # 严重程度: 'critical', 'high', 'medium', 'low', 'info'
    file_path: str  # 文件路径
    title: str = ""  # 问题标题
    line_number: Optional[int] = None  # 行号（如果可以确定）
    code_snippet: Optional[str] = None  # 代码片段
    description: str = ""  # 问题描述
    recommendation: str = ""  # 修复建议
    cwe_id: Optional[str] = None  # CWE ID
    owasp_category: Optional[str] = None  # OWASP 类别
    vulnerability_type: Optional[str] = None  # 漏洞类型
    confidence: str = "medium"  # 置信度: 'high', 'medium', 'low'

    @property
    def location(self) -> str:
        """Return a human-readable issue location."""

        if self.line_number:
            return f"{self.file_path}:{self.line_number}"
        return self.file_path

@dataclass
class ScanResult:
    """扫描结果类"""
    scan_id: str  # 扫描ID
    scan_path: str  # 扫描路径
    scan_type: str  # 扫描类型: 'file', 'directory', 'github', 'git-merge'
    timestamp: float  # 扫描时间戳
    scan_model: str = ""  # 使用的模型
    issues: List[VulnerabilityIssue] = field(default_factory=list)  # 发现的问题
    stats: Dict[str, Any] = field(default_factory=dict)  # 统计信息
    project_info: Dict[str, Any] = field(default_factory=dict)  # 项目信息
    
    @property
    def total_issues(self) -> int:
        """返回问题总数"""
        return len(self.issues)
    
    @property
    def issues_by_severity(self) -> Dict[str, int]:
        """按严重程度统计问题数量"""
        result = {"critical": 0, "high": 0, "medium": 0, "low": 0, "info": 0}
        for issue in self.issues:
            result[issue.severity] = result.get(issue.severity, 0) + 1
        return result
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "scan_id": self.scan_id,
            "scan_path": self.scan_path,
            "scan_type": self.scan_type,
            "timestamp": self.timestamp,
            "scan_model": self.scan_model,
            "issues": [vars(issue) for issue in self.issues],
            "stats": self.stats,
            "project_info": self.project_info
        }
    
    def to_json(self) -> str:
        """转换为JSON字符串"""
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ScanResult':
        """从字典创建实例"""
        issues = [VulnerabilityIssue(**issue_data) for issue_data in data.pop("issues", [])]
        result = cls(**{k: v for k, v in data.items() if k != "issues"})
        result.issues = issues
        return result
    
    @classmethod
    def from_json(cls, json_str: str) -> 'ScanResult':
        """从JSON字符串创建实例"""
        data = json.loads(json_str)
        return cls.from_dict(data)

class CodeScanner:
    """代码扫描器类"""
    
    def __init__(self, model_name: str = 'default', ai_service=None):
        """初始化扫描器
        
        Args:
            model_name: 使用的大模型名称
        """
        self.model_name = model_name
        self.ai_service = ai_service
        
        # 检查API配置是否存在
        model_config = config.get_model_config(model_name)
        if not model_config.get('api_key'):
            # 如果没有API密钥，尝试使用默认配置
            logger.warning(f"未找到模型'{model_name}'的API密钥配置，将使用默认配置")
            self.model_name = 'default'
            model_config = config.get_model_config(self.model_name)
            
        if self.ai_service is None:
            try:
                self.ai_service = AIAnalysisService(model_config)
                logger.info(f"使用模型: {self.model_name}")
            except Exception as e:
                logger.error(f"初始化AI分析服务时出错: {str(e)}")
                if self.model_name != 'default':
                    logger.info("尝试使用默认模型")
                    self.model_name = 'default'
                    self.ai_service = AIAnalysisService(config.get_model_config('default'))
        
        self.vulndb = VulnerabilityDB()
        
        # 获取配置
        scan_config = config.config.get('scan', {})
        self.excluded_dirs = set(scan_config.get('excluded_dirs', []))
        self.excluded_files = set(scan_config.get('excluded_files', []))
        self.max_file_size_mb = scan_config.get('max_file_size_mb', 10)
        self.timeout_seconds = scan_config.get('timeout_seconds', 60)

    @staticmethod
    def _coerce_to_dict(value: Any) -> Dict[str, Any]:
        """Convert Pydantic models or plain objects to dictionaries."""

        if isinstance(value, dict):
            return value
        if hasattr(value, "model_dump"):
            return value.model_dump()
        return {}

    @staticmethod
    def _map_ai_issue(file_path: str, issue: AIFileIssue) -> VulnerabilityIssue:
        """Convert an AI schema issue into the scanner domain model."""

        return VulnerabilityIssue(
            title=issue.title,
            severity=issue.severity,
            file_path=file_path,
            line_number=issue.line_number,
            code_snippet=issue.code_snippet,
            description=issue.description,
            recommendation=issue.recommendation,
            cwe_id=issue.cwe_id,
            confidence=issue.confidence,
        )

    def _build_rule_issues(
        self, file_path: str, content: str, relevant_patterns: List[Dict[str, Any]]
    ) -> List[AIFileIssue]:
        """Create normalized issues from rule matches."""

        issues: List[AIFileIssue] = []
        lines = content.split("\n")
        
        # Determine if we should be extra careful about prose false positives
        is_prose_file = file_path.lower().endswith(('.md', '.txt', '.rst', '.adoc'))

        for pattern in relevant_patterns:
            pattern_text = pattern.get("pattern", "")
            if not pattern_text:
                continue
                
            # If it's a secret-related pattern and we're in a prose file,
            # skip rule-based scanning to avoid false positives. 
            # AI analysis will still have a chance to look at it if the 
            # file is passed to it, but rules are too blunt.
            is_secret_pattern = any(word in pattern_text.lower() for word in ['password', 'secret', 'token', 'api_key', 'apikey', '密钥'])
            if is_prose_file and is_secret_pattern:
                continue

            try:
                pattern_re = re.compile(pattern_text, re.IGNORECASE)
            except re.error:
                logger.warning(f"跳过无效规则模式: {pattern_text}")
                continue

            if not pattern_re.search(content):
                continue

            line_number = None
            code_snippet = None
            for index, line in enumerate(lines):
                if pattern_re.search(line):
                    line_number = index + 1
                    start = max(0, index - 2)
                    end = min(len(lines), index + 3)
                    code_snippet = "\n".join(lines[start:end])
                    break

            issues.append(
                AIFileIssue(
                    title=pattern.get("name", "规则命中"),
                    severity=pattern.get("severity", "medium"),
                    description=pattern.get("description", "发现潜在漏洞"),
                    recommendation=pattern.get("recommendation", "请检查此处代码"),
                    confidence="medium",
                    line_number=line_number,
                    code_snippet=code_snippet,
                    cwe_id=pattern.get("cwe_id"),
                )
            )

        return issues
        
    def _should_exclude_path(self, path: str) -> bool:
        """检查路径是否应被排除
        
        Args:
            path: 文件或目录路径
            
        Returns:
            是否应被排除
        """
        path_parts = Path(path).parts
        
        # 检查排除的目录
        for excluded_dir in self.excluded_dirs:
            if excluded_dir in path_parts:
                return True
                
        # 检查排除的文件扩展名
        for excluded_ext in self.excluded_files:
            if path.endswith(excluded_ext):
                return True
                
        # 检查文件大小
        if os.path.isfile(path):
            size_mb = os.path.getsize(path) / (1024 * 1024)
            if size_mb > self.max_file_size_mb:
                logger.info(f"跳过大文件: {path} ({size_mb:.2f}MB > {self.max_file_size_mb}MB)")
                return True
                
        # 检查是否为二进制文件
        if os.path.isfile(path) and is_binary_file(path):
            logger.info(f"跳过二进制文件: {path}")
            return True
                
        return False
    
    def _collect_files(self, path: str) -> List[str]:
        """收集指定路径下的所有需要扫描的文件
        
        Args:
            path: 目录路径
            
        Returns:
            文件路径列表
        """
        files_to_scan = []
        
        for root, dirs, files in os.walk(path):
            # 过滤排除的目录
            dirs[:] = [d for d in dirs if d not in self.excluded_dirs]
            
            for file in files:
                file_path = os.path.join(root, file)
                if not self._should_exclude_path(file_path):
                    files_to_scan.append(file_path)
                    
        return files_to_scan
    
    def _analyze_file_content(self, file_path: str, content: str) -> List[VulnerabilityIssue]:
        """使用大语言模型分析文件内容查找漏洞
        
        Args:
            file_path: 文件路径
            content: 文件内容
            
        Returns:
            发现的漏洞列表
        """
        # 确定文件语言
        language = get_file_language(file_path)
        
        # 获取相关漏洞模式
        relevant_patterns = self.vulndb.get_patterns_for_language(language)
        rule_issues = self._build_rule_issues(file_path, content, relevant_patterns)
        
        try:
            logger.info(f"使用模型 {self.model_name} 分析文件: {file_path}")
            analysis_result = self.ai_service.analyze_file(
                file_path=file_path,
                language=language,
                content=content,
                rule_issues=rule_issues,
            )
            issues = analysis_result.get("issues", [])
            return [self._map_ai_issue(file_path, issue) for issue in issues]
                
        except Exception as e:
            logger.error(f"分析文件时出错 {file_path}: {str(e)}")
            fallback_issues = [self._map_ai_issue(file_path, issue) for issue in rule_issues]
            fallback_issues.append(
                VulnerabilityIssue(
                    title="AI分析失败",
                    severity="info",
                    file_path=file_path,
                    description=f"AI分析错误: {str(e)}",
                    recommendation="请检查模型配置、网络连接和AI服务依赖。",
                    confidence="high",
                )
            )
            return fallback_issues
    
    def scan_file(self, file_path: str) -> ScanResult:
        """扫描单个文件
        
        Args:
            file_path: 文件路径
            
        Returns:
            扫描结果
        """
        if not os.path.isfile(file_path):
            raise ValueError(f"文件不存在: {file_path}")
            
        if self._should_exclude_path(file_path):
            logger.info(f"跳过排除的文件: {file_path}")
            return ScanResult(
                scan_id=f"file_{int(time.time())}",
                scan_path=file_path,
                scan_type="file",
                scan_model=self.model_name,
                timestamp=time.time()
            )
            
        try:
            # 读取文件内容
            with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
                content = f.read()
                
            # 分析文件
            issues = self._analyze_file_content(file_path, content)
            
            # 统计信息
            stats = {
                "lines_of_code": count_lines(file_path),
                "language": get_file_language(file_path),
                "file_size_bytes": os.path.getsize(file_path)
            }
            
            # 提取简单文件信息
            file_info = extract_file_info(file_path, content)
            
            # 生成更详细的项目信息（单文件视为小项目）
            project_info = self._generate_file_info(file_path, content, stats)
            project_info["file_info"] = file_info
            
            return ScanResult(
                scan_id=f"file_{int(time.time())}",
                scan_path=file_path,
                scan_type="file",
                scan_model=self.model_name,
                timestamp=time.time(),
                issues=issues,
                stats=stats,
                project_info=project_info
            )
            
        except Exception as e:
            logger.error(f"扫描文件时出错 {file_path}: {str(e)}")
            return ScanResult(
                scan_id=f"file_{int(time.time())}_error",
                scan_path=file_path,
                scan_type="file",
                scan_model=self.model_name,
                timestamp=time.time(),
                stats={"error": str(e)}
            )
    
    def scan_directory(self, dir_path: str, max_workers: int = 5, progress_callback=None) -> ScanResult:
        """扫描目录
        
        Args:
            dir_path: 目录路径
            max_workers: 最大工作线程数
            progress_callback: 进度回调函数，接收消息字符串和完成百分比 (0-100)
            
        Returns:
            扫描结果
        """
        if not os.path.isdir(dir_path):
            raise ValueError(f"目录不存在: {dir_path}")
            
        # 扫描结果
        scan_result = ScanResult(
            scan_id=f"dir_{int(time.time())}",
            scan_path=dir_path,
            scan_type="directory",
            scan_model=self.model_name,
            timestamp=time.time()
        )
        
        try:
            # 收集文件
            if progress_callback:
                progress_callback("正在收集文件...", 5)
                
            files_to_scan = self._collect_files(dir_path)
            logger.info(f"找到 {len(files_to_scan)} 个文件需要扫描")
            
            if progress_callback:
                progress_callback(f"找到 {len(files_to_scan)} 个文件需要扫描", 10)
            
            if not files_to_scan:
                logger.warning(f"目录 {dir_path} 中没有可扫描的文件")
                scan_result.stats = {"error": "没有找到可扫描的文件"}
                if progress_callback:
                    progress_callback("没有找到可扫描的文件", 100)
                return scan_result
            
            # 统计项目信息
            languages = {}
            total_lines = 0
            file_counts = {}
            
            # 计算总文件数，用于进度计算
            total_files = len(files_to_scan)
            completed_files = 0
            
            # 使用线程池并行扫描文件
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                future_to_file = {
                    executor.submit(self.scan_file, file_path): file_path
                    for file_path in files_to_scan
                }
                
                for future in as_completed(future_to_file):
                    file_path = future_to_file[future]
                    try:
                        result = future.result()
                        scan_result.issues.extend(result.issues)
                        
                        # 更新统计信息
                        if "lines_of_code" in result.stats:
                            total_lines += result.stats["lines_of_code"]
                        
                        if "language" in result.stats:
                            lang = result.stats["language"]
                            languages[lang] = languages.get(lang, 0) + 1
                            
                        # 更新文件类型统计
                        ext = os.path.splitext(file_path)[1].lower()
                        file_counts[ext] = file_counts.get(ext, 0) + 1
                            
                    except Exception as e:
                        logger.error(f"处理文件结果时出错 {file_path}: {str(e)}")
                    
                    # 更新进度
                    completed_files += 1
                    if progress_callback and total_files > 0:
                        # 进度从10%~80%，按文件扫描进度计算
                        progress = 10 + int(70.0 * completed_files / total_files)
                        file_name = os.path.basename(file_path)
                        progress_callback(f"正在扫描({completed_files}/{total_files}): {file_name}", progress)
            
            # 填充项目信息
            if progress_callback:
                progress_callback("正在生成项目统计信息...", 85)
                
            scan_result.stats = {
                "total_files": len(files_to_scan),
                "total_lines_of_code": total_lines,
                "languages": languages,
                "file_extensions": file_counts
            }
            
            # 项目总体分析
            if progress_callback:
                progress_callback("正在进行项目分析...", 90)
                
            project_info = self._generate_project_info(dir_path, scan_result.stats)
            scan_result.project_info = project_info
            
            if progress_callback:
                progress_callback("扫描完成，正在生成报告...", 95)
            
        except Exception as e:
            logger.error(f"扫描目录过程中出错 {dir_path}: {str(e)}")
            scan_result.stats = {"error": str(e)}
            if progress_callback:
                progress_callback(f"扫描出错: {str(e)}", 100)
        
        return scan_result
    
    def create_merge_scan_result(self, base_path: str, scan_id: str, issues: List[VulnerabilityIssue], 
                                diff_files: List[str]) -> ScanResult:
        """创建合并扫描结果
        
        Args:
            base_path: 基础路径
            scan_id: 扫描ID
            issues: 问题列表
            diff_files: 差异文件列表
            
        Returns:
            扫描结果
        """
        # 创建扫描结果
        scan_result = ScanResult(
            scan_id=scan_id,
            scan_path=base_path,
            scan_type="git-merge",
            scan_model=self.model_name,
            timestamp=time.time(),
            issues=issues
        )
        
        # 统计信息
        total_lines = 0
        languages = {}
        file_counts = {}
        
        # 统计文件信息
        for file_path in diff_files:
            full_path = os.path.join(base_path, file_path)
            if os.path.isfile(full_path):
                try:
                    # 计算行数
                    lines = count_lines(full_path)
                    total_lines += lines
                    
                    # 确定语言
                    lang = get_file_language(full_path)
                    languages[lang] = languages.get(lang, 0) + 1
                    
                    # 更新文件类型统计
                    ext = os.path.splitext(file_path)[1].lower()
                    file_counts[ext] = file_counts.get(ext, 0) + 1
                    
                except Exception as e:
                    logger.error(f"统计文件信息时出错 {file_path}: {str(e)}")
        
        # 填充统计信息
        scan_result.stats = {
            "total_files": len(diff_files),
            "total_lines_of_code": total_lines,
            "languages": languages,
            "file_extensions": file_counts
        }
        
        # 项目信息
        scan_result.project_info = {
            "merge_info": {
                "diff_files": diff_files
            }
        }
        
        return scan_result
    
    def _generate_project_info(self, dir_path: str, stats: Dict[str, Any]) -> Dict[str, Any]:
        """生成项目信息
        
        Args:
            dir_path: 目录路径
            stats: 统计信息
            
        Returns:
            项目信息字典
        """
        # 获取目录结构
        structure = self._get_directory_structure(dir_path)

        try:
            project_info = self._coerce_to_dict(
                self.ai_service.summarize_project(dir_path, stats, structure)
            )
            project_info["stats"] = stats
            return project_info
        except Exception as e:
            logger.error(f"生成项目信息时出错: {str(e)}")
            return {"stats": stats}
    
    def _get_directory_structure(self, dir_path: str, max_depth: int = 3) -> Dict[str, Any]:
        """获取目录结构
        
        Args:
            dir_path: 目录路径
            max_depth: 最大深度
            
        Returns:
            目录结构字典
        """
        if max_depth <= 0:
            return {"...": "..."}
            
        result = {}
        
        try:
            for item in os.listdir(dir_path):
                item_path = os.path.join(dir_path, item)
                
                # 排除不需要的目录和文件
                if self._should_exclude_path(item_path):
                    continue
                    
                if os.path.isdir(item_path):
                    result[item] = self._get_directory_structure(item_path, max_depth - 1)
                else:
                    result[item] = {"type": "file", "size": os.path.getsize(item_path)}
        except Exception as e:
            logger.error(f"获取目录结构时出错 {dir_path}: {str(e)}")
        
        return result 

    def _generate_file_info(self, file_path: str, content: str, stats: Dict[str, Any]) -> Dict[str, Any]:
        """为单个文件生成项目信息
        
        Args:
            file_path: 文件路径
            content: 文件内容
            stats: 统计信息
            
        Returns:
            文件分析信息
        """
        language = stats.get("language", "Unknown")
        file_name = os.path.basename(file_path)

        try:
            file_info = self._coerce_to_dict(
                self.ai_service.summarize_file(file_path, language, stats, content)
            )
            return {
                "project_type": f"{language}文件",
                "main_functionality": file_info.get("file_purpose", f"{file_name} - 未能自动分析"),
                "components": file_info.get("main_components", []),
                "architecture": file_info.get("possible_role", "单文件分析"),
                "use_cases": [],
                "file_analysis": {
                    "code_quality": file_info.get("code_quality", "未分析"),
                    "suggested_improvements": file_info.get("suggested_improvements", []),
                },
                "stats": stats,
            }
        except Exception as e:
            logger.error(f"生成文件信息时出错: {str(e)}")
            return {
                "project_type": f"{language}文件",
                "main_functionality": file_name,
                "components": [],
                "architecture": "未能分析",
                "use_cases": [],
                "stats": stats
            } 
