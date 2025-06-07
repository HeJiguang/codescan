"""
命令行界面模块
~~~~~~~~~

处理命令行操作
"""

import os
import sys
import logging
import time
import tempfile
import shutil
import json
from typing import Dict, Any, List, Optional
import argparse
from pathlib import Path
import git

from .scanner import CodeScanner
from .report import get_report_generator
from .utils import generate_report_filename
from .vulndb import VulnerabilityDB
from .config import config

logger = logging.getLogger(__name__)

def setup_logging(verbose: bool = False) -> None:
    """设置日志
    
    Args:
        verbose: 是否显示详细日志
    """
    log_level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

def config_api(args: argparse.Namespace) -> int:
    """配置API设置
    
    Args:
        args: 命令行参数
        
    Returns:
        退出码
    """
    # 显示当前配置
    if args.show:
        models_config = config.config.get("models", {})
        default_config = models_config.get("default", {})
        
        print("当前API配置:")
        print(f"  提供商: {default_config.get('provider', 'deepseek')}")
        print(f"  模型: {default_config.get('model', 'deepseek-chat')}")
        api_key = default_config.get('api_key', '')
        if api_key:
            # 只显示API密钥的前6位和后4位
            masked_key = api_key[:6] + '*' * (len(api_key) - 10) + api_key[-4:] if len(api_key) > 10 else '******'
            print(f"  API密钥: {masked_key}")
        else:
            print("  API密钥: 未设置")
        print(f"  基础URL: {default_config.get('base_url', 'https://api.deepseek.com')}")
        
        # 显示代理设置
        http_proxy = os.environ.get("HTTP_PROXY", "")
        https_proxy = os.environ.get("HTTPS_PROXY", "")
        if http_proxy or https_proxy:
            print(f"  HTTP代理: {http_proxy or https_proxy}")
        else:
            print("  HTTP代理: 未设置")
            
        return 0
    
    # 更新配置
    try:
        # 获取当前配置
        models_config = config.config.get("models", {})
        default_config = models_config.get("default", {})
        
        # 更新配置
        provider = args.provider or default_config.get("provider", "deepseek")
        model_name = args.model or default_config.get("model", "deepseek-chat")
        
        # 设置基础URL
        base_url = args.base_url
        if not base_url and provider == "deepseek":
            base_url = "https://api.deepseek.com"
        elif not base_url:
            base_url = default_config.get("base_url", "")
        
        # 检查是否提供了API密钥
        api_key = args.api_key
        if not api_key:
            api_key = default_config.get("api_key", "")
            if not api_key:
                print("错误: 未提供API密钥。请使用 --api-key 参数设置API密钥。")
                return 1
        
        # 更新默认配置
        new_config = {
            "provider": provider,
            "model": model_name,
            "api_key": api_key,
            "max_tokens": 8192
        }
        
        if base_url:
            new_config["base_url"] = base_url
        
        # 更新配置
        models_config["default"] = new_config
        
        # 如果选择的是预定义提供商，也更新对应的具体配置
        if provider in ["deepseek", "openai", "anthropic"]:
            models_config[provider] = new_config.copy()
        
        config.config["models"] = models_config
        config.save_config()
        
        # 设置代理环境变量
        if args.http_proxy:
            os.environ["HTTP_PROXY"] = args.http_proxy
            os.environ["HTTPS_PROXY"] = args.http_proxy
            # 写入到用户环境变量配置
            with open(os.path.join(config.config_dir, 'env.json'), 'w') as f:
                json.dump({"HTTP_PROXY": args.http_proxy, "HTTPS_PROXY": args.http_proxy}, f)
        
        print(f"配置成功保存。使用提供商: {provider}, 模型: {model_name}")
        return 0
        
    except Exception as e:
        logger.error(f"配置API时出错: {str(e)}")
        return 1

def scan_file(args: argparse.Namespace) -> int:
    """扫描单个文件
    
    Args:
        args: 命令行参数
        
    Returns:
        退出码
    """
    file_path = args.path
    model_name = args.model
    output_path = args.output
    
    if not os.path.isfile(file_path):
        logger.error(f"文件不存在: {file_path}")
        return 1
    
    try:
        # 创建扫描器
        scanner = CodeScanner(model_name=model_name)
        
        # 扫描文件
        logger.info(f"开始扫描文件: {file_path}")
        scan_result = scanner.scan_file(file_path)
        
        # 生成报告
        if not output_path:
            output_path = generate_report_filename(file_path, 'html')
        
        report_format = os.path.splitext(output_path)[1][1:] or 'html'
        generator = get_report_generator(report_format)
        report_path = generator.generate_report(scan_result, output_path)
        
        logger.info(f"扫描完成，报告已保存到: {report_path}")
        logger.info(f"发现 {scan_result.total_issues} 个问题")
        
        return 0
        
    except Exception as e:
        logger.error(f"扫描文件时出错: {str(e)}")
        return 1

def scan_directory(args: argparse.Namespace) -> int:
    """扫描目录
    
    Args:
        args: 命令行参数
        
    Returns:
        退出码
    """
    dir_path = args.path
    model_name = args.model
    output_path = args.output
    exclude_pattern = args.exclude
    
    if not os.path.isdir(dir_path):
        logger.error(f"目录不存在: {dir_path}")
        return 1
    
    try:
        # 创建扫描器
        scanner = CodeScanner(model_name=model_name)
        
        # 扫描目录
        logger.info(f"开始扫描目录: {dir_path}")
        scan_result = scanner.scan_directory(dir_path)
        
        # 生成报告
        if not output_path:
            output_path = generate_report_filename(dir_path, 'html')
        
        report_format = os.path.splitext(output_path)[1][1:] or 'html'
        generator = get_report_generator(report_format)
        report_path = generator.generate_report(scan_result, output_path)
        
        logger.info(f"扫描完成，报告已保存到: {report_path}")
        logger.info(f"发现 {scan_result.total_issues} 个问题")
        
        return 0
        
    except Exception as e:
        logger.error(f"扫描目录时出错: {str(e)}")
        return 1

def scan_github_repo(args: argparse.Namespace) -> int:
    """扫描GitHub仓库
    
    Args:
        args: 命令行参数
        
    Returns:
        退出码
    """
    repo_url = args.url
    model_name = args.model
    output_path = args.output
    
    # 创建临时目录
    temp_dir = tempfile.mkdtemp(prefix="codescan_github_")
    
    try:
        # 克隆仓库
        logger.info(f"正在克隆仓库: {repo_url}")
        git.Repo.clone_from(repo_url, temp_dir)
        
        # 扫描目录
        logger.info(f"开始扫描克隆的仓库")
        scanner = CodeScanner(model_name=model_name)
        scan_result = scanner.scan_directory(temp_dir)
        
        # 生成报告
        if not output_path:
            repo_name = repo_url.split('/')[-1].replace('.git', '')
            output_path = generate_report_filename(repo_name, 'html')
        
        report_format = os.path.splitext(output_path)[1][1:] or 'html'
        generator = get_report_generator(report_format)
        report_path = generator.generate_report(scan_result, output_path)
        
        logger.info(f"扫描完成，报告已保存到: {report_path}")
        logger.info(f"发现 {scan_result.total_issues} 个问题")
        
        return 0
        
    except Exception as e:
        logger.error(f"扫描GitHub仓库时出错: {str(e)}")
        return 1
    finally:
        # 清理临时目录
        shutil.rmtree(temp_dir, ignore_errors=True)

def scan_git_merge(args: argparse.Namespace) -> int:
    """扫描Git合并
    
    Args:
        args: 命令行参数
        
    Returns:
        退出码
    """
    branch = args.branch
    model_name = args.model
    output_path = args.output
    
    try:
        # 获取当前目录
        current_dir = os.getcwd()
        
        # 检查是否是Git仓库
        try:
            repo = git.Repo(current_dir)
        except git.InvalidGitRepositoryError:
            logger.error(f"当前目录不是Git仓库")
            return 1
        
        # 检查分支是否存在
        if branch not in [b.name for b in repo.branches]:
            logger.error(f"分支不存在: {branch}")
            return 1
        
        # 获取当前分支
        current_branch = repo.active_branch.name
        
        # 获取合并的文件列表
        logger.info(f"获取与分支 {branch} 的差异文件")
        diff_index = repo.git.diff(f"{branch}..{current_branch}", name_only=True).split()
        
        if not diff_index:
            logger.info(f"没有差异文件需要扫描")
            return 0
        
        # 创建扫描器
        scanner = CodeScanner(model_name=model_name)
        
        # 扫描每个差异文件
        logger.info(f"开始扫描 {len(diff_index)} 个差异文件")
        issues = []
        
        for file_path in diff_index:
            full_path = os.path.join(current_dir, file_path)
            if os.path.isfile(full_path):
                result = scanner.scan_file(full_path)
                issues.extend(result.issues)
        
        # 创建合并扫描结果
        scan_result = scanner.create_merge_scan_result(
            current_dir, 
            f"git-merge-{branch}-{current_branch}",
            issues,
            diff_index
        )
        
        # 生成报告
        if not output_path:
            output_path = generate_report_filename(f"git_merge_{branch}_{current_branch}", 'html')
        
        report_format = os.path.splitext(output_path)[1][1:] or 'html'
        generator = get_report_generator(report_format)
        report_path = generator.generate_report(scan_result, output_path)
        
        logger.info(f"扫描完成，报告已保存到: {report_path}")
        logger.info(f"发现 {scan_result.total_issues} 个问题")
        
        return 0
        
    except Exception as e:
        logger.error(f"扫描Git合并时出错: {str(e)}")
        return 1

def update_vulndb(args: argparse.Namespace) -> int:
    """更新漏洞库
    
    Args:
        args: 命令行参数
        
    Returns:
        退出码
    """
    try:
        vulndb = VulnerabilityDB()
        success = vulndb.update()
        
        if success:
            logger.info("漏洞库更新成功")
            return 0
        else:
            logger.error("漏洞库更新失败")
            return 1
            
    except Exception as e:
        logger.error(f"更新漏洞库时出错: {str(e)}")
        return 1

def import_rule(args: argparse.Namespace) -> int:
    """导入规则
    
    Args:
        args: 命令行参数
        
    Returns:
        退出码
    """
    try:
        url = args.url
        vulndb = VulnerabilityDB()
        
        logger.info(f"从URL导入规则: {url}")
        success = vulndb.import_semgrep_from_url(url)
        
        if success:
            # 计算当前规则总数
            total_rules = sum(len(rules) for rules in vulndb.patterns.values())
            logger.info(f"规则导入成功，当前漏洞库包含 {total_rules} 条规则")
            return 0
        else:
            logger.error("规则导入失败")
            return 1
            
    except Exception as e:
        logger.error(f"导入规则时出错: {str(e)}")
        return 1

def import_github_rules(args: argparse.Namespace) -> int:
    """从GitHub导入规则
    
    Args:
        args: 命令行参数
        
    Returns:
        退出码
    """
    try:
        repo_url = args.repo_url
        branch = args.branch
        languages_str = args.languages
        
        # 解析语言列表
        languages = None
        if languages_str:
            languages = [lang.strip() for lang in languages_str.split(',') if lang.strip()]
            
        logger.info(f"从GitHub仓库导入规则: {repo_url} (分支: {branch})")
        if languages:
            logger.info(f"仅导入以下语言的规则: {', '.join(languages)}")
            
        vulndb = VulnerabilityDB()
        success, rule_count = vulndb.import_github_rules(repo_url, branch, languages)
        
        if success:
            logger.info(f"成功从GitHub导入了 {rule_count} 条规则")
            
            # 计算当前规则总数
            total_rules = sum(len(rules) for rules in vulndb.patterns.values())
            logger.info(f"当前漏洞库包含 {total_rules} 条规则")
            return 0
        else:
            logger.error("从GitHub导入规则失败")
            return 1
            
    except Exception as e:
        logger.error(f"导入规则时出错: {str(e)}")
        return 1

def main(args: argparse.Namespace) -> int:
    """主函数
    
    Args:
        args: 命令行参数
        
    Returns:
        退出码
    """
    # 配置日志
    setup_logging()
    
    # 根据命令分发
    command = args.command
    
    if command == 'file':
        return scan_file(args)
    elif command == 'dir':
        return scan_directory(args)
    elif command == 'github':
        return scan_github_repo(args)
    elif command == 'git-merge':
        return scan_git_merge(args)
    elif command == 'update':
        return update_vulndb(args)
    elif command == 'config':
        return config_api(args)
    elif command == 'import-rule':
        return import_rule(args)
    elif command == 'import-github':
        return import_github_rules(args)
    else:
        logger.error(f"未知命令: {command}")
        return 1

if __name__ == "__main__":
    # 这个文件不应该直接运行，应该通过__main__.py运行
    print("请通过 'python -m codescan <command>' 运行此程序")
    sys.exit(1) 