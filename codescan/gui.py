"""
图形界面模块
~~~~~~~~~

提供GUI界面
"""

import os
import sys
import logging
import threading
import time
from typing import Dict, Any, List, Optional
import tempfile
from datetime import datetime
import json
import markdown  # 导入markdown库
import io
import base64
import numpy as np

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QPushButton, QLabel, QFileDialog, QComboBox, QTabWidget, 
    QTextEdit, QProgressBar, QMessageBox, QDialog, QFormLayout,
    QLineEdit, QDialogButtonBox, QCheckBox, QGroupBox, QMenuBar, QAction,
    QProgressDialog, QInputDialog, QTableWidget, QTableWidgetItem, QScrollArea,
    QTextBrowser, QSplitter, QFrame, QStackedWidget, QGridLayout, QSpacerItem,
    QStyle
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QPropertyAnimation, QEasingCurve, QTimer, QSize, QRect
from PyQt5.QtGui import QTextOption, QIntValidator, QColor, QPainter, QPen, QBrush, QFont, QPixmap, QIcon
from PyQt5.QtChart import (
    QChartView, QChart, QPieSeries, QBarSeries, QBarSet, QBarCategoryAxis, 
    QValueAxis, QLineSeries, QSplineSeries, QPolarChart, QAreaSeries, QScatterSeries, QPieSlice
)

# 导入自定义样式模块
from .styles import Theme, AnimatedButton, TechCard, ModernProgressBar, apply_style
from .scanner import CodeScanner, ScanResult
from .models import list_available_models
from .report import get_report_generator
from .config import config
from .vulndb import VulnerabilityDB
from .rule_manager import RuleManagerWidget

logger = logging.getLogger(__name__)

class APISettingsDialog(QDialog):
    """API设置对话框"""
    
    def __init__(self, parent=None):
        """初始化设置对话框"""
        super().__init__(parent)
        self.setWindowTitle("API设置")
        self.resize(500, 300)
        self.setup_ui()
        self.load_settings()
        
    def setup_ui(self):
        """设置界面"""
        layout = QVBoxLayout(self)
        
        # 添加帮助说明文本
        help_text = QLabel("请配置DeepSeek API以启用代码扫描功能。需要您在DeepSeek官方网站获取API密钥。\n如果连接有问题，可以尝试配置HTTP代理解决网络连接问题。")
        help_text.setWordWrap(True)
        help_text.setStyleSheet("color: #555; font-style: italic; background: #f8f8f8; padding: 8px; border-radius: 4px;")
        layout.addWidget(help_text)
        
        # 创建标签页
        self.tabs = QTabWidget()
        
        # API设置标签页
        api_widget = QWidget()
        api_layout = QVBoxLayout(api_widget)
        
        # 创建主API设置组
        main_group = QGroupBox("大模型API设置")
        form_layout = QFormLayout(main_group)
        
        # 提供商选择
        self.provider_combo = QComboBox()
        self.provider_combo.addItems(["deepseek", "openai", "anthropic", "custom"])
        form_layout.addRow("API提供商:", self.provider_combo)
        
        # API密钥
        self.api_key_edit = QLineEdit()
        self.api_key_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self.api_key_edit.setPlaceholderText("输入API密钥")
        form_layout.addRow("API密钥:", self.api_key_edit)
        
        # 模型名称
        self.model_name_edit = QLineEdit()
        self.model_name_edit.setPlaceholderText("deepseek-chat")
        form_layout.addRow("模型名称:", self.model_name_edit)
        
        # API基础URL
        self.base_url_edit = QLineEdit()
        self.base_url_edit.setPlaceholderText("https://api.deepseek.com")
        form_layout.addRow("API基础URL:", self.base_url_edit)
        
        # 监听提供商变化，更新默认值
        self.provider_combo.currentTextChanged.connect(self.update_defaults)
        
        api_layout.addWidget(main_group)
        
        # 代理设置组
        proxy_group = QGroupBox("代理设置 (可选)")
        proxy_layout = QFormLayout(proxy_group)
        
        # HTTP代理
        self.http_proxy_edit = QLineEdit()
        self.http_proxy_edit.setPlaceholderText("例如: http://127.0.0.1:7890")
        proxy_layout.addRow("HTTP代理:", self.http_proxy_edit)
        
        api_layout.addWidget(proxy_group)
        
        # 添加测试按钮
        test_button = QPushButton("测试API连接")
        test_button.clicked.connect(self.test_api_connection)
        api_layout.addWidget(test_button)
        
        # 添加API标签页
        self.tabs.addTab(api_widget, "API设置")
        
        # 漏洞库设置标签页
        vulndb_widget = QWidget()
        vulndb_layout = QVBoxLayout(vulndb_widget)
        
        # 创建漏洞库设置组
        vulndb_group = QGroupBox("漏洞库设置")
        vulndb_form = QFormLayout(vulndb_group)
        
        # 更新URL
        self.vulndb_url_edit = QLineEdit()
        self.vulndb_url_edit.setPlaceholderText("https://example.com/vulndb/latest.json")
        vulndb_form.addRow("更新URL:", self.vulndb_url_edit)
        
        # 自动更新选项
        self.auto_update_check = QCheckBox("启用自动更新")
        vulndb_form.addRow("", self.auto_update_check)
        
        # 更新间隔
        self.update_interval_edit = QLineEdit()
        self.update_interval_edit.setPlaceholderText("7")
        self.update_interval_edit.setValidator(QIntValidator(1, 365))
        vulndb_form.addRow("更新间隔(天):", self.update_interval_edit)
        
        vulndb_layout.addWidget(vulndb_group)
        
        # 漏洞库状态
        vulndb_status_group = QGroupBox("漏洞库状态")
        vulndb_status_layout = QFormLayout(vulndb_status_group)
        
        # 加载漏洞库信息
        vulndb = VulnerabilityDB()
        
        # 漏洞数量
        pattern_count = sum(len(patterns) for patterns in vulndb.patterns.values())
        vulndb_status_layout.addRow("当前规则数:", QLabel(f"{pattern_count} 个"))
        
        # 最后更新时间
        last_update = "未知"
        try:
            if os.path.exists(vulndb.last_update_file):
                with open(vulndb.last_update_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    timestamp = data.get("last_update", 0)
                    last_update = datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')
        except:
            pass
        
        vulndb_status_layout.addRow("最后更新时间:", QLabel(last_update))
        
        vulndb_layout.addWidget(vulndb_status_group)
        
        # 添加规则导入区域
        import_group = QGroupBox("规则导入")
        import_layout = QVBoxLayout(import_group)
        
        # 从目录导入Semgrep规则
        semgrep_dir_btn = QPushButton("从目录导入Semgrep规则")
        semgrep_dir_btn.clicked.connect(self.import_semgrep_from_dir)
        import_layout.addWidget(semgrep_dir_btn)
        
        # 从URL导入Semgrep规则
        semgrep_url_btn = QPushButton("从URL导入Semgrep规则")
        semgrep_url_btn.clicked.connect(self.import_semgrep_from_url)
        import_layout.addWidget(semgrep_url_btn)
        
        # 从GitHub导入Semgrep规则
        semgrep_github_btn = QPushButton("从GitHub导入Semgrep规则")
        semgrep_github_btn.clicked.connect(self.import_from_github)
        semgrep_github_btn.setStyleSheet("background-color: #e6f3ff;")  # 高亮显示
        import_layout.addWidget(semgrep_github_btn)
        
        # 添加说明文本
        help_text = QLabel("Semgrep规则导入说明:\n"
                        "1. 从目录导入：选择包含Semgrep YAML规则的目录\n"
                        "2. 从URL导入：输入指向Semgrep规则的URL\n"
                        "3. 从GitHub导入：自动从semgrep-rules等仓库克隆并导入规则\n\n"
                        "推荐资源:\n"
                        "- GitHub: https://github.com/semgrep/semgrep-rules\n"
                        "- OWASP: https://github.com/OWASP/www-project-web-security-testing-guide")
        help_text.setWordWrap(True)
        help_text.setStyleSheet("color: #555; font-style: italic;")
        import_layout.addWidget(help_text)
        
        vulndb_layout.addWidget(import_group)
        
        # 添加漏洞库标签页
        self.tabs.addTab(vulndb_widget, "漏洞库")
        
        # 添加标签页到主布局
        layout.addWidget(self.tabs)
        
        # 按钮
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Save | 
                                     QDialogButtonBox.StandardButton.Cancel)
        button_box.accepted.connect(self.save_settings)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
    
    def update_defaults(self, provider):
        """根据选择的提供商更新默认值"""
        if provider == "deepseek":
            self.base_url_edit.setText("https://api.deepseek.com")
            self.model_name_edit.setText("deepseek-chat")
        elif provider == "openai":
            self.base_url_edit.clear()
            self.model_name_edit.setText("gpt-3.5-turbo")
        elif provider == "anthropic":
            self.base_url_edit.clear()
            self.model_name_edit.setText("claude-3-opus-20240229")
        elif provider == "custom":
            self.base_url_edit.clear()
            self.model_name_edit.clear()
    
    def load_settings(self):
        """加载配置"""
        # 加载API配置
        default_model = config.get_model_config("default")
        provider = default_model.get("provider", "deepseek")
        
        self.provider_combo.setCurrentText(provider)
        self.api_key_edit.setText(default_model.get("api_key", ""))
        self.model_name_edit.setText(default_model.get("model", "deepseek-chat"))
        self.base_url_edit.setText(default_model.get("base_url", "https://api.deepseek.com"))
        
        # 加载代理设置
        http_proxy = os.environ.get("HTTP_PROXY", "")
        https_proxy = os.environ.get("HTTPS_PROXY", "")
        self.http_proxy_edit.setText(http_proxy or https_proxy)
        
        # 加载漏洞库设置
        vulndb_config = config.config.get("vulndb", {})
        self.vulndb_url_edit.setText(vulndb_config.get("update_url", ""))
        self.auto_update_check.setChecked(vulndb_config.get("auto_update", False))
        self.update_interval_edit.setText(str(vulndb_config.get("update_interval_days", 7)))
    
    def save_settings(self):
        """保存配置"""
        try:
            # 保存API设置
            provider = self.provider_combo.currentText()
            api_key = self.api_key_edit.text().strip()
            model_name = self.model_name_edit.text().strip()
            base_url = self.base_url_edit.text().strip()
            
            # 验证必要字段
            if not api_key:
                self.tabs.setCurrentIndex(0)  # 切换到API设置标签
                QMessageBox.warning(self, "配置错误", "请提供API密钥")
                return
                
            if not model_name:
                self.tabs.setCurrentIndex(0)  # 切换到API设置标签
                QMessageBox.warning(self, "配置错误", "请提供模型名称")
                return
                
            # 保存API配置
            default_config = {
                "provider": provider,
                "model": model_name,
                "api_key": api_key,
                "max_tokens": 8192  # 使用默认值
            }
            
            # 如果设置了base_url，添加到配置中
            if base_url:
                default_config["base_url"] = base_url
                
            # 同时更新默认模型和对应的特定模型配置
            models_config = config.config.get("models", {})
            models_config["default"] = default_config
            
            # 如果选择的是预定义提供商，也更新对应的具体配置
            if provider in ["deepseek", "openai", "anthropic"]:
                models_config[provider] = default_config.copy()
            
            config.config["models"] = models_config
            
            # 保存漏洞库设置
            vulndb_url = self.vulndb_url_edit.text().strip()
            auto_update = self.auto_update_check.isChecked()
            
            try:
                update_interval = int(self.update_interval_edit.text().strip() or "7")
                if update_interval < 1:
                    update_interval = 7
            except ValueError:
                update_interval = 7
            
            vulndb_config = {
                "update_url": vulndb_url,
                "auto_update": auto_update,
                "update_interval_days": update_interval
            }
            
            config.config["vulndb"] = vulndb_config
            
            # 保存配置
            config.save_config()
            
            # 设置代理环境变量
            http_proxy = self.http_proxy_edit.text().strip()
            if http_proxy:
                os.environ["HTTP_PROXY"] = http_proxy
                os.environ["HTTPS_PROXY"] = http_proxy
                
            QMessageBox.information(self, "保存成功", "设置已成功保存")
            self.accept()
            
        except Exception as e:
            logger.error(f"保存设置时出错: {str(e)}")
            QMessageBox.critical(
                self,
                "保存失败",
                f"保存设置时出错: {str(e)}"
            )

    def test_api_connection(self):
        """测试API连接"""
        try:
            provider = self.provider_combo.currentText()
            api_key = self.api_key_edit.text().strip()
            model_name = self.model_name_edit.text().strip() or "deepseek-chat"
            base_url = self.base_url_edit.text().strip()
            
            # 验证必要字段
            if not api_key:
                QMessageBox.warning(self, "输入错误", "请提供API密钥")
                return
            
            # 设置代理
            http_proxy = self.http_proxy_edit.text().strip()
            old_http_proxy = os.environ.get("HTTP_PROXY", "")
            old_https_proxy = os.environ.get("HTTPS_PROXY", "")
            
            if http_proxy:
                os.environ["HTTP_PROXY"] = http_proxy
                os.environ["HTTPS_PROXY"] = http_proxy
            
            # 创建临时配置
            temp_config = {
                "provider": provider,
                "model": model_name,
                "api_key": api_key,
                "max_tokens": 100  # 测试用小值
            }
            
            # 添加base_url如果存在
            if base_url:
                temp_config["base_url"] = base_url
                
            # 创建测试文本
            test_prompt = "请回答'API连接测试成功'，不要包含其他内容。"
            
            # 根据提供商创建模型处理器
            from codescan.models import get_model_handler
            
            # 保存原始配置
            original_models_config = config.config.get("models", {}).copy()
            
            # 临时设置配置
            models_config = config.config.get("models", {})
            models_config["temp_test"] = temp_config
            config.config["models"] = models_config
            
            # 创建模型处理器
            model = get_model_handler("temp_test")
            
            # 测试API调用
            QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
            response = model.analyze_code(test_prompt)
            QApplication.restoreOverrideCursor()
            
            # 恢复配置和环境变量
            config.config["models"] = original_models_config
            
            if http_proxy:
                if old_http_proxy:
                    os.environ["HTTP_PROXY"] = old_http_proxy
                else:
                    os.environ.pop("HTTP_PROXY", None)
                    
                if old_https_proxy:
                    os.environ["HTTPS_PROXY"] = old_https_proxy
                else:
                    os.environ.pop("HTTPS_PROXY", None)
            
            # 显示成功消息
            QMessageBox.information(
                self,
                "API连接测试",
                f"连接测试成功!\n\n响应: {response[:100]}...",
            )
            
        except Exception as e:
            QApplication.restoreOverrideCursor()
            logger.error(f"API测试失败: {str(e)}")
            
            # 显示友好的错误信息
            error_msg = str(e)
            if "401" in error_msg:
                error_msg = "认证失败：API密钥无效或过期"
            elif "timeout" in error_msg.lower():
                error_msg = "连接超时，请检查网络或代理设置"
            elif "connection" in error_msg.lower():
                error_msg = "连接失败，请检查网络或API基础URL"
                
            QMessageBox.critical(
                self,
                "API连接测试",
                f"连接测试失败!\n\n错误: {error_msg}"
            )

    def import_semgrep_from_dir(self):
        """从目录导入Semgrep规则"""
        dir_path = QFileDialog.getExistingDirectory(
            self, "选择Semgrep规则目录", ""
        )
        
        if not dir_path:
            return
            
        # 检查目录是否存在YAML文件
        import glob
        yaml_files = glob.glob(os.path.join(dir_path, "**/*.y*ml"), recursive=True)
        if not yaml_files:
            QMessageBox.warning(
                self, 
                "没有找到规则文件",
                f"在目录 {dir_path} 中没有找到YAML规则文件。\n"
                "请选择包含Semgrep YAML规则文件的目录。"
            )
            return
        
        # 创建进度对话框
        progress = QProgressDialog("正在导入Semgrep规则...", "取消", 0, 100, self)
        progress.setWindowModality(Qt.WindowModality.WindowModal)
        progress.setMinimumDuration(500)  # 显示前等待500毫秒
        progress.setValue(10)
        
        # 创建导入线程
        class ImportThread(QThread):
            import_complete = pyqtSignal(bool, str, int)
            
            def __init__(self, directory):
                super().__init__()
                self.directory = directory
                
            def run(self):
                try:
                    vulndb = VulnerabilityDB()
                    success = vulndb.import_semgrep_rules(self.directory)
                    
                    if success:
                        # 计算导入的规则数
                        total_rules = sum(len(rules) for rules in vulndb.patterns.values())
                        self.import_complete.emit(True, "成功导入Semgrep规则", total_rules)
                    else:
                        self.import_complete.emit(False, "导入规则失败", 0)
                        
                except Exception as e:
                    self.import_complete.emit(False, f"导入过程出错: {str(e)}", 0)
        
        # 创建并启动导入线程
        self.import_thread = ImportThread(dir_path)
        self.import_thread.import_complete.connect(
            lambda success, msg, count: self.import_completed(success, msg, count, progress)
        )
        self.import_thread.start()
        
        # 更新进度
        progress.setValue(20)
    
    def import_semgrep_from_url(self):
        """从URL导入Semgrep规则"""
        url, ok = QInputDialog.getText(
            self,
            "输入Semgrep规则URL",
            "请输入Semgrep规则URL(GitHub raw文件或ZIP文件链接):",
            QLineEdit.EchoMode.Normal,
            "https://raw.githubusercontent.com/returntocorp/semgrep-rules/master/..."
        )
        
        if not ok or not url:
            return
            
        # 验证URL
        if not url.startswith("http"):
            QMessageBox.warning(
                self,
                "无效URL",
                "请输入有效的URL，例如 https://..."
            )
            return
        
        # 创建进度对话框
        progress = QProgressDialog("正在从URL导入Semgrep规则...", "取消", 0, 100, self)
        progress.setWindowModality(Qt.WindowModality.WindowModal)
        progress.setMinimumDuration(500)  # 显示前等待500毫秒
        progress.setValue(10)
        
        # 创建导入线程
        class ImportUrlThread(QThread):
            import_complete = pyqtSignal(bool, str, int)
            
            def __init__(self, url):
                super().__init__()
                self.url = url
                
            def run(self):
                try:
                    vulndb = VulnerabilityDB()
                    success = vulndb.import_semgrep_from_url(self.url)
                    
                    if success:
                        # 计算导入的规则数
                        total_rules = sum(len(rules) for rules in vulndb.patterns.values())
                        self.import_complete.emit(True, "成功从URL导入规则", total_rules)
                    else:
                        self.import_complete.emit(False, "从URL导入规则失败", 0)
                        
                except Exception as e:
                    self.import_complete.emit(False, f"导入过程出错: {str(e)}", 0)
        
        # 创建并启动导入线程
        self.import_url_thread = ImportUrlThread(url)
        self.import_url_thread.import_complete.connect(
            lambda success, msg, count: self.import_completed(success, msg, count, progress)
        )
        self.import_url_thread.start()
        
        # 更新进度
        progress.setValue(20)
    
    def import_from_github(self):
        """从GitHub仓库导入Semgrep规则"""
        import_dialog = QDialog(self)
        import_dialog.setWindowTitle("从GitHub导入规则")
        import_dialog.resize(500, 250)
        
        layout = QVBoxLayout(import_dialog)
        
        # 创建表单布局
        form_layout = QFormLayout()
        
        # 添加GitHub仓库URL输入框
        repo_url_edit = QLineEdit()
        repo_url_edit.setText("https://github.com/semgrep/semgrep-rules")
        form_layout.addRow("GitHub仓库URL:", repo_url_edit)
        
        # 添加分支名称输入框
        branch_edit = QLineEdit()
        branch_edit.setText("develop")
        form_layout.addRow("分支名称:", branch_edit)
        
        # 添加语言选择框
        languages_edit = QLineEdit()
        languages_edit.setPlaceholderText("可选，逗号分隔，例如: python,javascript,java")
        form_layout.addRow("要导入的语言:", languages_edit)
        
        layout.addLayout(form_layout)
        
        # 添加帮助文本
        help_text = QLabel("从GitHub导入Semgrep规则说明:\n"
                        "1. 默认URL已设为semgrep-rules官方仓库\n"
                        "2. 可以指定仓库分支，默认为'develop'\n"
                        "3. 语言字段为可选，不填写则导入全部语言规则\n"
                        "4. 导入过程可能需要几分钟，请耐心等待")
        help_text.setWordWrap(True)
        help_text.setStyleSheet("color: #555; font-style: italic; background: #f8f8f8; padding: 8px; border-radius: 4px;")
        layout.addWidget(help_text)
        
        # 添加按钮
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | 
                                     QDialogButtonBox.StandardButton.Cancel)
        button_box.accepted.connect(import_dialog.accept)
        button_box.rejected.connect(import_dialog.reject)
        layout.addWidget(button_box)
        
        if import_dialog.exec() != QDialog.DialogCode.Accepted:
            return
            
        # 获取输入值
        repo_url = repo_url_edit.text().strip()
        branch = branch_edit.text().strip()
        languages_text = languages_edit.text().strip()
        
        languages = None
        if languages_text:
            languages = [lang.strip() for lang in languages_text.split(',') if lang.strip()]
            
        # 验证URL
        if not repo_url.startswith("http"):
            QMessageBox.warning(
                self,
                "无效URL",
                "请输入有效的GitHub仓库URL，例如 https://github.com/username/repo"
            )
            return
        
        # 创建进度对话框
        progress = QProgressDialog("正在从GitHub导入规则...", "取消", 0, 100, self)
        progress.setWindowModality(Qt.WindowModality.WindowModal)
        progress.setMinimumDuration(500)
        progress.setValue(10)
        
        # 创建导入线程
        class ImportGitHubThread(QThread):
            import_complete = pyqtSignal(bool, str, int)
            
            def __init__(self, repo_url, branch, languages):
                super().__init__()
                self.repo_url = repo_url
                self.branch = branch
                self.languages = languages
                
            def run(self):
                try:
                    # 显示开始克隆信息
                    self.import_complete.emit(True, "正在克隆仓库，这可能需要几分钟...", 0)
                    
                    vulndb = VulnerabilityDB()
                    success, rule_count = vulndb.import_github_rules(self.repo_url, self.branch, self.languages)
                    
                    if success:
                        self.import_complete.emit(True, f"成功从GitHub导入规则", rule_count)
                    else:
                        self.import_complete.emit(False, "从GitHub导入规则失败", 0)
                        
                except Exception as e:
                    self.import_complete.emit(False, f"导入过程出错: {str(e)}", 0)
        
        # 创建并启动导入线程
        self.github_thread = ImportGitHubThread(repo_url, branch, languages)
        
        # 连接信号，处理进度更新
        def on_progress_update(success, msg, count):
            if success and count == 0:  # 这是克隆进行中的消息
                progress.setLabelText(msg)
                progress.setValue(30)
            else:
                self.import_completed(success, msg, count, progress)
                
        self.github_thread.import_complete.connect(on_progress_update)
        self.github_thread.start()
        
        # 更新进度
        progress.setValue(20)
    
    def import_completed(self, success: bool, message: str, rule_count: int, progress_dialog: QProgressDialog):
        """导入完成处理
        
        Args:
            success: 是否成功
            message: 消息
            rule_count: 规则数量
            progress_dialog: 进度对话框
        """
        # 关闭进度对话框
        progress_dialog.setValue(100)
        progress_dialog.close()
        
        # 显示结果
        if success:
            QMessageBox.information(
                self,
                "导入成功",
                f"{message}！\n\n"
                f"当前漏洞库包含 {rule_count} 条规则。"
            )
        else:
            QMessageBox.warning(
                self,
                "导入失败",
                message
            )

class ScanThread(QThread):
    """扫描线程"""
    scan_progress = pyqtSignal(str, int)  # 发送消息和进度百分比
    scan_complete = pyqtSignal(object)
    scan_error = pyqtSignal(str)
    
    def __init__(self, scan_type: str, path: str, model_name: str = 'default'):
        """初始化扫描线程"""
        super().__init__()
        self.scan_type = scan_type
        self.path = path
        self.model_name = model_name
        self.result = None
    
    def run(self):
        """运行扫描线程"""
        try:
            scanner = CodeScanner(model_name=self.model_name)
            
            # 将扫描类型转换为小写，并规范化
            scan_type_lower = self.scan_type.lower()
            
            # 检查是否请求中断
            if self.isInterruptionRequested():
                return
                
            if 'file' in scan_type_lower or '文件' in scan_type_lower:
                self.scan_progress.emit(f"正在扫描文件: {self.path}", 0)
                self.result = scanner.scan_file(self.path)
                self.scan_progress.emit("文件扫描完成", 90)
                
            elif 'dir' in scan_type_lower or '目录' in scan_type_lower:
                self.scan_progress.emit(f"正在准备扫描目录: {self.path}", 0)
                
                # 目录扫描过程中可能需要多次检查中断
                # 使用进度回调函数更新进度条
                def progress_update(message, percentage):
                    if self.isInterruptionRequested():
                        return
                    self.scan_progress.emit(message, percentage)
                
                self.result = scanner.scan_directory(self.path, progress_callback=progress_update)
                
                # 再次检查是否请求中断
                if self.isInterruptionRequested():
                    return
                
            elif 'github' in scan_type_lower:
                self.scan_progress.emit(f"正在克隆仓库: {self.path}", 10)
                
                # 创建临时目录
                temp_dir = tempfile.mkdtemp(prefix="codescan_github_")
                
                try:
                    import git
                    git.Repo.clone_from(self.path, temp_dir)
                    
                    # 检查是否请求中断
                    if self.isInterruptionRequested():
                        return
                        
                    self.scan_progress.emit(f"正在扫描仓库内容", 30)
                    
                    # 使用进度回调函数更新进度条
                    def progress_update(message, percentage):
                        if self.isInterruptionRequested():
                            return
                        # 调整百分比，使其在30-95之间
                        adjusted_percentage = 30 + int(percentage * 0.65)
                        self.scan_progress.emit(message, adjusted_percentage)
                    
                    self.result = scanner.scan_directory(temp_dir, progress_callback=progress_update)
                    
                finally:
                    # 清理临时目录
                    import shutil
                    shutil.rmtree(temp_dir, ignore_errors=True)
            else:
                raise ValueError(f"不支持的扫描类型: {self.scan_type}")
            
            # 如果线程被请求中断，不发送完成信号
            if self.isInterruptionRequested():
                return
                
            # 确保结果不为None
            if self.result is None:
                raise RuntimeError("扫描没有返回有效结果")
            
            self.scan_progress.emit("扫描完成，正在生成最终报告...", 98)
            self.scan_complete.emit(self.result)
            
        except Exception as e:
            # 如果线程被请求中断，不发送错误信号
            if self.isInterruptionRequested():
                return
                
            logger.error(f"扫描出错: {str(e)}")
            self.scan_error.emit(str(e))

class MainWindow(QMainWindow):
    """主窗口类"""
    
    # 定义样式常量
    LABEL_STYLE = "font-size: 13px; font-weight: bold; color: #333333;"
    FIELD_STYLE = "font-size: 13px; color: #0066cc;"
    TEXTEDIT_STYLE = """
        QTextEdit {
            font-size: 13px; 
            line-height: 140%; 
            background-color: #f8f8f8; 
            border: 1px solid #ddd;
            border-radius: 4px;
            padding: 5px;
        }
    """
    MARKDOWN_STYLE = """
        QTextBrowser {
            font-size: 13px;
            line-height: 150%;
            background-color: #ffffff;
            border: 1px solid #ddd;
            border-radius: 4px;
            padding: 10px;
        }
        h1, h2, h3 { color: #444; }
        h1 { font-size: 18px; }
        h2 { font-size: 16px; }
        h3 { font-size: 14px; }
        pre { 
            background-color: #f5f5f5; 
            padding: 8px; 
            border-radius: 3px; 
            border: 1px solid #e0e0e0;
        }
        code { 
            font-family: Consolas, Monaco, 'Courier New', monospace; 
            background-color: rgba(175, 184, 193, 0.2);
            padding: 0.2em 0.4em;
            font-size: 0.85em;
            border-radius: 3px;
        }
        table {
            border-collapse: collapse;
            width: 100%;
            margin: 10px 0;
        }
        th, td {
            padding: 8px;
            text-align: left;
            border: 1px solid #ddd;
        }
        th {
            background-color: #f2f2f2;
        }
        tr:nth-child(even) {
            background-color: #f9f9f9;
        }
        hr {
            border: 0;
            height: 1px;
            background: #e1e4e8;
            margin: 1.5em 0;
        }
        blockquote {
            padding: 0 1em;
            color: #6a737d;
            border-left: 0.25em solid #dfe2e5;
            margin: 0.5em 0;
        }
        .severity-critical { color: #d73a49; font-weight: bold; }
        .severity-high { color: #e36209; font-weight: bold; }
        .severity-medium { color: #b08800; font-weight: bold; }
        .severity-low { color: #005cc5; font-weight: bold; }
        .severity-info { color: #22863a; font-weight: bold; }
    """
    
    def __init__(self):
        """初始化主窗口"""
        super().__init__()
        
        # 设置窗口标题和大小
        self.setWindowTitle("代码安全扫描工具")
        self.resize(1024, 768)
        
        # 初始化 UI
        self.init_ui()
        
        # 设置日志记录器
        self.setup_logging()
        
        # 初始化成员变量
        self.scan_thread = None
        self.scan_result = None
        
        # 创建菜单栏
        self.setup_menu()
        
        # 显示状态栏
        self.statusBar().showMessage("就绪")
    
    def create_project_info_tab(self):
        """创建项目信息标签页"""
        # 项目信息标签页
        self.project_info_tab = QWidget()
        self.tabs.addTab(self.project_info_tab, "项目信息")
        
        # 主布局 - 使用垂直分割器
        main_layout = QVBoxLayout(self.project_info_tab)
        main_layout.setSpacing(15)
        main_layout.setContentsMargins(15, 15, 15, 15)
        
        # 创建顶部项目摘要卡片
        summary_card = TechCard("项目概览")
        summary_layout = QVBoxLayout(summary_card)
        summary_layout.setContentsMargins(15, 45, 15, 15)
        
        # 使用表格布局展示项目基本信息
        grid = QGridLayout()
        grid.setVerticalSpacing(10)
        grid.setHorizontalSpacing(20)
        
        # 创建标签
        path_label = QLabel("项目路径:")
        path_label.setStyleSheet(f"font-weight: bold; color: {Theme.TEXT_PRIMARY};")
        files_label = QLabel("文件总数:")
        files_label.setStyleSheet(f"font-weight: bold; color: {Theme.TEXT_PRIMARY};")
        lines_label = QLabel("代码行数:")
        lines_label.setStyleSheet(f"font-weight: bold; color: {Theme.TEXT_PRIMARY};")
        lang_label = QLabel("主要语言:")
        lang_label.setStyleSheet(f"font-weight: bold; color: {Theme.TEXT_PRIMARY};")
        
        # 创建值标签
        self.project_path_label = QLabel("未加载")
        self.project_path_label.setWordWrap(True)
        self.total_files_label = QLabel("未加载")
        self.total_lines_label = QLabel("未加载")
        self.main_language_label = QLabel("未加载")
        
        # 添加到布局
        grid.addWidget(path_label, 0, 0)
        grid.addWidget(self.project_path_label, 0, 1)
        grid.addWidget(files_label, 1, 0)
        grid.addWidget(self.total_files_label, 1, 1)
        grid.addWidget(lines_label, 2, 0)
        grid.addWidget(self.total_lines_label, 2, 1)
        grid.addWidget(lang_label, 3, 0)
        grid.addWidget(self.main_language_label, 3, 1)
        
        # 列宽设置
        grid.setColumnStretch(0, 1)
        grid.setColumnStretch(1, 3)
        
        summary_layout.addLayout(grid)
        main_layout.addWidget(summary_card)
        
        # 创建中部信息区域 - 分为左右两部分
        middle_splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # 左侧 - 语言分布图表
        language_card = TechCard("语言分布")
        language_layout = QVBoxLayout(language_card)
        language_layout.setContentsMargins(15, 45, 15, 15)
        
        # 创建语言分布饼图
        self.language_chart = QChart()
        self.language_chart.setTitle("语言分布")
        self.language_chart.setAnimationOptions(QChart.SeriesAnimations)
        self.language_chart.legend().setAlignment(Qt.AlignmentFlag.AlignRight)
        
        self.language_chart_view = QChartView(self.language_chart)
        self.language_chart_view.setRenderHint(QPainter.Antialiasing)
        language_layout.addWidget(self.language_chart_view)
        
        # 右侧 - 代码统计
        stats_card = TechCard("代码统计")
        stats_layout = QVBoxLayout(stats_card)
        stats_layout.setContentsMargins(15, 45, 15, 15)
        
        # 创建文件类型分布表格
        self.file_types_table = QTableWidget()
        self.file_types_table.setColumnCount(2)
        self.file_types_table.setHorizontalHeaderLabels(["文件类型", "数量"])
        self.file_types_table.horizontalHeader().setStretchLastSection(True)
        stats_layout.addWidget(self.file_types_table)
        
        # 添加左右面板到分割器
        middle_splitter.addWidget(language_card)
        middle_splitter.addWidget(stats_card)
        middle_splitter.setSizes([500, 500])
        
        main_layout.addWidget(middle_splitter)
        
        # 创建项目功能分析卡片
        analysis_card = TechCard("项目功能分析")
        analysis_layout = QVBoxLayout(analysis_card)
        analysis_layout.setContentsMargins(15, 45, 15, 15)
        
        analysis_form = QFormLayout()
        analysis_form.setVerticalSpacing(15)
        
        # 项目类型
        type_label = QLabel("项目类型:")
        type_label.setStyleSheet(f"font-weight: bold; color: {Theme.TEXT_PRIMARY};")
        self.project_type_label = QLabel("未分析")
        analysis_form.addRow(type_label, self.project_type_label)
        
        # 主要功能
        func_label = QLabel("主要功能:")
        func_label.setStyleSheet(f"font-weight: bold; color: {Theme.TEXT_PRIMARY};")
        self.main_functionality_label = QTextEdit()
        self.main_functionality_label.setReadOnly(True)
        self.main_functionality_label.setMaximumHeight(80)
        analysis_form.addRow(func_label, self.main_functionality_label)
        
        # 主要组件
        comp_label = QLabel("主要组件:")
        comp_label.setStyleSheet(f"font-weight: bold; color: {Theme.TEXT_PRIMARY};")
        self.components_label = QTextEdit()
        self.components_label.setReadOnly(True)
        self.components_label.setMaximumHeight(100)
        analysis_form.addRow(comp_label, self.components_label)
        
        # 架构概述
        arch_label = QLabel("架构概述:")
        arch_label.setStyleSheet(f"font-weight: bold; color: {Theme.TEXT_PRIMARY};")
        self.architecture_label = QTextEdit()
        self.architecture_label.setReadOnly(True)
        self.architecture_label.setMaximumHeight(100)
        analysis_form.addRow(arch_label, self.architecture_label)
        
        # 使用场景
        use_label = QLabel("使用场景:")
        use_label.setStyleSheet(f"font-weight: bold; color: {Theme.TEXT_PRIMARY};")
        self.use_cases_label = QTextEdit()
        self.use_cases_label.setReadOnly(True)
        self.use_cases_label.setMaximumHeight(80)
        analysis_form.addRow(use_label, self.use_cases_label)
        
        analysis_layout.addLayout(analysis_form)
        main_layout.addWidget(analysis_card)
        
    def update_project_info(self, result: ScanResult):
        """更新项目信息标签页
        
        Args:
            result: 扫描结果
        """
        # 更新基本信息
        self.project_path_label.setText(result.scan_path)
        
        # 获取统计信息
        stats = result.stats
        total_files = stats.get("total_files", 0)
        total_lines = stats.get("total_lines_of_code", 0)
        languages = stats.get("languages", {})
        file_types = stats.get("file_extensions", {})
        
        # 单文件扫描时的特殊处理
        if result.scan_type.lower() == "file":
            total_files = 1
            total_lines = stats.get("lines_of_code", 0)
            if "language" in stats:
                languages = {stats["language"]: 1}
                file_ext = os.path.splitext(result.scan_path)[1].lower()
                file_types = {file_ext: 1}
        
        # 更新统计信息标签
        self.total_files_label.setText(f"{total_files:,}")
        self.total_lines_label.setText(f"{total_lines:,}")
        
        # 确定主要语言
        main_language = "未知"
        if languages:
            main_language = max(languages.items(), key=lambda x: x[1])[0]
        self.main_language_label.setText(main_language)
        
        # 更新语言分布图表
        self.language_chart.removeAllSeries()
        lang_series = QPieSeries()
        
        # 添加语言数据
        for i, (lang, count) in enumerate(sorted(languages.items(), key=lambda x: x[1], reverse=True)):
            color_index = i % len(Theme.CHART_COLORS)
            slice = lang_series.append(f"{lang} ({count})", count)
            slice.setBrush(QColor(Theme.CHART_COLORS[color_index]))
        
        self.language_chart.addSeries(lang_series)
        lang_series.setLabelsVisible(True)
        
        # 更新文件类型表格
        self.file_types_table.setRowCount(len(file_types))
        for i, (ext, count) in enumerate(sorted(file_types.items(), key=lambda x: x[1], reverse=True)):
            ext_item = QTableWidgetItem(ext if ext else "无扩展名")
            count_item = QTableWidgetItem(str(count))
            self.file_types_table.setItem(i, 0, ext_item)
            self.file_types_table.setItem(i, 1, count_item)
        
        self.file_types_table.resizeColumnsToContents()
        
        # 更新项目功能概述
        project_info = result.project_info
        if not project_info:
            return
            
        # 尝试解析项目分析信息
        try:
            # 项目类型
            if "project_type" in project_info:
                self.project_type_label.setText(project_info["project_type"])
            
            # 主要功能
            if "main_functionality" in project_info:
                self.main_functionality_label.setText(project_info["main_functionality"])
            
            # 主要组件
            if "components" in project_info:
                if isinstance(project_info["components"], list):
                    components_text = "\n".join([f"• {comp}" for comp in project_info["components"]])
                else:
                    components_text = project_info["components"]
                self.components_label.setText(components_text)
            
            # 架构概述
            if "architecture" in project_info:
                self.architecture_label.setText(project_info["architecture"])
                
            # 使用场景
            if "use_cases" in project_info:
                if isinstance(project_info["use_cases"], list):
                    use_cases_text = "\n".join([f"• {case}" for case in project_info["use_cases"]])
                else:
                    use_cases_text = project_info["use_cases"]
                self.use_cases_label.setText(use_cases_text)
                
        except Exception as e:
            logger.error(f"解析项目信息时出错: {str(e)}")
    
    def init_ui(self):
        """初始化界面"""
        # 创建中央Widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 创建主布局
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(15)
        main_layout.setContentsMargins(15, 15, 15, 15)
        
        # 移除顶部header区域
        
        # 创建内容区域分割器 - 允许调整各部分大小
        content_splitter = QSplitter(Qt.Orientation.Vertical)
        content_splitter.setChildrenCollapsible(False) # 防止完全折叠
        
        # 创建扫描配置面板
        config_widget = QWidget()
        scan_config_layout = QVBoxLayout(config_widget)
        scan_config_layout.setContentsMargins(0, 0, 0, 0)
        
        scan_config = TechCard("扫描配置")
        scan_config_layout.addWidget(scan_config)
        
        card_layout = QVBoxLayout(scan_config)
        card_layout.setContentsMargins(20, 45, 20, 20)
        
        # 使用表单布局而不是网格布局，更适合表单项
        scan_form = QFormLayout()
        scan_form.setSpacing(15)
        scan_form.setLabelAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        scan_form.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.ExpandingFieldsGrow)
        
        # 添加扫描类型选择
        scan_type_label = QLabel("扫描类型:")
        scan_type_label.setStyleSheet(f"font-size: 14px; font-weight: bold; color: {Theme.TEXT_PRIMARY};")
        self.scan_type_combo = QComboBox()
        self.scan_type_combo.addItems(["文件", "目录", "GitHub仓库"])
        self.scan_type_combo.currentIndexChanged.connect(self.update_browse_button)
        self.scan_type_combo.setMinimumHeight(35) # 增加高度便于点击
        scan_form.addRow(scan_type_label, self.scan_type_combo)
        
        # 添加路径选择
        path_label = QLabel("扫描路径:")
        path_label.setStyleSheet(f"font-size: 14px; font-weight: bold; color: {Theme.TEXT_PRIMARY};")
        
        # 为路径编辑和浏览按钮创建水平布局
        path_layout = QHBoxLayout()
        path_layout.setSpacing(10)
        
        self.path_edit = QTextEdit()
        self.path_edit.setFixedHeight(60) # 减小一点高度
        self.path_edit.setPlaceholderText("输入文件路径、目录路径或GitHub仓库URL...")
        self.path_edit.setAcceptRichText(False)
        
        browse_button = AnimatedButton("浏览...")
        browse_button.setMinimumHeight(35) # 统一按钮高度
        browse_button.clicked.connect(self.browse_path)
        
        path_layout.addWidget(self.path_edit, 4)
        path_layout.addWidget(browse_button, 1)
        
        scan_form.addRow(path_label, path_layout)
        
        # 添加扫描按钮 - 独立布局以避免挤在一起
        button_layout = QHBoxLayout()
        button_layout.setContentsMargins(0, 10, 0, 0) # 增加顶部间距
        
        scan_button = AnimatedButton("开始扫描")
        scan_button.setMinimumHeight(40)
        scan_button.setMinimumWidth(200) # 设置最小宽度
        scan_button.clicked.connect(self.start_scan)
        
        # 在水平布局中居中按钮
        button_layout.addStretch(1)
        button_layout.addWidget(scan_button)
        button_layout.addStretch(1)
        
        # 添加表单和按钮布局到卡片布局
        card_layout.addLayout(scan_form)
        card_layout.addLayout(button_layout)
        
        # 添加配置面板到分割器
        content_splitter.addWidget(config_widget)
        
        # 创建标签页面板
        tabs_widget = QWidget()
        tabs_layout = QVBoxLayout(tabs_widget)
        tabs_layout.setContentsMargins(0, 0, 0, 0)
        
        # 创建标签页
        self.tabs = QTabWidget()
        self.tabs.setTabPosition(QTabWidget.TabPosition.North) # 确保标签在上方
        self.tabs.setMovable(True) # 允许拖动调整标签顺序
        self.tabs.setDocumentMode(True) # 更现代的外观
        
        # 日志标签页
        self.log_tab = QTextEdit()
        self.log_tab.setReadOnly(True)
        self.log_tab.setLineWrapMode(QTextEdit.LineWrapMode.WidgetWidth)
        self.tabs.addTab(self.log_tab, "日志")
        
        # 结果标签页
        self.result_tab = QTextBrowser()
        self.result_tab.setReadOnly(True)
        self.result_tab.setOpenExternalLinks(True)
        self.result_tab.setStyleSheet(self.MARKDOWN_STYLE)
        self.tabs.addTab(self.result_tab, "扫描结果")
        
        # 详细信息标签页
        self.details_tab = QTextBrowser()
        self.details_tab.setReadOnly(True)
        self.details_tab.setOpenExternalLinks(True)  # 允许打开外部链接
        self.details_tab.setStyleSheet(self.MARKDOWN_STYLE)
        self.tabs.addTab(self.details_tab, "详细信息")
        
        # 创建漏洞列表标签页(原视觉分析标签页)
        self.visual_tab = QWidget()
        visual_layout = QVBoxLayout(self.visual_tab)
        visual_layout.setSpacing(15)
        visual_layout.setContentsMargins(10, 10, 10, 10) # 减小边距，增加可用空间
        
        # 创建可视化面板分割器
        visual_splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # 左侧饼图和雷达图
        left_charts = QWidget()
        left_layout = QVBoxLayout(left_charts)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(10)
        
        # 添加严重性分布饼图
        severity_card = TechCard("漏洞严重性分布")
        severity_layout = QVBoxLayout(severity_card)
        severity_layout.setContentsMargins(15, 45, 15, 15)
        
        self.severity_chart = QChart()
        self.severity_chart.setTitle("漏洞严重性分布")
        self.severity_chart.setAnimationOptions(QChart.SeriesAnimations)
        self.severity_chart.legend().setAlignment(Qt.AlignmentFlag.AlignBottom)
        
        self.severity_chart_view = QChartView(self.severity_chart)
        self.severity_chart_view.setRenderHint(QPainter.Antialiasing)
        severity_layout.addWidget(self.severity_chart_view)
        
        # 添加漏洞类型分布饼图
        type_card = TechCard("漏洞类型分布")
        type_layout = QVBoxLayout(type_card)
        type_layout.setContentsMargins(15, 45, 15, 15)
        
        self.type_chart = QChart()
        self.type_chart.setTitle("漏洞类型分布")
        self.type_chart.setAnimationOptions(QChart.SeriesAnimations)
        self.type_chart.legend().setAlignment(Qt.AlignmentFlag.AlignBottom)
        
        self.type_chart_view = QChartView(self.type_chart)
        self.type_chart_view.setRenderHint(QPainter.Antialiasing)
        type_layout.addWidget(self.type_chart_view)
        
        # 将图表添加到左侧布局
        left_layout.addWidget(severity_card, 1)
        left_layout.addWidget(type_card, 1)
        
        # 右侧漏洞详细列表
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(0, 0, 0, 0)
        
        # 漏洞列表标签页
        issues_card = TechCard("漏洞列表")
        issues_layout = QVBoxLayout(issues_card)
        issues_layout.setContentsMargins(15, 45, 15, 15)
        
        self.issues_table = QTableWidget()
        self.issues_table.setColumnCount(6)  # 文件、行号、严重程度、置信度、描述、CWE ID
        self.issues_table.setHorizontalHeaderLabels(["严重度", "文件", "行号", "描述", "置信度", "CWE ID"])
        self.issues_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.issues_table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.issues_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.issues_table.cellClicked.connect(self.show_issue_details)
        self.issues_table.horizontalHeader().setStretchLastSection(True) # 让最后一列自动拉伸
        self.issues_table.verticalHeader().setVisible(False) # 隐藏垂直表头
        
        # 设置列宽
        self.issues_table.setColumnWidth(0, 80)  # 严重度
        self.issues_table.setColumnWidth(1, 180) # 文件
        self.issues_table.setColumnWidth(2, 60)  # 行号
        self.issues_table.setColumnWidth(3, 250) # 描述
        self.issues_table.setColumnWidth(4, 70)  # 置信度
        self.issues_table.setColumnWidth(5, 80)  # CWE ID
        
        issues_layout.addWidget(self.issues_table)
        right_layout.addWidget(issues_card)
        
        # 将左右图表区域添加到分割器
        visual_splitter.addWidget(left_charts)
        visual_splitter.addWidget(right_panel)
        
        # 添加分割器到视觉分析布局
        visual_layout.addWidget(visual_splitter)
        
        # 添加漏洞列表标签页
        self.tabs.addTab(self.visual_tab, "漏洞列表")
        
        # 添加项目信息标签页
        self.create_project_info_tab()
        
        tabs_layout.addWidget(self.tabs)
        content_splitter.addWidget(tabs_widget)
        
        # 设置分割器的初始大小
        content_splitter.setSizes([200, 600])  # 配置面板较小，内容区域较大
        
        # 将分割器添加到主布局
        main_layout.addWidget(content_splitter, 1) # 设置拉伸因子，使内容区域能自动扩展
        
        # 底部状态面板
        status_panel = QWidget()
        status_panel.setMaximumHeight(50)  # 限制底部面板高度
        status_layout = QHBoxLayout(status_panel)
        status_layout.setContentsMargins(0, 5, 0, 0)
        
        # 进度条 - 使用自定义动画进度条
        self.progress_bar = ModernProgressBar()
        self.progress_bar.setFixedHeight(24)
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setAlignment(Qt.AlignmentFlag.AlignCenter)
        status_layout.addWidget(self.progress_bar, 2)
        
        # 报告按钮布局
        report_layout = QHBoxLayout()
        report_layout.setSpacing(10)
        
        # HTML报告按钮
        html_button = AnimatedButton("生成HTML报告")
        html_button.clicked.connect(lambda: self.generate_report("html"))
        report_layout.addWidget(html_button)
        
        # JSON报告按钮
        json_button = AnimatedButton("生成JSON报告")
        json_button.clicked.connect(lambda: self.generate_report("json"))
        report_layout.addWidget(json_button)
        
        # 文本报告按钮
        text_button = AnimatedButton("生成文本报告")
        text_button.clicked.connect(lambda: self.generate_report("text"))
        report_layout.addWidget(text_button)
        
        status_layout.addLayout(report_layout, 1)
        main_layout.addWidget(status_panel)
        
        # 初始化进度条
        self.progress_bar.setValue(0)
        
        # 调用update_browse_button初始化占位符文本
        self.update_browse_button()
    
    def show_settings(self):
        """显示设置对话框"""
        dialog = APISettingsDialog(self)
        dialog.exec()
    
    def setup_logging(self):
        """设置日志"""
        class TextEditLogger(logging.Handler):
            def __init__(self, text_widget):
                super().__init__()
                self.text_widget = text_widget
                self.text_widget.setReadOnly(True)
                
            def emit(self, record):
                msg = self.format(record)
                self.text_widget.append(msg)
        
        logger_handler = TextEditLogger(self.log_tab)
        logger_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
        logger.addHandler(logger_handler)
        logger.setLevel(logging.INFO)
    
    def update_browse_button(self):
        """根据扫描类型更新浏览按钮功能"""
        scan_type = self.scan_type_combo.currentText().lower()
        if "github" in scan_type:
            self.path_edit.clear()
            self.path_edit.setPlaceholderText("输入GitHub仓库URL，例如: https://github.com/username/repo")
        elif "目录" in scan_type:
            self.path_edit.setPlaceholderText("输入目录路径或点击浏览按钮选择...")
        else:
            self.path_edit.setPlaceholderText("输入文件路径或点击浏览按钮选择...")
            
    def browse_path(self):
        """浏览文件或目录"""
        scan_type = self.scan_type_combo.currentText()
        
        if scan_type == "文件":
            path, _ = QFileDialog.getOpenFileName(
                self, "选择文件", "", "所有文件 (*.*)"
            )
        elif scan_type == "目录":
            path = QFileDialog.getExistingDirectory(
                self, "选择目录", ""
            )
        else:  # GitHub仓库
            self.path_edit.setFocus()
            return
            
        if path:
            self.path_edit.setText(path)
    
    def start_scan(self):
        """开始扫描"""
        if self.scan_thread is not None and self.scan_thread.isRunning():
            QMessageBox.warning(
                self,
                "扫描进行中",
                "已有扫描任务正在执行，请等待完成"
            )
            return
            
        path = self.path_edit.toPlainText().strip()
        if not path:
            QMessageBox.warning(
                self,
                "路径无效",
                "请输入有效的扫描路径"
            )
            return
            
        scan_type = self.scan_type_combo.currentText().lower()
        model_name = "default"  # 使用固定的默认模型
        
        # 检查路径
        if scan_type == "文件" and not os.path.isfile(path):
            QMessageBox.warning(
                self,
                "无效文件",
                f"文件不存在: {path}"
            )
            return
            
        elif scan_type == "目录" and not os.path.isdir(path):
            QMessageBox.warning(
                self,
                "无效目录",
                f"目录不存在: {path}"
            )
            return
        
        elif scan_type == "github仓库":
            # GitHub仓库URL格式简单验证
            if not path.lower().startswith(("http://", "https://")):
                QMessageBox.warning(
                    self,
                    "无效URL",
                    f"请输入有效的GitHub仓库URL"
                )
                return
            
        # 清除之前的结果
        self.result_tab.clear()
        self.details_tab.clear()
        self.issues_table.setRowCount(0)  # 清空漏洞列表
        self.scan_result = None  # 清除之前的结果对象
        
        # 启动扫描线程
        self.scan_thread = ScanThread(scan_type, path, model_name)
        self.scan_thread.scan_progress.connect(self.update_progress)
        self.scan_thread.scan_complete.connect(self.scan_completed)
        self.scan_thread.scan_error.connect(self.scan_error)
        
        self.progress_bar.setValue(0)
        self.progress_bar.setFormat("扫描中 %p%")
        self.scan_thread.start()
        
        logger.info(f"开始{scan_type}扫描: {path}, 使用模型: {model_name}")
    
    def update_progress(self, message: str, percentage: int = None):
        """更新进度信息"""
        # 更新进度条文本
        if percentage is not None:
            self.progress_bar.setValue(percentage)
        self.progress_bar.setFormat(f"{message} %p%")
        self.log_tab.append(message)
    
    def render_markdown(self, text: str) -> str:
        """渲染Markdown为HTML
        
        Args:
            text: Markdown格式的文本
            
        Returns:
            渲染后的HTML
        """
        # 配置Markdown扩展
        extensions = [
            'markdown.extensions.tables',       # 表格支持
            'markdown.extensions.fenced_code',  # 代码块支持
            'markdown.extensions.codehilite',   # 代码高亮
            'markdown.extensions.nl2br',        # 换行支持
            'markdown.extensions.sane_lists',   # 列表支持
        ]
        
        # 渲染Markdown为HTML
        html = markdown.markdown(text, extensions=extensions)
        
        # 添加自定义样式
        styled_html = f"""
        <html>
        <head>
            <style>
                body {{
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, 'Open Sans', 'Helvetica Neue', sans-serif;
                }}
                h1 {{ font-size: 1.4em; margin-top: 0.7em; margin-bottom: 0.5em; color: #1a1a1a; font-weight: 700; }}
                h2 {{ font-size: 1.3em; margin-top: 0.6em; margin-bottom: 0.4em; color: #1a1a1a; font-weight: 700; }}
                h3 {{ font-size: 1.2em; margin-top: 0.5em; margin-bottom: 0.3em; color: #1a1a1a; font-weight: 700; }}
                p {{ margin: 0.5em 0; line-height: 1.4; }}
                ul, ol {{ padding-left: 2em; margin: 0.5em 0; }}
                li {{ margin: 0.3em 0; }}
                pre {{ 
                    background-color: #f6f8fa; 
                    border-radius: 3px;
                    padding: 10px;
                    overflow: auto;
                    font-size: 0.9em;
                    margin: 1em 0;
                }}
                code {{ 
                    font-family: Consolas, Monaco, 'Courier New', monospace; 
                    background-color: rgba(175, 184, 193, 0.2);
                    padding: 0.2em 0.4em;
                    font-size: 0.85em;
                    border-radius: 3px;
                }}
                table {{
                    border-collapse: collapse;
                    width: 100%;
                    margin: 1em 0;
                }}
                th, td {{
                    padding: 8px;
                    text-align: left;
                    border: 1px solid #ddd;
                }}
                th {{
                    background-color: #f2f2f2;
                }}
                tr:nth-child(even) {{
                    background-color: #f9f9f9;
                }}
                hr {{
                    border: 0;
                    height: 1px;
                    background: #e1e4e8;
                    margin: 1.5em 0;
                }}
                blockquote {{
                    padding: 0 1em;
                    color: #6a737d;
                    border-left: 0.25em solid #dfe2e5;
                    margin: 0.5em 0;
                }}
                .severity-critical {{ color: #d73a49; font-weight: bold; }}
                .severity-high {{ color: #e36209; font-weight: bold; }}
                .severity-medium {{ color: #b08800; font-weight: bold; }}
                .severity-low {{ color: #005cc5; font-weight: bold; }}
                .severity-info {{ color: #22863a; font-weight: bold; }}
            </style>
        </head>
        <body>
            {html}
        </body>
        </html>
        """
        
        return styled_html

    def update_severity_chart(self, result: ScanResult):
        """更新严重程度分布图表
        
        Args:
            result: 扫描结果
        """
        # 清除现有系列
        self.severity_chart.removeAllSeries()
        
        # 获取严重度统计
        severity_counts = result.issues_by_severity
        
        # 创建饼图系列
        series = QPieSeries()
        
        # 设置饼图颜色和数据
        severity_colors = {
            "critical": Theme.CRITICAL,
            "high": Theme.HIGH,
            "medium": Theme.MEDIUM,
            "low": Theme.LOW,
            "info": Theme.INFO
        }
        
        severity_names = {
            "critical": "严重",
            "high": "高危",
            "medium": "中危",
            "low": "低危",
            "info": "提示"
        }
        
        # 添加饼图切片
        for severity, count in severity_counts.items():
            if count > 0:
                slice = series.append(severity_names.get(severity, severity), count)
                slice.setBrush(QColor(severity_colors.get(severity, Theme.SECONDARY)))
                slice.setLabelVisible(True)
                slice.setLabelPosition(QPieSlice.LabelPosition.LabelOutside)
                slice.setLabelColor(QColor(Theme.TEXT_PRIMARY))
                slice.setLabelFont(QFont(Theme.FONT_FAMILY, Theme.FONT_SIZE_NORMAL))
        
        # 添加系列到图表
        self.severity_chart.addSeries(series)
        
        # 设置动画效果
        series.setLabelsVisible(True)
        
        # 设置图表主题
        self.severity_chart.setTheme(QChart.ChartTheme.ChartThemeLight)
        
        # 设置动画
        self.severity_chart.setAnimationOptions(QChart.SeriesAnimations)
        
        # 更新图表视图
        self.severity_chart_view.update()
    
    def update_vulnerability_types_chart(self, result: ScanResult):
        """更新漏洞类型分布图表
        
        Args:
            result: 扫描结果
        """
        # 清除现有系列
        self.type_chart.removeAllSeries()
        
        # 收集漏洞类型数据
        # 这里我们基于CWE ID或描述来分类
        type_counts = {}
        
        for issue in result.issues:
            # 尝试使用CWE ID作为类型
            if issue.cwe_id:
                type_name = f"CWE-{issue.cwe_id}"
            else:
                # 如果没有CWE ID，使用描述的前15个字符作为类型
                desc = issue.description.strip()
                type_name = desc[:15] + "..." if len(desc) > 15 else desc
            
            type_counts[type_name] = type_counts.get(type_name, 0) + 1
        
        # 限制类型数量，避免图表过于复杂
        if len(type_counts) > 8:
            # 保留前7个最常见类型，其余归为"其他"
            sorted_types = sorted(type_counts.items(), key=lambda x: x[1], reverse=True)
            top_types = sorted_types[:7]
            other_count = sum(count for _, count in sorted_types[7:])
            
            type_counts = {name: count for name, count in top_types}
            if other_count > 0:
                type_counts["其他"] = other_count
        
        # 创建饼图系列
        series = QPieSeries()
        
        # 设置多彩的饼图
        for i, (type_name, count) in enumerate(type_counts.items()):
            slice = series.append(f"{type_name} ({count})", count)
            color_index = i % len(Theme.CHART_COLORS)
            slice.setBrush(QColor(Theme.CHART_COLORS[color_index]))
            slice.setLabelVisible(True)
        
        # 添加系列到图表
        self.type_chart.addSeries(series)
        
        # 设置动画
        self.type_chart.setAnimationOptions(QChart.SeriesAnimations)
        
        # 更新图表视图
        self.type_chart_view.update()

    def scan_completed(self, result: ScanResult):
        """扫描完成后的处理"""
        # 保存线程引用，稍后释放
        thread = self.scan_thread
        self.scan_thread = None
        self.progress_bar.setValue(100)
        
        # 检查结果是否为None
        if result is None:
            self.progress_bar.setFormat("扫描失败")
            QMessageBox.critical(
                self,
                "扫描失败",
                "扫描过程中出错，未能获取有效结果。"
            )
            logger.error("扫描完成但结果为None")
            return
            
        self.scan_result = result
        self.progress_bar.setFormat("扫描完成")
        
        # 切换到结果标签页
        self.tabs.setCurrentIndex(1)
        
        # 更新结果标签内容
        severity_counts = result.issues_by_severity
        summary = f"""# 扫描结果摘要

- **扫描路径**: {result.scan_path}
- **扫描类型**: {result.scan_type}
- **扫描时间**: {datetime.fromtimestamp(result.timestamp).strftime('%Y-%m-%d %H:%M:%S')}
- **扫描ID**: {result.scan_id}

## 问题统计
- **总计**: {result.total_issues}个问题
- <span class="severity-critical">**严重**</span>: {severity_counts.get('critical', 0)}
- <span class="severity-high">**高危**</span>: {severity_counts.get('high', 0)}
- <span class="severity-medium">**中危**</span>: {severity_counts.get('medium', 0)}
- <span class="severity-low">**低危**</span>: {severity_counts.get('low', 0)}
- <span class="severity-info">**提示**</span>: {severity_counts.get('info', 0)}
"""
        # 渲染并显示结果
        self.result_tab.setHtml(self.render_markdown(summary))
        
        # 更新详情标签内容
        details = "# 问题详情\n\n"
        
        # 更新问题表格
        self.issues_table.setRowCount(len(result.issues))
        
        # 定义严重度颜色映射
        severity_colors = {
            'critical': QColor(Theme.CRITICAL),
            'high': QColor(Theme.HIGH),
            'medium': QColor(Theme.MEDIUM),
            'low': QColor(Theme.LOW),
            'info': QColor(Theme.INFO)
        }
        
        # 严重度名称映射
        severity_names = {
            'critical': '严重',
            'high': '高危',
            'medium': '中危',
            'low': '低危',
            'info': '提示'
        }
        
        for i, issue in enumerate(result.issues):
            # 设置严重度单元格，带有颜色标识
            severity_item = QTableWidgetItem(severity_names.get(issue.severity, issue.severity))
            severity_item.setForeground(severity_colors.get(issue.severity, QColor(Theme.TEXT_PRIMARY)))
            severity_item.setFont(QFont(Theme.FONT_FAMILY, Theme.FONT_SIZE_NORMAL, QFont.Bold))
            self.issues_table.setItem(i, 0, severity_item)
            
            # 设置文件路径
            file_item = QTableWidgetItem(os.path.basename(issue.file_path))
            file_item.setToolTip(issue.file_path)
            self.issues_table.setItem(i, 1, file_item)
            
            # 设置行号
            line_item = QTableWidgetItem(str(issue.line_number) if issue.line_number else "N/A")
            self.issues_table.setItem(i, 2, line_item)
            
            # 设置描述
            desc_item = QTableWidgetItem(issue.description)
            self.issues_table.setItem(i, 3, desc_item)
            
            # 设置置信度
            confidence_item = QTableWidgetItem(issue.confidence)
            self.issues_table.setItem(i, 4, confidence_item)
            
            # 设置CWE ID
            cwe_item = QTableWidgetItem(issue.cwe_id if issue.cwe_id else "N/A")
            self.issues_table.setItem(i, 5, cwe_item)
            
            # 为详情生成问题信息
            details += f"## 问题 {i+1}: {issue.description}\n\n"
            details += f"- **严重度**: {severity_names.get(issue.severity, issue.severity)}\n"
            details += f"- **文件**: `{issue.file_path}`\n"
            details += f"- **行号**: {issue.line_number if issue.line_number else 'N/A'}\n"
            details += f"- **置信度**: {issue.confidence}\n"
            if issue.cwe_id:
                details += f"- **CWE ID**: {issue.cwe_id}\n"
            details += "\n"
            
            if issue.code_snippet:
                details += "### 代码片段\n\n```\n"
                details += issue.code_snippet
                details += "\n```\n\n"
                
            if issue.recommendation:
                details += "### 修复建议\n\n"
                details += issue.recommendation
                details += "\n\n"
                
            details += "---\n\n"
        
        # 设置详情内容
        self.details_tab.setHtml(self.render_markdown(details))
        
        # 更新项目信息标签页
        self.update_project_info(result)
        
        # 更新图表数据
        self.update_severity_chart(result)
        self.update_vulnerability_types_chart(result)
        
        # 添加完成动画效果 - 短暂显示视觉分析标签页
        QTimer.singleShot(1500, lambda: self.tabs.setCurrentIndex(3))
    
    def scan_error(self, error_message: str):
        """扫描出错处理"""
        # 保存线程引用，稍后释放
        thread = self.scan_thread
        self.scan_thread = None
        self.progress_bar.setValue(0)
        self.progress_bar.setFormat("扫描失败")
        
        # 提供友好的错误信息
        friendly_error = error_message
        if "401" in error_message and ("authentication" in error_message.lower() or "api key" in error_message.lower()):
            friendly_error = "API认证失败：您的API密钥无效或已过期。\n请点击「设置」按钮配置有效的API密钥。"
        elif "timeout" in error_message.lower():
            friendly_error = "API请求超时：服务器响应时间过长。\n请检查您的网络连接或考虑配置代理服务器。"
        elif "connection" in error_message.lower():
            friendly_error = "连接失败：无法连接到API服务器。\n请检查您的网络连接和API配置。"
            
        QMessageBox.critical(
            self,
            "扫描失败",
            f"扫描过程出错：\n\n{friendly_error}"
        )
        
        # 确保线程已完成后安全删除
        if thread and thread.isRunning():
            thread.wait()
    
    def generate_report(self, report_format: str):
        """生成报告
        
        Args:
            report_format: 报告格式
        """
        if not hasattr(self, 'scan_result') or not self.scan_result:
            QMessageBox.warning(self, "警告", "没有可用的扫描结果")
            return
            
        # 确定默认扩展名
        if report_format == 'html':
            default_ext = '.html'
        elif report_format == 'json':
            default_ext = '.json'
        else:  # 文本
            default_ext = '.txt'
            
        # 提示用户选择保存位置
        output_path, _ = QFileDialog.getSaveFileName(
            self,
            "保存报告",
            os.path.join(os.path.expanduser("~"), f"codescan_report{default_ext}"),
            f"{report_format.upper()}文件 (*{default_ext});;所有文件 (*.*)"
        )
        
        if not output_path:
            return
            
        # 显示进度对话框
        progress = QProgressDialog("正在生成报告...", "取消", 0, 100, self)
        progress.setWindowTitle("生成报告")
        progress.setWindowModality(Qt.WindowModal)
        progress.show()
        
        try:
            # 生成报告
            generator = get_report_generator(report_format)
            report_path = generator.generate_report(self.scan_result, output_path)
            
            # 关闭进度对话框
            progress.close()
            
            # 显示成功消息
            QMessageBox.information(
                self, 
                "报告生成成功", 
                f"报告已保存到：{report_path}"
            )
            
            # 如果是HTML报告，自动打开
            if report_format == 'html':
                import webbrowser
                webbrowser.open(f"file://{os.path.abspath(report_path)}")
                
        except Exception as e:
            progress.close()
            logger.error(f"生成报告时出错: {str(e)}")
            QMessageBox.critical(self, "错误", f"生成报告时出错: {str(e)}")
    
    def save_report(self):
        """保存报告对话框"""
        if not hasattr(self, 'scan_result') or not self.scan_result:
            QMessageBox.warning(self, "警告", "没有可用的扫描结果")
            return
            
        # 创建对话框
        dialog = QDialog(self)
        dialog.setWindowTitle("保存报告")
        dialog.resize(400, 150)
        
        # 设置布局
        layout = QVBoxLayout(dialog)
        
        # 添加说明标签
        label = QLabel("选择报告格式：")
        layout.addWidget(label)
        
        # 添加格式选择下拉框
        format_combo = QComboBox()
        format_combo.addItems(["HTML报告", "JSON报告", "文本报告"])
        layout.addWidget(format_combo)
        
        # 添加按钮
        button_layout = QHBoxLayout()
        save_button = QPushButton("保存")
        cancel_button = QPushButton("取消")
        button_layout.addWidget(save_button)
        button_layout.addWidget(cancel_button)
        layout.addLayout(button_layout)
        
        # 绑定事件
        save_button.clicked.connect(dialog.accept)
        cancel_button.clicked.connect(dialog.reject)
        
        # 显示对话框
        result = dialog.exec_()
        
        if result == QDialog.Accepted:
            # 根据选择的格式生成报告
            format_name = format_combo.currentText()
            formats = {
                "HTML报告": "html",
                "JSON报告": "json",
                "文本报告": "text"
            }
            
            self.generate_report(formats[format_name])

    def show_rule_manager(self):
        """显示规则管理器"""
        try:
            # 创建规则管理器对话框
            dialog = QDialog(self)
            dialog.setWindowTitle("规则管理")
            dialog.setMinimumSize(800, 600)
            
            layout = QVBoxLayout(dialog)
            
            # 创建规则管理器
            manager = RuleManagerWidget(dialog)
            layout.addWidget(manager)
            
            # 底部按钮区
            button_box = QDialogButtonBox(QDialogButtonBox.Close)
            button_box.rejected.connect(dialog.close)
            layout.addWidget(button_box)
            
            # 显示对话框
            dialog.exec_()
            
        except Exception as e:
            QMessageBox.warning(
                self,
                "错误",
                f"打开规则管理器失败: {str(e)}"
            )

    def show_issue_details(self, row, column):
        """显示漏洞详情
        
        Args:
            row: 行索引
            column: 列索引
        """
        # 检查是否有扫描结果
        if not hasattr(self, 'scan_result') or not self.scan_result:
            QMessageBox.warning(self, "警告", "没有可用的扫描结果")
            return
            
        # 获取点击的漏洞
        issue = self.scan_result.issues[row]
        
        # 构建详细信息
        details = f"# {issue.description}\n\n"
        
        if issue.severity:
            severity_label = self.get_severity_label(issue.severity)
            details += f"**严重程度:** {severity_label}\n\n"
        
        if issue.location:
            details += f"**位置:** `{issue.location}`\n\n"
            
        if issue.description:
            details += f"## 问题描述\n{issue.description}\n\n"
            
        if issue.cwe_id:
            details += f"**CWE ID:** [{issue.cwe_id}](https://cwe.mitre.org/data/definitions/{issue.cwe_id.replace('CWE-', '')}.html)\n\n"
            
        if issue.owasp_category:
            details += f"**OWASP 类别:** {issue.owasp_category}\n\n"
            
        if issue.vulnerability_type:
            details += f"**漏洞类型:** {issue.vulnerability_type}\n\n"
            
        if issue.code_snippet:
            details += f"\n## 代码片段\n```\n{issue.code_snippet}\n```\n"
            
        if issue.recommendation:
            details += f"\n## 修复建议\n{issue.recommendation}\n"
        
        # 设置详细信息并切换到详情标签页
        self.details_tab.setHtml(self.render_markdown(details))
        self.tabs.setCurrentWidget(self.details_tab)

    def setup_menu(self):
        """设置菜单栏和工具栏"""
        # 创建菜单栏
        menubar = self.menuBar()
        
        # 文件菜单
        file_menu = menubar.addMenu("文件")
        
        # 保存报告动作
        save_report_action = QAction("保存报告", self)
        save_report_action.triggered.connect(self.save_report)
        file_menu.addAction(save_report_action)
        
        # 退出动作
        exit_action = QAction("退出", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # 工具菜单
        tools_menu = menubar.addMenu("工具")
        
        # 规则管理器动作
        rule_manager_action = QAction("规则管理", self)
        rule_manager_action.triggered.connect(self.show_rule_manager)
        tools_menu.addAction(rule_manager_action)
        
        # 更新漏洞库动作
        update_vulndb_action = QAction("更新漏洞库", self)
        update_vulndb_action.triggered.connect(self.update_vulndb)
        tools_menu.addAction(update_vulndb_action)
        
        # 添加设置动作到菜单
        settings_action = QAction("设置", self)
        settings_action.triggered.connect(self.show_settings)
        tools_menu.addAction(settings_action)
        
        # 创建工具栏
        toolbar = self.addToolBar("工具栏")
        toolbar.setMovable(False)  # 固定工具栏
        toolbar.setIconSize(QSize(24, 24))  # 设置图标大小
        toolbar.setStyleSheet(f"""
            QToolBar {{
                background-color: {Theme.BACKGROUND};
                border-bottom: 1px solid {Theme.BORDER};
                spacing: 5px;
            }}
            QToolButton {{
                border: none;
                border-radius: 4px;
                padding: 5px;
            }}
            QToolButton:hover {{
                background-color: {Theme.HOVER_BACKGROUND};
            }}
            QToolButton:pressed {{
                background-color: {Theme.PRIMARY_LIGHT};
            }}
        """)
        
        # 添加设置按钮到工具栏
        settings_toolbar_action = QAction("设置", self)
        settings_toolbar_action.setIcon(self.get_icon("settings"))
        settings_toolbar_action.setToolTip("打开设置对话框")
        settings_toolbar_action.triggered.connect(self.show_settings)
        toolbar.addAction(settings_toolbar_action)
        
        # 添加规则管理按钮到工具栏
        rule_manager_toolbar_action = QAction("规则管理", self)
        rule_manager_toolbar_action.setIcon(self.get_icon("rules"))
        rule_manager_toolbar_action.setToolTip("管理扫描规则")
        rule_manager_toolbar_action.triggered.connect(self.show_rule_manager)
        toolbar.addAction(rule_manager_toolbar_action)
        
        # 添加更新漏洞库按钮
        update_vulndb_toolbar_action = QAction("更新漏洞库", self)
        update_vulndb_toolbar_action.setIcon(self.get_icon("update"))
        update_vulndb_toolbar_action.setToolTip("更新漏洞库")
        update_vulndb_toolbar_action.triggered.connect(self.update_vulndb)
        toolbar.addAction(update_vulndb_toolbar_action)
    
    def get_icon(self, icon_name):
        """获取图标
        
        Args:
            icon_name: 图标名称
            
        Returns:
            QIcon对象
        """
        # 使用内置图标
        if icon_name == "settings":
            return self.style().standardIcon(QStyle.StandardPixmap.SP_FileDialogDetailedView)
        elif icon_name == "rules":
            return self.style().standardIcon(QStyle.StandardPixmap.SP_FileDialogListView)
        elif icon_name == "update":
            return self.style().standardIcon(QStyle.StandardPixmap.SP_BrowserReload)
        else:
            # 默认图标
            return self.style().standardIcon(QStyle.StandardPixmap.SP_FileIcon)

    def update_vulndb(self):
        """更新漏洞库"""
        from .vulndb import VulnerabilityDB
        
        # 创建进度对话框
        progress_dialog = QProgressDialog("正在更新漏洞库...", "取消", 0, 0, self)
        progress_dialog.setWindowTitle("更新漏洞库")
        progress_dialog.setWindowModality(Qt.WindowModality.WindowModal)
        progress_dialog.setMinimumDuration(0)
        progress_dialog.setValue(0)
        progress_dialog.setAutoClose(False)
        progress_dialog.show()
        
        # 创建更新线程
        class UpdateThread(QThread):
            update_success = pyqtSignal(bool, str)
            
            def run(self):
                try:
                    vulndb = VulnerabilityDB()
                    success = vulndb.update()
                    
                    if success:
                        self.update_success.emit(True, "漏洞库更新成功！")
                    else:
                        self.update_success.emit(False, "漏洞库更新失败，请检查网络连接和配置。")
                except Exception as e:
                    self.update_success.emit(False, f"更新漏洞库时出错: {str(e)}")
        
        # 创建并启动线程
        self.update_thread = UpdateThread()
        self.update_thread.update_success.connect(
            lambda success, msg: self.update_vulndb_completed(success, msg, progress_dialog)
        )
        self.update_thread.start()
    
    def update_vulndb_completed(self, success: bool, message: str, progress_dialog: QProgressDialog):
        """漏洞库更新完成处理
        
        Args:
            success: 是否成功
            message: 更新消息
            progress_dialog: 进度对话框
        """
        # 关闭进度对话框
        if progress_dialog:
            progress_dialog.close()
        
        # 显示结果消息
        if success:
            QMessageBox.information(self, "更新成功", message)
        else:
            QMessageBox.warning(self, "更新失败", message)
        
        # 安全处理线程
        if hasattr(self, 'update_thread'):
            self.update_thread.wait()
            self.update_thread = None

def main(app=None):
    """主函数，启动GUI界面
    
    Args:
        app: 可选的QApplication实例，如果为None则创建新的实例
        
    Returns:
        退出代码
    """
    # 确保我们有一个应用程序实例
    if app is None:
        app = QApplication(sys.argv)
        apply_style(app)  # 应用样式
    
    try:
        # 创建并显示主窗口
        main_window = MainWindow()
        main_window.show()
        
        # 启动事件循环
        return app.exec_()
    except Exception as e:
        logger.error(f"启动GUI时出错: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1