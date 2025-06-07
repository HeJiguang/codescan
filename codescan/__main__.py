"""命令行入口模块"""

import sys
import os
import argparse
from .cli import main as cli_main
from .gui import main as gui_main
from .__init__ import __version__
from .config import config
from .styles import apply_style  # 导入样式应用函数

def check_api_config() -> bool:
    """检查API配置是否有效
    
    Returns:
        API配置是否有效
    """
    models_config = config.config.get("models", {})
    default_config = models_config.get("default", {})
    
    # 检查是否有API密钥
    api_key = default_config.get('api_key', '')
    return bool(api_key)

def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="代码安全扫描工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""示例:
  扫描单个文件:
    python -m codescan scan-file path/to/file.py
  
  扫描目录:
    python -m codescan scan-dir path/to/directory
  
  扫描GitHub仓库:
    python -m codescan scan-github https://github.com/user/repo
  
  生成HTML报告:
    python -m codescan scan-dir path/to/directory --output report.html
  
  启动GUI界面:
    python -m codescan gui
  
  配置API密钥:
    python -m codescan config --api-key YOUR_API_KEY
        """
    )
    
    parser.add_argument('--version', action='version', version=f'%(prog)s {__version__}')
    
    # 创建子命令
    subparsers = parser.add_subparsers(dest='command', help='命令')
    
    # 配置命令
    config_parser = subparsers.add_parser('config', help='配置工具')
    config_parser.add_argument('--api-key', help='设置API密钥')
    config_parser.add_argument('--api-base', help='设置API基础URL')
    config_parser.add_argument('--api-provider', choices=['openai', 'azure', 'anthropic', 'custom'], 
                                help='设置API提供商')
    config_parser.add_argument('--proxy', help='设置HTTP代理')
    
    # 扫描文件命令
    scan_file_parser = subparsers.add_parser('scan-file', help='扫描单个文件')
    scan_file_parser.add_argument('path', help='文件路径')
    scan_file_parser.add_argument('--output', '-o', help='输出报告路径')
    scan_file_parser.add_argument('--model', '-m', help='使用的模型名称', default='default')
    
    # 扫描目录命令
    scan_dir_parser = subparsers.add_parser('scan-dir', help='扫描目录')
    scan_dir_parser.add_argument('path', help='目录路径')
    scan_dir_parser.add_argument('--output', '-o', help='输出报告路径')
    scan_dir_parser.add_argument('--model', '-m', help='使用的模型名称', default='default')
    scan_dir_parser.add_argument('--exclude', '-e', help='排除的文件/目录模式（glob格式）')
    
    # 扫描GitHub仓库命令
    scan_github_parser = subparsers.add_parser('scan-github', help='扫描GitHub仓库')
    scan_github_parser.add_argument('url', help='GitHub仓库URL')
    scan_github_parser.add_argument('--output', '-o', help='输出报告路径')
    scan_github_parser.add_argument('--model', '-m', help='使用的模型名称', default='default')
    
    # 规则管理命令
    rule_parser = subparsers.add_parser('rule', help='规则管理')
    rule_parser.add_argument('--import-dir', help='从目录导入规则')
    rule_parser.add_argument('--import-url', help='从URL导入规则')
    rule_parser.add_argument('--list', action='store_true', help='列出所有规则')
    
    # GUI命令
    subparsers.add_parser('gui', help='启动图形界面')
    
    # 解析命令行参数
    args = parser.parse_args()
    
    if args.command is None:
        parser.print_help()
        if not check_api_config():
            print("\n提示: 您需要先配置API密钥才能使用分析功能。")
            print("请使用以下命令配置API密钥:")
            print("python -m codescan config --api-key YOUR_API_KEY")
        return 0
    
    if args.command == 'gui':
        # 应用新样式
        from PyQt5.QtWidgets import QApplication
        app = QApplication(sys.argv)
        apply_style(app)  # 应用自定义样式
        return gui_main(app)  # 传递应用程序实例
    else:
        return cli_main(args)

if __name__ == '__main__':
    sys.exit(main()) 