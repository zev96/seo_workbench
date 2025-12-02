"""
AI 内容改写对话框（支持多列选择）
"""
from typing import List, Dict, Optional
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, 
    QLabel, QPlainTextEdit, QWidget, QListWidgetItem
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from qfluentwidgets import (
    LineEdit, SpinBox, ComboBox, PushButton, PrimaryPushButton,
    PlainTextEdit, MessageBox, InfoBar, InfoBarPosition,
    FluentIcon as FIF, ProgressRing, BodyLabel, ListWidget, CheckBox, RadioButton
)
from loguru import logger

from ...config.settings import ProfileConfig
from ...ai.api_client import AIClient


class AIRewriteWorker(QThread):
    """AI 改写工作线程（支持多列）"""
    
    progress = pyqtSignal(str, int, int)  # 状态信息, 当前进度, 总数
    finished = pyqtSignal(dict)  # 改写结果字典 {列索引: [内容列表]}
    error = pyqtSignal(str)  # 错误信息
    
    def __init__(self, ai_client: AIClient, columns_data: Dict[int, List[str]], 
                 rewrite_count: int, is_simple_mode: bool, rewrite_style: str = None, 
                 prompt_template: str = None):
        """
        Args:
            ai_client: AI 客户端
            columns_data: {列索引: [原始内容列表], ...}
            rewrite_count: 每列生成数量
            is_simple_mode: 是否为快捷模式
            rewrite_style: 改写风格（快捷模式使用）
            prompt_template: Prompt 模板（高级模式使用）
        """
        super().__init__()
        self.ai_client = ai_client
        self.columns_data = columns_data
        self.rewrite_count = rewrite_count
        self.is_simple_mode = is_simple_mode
        self.rewrite_style = rewrite_style
        self.prompt_template = prompt_template
        self._is_cancelled = False
        
    def run(self):
        """执行改写任务"""
        try:
            result_dict = {}
            total_columns = len(self.columns_data)
            current_column_index = 0
            
            # 计算总任务数
            total_tasks = total_columns * self.rewrite_count
            completed_tasks = 0
            
            # 对每个列分别改写
            for col_idx, original_contents in self.columns_data.items():
                if self._is_cancelled:
                    break
                
                current_column_index += 1
                self.progress.emit(
                    f"正在改写第 {col_idx + 1} 列... ({current_column_index}/{total_columns})",
                    completed_tasks,
                    total_tasks
                )
                
                rewritten_list = []
                
                # 为该列生成指定数量的内容
                for i in range(self.rewrite_count):
                    if self._is_cancelled:
                        break
                    
                    # 随机选择一个原始内容作为基础
                    import random
                    base_content = random.choice(original_contents)
                    
                    # 根据模式构建 Prompt
                    if self.is_simple_mode:
                        # 快捷模式：使用预设模板 + 风格
                        default_template = """请对以下内容进行改写，要求：
1. {style}
2. 保持内容的核心意思不变
3. 直接输出改写后的内容，不要添加任何解释
4. 不要输出序号或标记

原始内容：
{content}

改写后的内容："""
                        prompt = default_template.replace("{style}", self.rewrite_style)
                        prompt = prompt.replace("{content}", base_content)
                    else:
                        # 高级模式：使用用户自定义模板
                        prompt = self.prompt_template.replace("{content}", base_content)
                    
                    # 调用 AI
                    result = self.ai_client.generate_text(prompt)
                    if result and result.strip():
                        rewritten_list.append(result.strip())
                    
                    # 更新进度
                    completed_tasks += 1
                    self.progress.emit(
                        f"正在改写第 {col_idx + 1} 列... ({current_column_index}/{total_columns})",
                        completed_tasks,
                        total_tasks
                    )
                
                # 保存该列的结果
                if rewritten_list:
                    result_dict[col_idx] = rewritten_list
            
            self.finished.emit(result_dict)
            
        except Exception as e:
            logger.error(f"AI 改写失败: {e}")
            self.error.emit(str(e))
    
    def cancel(self):
        """取消任务"""
        self._is_cancelled = True


class ColumnCheckBoxItem(QWidget):
    """带复选框的列选择项"""
    
    def __init__(self, col_index: int, col_type: str, content_count: int, parent=None):
        super().__init__(parent)
        self.col_index = col_index
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 4, 8, 4)
        
        # 复选框
        self.checkbox = CheckBox(self)
        layout.addWidget(self.checkbox)
        
        # 列信息标签
        info_text = f"第 {col_index + 1} 列 ({col_type}) - {content_count} 个内容"
        self.label = BodyLabel(info_text, self)
        layout.addWidget(self.label)
        
        layout.addStretch()
    
    def is_checked(self) -> bool:
        """是否选中"""
        return self.checkbox.isChecked()
    
    def set_checked(self, checked: bool):
        """设置选中状态"""
        self.checkbox.setChecked(checked)


class AIRewriteDialog(QDialog):
    """AI 内容改写对话框（支持多列选择）"""
    
    def __init__(self, config: ProfileConfig, grid_data: List[List[str]], parent=None):
        super().__init__(parent)
        self.config = config
        self.grid_data = grid_data  # 完整的网格数据
        self.rewritten_results: Dict[int, List[str]] = {}  # {列索引: [内容列表]}
        self.worker = None
        self._init_ui()
        
    def _init_ui(self):
        """初始化界面"""
        self.setWindowTitle("AI 内容改写")
        self.setMinimumSize(800, 700)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        
        # === 提示说明 ===
        hint_label = BodyLabel("💡 提示：可勾选多个列进行批量改写。AI 将基于每列的现有内容生成新变体，并分别追加到各列底部。")
        hint_label.setWordWrap(True)
        hint_label.setStyleSheet("color: #666; padding: 10px; background: #f5f5f5; border-radius: 6px;")
        layout.addWidget(hint_label)
        
        # === 列选择区 ===
        column_select_label = QLabel("选择要改写的列（可多选）:")
        column_select_label.setStyleSheet("font-weight: bold;")
        layout.addWidget(column_select_label)
        
        # 列表
        self.column_list = ListWidget()
        self.column_list.setFixedHeight(180)
        self._populate_column_list()
        layout.addWidget(self.column_list)
        
        # 快捷按钮
        quick_btn_layout = QHBoxLayout()
        quick_btn_layout.addStretch()
        
        self.select_all_btn = PushButton("全选", self)
        self.select_all_btn.clicked.connect(self._select_all_columns)
        quick_btn_layout.addWidget(self.select_all_btn)
        
        self.deselect_all_btn = PushButton("取消全选", self)
        self.deselect_all_btn.clicked.connect(self._deselect_all_columns)
        quick_btn_layout.addWidget(self.deselect_all_btn)
        
        layout.addLayout(quick_btn_layout)
        
        # === 设置区 ===
        settings_widget = QWidget()
        settings_layout = QFormLayout(settings_widget)
        settings_layout.setSpacing(10)
        
        # 每列生成数量
        self.count_spin = SpinBox()
        self.count_spin.setRange(1, 500)
        self.count_spin.setValue(20)
        settings_layout.addRow("每列生成数量:", self.count_spin)
        
        layout.addWidget(settings_widget)
        
        # === 改写模式选择 ===
        mode_label = QLabel("改写模式:")
        mode_label.setStyleSheet("font-weight: bold; margin-top: 5px;")
        layout.addWidget(mode_label)
        
        # 模式选择单选按钮组
        mode_widget = QWidget()
        mode_layout = QVBoxLayout(mode_widget)
        mode_layout.setContentsMargins(0, 0, 0, 0)
        mode_layout.setSpacing(15)
        
        # 快捷模式
        self.mode_radio_simple = RadioButton("快捷模式（使用预设风格）", self)
        self.mode_radio_simple.setChecked(True)  # 默认选中
        self.mode_radio_simple.toggled.connect(self._on_mode_changed)
        mode_layout.addWidget(self.mode_radio_simple)
        
        # 快捷模式区域
        self.simple_mode_widget = QWidget()
        simple_mode_layout = QVBoxLayout(self.simple_mode_widget)
        simple_mode_layout.setContentsMargins(30, 5, 0, 5)
        simple_mode_layout.setSpacing(8)
        
        # 改写风格下拉框
        style_label = QLabel("改写风格:")
        simple_mode_layout.addWidget(style_label)
        
        self.style_combo = ComboBox()
        self.style_combo.addItems([
            "保持原意，换种表达",
            "更专业正式",
            "更通俗易懂",
            "更简洁精炼",
            "更详细丰富",
            "更吸引人"
        ])
        self.style_combo.setCurrentIndex(0)
        simple_mode_layout.addWidget(self.style_combo)
        
        # 提示文字
        simple_hint = BodyLabel("💡 AI 将使用预设模板配合您选择的风格进行改写")
        simple_hint.setStyleSheet("color: #888; font-size: 12px;")
        simple_mode_layout.addWidget(simple_hint)
        
        mode_layout.addWidget(self.simple_mode_widget)
        
        # 高级模式
        self.mode_radio_advanced = RadioButton("高级模式（自定义 Prompt）", self)
        self.mode_radio_advanced.toggled.connect(self._on_mode_changed)
        mode_layout.addWidget(self.mode_radio_advanced)
        
        # 高级模式区域
        self.advanced_mode_widget = QWidget()
        advanced_mode_layout = QVBoxLayout(self.advanced_mode_widget)
        advanced_mode_layout.setContentsMargins(30, 5, 0, 5)
        advanced_mode_layout.setSpacing(8)
        
        # Prompt 模板输入框
        prompt_label = QLabel("Prompt 模板:")
        advanced_mode_layout.addWidget(prompt_label)
        
        self.prompt_edit = PlainTextEdit()
        self.prompt_edit.setPlaceholderText("请输入自定义 Prompt，使用 {content} 作为原始内容的占位符...")
        self.prompt_edit.setFixedHeight(100)
        advanced_mode_layout.addWidget(self.prompt_edit)
        
        # 提示文字
        advanced_hint = BodyLabel("💡 您可以完全自定义 Prompt，{content} 将被替换为原始内容")
        advanced_hint.setStyleSheet("color: #888; font-size: 12px;")
        advanced_mode_layout.addWidget(advanced_hint)
        
        mode_layout.addWidget(self.advanced_mode_widget)
        
        layout.addWidget(mode_widget)
        
        # 初始化模式状态
        self._on_mode_changed()
        
        # === 开始生成按钮 ===
        generate_btn_layout = QHBoxLayout()
        generate_btn_layout.addStretch()
        
        # 进度环
        self.progress_ring = ProgressRing()
        self.progress_ring.setFixedSize(24, 24)
        self.progress_ring.hide()
        generate_btn_layout.addWidget(self.progress_ring)
        
        self.progress_label = BodyLabel("")
        self.progress_label.hide()
        generate_btn_layout.addWidget(self.progress_label)
        
        self.generate_btn = PushButton(FIF.SYNC, "开始改写")
        self.generate_btn.clicked.connect(self._on_generate)
        generate_btn_layout.addWidget(self.generate_btn)
        
        layout.addLayout(generate_btn_layout)
        
        # === 结果预览区 ===
        preview_label = QLabel("改写结果预览:")
        preview_label.setStyleSheet("font-weight: bold;")
        layout.addWidget(preview_label)
        
        self.result_edit = PlainTextEdit()
        self.result_edit.setPlaceholderText("点击【开始改写】后，AI 生成的新内容将显示在这里...")
        self.result_edit.setReadOnly(True)
        self.result_edit.setFixedHeight(120)
        layout.addWidget(self.result_edit)
        
        # === 确认区 ===
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        self.cancel_btn = PushButton("取消")
        self.cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_btn)
        
        self.confirm_btn = PrimaryPushButton(FIF.ACCEPT, "确认追加")
        self.confirm_btn.clicked.connect(self._on_confirm)
        self.confirm_btn.setEnabled(False)
        button_layout.addWidget(self.confirm_btn)
        
        layout.addLayout(button_layout)
    
    def _populate_column_list(self):
        """填充列选择列表"""
        if not self.grid_data:
            return
        
        max_cols = max(len(row) for row in self.grid_data) if self.grid_data else 0
        
        for col_idx in range(max_cols):
            # 统计该列的有效内容数量
            content_count = 0
            for row in self.grid_data:
                if col_idx < len(row) and row[col_idx] and row[col_idx].strip():
                    content_count += 1
            
            # 只添加有内容的列
            if content_count > 0:
                col_type = self.config.get_column_type(col_idx)
                
                # 创建带复选框的列表项
                item_widget = ColumnCheckBoxItem(col_idx, col_type, content_count)
                
                # 添加到列表
                list_item = QListWidgetItem(self.column_list)
                list_item.setSizeHint(item_widget.sizeHint())
                self.column_list.addItem(list_item)
                self.column_list.setItemWidget(list_item, item_widget)
    
    def _select_all_columns(self):
        """全选"""
        for i in range(self.column_list.count()):
            item = self.column_list.item(i)
            widget = self.column_list.itemWidget(item)
            if widget:
                widget.set_checked(True)
    
    def _deselect_all_columns(self):
        """取消全选"""
        for i in range(self.column_list.count()):
            item = self.column_list.item(i)
            widget = self.column_list.itemWidget(item)
            if widget:
                widget.set_checked(False)
    
    def _get_selected_columns(self) -> Dict[int, List[str]]:
        """
        获取选中的列及其内容
        
        Returns:
            {列索引: [原始内容列表], ...}
        """
        selected_columns = {}
        
        for i in range(self.column_list.count()):
            item = self.column_list.item(i)
            widget = self.column_list.itemWidget(item)
            
            if widget and widget.is_checked():
                col_idx = widget.col_index
                
                # 收集该列的所有有效内容
                contents = []
                for row in self.grid_data:
                    if col_idx < len(row) and row[col_idx] and row[col_idx].strip():
                        contents.append(row[col_idx].strip())
                
                if contents:
                    selected_columns[col_idx] = contents
        
        return selected_columns
    
    def _on_mode_changed(self):
        """改写模式切换"""
        is_simple_mode = self.mode_radio_simple.isChecked()
        
        # 启用/禁用对应区域
        self.simple_mode_widget.setEnabled(is_simple_mode)
        self.advanced_mode_widget.setEnabled(not is_simple_mode)
        
        # 设置视觉效果
        if is_simple_mode:
            self.simple_mode_widget.setStyleSheet("")
            self.advanced_mode_widget.setStyleSheet("color: #999; background-color: #f5f5f5;")
            self.style_combo.setEnabled(True)
            self.prompt_edit.setEnabled(False)
        else:
            self.simple_mode_widget.setStyleSheet("color: #999; background-color: #f5f5f5;")
            self.advanced_mode_widget.setStyleSheet("")
            self.style_combo.setEnabled(False)
            self.prompt_edit.setEnabled(True)
    
    def _get_default_prompt_template(self) -> str:
        """获取默认 Prompt 模板（用于快捷模式）"""
        return """请对以下内容进行改写，要求：
1. {style}
2. 保持内容的核心意思不变
3. 直接输出改写后的内容，不要添加任何解释
4. 不要输出序号或标记

原始内容：
{content}

改写后的内容："""
    
    def _on_generate(self):
        """开始生成"""
        # 获取选中的列
        selected_columns = self._get_selected_columns()
        
        if not selected_columns:
            InfoBar.warning(
                title='请选择列',
                content='请至少勾选一个要改写的列',
                orient=Qt.Orientation.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP_RIGHT,
                duration=3000,
                parent=self
            )
            return
        
        # 检查 API 配置
        if not self.config.api_config.api_key:
            InfoBar.error(
                title='API 未配置',
                content='请先在工具栏配置 API 设置',
                orient=Qt.Orientation.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP_RIGHT,
                duration=3000,
                parent=self
            )
            return
        
        # 禁用按钮
        self.generate_btn.setEnabled(False)
        self.confirm_btn.setEnabled(False)
        self.progress_ring.show()
        self.progress_label.show()
        self.progress_label.setText("准备中...")
        
        # 创建 AI 客户端
        ai_client = AIClient(config=self.config.api_config)
        
        # 获取参数
        rewrite_count = self.count_spin.value()
        is_simple_mode = self.mode_radio_simple.isChecked()
        
        # 根据模式获取参数
        if is_simple_mode:
            # 快捷模式
            rewrite_style = self.style_combo.currentText()
            prompt_template = None
        else:
            # 高级模式
            rewrite_style = None
            prompt_template = self.prompt_edit.toPlainText()
            
            # 验证高级模式下 Prompt 不能为空
            if not prompt_template or not prompt_template.strip():
                InfoBar.warning(
                    title='Prompt 为空',
                    content='高级模式下请输入自定义 Prompt 模板',
                    orient=Qt.Orientation.Horizontal,
                    isClosable=True,
                    position=InfoBarPosition.TOP_RIGHT,
                    duration=3000,
                    parent=self
                )
                self.generate_btn.setEnabled(True)
                self.progress_ring.hide()
                self.progress_label.hide()
                return
        
        # 创建工作线程
        self.worker = AIRewriteWorker(
            ai_client=ai_client,
            columns_data=selected_columns,
            rewrite_count=rewrite_count,
            is_simple_mode=is_simple_mode,
            rewrite_style=rewrite_style,
            prompt_template=prompt_template
        )
        
        self.worker.progress.connect(self._on_progress)
        self.worker.finished.connect(self._on_finished)
        self.worker.error.connect(self._on_error)
        self.worker.start()
        
        logger.info(f"开始 AI 改写：选中 {len(selected_columns)} 列，每列生成 {rewrite_count} 个新内容")
    
    def _on_progress(self, status: str, current: int, total: int):
        """更新进度"""
        if total > 0:
            percentage = int(current / total * 100)
            self.progress_label.setText(f"{status} {percentage}%")
        else:
            self.progress_label.setText(status)
        logger.debug(f"改写进度: {status} ({current}/{total})")
    
    def _on_finished(self, result_dict: Dict[int, List[str]]):
        """生成完成"""
        self.rewritten_results = result_dict
        
        # 显示结果摘要
        summary_lines = []
        total_count = 0
        for col_idx, contents in sorted(result_dict.items()):
            summary_lines.append(f"第 {col_idx + 1} 列: {len(contents)} 个新内容")
            total_count += len(contents)
        
        summary_text = "\n".join(summary_lines)
        summary_text += f"\n\n总计: {total_count} 个新内容"
        
        self.result_edit.setPlainText(summary_text)
        
        # 恢复按钮状态
        self.generate_btn.setEnabled(True)
        self.confirm_btn.setEnabled(True)
        self.progress_ring.hide()
        self.progress_label.hide()
        
        InfoBar.success(
            title='生成成功',
            content=f'已为 {len(result_dict)} 列生成共 {total_count} 个改写内容',
            orient=Qt.Orientation.Horizontal,
            isClosable=True,
            position=InfoBarPosition.TOP_RIGHT,
            duration=2000,
            parent=self
        )
        
        logger.info(f"AI 改写完成：{len(result_dict)} 列，共 {total_count} 个新内容")
    
    def _on_error(self, error_msg: str):
        """生成出错"""
        self.generate_btn.setEnabled(True)
        self.progress_ring.hide()
        self.progress_label.hide()
        
        InfoBar.error(
            title='生成失败',
            content=error_msg,
            orient=Qt.Orientation.Horizontal,
            isClosable=True,
            position=InfoBarPosition.TOP_RIGHT,
            duration=5000,
            parent=self
        )
    
    def _on_confirm(self):
        """确认追加"""
        if not self.rewritten_results:
            InfoBar.warning(
                title='无内容',
                content='没有可追加的内容',
                orient=Qt.Orientation.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP_RIGHT,
                duration=2000,
                parent=self
            )
            return
        
        # 关闭对话框，返回成功
        self.accept()
    
    def get_rewritten_results(self) -> Dict[int, List[str]]:
        """
        获取改写后的结果
        
        Returns:
            {列索引: [内容列表], ...}
        """
        return self.rewritten_results
    
    def closeEvent(self, event):
        """关闭事件"""
        # 如果有正在运行的任务，取消它
        if self.worker and self.worker.isRunning():
            self.worker.cancel()
            self.worker.wait()
        event.accept()
