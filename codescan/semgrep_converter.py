"""
Semgrep规则转换模块
~~~~~~~~~

将Semgrep规则转换为我们自己的漏洞库格式
"""

import os
import yaml
import glob
import re
import logging
from typing import Dict, List, Any, Optional, Tuple

logger = logging.getLogger(__name__)

def convert_semgrep_rule(rule: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    转换单个Semgrep规则为我们的格式
    
    Args:
        rule: Semgrep规则字典
        
    Returns:
        转换后的规则字典，如果无法转换则返回None
    """
    try:
        # 提取基本信息
        rule_id = rule.get('id', '')
        languages = rule.get('languages', [])
        severity = rule.get('severity', 'medium').lower()
        message = rule.get('message', '')
        
        # 规则名称可能来自不同字段
        rule_name = rule.get('name', '') or rule.get('message', '')[:50]
        
        # 处理模式 - 改进的模式提取
        pattern = None
        
        # 处理简单的pattern字段
        if 'pattern' in rule:
            if isinstance(rule['pattern'], str):
                pattern = rule['pattern']
            elif isinstance(rule['pattern'], dict) and 'pattern' in rule['pattern']:
                # 处理嵌套的pattern
                pattern = rule['pattern'].get('pattern', '')
        
        # 处理pattern-either字段
        elif 'pattern-either' in rule:
            patterns = rule.get('pattern-either', [])
            if patterns:
                # 确保所有模式都是字符串
                string_patterns = []
                for p in patterns:
                    if isinstance(p, str):
                        string_patterns.append(p)
                    elif isinstance(p, dict) and 'pattern' in p:
                        if isinstance(p['pattern'], str):
                            string_patterns.append(p['pattern'])
                
                if string_patterns:
                    pattern = "|".join([p.replace('\n', ' ') if isinstance(p, str) else '' for p in string_patterns])
        
        # 处理pattern-regex字段
        elif 'pattern-regex' in rule:
            if isinstance(rule['pattern-regex'], str):
                pattern = rule['pattern-regex']
        
        # 尝试提取pattern-inside或pattern-not
        elif 'pattern-inside' in rule:
            if isinstance(rule['pattern-inside'], str):
                pattern = rule['pattern-inside']
        elif 'pattern-not' in rule:
            if isinstance(rule['pattern-not'], str):
                pattern = f"(?!{rule['pattern-not']})"
        
        # 如果没有找到主要模式，尝试提取patterns中的第一个模式
        if not pattern and 'patterns' in rule and isinstance(rule['patterns'], list) and rule['patterns']:
            for pattern_entry in rule['patterns']:
                if isinstance(pattern_entry, dict):
                    if 'pattern' in pattern_entry and isinstance(pattern_entry['pattern'], str):
                        pattern = pattern_entry['pattern']
                        break
                    elif 'patterns' in pattern_entry and isinstance(pattern_entry['patterns'], list):
                        for nested_pattern in pattern_entry['patterns']:
                            if isinstance(nested_pattern, dict) and 'pattern' in nested_pattern and isinstance(nested_pattern['pattern'], str):
                                pattern = nested_pattern['pattern']
                                break
                        if pattern:
                            break
        
        # 如果最终还是没找到模式，尝试提取rules中的第一条规则
        if not pattern and 'rules' in rule and isinstance(rule['rules'], list) and rule['rules']:
            for subrule in rule['rules']:
                if isinstance(subrule, dict):
                    if 'pattern' in subrule and isinstance(subrule['pattern'], str):
                        pattern = subrule['pattern']
                        break
        
        # 如果最终还是没找到模式，无法转换
        if not pattern:
            # 如果有一个最小模式说明，也可以用作模式
            if 'metadata' in rule and isinstance(rule['metadata'], dict):
                if 'cwe' in rule['metadata']:
                    pattern = f"# CWE-{rule['metadata']['cwe']}"
                elif 'owasp' in rule['metadata']:
                    pattern = f"# OWASP-{rule['metadata']['owasp']}"
                else:
                    # 使用规则ID作为模式，避免完全失败
                    pattern = f"# {rule_id}"
            else:
                # 使用规则ID作为模式，避免完全失败
                pattern = f"# {rule_id}"
        
        # 确保pattern是字符串
        if not isinstance(pattern, str):
            logger.warning(f"规则 {rule_id} 的模式不是字符串: {type(pattern)}")
            pattern = str(pattern)
            
        # 过滤掉Semgrep特有的语法元素，安全处理
        try:
            pattern = re.sub(r'[$][A-Z_]+', '', pattern)  # 移除metavariables
            pattern = pattern.replace('...', '.*?')  # 替换省略号为正则表达式
        except Exception as pattern_err:
            logger.warning(f"处理模式语法时出错: {pattern_err}")
        
        # 转换为正则表达式安全的格式，安全处理
        try:
            pattern = re.escape(pattern)
        except Exception as escape_err:
            logger.warning(f"转换正则表达式时出错: {escape_err}")
            # 如果无法转义，直接使用原始模式
            pass
        
        # 创建我们格式的规则
        converted_rule = {
            "id": rule_id,
            "name": rule_name,
            "pattern": pattern,
            "description": message,
            "severity": severity,
            "languages": languages,
            "source": "semgrep"
        }
        
        # 添加元数据
        if 'metadata' in rule and isinstance(rule['metadata'], dict):
            converted_rule["metadata"] = rule['metadata']
        
        return converted_rule
    except Exception as e:
        logger.error(f"转换规则 {rule.get('id', '未知')} 时出错: {str(e)}")
        return None

def convert_semgrep_rules_file(filepath: str) -> Dict[str, List[Dict[str, Any]]]:
    """
    转换Semgrep规则文件为我们的格式
    
    Args:
        filepath: Semgrep规则文件路径
        
    Returns:
        按语言分类的规则字典
    """
    result = {}
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            # 尝试加载YAML
            content = yaml.safe_load(f)
        
        # 检查文件格式
        if content is None:
            logger.warning(f"文件 {filepath} 内容为空")
            return result
            
        # 处理不同格式的规则文件
        rules = []
        
        if isinstance(content, dict):
            # 标准规则格式
            if 'rules' in content and isinstance(content['rules'], list):
                rules = content['rules']
            # 单规则格式
            elif 'id' in content and 'pattern' in content:
                rules = [content]
            # 其他格式
            else:
                # 尝试找出规则定义
                for key, value in content.items():
                    if isinstance(value, dict) and 'rules' in value and isinstance(value['rules'], list):
                        rules.extend(value['rules'])
                    elif isinstance(value, dict) and 'pattern' in value:
                        rules.append(value)
        elif isinstance(content, list):
            # 规则列表格式
            rules = content
            
        # 如果没有找到规则，返回空结果
        if not rules:
            logger.warning(f"文件 {filepath} 中没有找到规则")
            return result
            
        # 转换每条规则
        for rule in rules:
            if not isinstance(rule, dict):
                continue  # 跳过非字典类型的规则
                
            converted = convert_semgrep_rule(rule)
            if not converted:
                continue
                
            # 按语言分类
            languages = converted.get('languages', ['common'])
            if not languages:
                languages = ['common']  # 确保至少有一个语言分类
                
            # 确保每项都是字符串
            languages = [str(lang).lower() if lang else 'common' for lang in languages]
                
            for lang in languages:
                lang_key = lang.lower()
                if lang_key not in result:
                    result[lang_key] = []
                result[lang_key].append(converted)
    except Exception as e:
        logger.error(f"处理文件 {filepath} 时出错: {str(e)}")
    
    return result

def convert_semgrep_rules_dir(directory: str) -> Dict[str, List[Dict[str, Any]]]:
    """
    转换目录中的所有Semgrep规则文件
    
    Args:
        directory: 规则目录路径
        
    Returns:
        按语言分类的规则字典
    """
    result = {
        "common": [],
        "python": [],
        "javascript": [],
        "java": [],
        "go": [],
        "ruby": [],
        "php": [],
        "c": [],
        "cpp": []
    }
    
    # 寻找所有YAML文件
    yaml_files = []
    yaml_files.extend(glob.glob(os.path.join(directory, "**/*.yaml"), recursive=True))
    yaml_files.extend(glob.glob(os.path.join(directory, "**/*.yml"), recursive=True))
    
    logger.info(f"在 {directory} 中找到 {len(yaml_files)} 个YAML文件")
    
    # 处理每个文件
    for file in yaml_files:
        file_rules = convert_semgrep_rules_file(file)
        
        # 合并规则
        for lang, rules in file_rules.items():
            if lang not in result:
                result[lang] = []
            result[lang].extend(rules)
    
    # 统计结果
    total_rules = sum(len(rules) for rules in result.values())
    logger.info(f"成功转换 {total_rules} 条规则")
    
    return result

def download_semgrep_rules(url: str) -> Dict[str, List[Dict[str, Any]]]:
    """
    从URL下载并转换Semgrep规则
    
    Args:
        url: 规则URL
        
    Returns:
        按语言分类的规则字典
    """
    import requests
    import tempfile
    import shutil
    
    # 创建临时目录
    temp_dir = tempfile.mkdtemp(prefix="semgrep_rules_")
    
    try:
        # 下载规则
        response = requests.get(url, timeout=30)
        if response.status_code != 200:
            logger.error(f"下载规则失败: HTTP状态码 {response.status_code}")
            return {}
        
        # 保存到临时文件
        if url.endswith(".zip"):
            # 保存并解压ZIP文件
            zip_path = os.path.join(temp_dir, "rules.zip")
            with open(zip_path, 'wb') as f:
                f.write(response.content)
            
            import zipfile
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(temp_dir)
            
            # 转换规则
            return convert_semgrep_rules_dir(temp_dir)
        else:
            # 假设是单个YAML文件
            yaml_path = os.path.join(temp_dir, "rule.yaml")
            with open(yaml_path, 'wb') as f:
                f.write(response.content)
            
            return convert_semgrep_rules_file(yaml_path)
    
    except Exception as e:
        logger.error(f"下载或转换规则时出错: {str(e)}")
        return {}
    
    finally:
        # 清理临时目录
        shutil.rmtree(temp_dir, ignore_errors=True)

def import_from_github(repo_url: str, branch: str = "develop", languages: List[str] = None) -> Tuple[Dict[str, List[Dict[str, Any]]], int]:
    """
    从GitHub仓库导入Semgrep规则
    
    Args:
        repo_url: GitHub仓库URL
        branch: 要克隆的分支
        languages: 要导入的语言列表，如果为None则导入所有语言
        
    Returns:
        按语言分类的规则字典和成功导入的规则数量
    """
    import tempfile
    import shutil
    
    # 创建临时目录
    temp_dir = tempfile.mkdtemp(prefix="github_semgrep_rules_")
    
    try:
        logger.info(f"从 {repo_url} 克隆仓库 (分支: {branch})...")
        
        # 从GitHub克隆仓库
        import subprocess
        from time import sleep
        
        # 设置超时和重试参数
        retry_times = 3
        timeout_seconds = 60  # 每次尝试的超时时间
        current_try = 1
        
        success = False
        error_msg = ""
        
        # 准备克隆命令，添加超时设置
        clone_cmd = ["git", "clone", "--depth", "1", "--branch", branch, "--single-branch"]
        
        # 检查操作系统，根据不同的操作系统添加超时参数
        import platform
        if platform.system() == "Windows":
            # Windows版本
            clone_cmd.append("--config")
            clone_cmd.append(f"http.timeout={timeout_seconds}")
        else:
            # Linux/Mac版本
            clone_cmd.append("--config")
            clone_cmd.append(f"http.timeout={timeout_seconds}")
            
        # 添加仓库URL和目标目录
        clone_cmd.extend([repo_url, temp_dir])
            
        # 重试克隆
        while current_try <= retry_times and not success:
            try:
                logger.info(f"尝试克隆 ({current_try}/{retry_times})...")
                process = subprocess.run(clone_cmd, check=True, capture_output=True, text=True, timeout=timeout_seconds)
                success = True
                logger.info("仓库克隆成功")
            except subprocess.TimeoutExpired:
                logger.warning(f"克隆超时 (尝试 {current_try}/{retry_times})")
                error_msg = "操作超时"
            except subprocess.CalledProcessError as e:
                logger.warning(f"克隆失败: {e.stderr} (尝试 {current_try}/{retry_times})")
                error_msg = e.stderr
            except Exception as e:
                logger.warning(f"克隆时出错: {str(e)} (尝试 {current_try}/{retry_times})")
                error_msg = str(e)
                
            if not success:
                # 如果不是最后一次尝试，等待一会儿再重试
                if current_try < retry_times:
                    wait_seconds = current_try * 2  # 每次重试等待时间增加
                    logger.info(f"等待 {wait_seconds} 秒后重试...")
                    sleep(wait_seconds)
                current_try += 1
                
        if not success:
            logger.error(f"克隆仓库失败: {error_msg}")
            return {}, 0
            
        logger.info("仓库克隆成功，开始处理规则...")
        
        result = {}
        total_rules = 0
        processed_files = 0
        
        # 如果指定了语言，只处理这些语言目录
        if languages:
            for lang in languages:
                lang_dir = os.path.join(temp_dir, lang.lower())
                if os.path.isdir(lang_dir):
                    logger.info(f"处理 {lang} 语言规则...")
                    lang_rules = convert_semgrep_rules_dir(lang_dir)
                    
                    # 合并规则
                    for key, rules in lang_rules.items():
                        if key not in result:
                            result[key] = []
                        result[key].extend(rules)
                else:
                    logger.warning(f"未找到语言目录: {lang_dir}")
        else:
            # 处理整个仓库，但排除特定目录
            excluded_dirs = ['.git', '.github', 'tests', 'docs', '__pycache__']
            
            # 处理仓库根目录的子目录
            for item in os.listdir(temp_dir):
                item_path = os.path.join(temp_dir, item)
                
                # 如果是目录，并且不在排除列表中
                if os.path.isdir(item_path) and item not in excluded_dirs:
                    logger.info(f"处理目录: {item}")
                    dir_rules = convert_semgrep_rules_dir(item_path)
                    
                    # 合并规则
                    for key, rules in dir_rules.items():
                        if key not in result:
                            result[key] = []
                        result[key].extend(rules)
                        
                    processed_files += 1
        
        # 计算导入的规则总数
        for rules in result.values():
            total_rules += len(rules)
            
        if total_rules > 0:
            logger.info(f"从GitHub导入了 {total_rules} 条规则 (从 {processed_files} 个目录)")
        else:
            logger.warning(f"未找到有效规则，处理了 {processed_files} 个目录")
        
        return result, total_rules
    
    except Exception as e:
        logger.error(f"从GitHub导入规则时出错: {str(e)}")
        return {}, 0
    
    finally:
        # 清理临时目录
        try:
            shutil.rmtree(temp_dir, ignore_errors=True)
            logger.debug(f"清理临时目录: {temp_dir}")
        except Exception as e:
            logger.warning(f"清理临时目录时出错: {str(e)}") 