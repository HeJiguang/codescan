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
from typing import Dict, List, Any, Set, Optional, Tuple, Generator
from dataclasses import dataclass, field
from concurrent.futures import ThreadPoolExecutor, as_completed
import json

from .config import config
from .models import get_model_handler
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
    line_number: Optional[int] = None  # 行号（如果可以确定）
    code_snippet: Optional[str] = None  # 代码片段
    description: str = ""  # 问题描述
    recommendation: str = ""  # 修复建议
    cwe_id: Optional[str] = None  # CWE ID
    confidence: str = "medium"  # 置信度: 'high', 'medium', 'low'

@dataclass
class ScanResult:
    """扫描结果类"""
    scan_id: str  # 扫描ID
    scan_path: str  # 扫描路径
    scan_type: str  # 扫描类型: 'file', 'directory', 'github', 'git-merge'
    timestamp: float  # 扫描时间戳
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
    
    def __init__(self, model_name: str = 'default'):
        """初始化扫描器
        
        Args:
            model_name: 使用的大模型名称
        """
        self.model_name = model_name
        
        # 检查API配置是否存在
        model_config = config.get_model_config(model_name)
        if not model_config.get('api_key'):
            # 如果没有API密钥，尝试使用默认配置
            logger.warning(f"未找到模型'{model_name}'的API密钥配置，将使用默认配置")
            self.model_name = 'default'
            
        # 获取模型处理器
        try:
            self.model = get_model_handler(self.model_name)
            logger.info(f"使用模型: {self.model_name}")
        except Exception as e:
            logger.error(f"初始化模型处理器时出错: {str(e)}")
            # 降级到默认模型
            if self.model_name != 'default':
                logger.info("尝试使用默认模型")
                self.model_name = 'default'
                self.model = get_model_handler('default')
        
        self.vulndb = VulnerabilityDB()
        
        # 获取配置
        scan_config = config.config.get('scan', {})
        self.excluded_dirs = set(scan_config.get('excluded_dirs', []))
        self.excluded_files = set(scan_config.get('excluded_files', []))
        self.max_file_size_mb = scan_config.get('max_file_size_mb', 10)
        self.timeout_seconds = scan_config.get('timeout_seconds', 60)
        
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
        
        # 准备分析提示
        prompt = f"""
分析下面的{language}代码，查找安全漏洞、潜在bug和不良实践。
文件路径：{file_path}

特别注意以下几点：
1. SQL注入、XSS等常见安全漏洞
2. 不安全的依赖和API使用
3. 硬编码的秘钥和凭证
4. 未处理的错误和异常
5. 内存/资源泄漏
6. 逻辑错误
7. 代码质量问题

```
{content}
```

请按以下JSON格式返回结果：
```json
[
  {{
    "severity": "critical|high|medium|low|info",
    "description": "问题描述",
    "line_number": 42,
    "code_snippet": "有问题的代码片段",
    "recommendation": "修复建议",
    "cwe_id": "CWE编号",
    "confidence": "high|medium|low"
  }}
]
```
如果没有发现问题，则返回空数组 []。
"""
        
        try:
            # 调用大语言模型
            logger.info(f"使用模型 {self.model_name} 分析文件: {file_path}")
            analysis_result = self.model.analyze_code(prompt)
            
            # 提取JSON结果
            issues = []
            
            # 查找JSON部分
            json_pattern = r"```json\s*([\s\S]*?)\s*```|^\s*\[\s*\{[\s\S]*\}\s*\]\s*$"
            matches = re.findall(json_pattern, analysis_result)
            
            json_str = ""
            for match in matches:
                if match.strip():
                    json_str = match
                    break
                    
            if not json_str:
                # 尝试直接解析整个结果
                json_str = analysis_result
            
            try:
                # 清理JSON字符串
                json_str = json_str.strip()
                # 如果JSON字符串不是以[开头，可能需要进一步处理
                if not json_str.startswith("["):
                    start_idx = json_str.find("[")
                    end_idx = json_str.rfind("]")
                    if start_idx != -1 and end_idx != -1:
                        json_str = json_str[start_idx:end_idx+1]
                
                issues_data = json.loads(json_str)
                
                # 处理结果
                for issue_data in issues_data:
                    issues.append(VulnerabilityIssue(
                        severity=issue_data.get("severity", "medium"),
                        file_path=file_path,
                        line_number=issue_data.get("line_number"),
                        code_snippet=issue_data.get("code_snippet"),
                        description=issue_data.get("description", "未提供描述"),
                        recommendation=issue_data.get("recommendation", ""),
                        cwe_id=issue_data.get("cwe_id"),
                        confidence=issue_data.get("confidence", "medium")
                    ))
            except json.JSONDecodeError:
                # 如果JSON解析失败，添加一个说明问题
                logger.warning(f"无法解析模型返回的JSON: {file_path}")
                issues.append(VulnerabilityIssue(
                    severity="info",
                    file_path=file_path,
                    description="模型未返回标准JSON格式，无法完成深度分析",
                    recommendation="请检查API设置并重试",
                    confidence="low"
                ))
                
            # 根据漏洞库规则添加更多问题
            for pattern in relevant_patterns:
                pattern_re = re.compile(pattern.get("pattern", ""), re.IGNORECASE)
                
                if pattern_re.search(content):
                    # 找到匹配项，添加到问题列表
                    line_number = None
                    code_snippet = None
                    
                    # 尝试定位行号和代码片段
                    lines = content.split("\n")
                    for i, line in enumerate(lines):
                        if pattern_re.search(line):
                            line_number = i + 1
                            start = max(0, i - 2)
                            end = min(len(lines), i + 3)
                            code_snippet = "\n".join(lines[start:end])
                            break
                    
                    issues.append(VulnerabilityIssue(
                        severity=pattern.get("severity", "medium"),
                        file_path=file_path,
                        line_number=line_number,
                        code_snippet=code_snippet,
                        description=pattern.get("description", "发现潜在漏洞"),
                        recommendation=pattern.get("recommendation", "请检查此处代码"),
                        confidence="medium"
                    ))
                
            return issues
                
        except Exception as e:
            logger.error(f"分析文件时出错 {file_path}: {str(e)}")
            # 添加一个说明问题的Issue
            return [VulnerabilityIssue(
                severity="info",
                file_path=file_path,
                description=f"API连接错误: {str(e)}",
                recommendation="请在设置中检查您的API配置，确保API密钥正确且网络连接正常。",
                confidence="high"
            )]
    
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
        # 找出主要语言
        main_language = max(stats.get("languages", {}).items(), 
                            key=lambda x: x[1], default=("Unknown", 0))[0]
        
        # 获取目录结构
        structure = self._get_directory_structure(dir_path)
        
        # 使用大模型生成项目概述
        prompt = f"""
根据以下项目统计信息，分析这个项目的类型、结构和主要功能。

项目路径: {dir_path}
总文件数: {stats.get("total_files", 0)}
代码行数: {stats.get("total_lines_of_code", 0)}
主要语言: {main_language}
语言分布: {stats.get("languages", {})}
文件类型分布: {stats.get("file_extensions", {})}

目录结构:
{json.dumps(structure, ensure_ascii=False, indent=2)}

请提供:
1. 项目大致类型和功能
2. 主要组件和模块
3. 项目架构概述
4. 可能的使用场景

必须以严格的JSON格式回答，包含以下字段:
- "project_type": 项目类型
- "main_functionality": 主要功能
- "components": 主要组件列表
- "architecture": 架构简述
- "use_cases": 可能的使用场景列表

示例格式:
{{
  "project_type": "Web应用",
  "main_functionality": "用户认证和授权管理系统",
  "components": ["用户管理", "权限控制", "登录模块"],
  "architecture": "前后端分离架构，使用React前端和Django后端",
  "use_cases": ["企业内部系统", "SaaS平台"]
}}

确保返回值是有效的JSON，不包含任何额外文本、代码块标记或解释。
"""

        try:
            # 调用大语言模型分析
            analysis_result = self.model.analyze_code(prompt)
            
            # 尝试解析JSON结果
            try:
                # 先尝试直接解析
                try:
                    project_info = json.loads(analysis_result)
                except json.JSONDecodeError:
                    # 如果直接解析失败，尝试从文本中提取JSON部分
                    json_pattern = r'```json\s*([\s\S]*?)\s*```|```\s*([\s\S]*?)\s*```|\{\s*"project_type"[\s\S]*\}'
                    matches = re.search(json_pattern, analysis_result)
                    
                    if matches:
                        # 使用第一个非空匹配组
                        for group in matches.groups():
                            if group:
                                json_content = group.strip()
                                project_info = json.loads(json_content)
                                break
                    else:
                        # 如果无法提取JSON，创建一个简单的解析结果
                        raise json.JSONDecodeError("无法提取有效JSON", analysis_result, 0)
                
                # 验证必要的字段
                required_fields = ["project_type", "main_functionality", "components", "architecture", "use_cases"]
                for field in required_fields:
                    if field not in project_info:
                        project_info[field] = "未提供" if field != "components" and field != "use_cases" else []
                
                # 添加统计信息
                project_info["stats"] = stats
                return project_info
                
            except json.JSONDecodeError as e:
                logger.error(f"无法解析项目分析结果: {str(e)}")
                # 创建一个基本的项目信息对象，使用文本分析提取关键信息
                analysis_text = analysis_result.replace("```json", "").replace("```", "")
                
                # 创建一个基本信息对象
                project_info = {
                    "project_type": "未能自动分析",
                    "main_functionality": "未能自动分析",
                    "components": [],
                    "architecture": "未能自动分析",
                    "use_cases": [],
                    "stats": stats,
                    "analysis_text": analysis_text  # 保存原始文本以备后用
                }
                
                # 尝试从文本中提取项目类型
                type_match = re.search(r'项目类型[：:]\s*(.+?)(?:\n|$|\.|，|。)', analysis_text)
                if type_match:
                    project_info["project_type"] = type_match.group(1).strip()
                
                # 尝试从文本中提取主要功能
                func_match = re.search(r'主要功能[：:]\s*(.+?)(?:\n\n|$)', analysis_text, re.DOTALL)
                if func_match:
                    project_info["main_functionality"] = func_match.group(1).strip()
                
                # 提取组件列表
                components_match = re.search(r'主要组件[：:]\s*(.+?)(?:\n\n|$)', analysis_text, re.DOTALL)
                if components_match:
                    components_text = components_match.group(1)
                    components = re.findall(r'[\-\*•]\s*([^\n]+)', components_text)
                    if components:
                        project_info["components"] = [c.strip() for c in components]
                    else:
                        project_info["components"] = [s.strip() for s in components_text.split(',') if s.strip()]
                
                # 提取架构信息
                arch_match = re.search(r'架构[：:]\s*(.+?)(?:\n\n|$)', analysis_text, re.DOTALL)
                if arch_match:
                    project_info["architecture"] = arch_match.group(1).strip()
                
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
        # 获取文件语言和扩展名
        language = stats.get("language", "Unknown")
        file_ext = os.path.splitext(file_path)[1].lower()
        file_name = os.path.basename(file_path)
        
        # 使用大模型生成文件概述
        prompt = f"""
根据以下文件信息，提供简要但全面的文件分析。

文件名: {file_name}
文件路径: {file_path}
语言: {language}
代码行数: {stats.get("lines_of_code", 0)}
文件大小: {stats.get("file_size_bytes", 0)} 字节

文件内容:
```
{content[:3000]}  # 提供文件内容前3000个字符供分析
```
{"..." if len(content) > 3000 else ""}

请提供:
1. 文件的主要功能和用途
2. 主要的类、函数或组件
3. 文件在项目中可能的角色
4. 代码质量和结构评估

必须以严格的JSON格式回答，包含以下字段:
- "file_purpose": 文件的主要功能和用途
- "main_components": 主要的类、函数或组件列表
- "possible_role": 文件在项目中可能的角色
- "code_quality": 代码质量和结构评估
- "suggested_improvements": 建议的改进列表

确保返回值是有效的JSON，不包含任何额外文本、代码块标记或解释。
"""

        try:
            # 调用大语言模型分析
            analysis_result = self.model.analyze_code(prompt)
            
            # 尝试解析JSON结果
            try:
                # 先尝试直接解析
                try:
                    file_info = json.loads(analysis_result)
                except json.JSONDecodeError:
                    # 如果直接解析失败，尝试从文本中提取JSON部分
                    json_pattern = r'```json\s*([\s\S]*?)\s*```|```\s*([\s\S]*?)\s*```|\{\s*"file_purpose"[\s\S]*\}'
                    matches = re.search(json_pattern, analysis_result)
                    
                    if matches:
                        # 使用第一个非空匹配组
                        for group in matches.groups():
                            if group:
                                json_content = group.strip()
                                file_info = json.loads(json_content)
                                break
                    else:
                        # 如果无法提取JSON，创建一个简单的解析结果
                        raise json.JSONDecodeError("无法提取有效JSON", analysis_result, 0)
                
                # 验证必要的字段
                required_fields = ["file_purpose", "main_components", "possible_role", "code_quality", "suggested_improvements"]
                for field in required_fields:
                    if field not in file_info:
                        if field in ["main_components", "suggested_improvements"]:
                            file_info[field] = []
                        else:
                            file_info[field] = "未分析"
                
                # 构建适合项目信息格式的结果
                result = {
                    "project_type": f"{language}文件",
                    "main_functionality": file_info["file_purpose"],
                    "components": file_info["main_components"],
                    "architecture": file_info["possible_role"],
                    "use_cases": [],
                    "file_analysis": {
                        "code_quality": file_info["code_quality"],
                        "suggested_improvements": file_info["suggested_improvements"]
                    },
                    "stats": stats
                }
                
                return result
                
            except json.JSONDecodeError as e:
                logger.error(f"无法解析文件分析结果: {str(e)}")
                # 提取基本信息
                return {
                    "project_type": f"{language}文件",
                    "main_functionality": f"{file_name} - 未能自动分析",
                    "components": [],
                    "architecture": "单文件分析",
                    "use_cases": [],
                    "stats": stats,
                    "analysis_text": analysis_result
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