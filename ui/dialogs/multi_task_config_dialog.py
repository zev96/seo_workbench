"""
多任务配置对话框
支持创建多个对比表任务，每个任务独立配置
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QListWidget, QListWidgetItem, QPushButton,
    QGroupBox, QGridLayout, QScrollArea, QCheckBox,
    QMessageBox, QInputDialog
)
from PyQt6.QtCore import Qt, pyqtSignal
from qfluentwidgets import (
    MessageBoxBase, SubtitleLabel, LineEdit, SpinBox,
    ComboBox, PrimaryPushButton, PushButton, ListWidget,
    FluentIcon as FIF, MessageBox as FMessageBox, InfoBar, InfoBarPosition
)
from loguru import logger
from typing import List, Dict


class MultiTaskConfigDialog(MessageBoxBase):
    """多任务配置对话框"""
    
    def __init__(self, db_manager, category_id: int, parent=None):
        super().__init__(parent)
        self.db_manager = db_manager
        self.category_id = category_id
        self.current_task_id = None
        
        # 加载全局配置
        self.global_config = db_manager.get_config('insert_strategy') or {}
        logger.info(f"加载全局配置: {self.global_config}")
        
        self._init_ui()
        self._load_tasks()
    
    def _init_ui(self):
        """初始化UI"""
        self.titleLabel = SubtitleLabel("对比表任务配置")
        
        main_layout = QVBoxLayout()
        main_layout.setSpacing(15)
        
        # ==================== 全局设置 ====================
        global_group = self._create_global_settings()
        main_layout.addWidget(global_group)
        
        # ==================== 任务列表 + 详细配置 ====================
        content_layout = QHBoxLayout()
        content_layout.setSpacing(15)
        
        # 左侧：任务列表
        left_panel = self._create_task_list_panel()
        content_layout.addWidget(left_panel, 1)
        
        # 右侧：任务详细配置
        right_panel = self._create_task_config_panel()
        content_layout.addWidget(right_panel, 2)
        
        main_layout.addLayout(content_layout)
        
        # 将主布局添加到视图
        self.viewLayout.addLayout(main_layout)
        
        # 设置对话框属性
        self.widget.setMinimumWidth(900)
        self.widget.setMinimumHeight(600)
        
        # 添加按钮
        self.yesButton.setText("保存全部")
        self.cancelButton.setText("取消")
        
        self.yesButton.clicked.connect(self._save_all)
    
    def _create_global_settings(self) -> QGroupBox:
        """创建全局设置区域"""
        group = QGroupBox("全局设置（所有任务共用）")
        group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 2px solid #e0e0e0;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
            }
        """)
        
        layout = QHBoxLayout()
        layout.setSpacing(20)
        
        # 我方品牌
        layout.addWidget(QLabel("我方品牌名称:"))
        self.own_brand_input = LineEdit()
        self.own_brand_input.setText(self.global_config.get('own_brand_name', ''))
        self.own_brand_input.setPlaceholderText("如: CEWEY DS18")
        self.own_brand_input.setFixedWidth(200)
        layout.addWidget(self.own_brand_input)
        
        # 保底竞品数量
        layout.addWidget(QLabel("保底竞品数量:"))
        fallback_count = self.global_config.get('fallback_competitor_count', 2)
        self.fallback_count_spin = SpinBox()
        self.fallback_count_spin.setRange(1, 10)
        self.fallback_count_spin.setValue(fallback_count)
        self.fallback_count_spin.setMinimumWidth(100)
        self.fallback_count_spin.setMaximumWidth(150)
        logger.info(f"保底竞品数量设置为: {fallback_count}")
        layout.addWidget(self.fallback_count_spin)
        
        layout.addStretch()
        
        group.setLayout(layout)
        return group
    
    def _create_task_list_panel(self) -> QWidget:
        """创建任务列表面板"""
        panel = QWidget()
        panel.setFixedWidth(250)
        
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)
        
        # 标题
        title = QLabel("任务列表")
        title.setStyleSheet("font-weight: bold; font-size: 14px;")
        layout.addWidget(title)
        
        # 任务列表
        self.task_list = ListWidget()
        self.task_list.itemClicked.connect(self._on_task_selected)
        layout.addWidget(self.task_list)
        
        # 按钮
        btn_layout = QVBoxLayout()
        btn_layout.setSpacing(8)
        
        self.btn_new_task = PrimaryPushButton(FIF.ADD, "新增任务")
        self.btn_new_task.clicked.connect(self._on_new_task)
        btn_layout.addWidget(self.btn_new_task)
        
        self.btn_delete_task = PushButton(FIF.DELETE, "删除任务")
        self.btn_delete_task.clicked.connect(self._on_delete_task)
        btn_layout.addWidget(self.btn_delete_task)
        
        layout.addLayout(btn_layout)
        
        return panel
    
    def _create_task_config_panel(self) -> QWidget:
        """创建任务配置面板"""
        panel = QWidget()
        
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(15)
        
        # 任务名称
        name_layout = QHBoxLayout()
        name_layout.addWidget(QLabel("任务名称:"))
        self.task_name_input = LineEdit()
        self.task_name_input.setPlaceholderText("如: 价格对比表")
        name_layout.addWidget(self.task_name_input)
        layout.addLayout(name_layout)
        
        # 参数选择区域
        param_group = self._create_parameter_selection()
        layout.addWidget(param_group)
        
        # 插入位置配置
        position_group = self._create_position_config()
        layout.addWidget(position_group)
        
        # 样式配置
        style_group = self._create_style_config()
        layout.addWidget(style_group)
        
        # 保存按钮
        self.btn_save_task = PrimaryPushButton("保存当前任务")
        self.btn_save_task.clicked.connect(self._on_save_current_task)
        layout.addWidget(self.btn_save_task)
        
        return panel
    
    def _create_parameter_selection(self) -> QGroupBox:
        """创建参数选择区域"""
        group = QGroupBox("参数选择")
        group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 2px solid #e0e0e0;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
            }
        """)
        
        layout = QVBoxLayout()
        
        # 按钮行
        btn_layout = QHBoxLayout()
        self.btn_select_all = PushButton("全选")
        self.btn_select_all.clicked.connect(self._on_select_all_params)
        btn_layout.addWidget(self.btn_select_all)
        
        self.btn_deselect_all = PushButton("反选")
        self.btn_deselect_all.clicked.connect(self._on_deselect_all_params)
        btn_layout.addWidget(self.btn_deselect_all)
        btn_layout.addStretch()
        
        layout.addLayout(btn_layout)
        
        # 参数复选框列表（可滚动）
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setMaximumHeight(200)
        
        scroll_widget = QWidget()
        self.param_checkboxes_layout = QVBoxLayout(scroll_widget)
        self.param_checkboxes_layout.setSpacing(5)
        
        # 加载参数列表
        self.param_checkboxes = []
        parameters = self.db_manager.get_parameters_by_category(self.category_id)
        for param in parameters:
            checkbox = QCheckBox(param.name)
            checkbox.setProperty('param_id', param.id)
            self.param_checkboxes.append(checkbox)
            self.param_checkboxes_layout.addWidget(checkbox)
        
        scroll.setWidget(scroll_widget)
        layout.addWidget(scroll)
        
        group.setLayout(layout)
        return group
    
    def _create_position_config(self) -> QGroupBox:
        """创建插入位置配置"""
        group = QGroupBox("插入位置")
        group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 2px solid #e0e0e0;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
            }
        """)
        
        layout = QGridLayout()
        layout.setSpacing(10)
        
        # 插入模式
        layout.addWidget(QLabel("插入模式:"), 0, 0)
        self.insert_mode_combo = ComboBox()
        self.insert_mode_combo.addItems(["按列插入", "智能锚点"])
        self.insert_mode_combo.currentIndexChanged.connect(self._on_insert_mode_changed)
        layout.addWidget(self.insert_mode_combo, 0, 1)
        
        # 按列插入
        self.insert_column_label = QLabel("插入列号:")
        layout.addWidget(self.insert_column_label, 1, 0)
        self.insert_column_spin = SpinBox()
        self.insert_column_spin.setRange(1, 100)  # 支持最多100列
        self.insert_column_spin.setValue(1)
        layout.addWidget(self.insert_column_spin, 1, 1)
        
        # 智能锚点
        self.anchor_text_label = QLabel("锚点文本:")
        layout.addWidget(self.anchor_text_label, 2, 0)
        self.anchor_text_input = LineEdit()
        self.anchor_text_input.setPlaceholderText("如: 参数对比")
        layout.addWidget(self.anchor_text_input, 2, 1)
        
        group.setLayout(layout)
        return group
    
    def _create_style_config(self) -> QGroupBox:
        """创建样式配置"""
        group = QGroupBox("表格样式")
        group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 2px solid #e0e0e0;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
            }
        """)
        
        layout = QGridLayout()
        layout.setSpacing(10)
        
        # 预设风格
        layout.addWidget(QLabel("预设风格:"), 0, 0)
        self.style_preset_combo = ComboBox()
        self.style_preset_combo.addItems(["商务蓝", "清新绿", "强对比黄"])
        layout.addWidget(self.style_preset_combo, 0, 1)
        
        # DPI
        layout.addWidget(QLabel("分辨率(DPI):"), 1, 0)
        self.dpi_combo = ComboBox()
        self.dpi_combo.addItems(["150", "200", "300", "400"])
        self.dpi_combo.setCurrentText("300")
        layout.addWidget(self.dpi_combo, 1, 1)
        
        group.setLayout(layout)
        return group
    
    # ==================== 事件处理 ====================
    
    def _load_tasks(self):
        """加载任务列表"""
        self.task_list.clear()
        tasks = self.db_manager.get_tasks_by_category(self.category_id)
        
        for task in tasks:
            item_text = f"📋 {task.task_name}"
            item = QListWidgetItem(item_text)
            item.setData(Qt.ItemDataRole.UserRole, task.id)
            self.task_list.addItem(item)
    
    def _on_task_selected(self, item):
        """任务被选中"""
        task_id = item.data(Qt.ItemDataRole.UserRole)
        self.current_task_id = task_id
        self._load_task_config(task_id)
    
    def _load_task_config(self, task_id: int):
        """加载任务配置"""
        task_data = self.db_manager.get_task_full_data(task_id)
        if not task_data:
            return
        
        task = task_data['task']
        selected_param_ids = task_data['selected_parameter_ids']
        
        # 任务名称
        self.task_name_input.setText(task.task_name)
        
        # 参数选择
        for checkbox in self.param_checkboxes:
            param_id = checkbox.property('param_id')
            checkbox.setChecked(param_id in selected_param_ids)
        
        # 插入位置
        if task.insert_mode == 'column':
            self.insert_mode_combo.setCurrentIndex(0)
            self.insert_column_spin.setValue(task.insert_column)
        else:
            self.insert_mode_combo.setCurrentIndex(1)
            self.anchor_text_input.setText(task.insert_anchor_text or '')
        
        # 样式
        style_config = task.get_style_dict()
        preset = style_config.get('preset', 'business_blue')
        preset_map = {'business_blue': 0, 'fresh_green': 1, 'high_contrast': 2}
        self.style_preset_combo.setCurrentIndex(preset_map.get(preset, 0))
        self.dpi_combo.setCurrentText(str(style_config.get('dpi', 300)))
    
    def _on_new_task(self):
        """新增任务"""
        name, ok = QInputDialog.getText(self, "新增任务", "请输入任务名称：")
        if ok and name.strip():
            task = self.db_manager.add_task(
                category_id=self.category_id,
                task_name=name.strip(),
                sort_order=self.task_list.count()
            )
            if task:
                InfoBar.success(
                    title="成功",
                    content=f"任务 '{name}' 创建成功",
                    parent=self,
                    position=InfoBarPosition.TOP
                )
                self._load_tasks()
    
    def _on_delete_task(self):
        """删除任务"""
        current_item = self.task_list.currentItem()
        if not current_item:
            InfoBar.warning(
                title="提示",
                content="请先选择一个任务",
                parent=self,
                position=InfoBarPosition.TOP
            )
            return
        
        task_id = current_item.data(Qt.ItemDataRole.UserRole)
        task_name = current_item.text().replace("📋 ", "")
        
        reply = FMessageBox(
            "确认删除",
            f"确定要删除任务 '{task_name}' 吗？",
            self
        ).exec()
        
        if reply:
            if self.db_manager.delete_task(task_id):
                InfoBar.success(
                    title="成功",
                    content=f"任务 '{task_name}' 已删除",
                    parent=self,
                    position=InfoBarPosition.TOP
                )
                self._load_tasks()
                self.current_task_id = None
    
    def _on_save_current_task(self):
        """保存当前任务"""
        if not self.current_task_id:
            InfoBar.warning(
                title="提示",
                content="请先选择一个任务",
                parent=self,
                position=InfoBarPosition.TOP
            )
            return
        
        # 收集配置
        task_name = self.task_name_input.text().strip()
        if not task_name:
            InfoBar.warning(
                title="提示",
                content="请输入任务名称",
                parent=self,
                position=InfoBarPosition.TOP
            )
            return
        
        # 参数选择
        selected_param_ids = [
            cb.property('param_id') 
            for cb in self.param_checkboxes 
            if cb.isChecked()
        ]
        
        if not selected_param_ids:
            InfoBar.warning(
                title="提示",
                content="请至少选择一个参数",
                parent=self,
                position=InfoBarPosition.TOP
            )
            return
        
        # 插入位置
        insert_mode = 'column' if self.insert_mode_combo.currentIndex() == 0 else 'anchor'
        insert_column = self.insert_column_spin.value()
        insert_anchor_text = self.anchor_text_input.text().strip()
        
        # 样式配置
        preset_map = {0: 'business_blue', 1: 'fresh_green', 2: 'high_contrast'}
        style_config = {
            'preset': preset_map[self.style_preset_combo.currentIndex()],
            'dpi': int(self.dpi_combo.currentText()),
            'header_bg_color': '#4472C4',
            'header_text_color': '#FFFFFF',
            'own_brand_bg_color': '#FFF2CC',
            'border_width': 1.5,
            'image_width': 15,
            'font_name': 'Microsoft YaHei',
            'font_size': 10
        }
        
        # 更新任务
        success = self.db_manager.update_task(
            self.current_task_id,
            task_name=task_name,
            insert_mode=insert_mode,
            insert_column=insert_column,
            insert_anchor_text=insert_anchor_text,
            style_config=style_config
        )
        
        if success:
            # 更新参数选择
            self.db_manager.set_task_parameters(self.current_task_id, selected_param_ids)
            
            InfoBar.success(
                title="成功",
                content="任务配置已保存",
                parent=self,
                position=InfoBarPosition.TOP
            )
            self._load_tasks()
    
    def _on_select_all_params(self):
        """全选参数"""
        for checkbox in self.param_checkboxes:
            checkbox.setChecked(True)
    
    def _on_deselect_all_params(self):
        """反选参数"""
        for checkbox in self.param_checkboxes:
            checkbox.setChecked(not checkbox.isChecked())
    
    def _on_insert_mode_changed(self, index):
        """插入模式改变"""
        if index == 0:  # 按列
            self.insert_column_label.setVisible(True)
            self.insert_column_spin.setVisible(True)
            self.anchor_text_label.setVisible(False)
            self.anchor_text_input.setVisible(False)
        else:  # 锚点
            self.insert_column_label.setVisible(False)
            self.insert_column_spin.setVisible(False)
            self.anchor_text_label.setVisible(True)
            self.anchor_text_input.setVisible(True)
    
    def _save_all(self):
        """保存全局配置"""
        # 保存全局配置
        global_config = {
            'own_brand_name': self.own_brand_input.text().strip(),
            'fallback_competitor_count': self.fallback_count_spin.value()
        }
        
        if self.db_manager.save_config('insert_strategy', global_config):
            logger.info("全局配置保存成功")
            self.accept()
        else:
            logger.error("全局配置保存失败")

