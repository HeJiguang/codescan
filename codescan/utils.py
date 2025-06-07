"""
工具函数模块
~~~~~~~~~

提供各种辅助函数
"""

import os
import re
import json
from typing import Dict, Any, List, Optional, Set, Tuple
import mimetypes
import logging

logger = logging.getLogger(__name__)

# 文件类型到语言的映射
FILE_EXTENSIONS = {
    '.py': 'python',
    '.js': 'javascript',
    '.ts': 'typescript',
    '.jsx': 'javascript',
    '.tsx': 'typescript',
    '.java': 'java',
    '.c': 'c',
    '.cpp': 'c++',
    '.cs': 'c#',
    '.go': 'golang',
    '.rs': 'rust',
    '.php': 'php',
    '.rb': 'ruby',
    '.swift': 'swift',
    '.kt': 'kotlin',
    '.scala': 'scala',
    '.m': 'objective-c',
    '.h': 'c',
    '.sh': 'bash',
    '.bat': 'batch',
    '.ps1': 'powershell',
    '.sql': 'sql',
    '.html': 'html',
    '.css': 'css',
    '.scss': 'scss',
    '.less': 'less',
    '.xml': 'xml',
    '.json': 'json',
    '.yaml': 'yaml',
    '.yml': 'yaml',
    '.md': 'markdown',
    '.tex': 'latex',
    '.r': 'r',
    '.dart': 'dart',
    '.lua': 'lua',
    '.pl': 'perl',
    '.groovy': 'groovy',
    '.vb': 'visual basic'
}

# 二进制文件的mime类型前缀
BINARY_MIME_PREFIXES = ['image/', 'audio/', 'video/', 'application/octet-stream', 
                        'application/zip', 'application/x-rar', 'application/pdf',
                        'application/msword', 'application/vnd.ms-']

def get_file_language(file_path: str) -> str:
    """
    根据文件扩展名确定编程语言
    
    Args:
        file_path: 文件路径
        
    Returns:
        编程语言名称，如果未知则返回"unknown"
    """
    _, ext = os.path.splitext(file_path.lower())
    return FILE_EXTENSIONS.get(ext, "unknown")

def count_lines(file_path: str) -> int:
    """
    计算文件行数
    
    Args:
        file_path: 文件路径
        
    Returns:
        文件行数
    """
    try:
        with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
            return sum(1 for _ in f)
    except Exception as e:
        logger.error(f"计算文件行数出错 {file_path}: {str(e)}")
        return 0

def is_binary_file(file_path: str) -> bool:
    """
    检查文件是否为二进制文件
    
    Args:
        file_path: 文件路径
        
    Returns:
        是否为二进制文件
    """
    # 检查MIME类型
    mime_type, _ = mimetypes.guess_type(file_path)
    if mime_type:
        for prefix in BINARY_MIME_PREFIXES:
            if mime_type.startswith(prefix):
                return True
    
    # 如果MIME类型检查未确定，尝试读取文件内容
    try:
        with open(file_path, 'rb') as f:
            chunk = f.read(1024)
            # 检查NULL字节，通常存在于二进制文件中
            if b'\x00' in chunk:
                return True
            
            # 尝试以文本方式解码
            try:
                chunk.decode('utf-8')
                return False
            except UnicodeDecodeError:
                return True
    except Exception:
        # 如果无法打开文件，保守起见认为是二进制
        return True
    
    return False

def extract_file_info(file_path: str, content: str) -> Dict[str, Any]:
    """
    提取文件信息，如类、函数、导入语句等
    
    Args:
        file_path: 文件路径
        content: 文件内容
        
    Returns:
        文件信息字典
    """
    language = get_file_language(file_path)
    info = {
        "language": language,
        "imports": [],
        "classes": [],
        "functions": [],
        "file_summary": ""
    }
    
    # 根据不同语言提取信息
    if language == "python":
        # 提取导入语句
        import_pattern = r'^(?:from\s+[\w.]+\s+import\s+.+|import\s+.+)'
        info["imports"] = re.findall(import_pattern, content, re.MULTILINE)
        
        # 提取类定义
        class_pattern = r'^\s*class\s+(\w+)'
        info["classes"] = re.findall(class_pattern, content, re.MULTILINE)
        
        # 提取函数定义
        function_pattern = r'^\s*def\s+(\w+)'
        info["functions"] = re.findall(function_pattern, content, re.MULTILINE)
    
    elif language == "javascript" or language == "typescript":
        # 提取导入语句
        import_pattern = r'^(?:import\s+.+?from\s+.+?|const\s+.+?\s*=\s*require\(.+?\))'
        info["imports"] = re.findall(import_pattern, content, re.MULTILINE)
        
        # 提取类定义
        class_pattern = r'(?:^|\s)class\s+(\w+)'
        info["classes"] = re.findall(class_pattern, content, re.MULTILINE)
        
        # 提取函数定义
        function_pattern = r'(?:^|\s)function\s+(\w+)|const\s+(\w+)\s*=\s*(?:function|\()'
        for match in re.finditer(function_pattern, content, re.MULTILINE):
            func_name = match.group(1) or match.group(2)
            if func_name:
                info["functions"].append(func_name)
    
    elif language == "java":
        # 提取导入语句
        import_pattern = r'^import\s+.+?;'
        info["imports"] = re.findall(import_pattern, content, re.MULTILINE)
        
        # 提取类定义
        class_pattern = r'(?:public|private|protected)?\s+class\s+(\w+)'
        info["classes"] = re.findall(class_pattern, content, re.MULTILINE)
        
        # 提取函数定义
        function_pattern = r'(?:public|private|protected)?\s+\w+\s+(\w+)\s*\('
        info["functions"] = re.findall(function_pattern, content, re.MULTILINE)
    
    # 为其他语言添加更多提取逻辑...
    
    # 生成文件摘要
    docstring = extract_docstring(content, language)
    if docstring:
        info["file_summary"] = docstring
    else:
        # 尝试从文件前几行生成摘要
        first_lines = '\n'.join(content.split('\n')[:10])
        info["file_summary"] = first_lines
    
    return info

def extract_docstring(content: str, language: str) -> str:
    """
    提取文件的文档字符串
    
    Args:
        content: 文件内容
        language: 编程语言
        
    Returns:
        文档字符串，如果没有则返回空字符串
    """
    if language == "python":
        # Python文档字符串模式
        docstring_pattern = r'^("""|\'\'\')(.*?)("""|\'\'\')'
        match = re.search(docstring_pattern, content, re.DOTALL)
        if match:
            return match.group(2).strip()
    
    elif language in ["javascript", "typescript"]:
        # JS/TS文档注释模式
        docstring_pattern = r'^/\*\*(.*?)\*/'
        match = re.search(docstring_pattern, content, re.DOTALL)
        if match:
            return match.group(1).strip()
    
    elif language == "java":
        # Java文档注释模式
        docstring_pattern = r'^/\*\*(.*?)\*/'
        match = re.search(docstring_pattern, content, re.DOTALL)
        if match:
            return match.group(1).strip()
    
    return ""

def format_timestamp(timestamp: float) -> str:
    """
    格式化时间戳为人类可读形式
    
    Args:
        timestamp: UNIX时间戳
        
    Returns:
        格式化的时间字符串
    """
    from datetime import datetime
    return datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')

def get_file_extension_stats(file_list: List[str]) -> Dict[str, int]:
    """
    统计文件扩展名分布
    
    Args:
        file_list: 文件路径列表
        
    Returns:
        扩展名计数字典
    """
    extension_counts = {}
    for file_path in file_list:
        _, ext = os.path.splitext(file_path.lower())
        if ext:
            extension_counts[ext] = extension_counts.get(ext, 0) + 1
    
    return extension_counts

def generate_report_filename(base_path: str, extension: str = 'html') -> str:
    """
    生成报告文件名
    
    Args:
        base_path: 基础路径
        extension: 文件扩展名
        
    Returns:
        报告文件名
    """
    from datetime import datetime
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    if os.path.isfile(base_path):
        base_name = os.path.basename(base_path)
        name_without_ext = os.path.splitext(base_name)[0]
    else:
        name_without_ext = os.path.basename(base_path)
    
    return f"codescan_{name_without_ext}_{timestamp}.{extension}" 