"""
对比表管理界面
左侧类目栏 + 右侧表格编辑区
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QListWidget, QTableWidget,
    QTableWidgetItem, QPushButton, QLabel, QFileDialog, QMenu,
    QHeaderView, QMessageBox, QInputDialog, QSplitter
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QIcon, QColor, QBrush, QAction
from qfluentwidgets import (
    PushButton, PrimaryPushButton, ListWidget,
    ToolButton, FluentIcon as FIF, MessageBox,
    InfoBar, InfoBarPosition, LineEdit
)
from loguru import logger
import openpyxl
from typing import Optional

from ...database.comparison_db_manager import ComparisonDBManager


class ComparisonTableWidget(QWidget):
    """对比表管理主界面"""
    
    def __init__(self):
        super().__init__()
        self.setObjectName("comparison_table_widget")  # 设置对象名称
        self.db_manager = ComparisonDBManager()
        self.current_category_id = None
        self.current_table_data = None
        
        self._init_ui()
        self._load_categories()
    
    def _init_ui(self):
        """初始化UI"""
        # 主布局（水平分割）
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # 使用 Splitter 实现可调节布局
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # ==================== 左侧类目栏 ====================
        left_panel = self._create_left_panel()
        splitter.addWidget(left_panel)
        
        # ==================== 右侧编辑区 ====================
        right_panel = self._create_right_panel()
        splitter.addWidget(right_panel)
        
        # 设置初始宽度比例 (240px : 剩余)
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)
        splitter.setSizes([240, 800])
        
        main_layout.addWidget(splitter)
    
    def _create_left_panel(self) -> QWidget:
        """创建左侧类目栏"""
        panel = QWidget()
        panel.setFixedWidth(240)
        panel.setStyleSheet("""
            QWidget {
                background-color: #f8f8f8;
                border-right: 1px solid #e0e0e0;
            }
        """)
        
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        
        # 标题
        title_label = QLabel("类目列表")
        title_label.setStyleSheet("""
            QLabel {
                font-size: 16px;
                font-weight: bold;
                color: #333;
                background: transparent;
                border: none;
            }
        """)
        layout.addWidget(title_label)
        
        # 类目列表
        self.category_list = ListWidget()
        self.category_list.setStyleSheet("""
            ListWidget {
                background-color: white;
                border: 1px solid #e0e0e0;
                border-radius: 5px;
            }
        """)
        self.category_list.itemClicked.connect(self._on_category_selected)
        layout.addWidget(self.category_list)
        
        # 底部按钮
        btn_layout = QVBoxLayout()
        btn_layout.setSpacing(8)
        
        self.btn_new_category = PrimaryPushButton(FIF.ADD, "新建类目")
        self.btn_new_category.clicked.connect(self._on_new_category)
        btn_layout.addWidget(self.btn_new_category)
        
        self.btn_import_excel = PushButton(FIF.DOCUMENT, "导入 Excel")
        self.btn_import_excel.clicked.connect(self._on_import_excel)
        btn_layout.addWidget(self.btn_import_excel)
        
        self.btn_delete_category = PushButton(FIF.DELETE, "删除类目")
        self.btn_delete_category.clicked.connect(self._on_delete_category)
        btn_layout.addWidget(self.btn_delete_category)
        
        layout.addLayout(btn_layout)
        
        return panel
    
    def _create_right_panel(self) -> QWidget:
        """创建右侧编辑区"""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # 顶部工具栏
        toolbar_layout = QHBoxLayout()
        
        self.btn_save_data = PrimaryPushButton(FIF.SAVE, "保存数据")
        self.btn_save_data.clicked.connect(self._on_save_data)
        toolbar_layout.addWidget(self.btn_save_data)
        
        self.btn_table_style = PushButton(FIF.PALETTE, "表格样式设置")
        self.btn_table_style.clicked.connect(self._on_table_style_settings)
        toolbar_layout.addWidget(self.btn_table_style)
        
        self.btn_insert_strategy = PushButton(FIF.SETTING, "插入策略配置")
        self.btn_insert_strategy.clicked.connect(self._on_insert_strategy_settings)
        toolbar_layout.addWidget(self.btn_insert_strategy)
        
        toolbar_layout.addStretch()
        layout.addLayout(toolbar_layout)
        
        # 表格编辑区
        self.table_widget = QTableWidget()
        self.table_widget.setStyleSheet("""
            QTableWidget {
                background-color: white;
                border: 1px solid #e0e0e0;
                border-radius: 5px;
                gridline-color: #e0e0e0;
            }
            QTableWidget::item {
                padding: 8px;
            }
            QTableWidget::item:selected {
                background-color: #cce8ff;
            }
            QHeaderView::section {
                background-color: #f0f0f0;
                padding: 8px;
                border: none;
                border-right: 1px solid #e0e0e0;
                border-bottom: 1px solid #e0e0e0;
                font-weight: bold;
            }
        """)
        
        # 设置表格属性
        self.table_widget.setAlternatingRowColors(True)
        self.table_widget.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectItems)
        self.table_widget.setEditTriggers(QTableWidget.EditTrigger.DoubleClicked)
        
        # 允许调整列宽
        self.table_widget.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        self.table_widget.horizontalHeader().setStretchLastSection(True)
        
        # 右键菜单
        self.table_widget.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.table_widget.customContextMenuRequested.connect(self._show_context_menu)
        
        # 单元格改变信号
        self.table_widget.itemChanged.connect(self._on_cell_changed)
        
        layout.addWidget(self.table_widget)
        
        # 提示信息
        hint_label = QLabel("提示：双击单元格编辑，拖拽列边界调整宽度，右键查看更多操作")
        hint_label.setStyleSheet("""
            QLabel {
                color: #888;
                font-size: 12px;
            }
        """)
        layout.addWidget(hint_label)
        
        return panel
    
    # ==================== 类目操作 ====================
    
    def _load_categories(self):
        """加载类目列表"""
        self.category_list.clear()
        categories = self.db_manager.get_all_categories()
        
        for category in categories:
            item_text = f"📂 {category.name}"
            self.category_list.addItem(item_text)
            # 将 category.id 存储在 item 的 data 中
            item = self.category_list.item(self.category_list.count() - 1)
            item.setData(Qt.ItemDataRole.UserRole, category.id)
    
    def _on_category_selected(self, item):
        """类目被选中"""
        category_id = item.data(Qt.ItemDataRole.UserRole)
        self.current_category_id = category_id
        self._load_table_data(category_id)
    
    def _on_new_category(self):
        """新建类目"""
        name, ok = QInputDialog.getText(self, "新建类目", "请输入类目名称：")
        if ok and name.strip():
            result = self.db_manager.add_category(name.strip())
            if result:
                InfoBar.success(
                    title="成功",
                    content=f"类目 '{name}' 创建成功",
                    parent=self,
                    position=InfoBarPosition.TOP
                )
                self._load_categories()
            else:
                InfoBar.error(
                    title="失败",
                    content="类目已存在或创建失败",
                    parent=self,
                    position=InfoBarPosition.TOP
                )
    
    def _on_delete_category(self):
        """删除类目"""
        current_item = self.category_list.currentItem()
        if not current_item:
            InfoBar.warning(
                title="提示",
                content="请先选择一个类目",
                parent=self,
                position=InfoBarPosition.TOP
            )
            return
        
        category_id = current_item.data(Qt.ItemDataRole.UserRole)
        category_name = current_item.text().replace("📂 ", "")
        
        # 确认对话框
        reply = MessageBox(
            "确认删除",
            f"确定要删除类目 '{category_name}' 吗？\n这将删除该类目下的所有数据！",
            self
        ).exec()
        
        if reply:
            if self.db_manager.delete_category(category_id):
                InfoBar.success(
                    title="成功",
                    content=f"类目 '{category_name}' 已删除",
                    parent=self,
                    position=InfoBarPosition.TOP
                )
                self._load_categories()
                self.table_widget.clear()
                self.table_widget.setRowCount(0)
                self.table_widget.setColumnCount(0)
                self.current_category_id = None
            else:
                InfoBar.error(
                    title="失败",
                    content="删除失败",
                    parent=self,
                    position=InfoBarPosition.TOP
                )
    
    def _on_import_excel(self):
        """导入 Excel"""
        if not self.current_category_id:
            InfoBar.warning(
                title="提示",
                content="请先选择一个类目",
                parent=self,
                position=InfoBarPosition.TOP
            )
            return
        
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "选择 Excel 文件",
            "",
            "Excel Files (*.xlsx *.xls)"
        )
        
        if not file_path:
            return
        
        try:
            # 读取 Excel
            workbook = openpyxl.load_workbook(file_path)
            sheet = workbook.active
            
            # 转换为二维数组
            data = []
            for row in sheet.iter_rows(values_only=True):
                data.append([str(cell) if cell is not None else "" for cell in row])
            
            # 导入数据库
            if self.db_manager.import_from_excel_data(self.current_category_id, data):
                InfoBar.success(
                    title="成功",
                    content="Excel 数据导入成功",
                    parent=self,
                    position=InfoBarPosition.TOP
                )
                self._load_table_data(self.current_category_id)
            else:
                InfoBar.error(
                    title="失败",
                    content="数据导入失败",
                    parent=self,
                    position=InfoBarPosition.TOP
                )
        
        except Exception as e:
            logger.error(f"Excel 导入失败: {e}")
            InfoBar.error(
                title="错误",
                content=f"Excel 导入失败: {str(e)}",
                parent=self,
                position=InfoBarPosition.TOP
            )
    
    # ==================== 表格操作 ====================
    
    def _load_table_data(self, category_id: int):
        """加载表格数据"""
        try:
            self.current_table_data = self.db_manager.get_table_data(category_id)
            
            brands = self.current_table_data['brands']
            parameters = self.current_table_data['parameters']
            values = self.current_table_data['values']
            
            # 设置表格尺寸（+1 为表头行/列）
            self.table_widget.setRowCount(len(parameters) + 1)
            self.table_widget.setColumnCount(len(brands) + 1)
            
            # 禁用信号防止触发 itemChanged
            self.table_widget.blockSignals(True)
            
            # 设置表头（第一行 - 品牌）
            self.table_widget.setItem(0, 0, QTableWidgetItem("参数/品牌"))
            for col_idx, brand in enumerate(brands):
                item = QTableWidgetItem(brand['name'])
                item.setData(Qt.ItemDataRole.UserRole, brand['id'])
                
                # 我方品牌高亮
                if brand['is_own'] == 1:
                    item.setBackground(QBrush(QColor("#fff3cd")))
                    item.setForeground(QBrush(QColor("#856404")))
                
                self.table_widget.setItem(0, col_idx + 1, item)
            
            # 设置第一列（参数名）
            for row_idx, parameter in enumerate(parameters):
                item = QTableWidgetItem(parameter['name'])
                item.setData(Qt.ItemDataRole.UserRole, parameter['id'])
                item.setBackground(QBrush(QColor("#f0f0f0")))
                self.table_widget.setItem(row_idx + 1, 0, item)
            
            # 填充数值
            for row_idx, parameter in enumerate(parameters):
                for col_idx, brand in enumerate(brands):
                    value = values.get((brand['id'], parameter['id']), "")
                    item = QTableWidgetItem(value)
                    item.setData(Qt.ItemDataRole.UserRole, {
                        'brand_id': brand['id'],
                        'parameter_id': parameter['id']
                    })
                    self.table_widget.setItem(row_idx + 1, col_idx + 1, item)
            
            # 恢复信号
            self.table_widget.blockSignals(False)
            
            logger.info(f"表格数据加载成功: 类目ID={category_id}")
            
        except Exception as e:
            logger.error(f"加载表格数据失败: {e}")
            InfoBar.error(
                title="错误",
                content=f"加载数据失败: {str(e)}",
                parent=self,
                position=InfoBarPosition.TOP
            )
    
    def _on_cell_changed(self, item: QTableWidgetItem):
        """单元格内容改变"""
        # 忽略表头的修改
        row = item.row()
        col = item.column()
        
        if row == 0 or col == 0:
            return
        
        # 获取品牌ID和参数ID
        data = item.data(Qt.ItemDataRole.UserRole)
        if isinstance(data, dict):
            brand_id = data['brand_id']
            parameter_id = data['parameter_id']
            value = item.text()
            
            # 更新到数据库
            self.db_manager.set_value(
                self.current_category_id,
                brand_id,
                parameter_id,
                value
            )
    
    def _on_save_data(self):
        """保存数据（手动触发）"""
        if not self.current_category_id:
            InfoBar.warning(
                title="提示",
                content="请先选择一个类目",
                parent=self,
                position=InfoBarPosition.TOP
            )
            return
        
        InfoBar.success(
            title="成功",
            content="数据已保存",
            parent=self,
            position=InfoBarPosition.TOP
        )
    
    def _show_context_menu(self, pos):
        """显示右键菜单"""
        menu = QMenu(self)
        
        add_row_action = QAction("插入行", self)
        add_row_action.triggered.connect(self._add_row)
        menu.addAction(add_row_action)
        
        add_col_action = QAction("插入列", self)
        add_col_action.triggered.connect(self._add_column)
        menu.addAction(add_col_action)
        
        menu.addSeparator()
        
        del_row_action = QAction("删除行", self)
        del_row_action.triggered.connect(self._delete_row)
        menu.addAction(del_row_action)
        
        del_col_action = QAction("删除列", self)
        del_col_action.triggered.connect(self._delete_column)
        menu.addAction(del_col_action)
        
        menu.addSeparator()
        
        clear_action = QAction("清空内容", self)
        clear_action.triggered.connect(self._clear_cell)
        menu.addAction(clear_action)
        
        menu.exec(self.table_widget.viewport().mapToGlobal(pos))
    
    def _add_row(self):
        """添加行（参数）"""
        if not self.current_category_id:
            return
        
        name, ok = QInputDialog.getText(self, "添加参数", "请输入参数名称：")
        if ok and name.strip():
            result = self.db_manager.add_parameter(
                self.current_category_id,
                name.strip(),
                sort_order=len(self.current_table_data['parameters'])
            )
            if result:
                self._load_table_data(self.current_category_id)
    
    def _add_column(self):
        """添加列（品牌）"""
        if not self.current_category_id:
            return
        
        name, ok = QInputDialog.getText(self, "添加品牌", "请输入品牌名称：")
        if ok and name.strip():
            result = self.db_manager.add_brand(
                self.current_category_id,
                name.strip(),
                sort_order=len(self.current_table_data['brands'])
            )
            if result:
                self._load_table_data(self.current_category_id)
    
    def _delete_row(self):
        """删除行（参数）"""
        current_row = self.table_widget.currentRow()
        if current_row <= 0:
            return
        
        # 获取参数ID
        item = self.table_widget.item(current_row, 0)
        parameter_id = item.data(Qt.ItemDataRole.UserRole)
        
        if self.db_manager.delete_parameter(parameter_id):
            self._load_table_data(self.current_category_id)
    
    def _delete_column(self):
        """删除列（品牌）"""
        current_col = self.table_widget.currentColumn()
        if current_col <= 0:
            return
        
        # 获取品牌ID
        item = self.table_widget.item(0, current_col)
        brand_id = item.data(Qt.ItemDataRole.UserRole)
        
        if self.db_manager.delete_brand(brand_id):
            self._load_table_data(self.current_category_id)
    
    def _clear_cell(self):
        """清空单元格"""
        current_item = self.table_widget.currentItem()
        if current_item:
            current_item.setText("")
    
    # ==================== 配置对话框 ====================
    
    def _on_table_style_settings(self):
        """打开表格样式设置对话框"""
        from ..dialogs.table_style_dialog import TableStyleDialog
        dialog = TableStyleDialog(self.db_manager, self)
        dialog.exec()
    
    def _on_insert_strategy_settings(self):
        """打开插入策略配置对话框（多任务版）"""
        if not self.current_category_id:
            InfoBar.warning(
                title="提示",
                content="请先选择一个类目",
                parent=self,
                position=InfoBarPosition.TOP
            )
            return
        
        from ..dialogs.multi_task_config_dialog import MultiTaskConfigDialog
        dialog = MultiTaskConfigDialog(self.db_manager, self.current_category_id, self)
        dialog.exec()

