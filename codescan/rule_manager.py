"""
规则管理器模块
~~~~~~~~~

用于管理、查看和编辑漏洞规则
"""

import os
import json
import logging
from typing import Dict, List, Any, Optional
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QComboBox, QLabel, QDialog, QFormLayout,
    QLineEdit, QTextEdit, QDialogButtonBox, QMessageBox, QHeaderView,
    QSplitter
)
from PyQt5.QtCore import Qt, pyqtSignal

from .vulndb import VulnerabilityDB

logger = logging.getLogger(__name__)

class RuleDialog(QDialog):
    """规则编辑对话框"""
    
    def __init__(self, parent=None, rule=None, is_new=False):
        """初始化规则编辑对话框
        
        Args:
            parent: 父窗口
            rule: 规则数据
            is_new: 是否新规则
        """
        super().__init__(parent)
        self.rule = rule or {}
        self.is_new = is_new
        
        self.setWindowTitle("编辑规则" if not is_new else "添加新规则")
        self.setup_ui()
        
    def setup_ui(self):
        """设置界面"""
        layout = QVBoxLayout(self)
        
        # 表单布局
        form_layout = QFormLayout()
        
        # ID
        self.id_edit = QLineEdit(self.rule.get('id', ''))
        if not self.is_new:  # 已有规则ID不可修改
            self.id_edit.setReadOnly(True)
        form_layout.addRow("ID:", self.id_edit)
        
        # 名称
        self.name_edit = QLineEdit(self.rule.get('name', ''))
        form_layout.addRow("名称:", self.name_edit)
        
        # 描述
        self.desc_edit = QTextEdit()
        self.desc_edit.setText(self.rule.get('description', ''))
        form_layout.addRow("描述:", self.desc_edit)
        
        # 语言
        self.lang_combo = QComboBox()
        languages = [
            'common', 'python', 'javascript', 'java', 'go', 
            'ruby', 'php', 'c', 'cpp'
        ]
        self.lang_combo.addItems(languages)
        
        # 设置当前语言
        current_langs = self.rule.get('languages', ['common'])
        if current_langs and current_langs[0] in languages:
            self.lang_combo.setCurrentText(current_langs[0])
        
        form_layout.addRow("语言:", self.lang_combo)
        
        # 严重性
        self.severity_combo = QComboBox()
        severities = ['low', 'medium', 'high', 'critical']
        self.severity_combo.addItems(severities)
        
        # 设置当前严重性
        current_severity = self.rule.get('severity', 'medium')
        if current_severity in severities:
            self.severity_combo.setCurrentText(current_severity)
            
        form_layout.addRow("严重性:", self.severity_combo)
        
        # 模式
        self.pattern_edit = QTextEdit()
        self.pattern_edit.setText(self.rule.get('pattern', ''))
        form_layout.addRow("模式:", self.pattern_edit)
        
        # 添加表单
        layout.addLayout(form_layout)
        
        # 按钮
        self.button_box = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        layout.addWidget(self.button_box)
        
        # 调整对话框大小
        self.resize(600, 500)
        
    def get_rule_data(self) -> Dict[str, Any]:
        """获取规则数据
        
        Returns:
            规则数据字典
        """
        rule_data = {
            'id': self.id_edit.text(),
            'name': self.name_edit.text(),
            'description': self.desc_edit.toPlainText(),
            'languages': [self.lang_combo.currentText()],
            'severity': self.severity_combo.currentText(),
            'pattern': self.pattern_edit.toPlainText()
        }
        
        # 添加来源
        if 'source' in self.rule:
            rule_data['source'] = self.rule['source']
        else:
            rule_data['source'] = 'user'
            
        return rule_data
        
    def accept(self) -> None:
        """确认按钮处理"""
        # 验证数据
        if not self.id_edit.text():
            QMessageBox.warning(self, "验证失败", "规则ID不能为空")
            return
            
        if not self.name_edit.text():
            QMessageBox.warning(self, "验证失败", "规则名称不能为空")
            return
            
        if not self.pattern_edit.toPlainText():
            QMessageBox.warning(self, "验证失败", "规则模式不能为空")
            return
            
        super().accept()

class RuleManagerWidget(QWidget):
    """规则管理器窗口部件"""
    
    rule_changed = pyqtSignal()
    
    def __init__(self, parent=None):
        """初始化规则管理器
        
        Args:
            parent: 父窗口
        """
        super().__init__(parent)
        
        self.vulndb = VulnerabilityDB()
        self.current_language = "common"
        
        self.setup_ui()
        self.load_rules()
        
    def setup_ui(self):
        """设置UI"""
        layout = QVBoxLayout(self)
        
        # 顶部工具栏
        top_layout = QHBoxLayout()
        
        # 语言选择
        self.lang_label = QLabel("语言:")
        self.lang_combo = QComboBox()
        self.lang_combo.addItems([
            'common', 'python', 'javascript', 'java', 'go', 
            'ruby', 'php', 'c', 'cpp'
        ])
        self.lang_combo.currentTextChanged.connect(self.language_changed)
        
        top_layout.addWidget(self.lang_label)
        top_layout.addWidget(self.lang_combo)
        top_layout.addStretch(1)
        
        # 按钮
        self.add_btn = QPushButton("添加规则")
        self.add_btn.clicked.connect(self.add_rule)
        
        self.edit_btn = QPushButton("编辑规则")
        self.edit_btn.clicked.connect(self.edit_rule)
        
        self.delete_btn = QPushButton("删除规则")
        self.delete_btn.clicked.connect(self.delete_rule)
        
        self.export_btn = QPushButton("导出规则")
        self.export_btn.clicked.connect(self.export_rules)
        
        top_layout.addWidget(self.add_btn)
        top_layout.addWidget(self.edit_btn)
        top_layout.addWidget(self.delete_btn)
        top_layout.addWidget(self.export_btn)
        
        layout.addLayout(top_layout)
        
        # 规则表格和详情
        splitter = QSplitter(Qt.Orientation.Vertical)
        
        # 规则表格
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["ID", "名称", "严重性", "来源", "描述"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)
        self.table.verticalHeader().setVisible(False)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.table.itemSelectionChanged.connect(self.selection_changed)
        
        splitter.addWidget(self.table)
        
        # 规则详情
        details_widget = QWidget()
        details_layout = QVBoxLayout(details_widget)
        
        self.details_header = QLabel("规则详情")
        details_layout.addWidget(self.details_header)
        
        self.pattern_edit = QTextEdit()
        self.pattern_edit.setReadOnly(True)
        details_layout.addWidget(self.pattern_edit)
        
        splitter.addWidget(details_widget)
        
        layout.addWidget(splitter)
        
        # 设置比例
        splitter.setSizes([300, 200])
        
    def language_changed(self, language):
        """语言变更处理
        
        Args:
            language: 选择的语言
        """
        self.current_language = language
        self.load_rules()
        
    def load_rules(self):
        """加载规则列表"""
        # 清空表格
        self.table.setRowCount(0)
        self.pattern_edit.clear()
        
        # 获取规则
        rules = self.vulndb.patterns.get(self.current_language, [])
        
        # 添加规则到表格
        self.table.setRowCount(len(rules))
        
        for i, rule in enumerate(rules):
            # ID
            id_item = QTableWidgetItem(rule.get('id', ''))
            self.table.setItem(i, 0, id_item)
            
            # 名称
            name_item = QTableWidgetItem(rule.get('name', ''))
            self.table.setItem(i, 1, name_item)
            
            # 严重性
            severity = rule.get('severity', 'medium')
            severity_item = QTableWidgetItem(severity)
            
            # 设置颜色
            if severity == 'critical':
                severity_item.setForeground(Qt.GlobalColor.red)
            elif severity == 'high':
                severity_item.setForeground(Qt.GlobalColor.darkRed)
            elif severity == 'medium':
                severity_item.setForeground(Qt.GlobalColor.darkYellow)
                
            self.table.setItem(i, 2, severity_item)
            
            # 来源
            source_item = QTableWidgetItem(rule.get('source', 'user'))
            self.table.setItem(i, 3, source_item)
            
            # 描述
            desc_item = QTableWidgetItem(rule.get('description', '')[:100])
            self.table.setItem(i, 4, desc_item)
            
        # 调整表格
        self.table.resizeColumnsToContents()
        
    def selection_changed(self):
        """选择变更处理"""
        selected = self.table.selectedItems()
        if not selected:
            self.pattern_edit.clear()
            return
            
        row = selected[0].row()
        rule_id = self.table.item(row, 0).text()
        
        # 查找规则
        rule = None
        for r in self.vulndb.patterns.get(self.current_language, []):
            if r.get('id') == rule_id:
                rule = r
                break
                
        if rule:
            self.details_header.setText(f"规则详情: {rule.get('name')}")
            self.pattern_edit.setText(rule.get('pattern', ''))
        else:
            self.pattern_edit.clear()
            
    def add_rule(self):
        """添加新规则"""
        # 创建新规则ID
        import uuid
        new_id = f"user-{str(uuid.uuid4())[:8]}"
        
        # 创建空规则
        new_rule = {
            'id': new_id,
            'name': '',
            'description': '',
            'languages': [self.current_language],
            'severity': 'medium',
            'pattern': '',
            'source': 'user'
        }
        
        # 打开规则编辑对话框
        dialog = RuleDialog(self, new_rule, is_new=True)
        if dialog.exec_():
            # 获取规则数据
            rule_data = dialog.get_rule_data()
            
            # 添加规则
            lang = rule_data.get('languages', ['common'])[0]
            if lang not in self.vulndb.patterns:
                self.vulndb.patterns[lang] = []
                
            self.vulndb.patterns[lang].append(rule_data)
            
            # 保存规则
            self.vulndb._save_patterns()
            
            # 更新界面
            if lang == self.current_language:
                self.load_rules()
                
            self.rule_changed.emit()
                
    def edit_rule(self):
        """编辑规则"""
        selected = self.table.selectedItems()
        if not selected:
            QMessageBox.information(
                self,
                "未选择规则",
                "请先选择要编辑的规则。"
            )
            return
            
        row = selected[0].row()
        rule_id = self.table.item(row, 0).text()
        
        # 查找规则
        rule = None
        rule_index = -1
        rules = self.vulndb.patterns.get(self.current_language, [])
        
        for i, r in enumerate(rules):
            if r.get('id') == rule_id:
                rule = r
                rule_index = i
                break
                
        if rule is None:
            QMessageBox.warning(
                self,
                "规则不存在",
                "找不到选择的规则。"
            )
            return
            
        # 打开规则编辑对话框
        dialog = RuleDialog(self, rule)
        if dialog.exec_():
            # 获取规则数据
            new_rule_data = dialog.get_rule_data()
            
            # 检查语言是否改变
            old_lang = rule.get('languages', ['common'])[0]
            new_lang = new_rule_data.get('languages', ['common'])[0]
            
            if old_lang != new_lang:
                # 移除旧规则
                self.vulndb.patterns[old_lang].pop(rule_index)
                
                # 添加新规则
                if new_lang not in self.vulndb.patterns:
                    self.vulndb.patterns[new_lang] = []
                
                self.vulndb.patterns[new_lang].append(new_rule_data)
            else:
                # 更新规则
                self.vulndb.patterns[old_lang][rule_index] = new_rule_data
                
            # 保存规则
            self.vulndb._save_patterns()
            
            # 更新界面
            self.load_rules()
            self.rule_changed.emit()
                
    def delete_rule(self):
        """删除规则"""
        selected = self.table.selectedItems()
        if not selected:
            QMessageBox.information(
                self,
                "未选择规则",
                "请先选择要编辑的规则。"
            )
            return
            
        row = selected[0].row()
        rule_id = self.table.item(row, 0).text()
        
        # 确认删除
        reply = QMessageBox.question(
            self,
            "确认删除",
            f"确定要删除规则「{rule_id}」吗？",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.No:
            return
            
        # 查找规则
        rule_index = -1
        rules = self.vulndb.patterns.get(self.current_language, [])
        
        for i, rule in enumerate(rules):
            if rule.get('id') == rule_id:
                rule_index = i
                break
                
        if rule_index >= 0:
            # 删除规则
            self.vulndb.patterns[self.current_language].pop(rule_index)
            
            # 保存规则
            self.vulndb._save_patterns()
            
            # 更新界面
            self.load_rules()
            self.rule_changed.emit()
                
    def export_rules(self):
        """导出规则"""
        from PyQt5.QtWidgets import QFileDialog
        
        # 选择保存路径
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "导出规则",
            "",
            "JSON文件 (*.json)"
        )
        
        if not file_path:
            return
            
        # 如果没有扩展名，添加.json
        if not file_path.endswith('.json'):
            file_path += '.json'
            
        try:
            # 保存规则
            with open(file_path, 'w', encoding='utf-8') as f:
                if self.current_language == "all":
                    # 导出所有规则
                    json.dump(self.vulndb.patterns, f, indent=2, ensure_ascii=False)
                else:
                    # 导出当前语言规则
                    json.dump(
                        {self.current_language: self.vulndb.patterns.get(self.current_language, [])},
                        f,
                        indent=2,
                        ensure_ascii=False
                    )
                    
            QMessageBox.information(
                self,
                "导出成功",
                f"规则已成功导出到 {file_path}"
            )
        except Exception as e:
            QMessageBox.warning(
                self,
                "导出失败",
                f"导出规则时出错: {str(e)}"
            )
