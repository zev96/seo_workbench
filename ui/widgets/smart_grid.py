"""
智能网格编辑器
采用 Fluent Design 风格
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QHeaderView, QTableWidgetItem, 
    QFileDialog, QLabel
)
from PyQt6.QtCore import Qt, pyqtSignal, QSize
from PyQt6.QtGui import QColor, QBrush
from qfluentwidgets import (
    TableWidget, InfoBar, InfoBarPosition, MessageBox, ComboBox, 
    PushButton, FluentIcon as FIF, TransparentToolButton
)
from loguru import logger
import pandas as pd
import ast

from ...config.settings import ProfileConfig
from ...utils.file_handler import FileHandler
from ..dialogs.image_selector import ImageSelectorDialog


class SmartGrid(QWidget):
    """智能网格组件 (Fluent 风格)"""
    
    data_changed = pyqtSignal()
    import_clicked = pyqtSignal()
    bold_tool_clicked = pyqtSignal()

    COLUMN_TYPES = ['标题一', '标题二', '标题三', '标题四', '正文', '列表', '忽略']
    
    # 中英文映射
    TYPE_MAP = {
        '标题一': 'H1',
        '标题二': 'H2',
        '标题三': 'H3',
        '标题四': 'H4',
        '正文': 'Body',
        '列表': 'List',
        '忽略': 'Ignore'
    }
    
    # 英文到中文的反向映射
    TYPE_MAP_REVERSE = {v: k for k, v in TYPE_MAP.items()}
    
    def __init__(self, config: ProfileConfig):
        super().__init__()
        self.config = config
        self._init_ui()
    
    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(10)
        
        # 存储表头控制控件（标签 + 下拉框）
        self.column_controls = []
        
        # 空状态提示
        self.empty_hint = QLabel("请导入 Excel 或从左侧拖入素材")
        self.empty_hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.empty_hint.setStyleSheet("""
            QLabel {
                color: #999;
                font-size: 16px;
                padding: 50px;
            }
        """)
        layout.addWidget(self.empty_hint)
        
        # Fluent 表格组件
        self.table = TableWidget(self)
        self.table.setBorderVisible(True)
        self.table.setBorderRadius(16)
        self.table.setWordWrap(False)
        self.table.setRowCount(20)
        self.table.setColumnCount(10)
        
        # 开启斑马纹
        self.table.setAlternatingRowColors(True)
        
        # 启用拖拽接收
        self.table.setAcceptDrops(True)
        self.table.setDragEnabled(True)
        self.table.setDropIndicatorShown(True)
        
        # 性能优化设置
        self.table.setUpdatesEnabled(True)
        # 使用滚动模式而非逐项模式，提高大数据量性能
        self.table.setVerticalScrollMode(self.table.ScrollMode.ScrollPerPixel)
        self.table.setHorizontalScrollMode(self.table.ScrollMode.ScrollPerPixel)
        
        # 设置表头
        self._setup_headers()
        
        # 表格属性
        header = self.table.horizontalHeader()
        header.setStretchLastSection(False)
        header.setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        header.setDefaultSectionSize(120)
        header.setFixedHeight(80)
        self.table.verticalHeader().hide()
        self.table.itemChanged.connect(self._on_item_changed)
        header.sectionResized.connect(self._on_column_resized)
        header.sectionMoved.connect(lambda *_: self._update_column_control_positions())
        self.table.horizontalScrollBar().valueChanged.connect(lambda _: self._update_column_control_positions())
        
        # 启用水平滚动条
        self.table.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        
        layout.addWidget(self.table)
        
        # 创建列头控制
        self._setup_column_controls()
        
        # 初始隐藏表格，显示空状态
        self.table.hide()
    
    def _setup_headers(self):
        """设置表头"""
        for col in range(self.table.columnCount()):
            item = QTableWidgetItem("")
            self.table.setHorizontalHeaderItem(col, item)
    
    def _setup_column_controls(self):
        """创建/刷新列控制控件"""
        header = self.table.horizontalHeader()
        for ctrl in self.column_controls:
            ctrl["widget"].deleteLater()
        self.column_controls.clear()
        
        for col in range(self.table.columnCount()):
            widget = QWidget(header.viewport())
            layout = QVBoxLayout(widget)
            layout.setContentsMargins(4, 2, 4, 2)
            layout.setSpacing(4)
            
            label = QLabel(f"第 {col+1} 列", widget)
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            label.setStyleSheet("font-weight:600; color:#333;")
            layout.addWidget(label)
            
            combo = ComboBox(widget)
            combo.addItems(self.COLUMN_TYPES)
            col_type_en = self.config.get_column_type(col)
            combo.setCurrentText(self.TYPE_MAP_REVERSE.get(col_type_en, '正文'))
            combo.currentTextChanged.connect(lambda text, c=col: self._on_column_format_changed(c, text))
            layout.addWidget(combo)
            
            # 添加图片按钮
            img_btn = TransparentToolButton(FIF.PHOTO, widget)
            img_btn.setIconSize(QSize(16, 16))
            img_btn.setFixedSize(24, 24)
            img_btn.setToolTip("添加图片组")
            img_btn.clicked.connect(lambda checked, c=col: self._on_manage_images(c))
            
            # 如果该列已有图片，显示标记
            if col in self.config.column_images and self.config.column_images[col]:
                img_btn.setStyleSheet("background-color: #0078D4; border-radius: 4px;")
                img_btn.setToolTip(f"已添加 {len(self.config.column_images[col])} 张图片")
            
            layout.addWidget(img_btn, alignment=Qt.AlignmentFlag.AlignCenter)
            
            self.column_controls.append({"widget": widget, "combo": combo, "img_btn": img_btn})
        
        self._update_column_control_positions()
    
    def _update_column_control_positions(self):
        """根据列位置更新控件位置"""
        header = self.table.horizontalHeader()
        offset = header.offset()
        for col, ctrl in enumerate(self.column_controls):
            widget = ctrl["widget"]
            combo = ctrl["combo"]
            x = header.sectionPosition(col) - offset
            width = header.sectionSize(col)
            widget.setGeometry(x, 0, width, header.height())
            combo.setFixedWidth(max(width - 8, 60))
            widget.show()
    
    def _setup_column_format_combos(self):
        """兼容旧方法名称，调用新实现"""
        self._setup_column_controls()
    
    def _on_column_resized(self, col: int, old_width: int, new_width: int):
        """列宽改变时同步更新下拉框宽度"""
        self._update_column_control_positions()
    
    def _on_column_format_changed(self, col: int, col_type_cn: str):
        """列格式下拉框改变（接收中文，转换为英文保存）"""
        col_type_en = self.TYPE_MAP.get(col_type_cn, 'Body')
        self._set_column_type(col, col_type_en)
    
        
    def _set_column_type(self, col: int, col_type: str):
        """设置列类型"""
        self.config.set_column_type(col, col_type, f"列{col + 1}")
        self.config.save_config()  # 保存配置
        
        logger.info(f"列 {col+1} 类型设置为: {col_type}")
        
        # Toast 提示
        InfoBar.success(
            title='设置成功',
            content=f'列 {col+1} 已设置为 {col_type}',
            orient=Qt.Orientation.Horizontal,
            isClosable=False,
            position=InfoBarPosition.BOTTOM_RIGHT,
            duration=1500,
            parent=self.window()
        )
        
    def _on_manage_images(self, col: int):
        """管理列图片组"""
        # 获取当前列的图片列表
        current_images = self.config.column_images.get(col, [])
        logger.info(f"[图片管理] 列 {col+1} 当前有 {len(current_images)} 张图片")
        
        # 打开图片选择对话框
        dialog = ImageSelectorDialog(self, current_images)
        if dialog.exec():
            image_paths = dialog.get_image_paths()
            logger.info(f"[图片管理] 对话框返回 {len(image_paths)} 张图片")
            logger.info(f"[图片管理] 返回的图片列表: {image_paths}")
            
            # 保存到配置
            if image_paths:
                self.config.column_images[col] = image_paths
                self.config.save_config()  # ← 关键：保存配置到文件
                logger.info(f"列 {col+1} 添加了 {len(image_paths)} 张图片")
                
                # Toast 提示
                InfoBar.success(
                    title='设置成功',
                    content=f'列 {col+1} 已添加 {len(image_paths)} 张图片',
                    orient=Qt.Orientation.Horizontal,
                    isClosable=False,
                    position=InfoBarPosition.BOTTOM_RIGHT,
                    duration=2000,
                    parent=self.window()
                )
            else:
                # 清空图片
                logger.info(f"[图片管理] 准备清空列 {col+1} 的图片")
                logger.info(f"[图片管理] 清空前 column_images: {self.config.column_images}")
                
                if col in self.config.column_images:
                    del self.config.column_images[col]
                    logger.info(f"[图片管理] 已从 column_images 中删除列 {col}")
                
                logger.info(f"[图片管理] 清空后 column_images: {self.config.column_images}")
                self.config.save_config()  # ← 关键：保存配置到文件
                logger.info(f"列 {col+1} 清空了图片")
                
                # Toast 提示
                InfoBar.success(
                    title='已清空',
                    content=f'列 {col+1} 的图片已清空',
                    orient=Qt.Orientation.Horizontal,
                    isClosable=False,
                    position=InfoBarPosition.BOTTOM_RIGHT,
                    duration=2000,
                    parent=self.window()
                )
            
            # 刷新按钮视觉状态
            self._update_image_button_style(col)
    
    def _update_image_button_style(self, col: int):
        """更新图片按钮的视觉状态"""
        if col < len(self.column_controls):
            ctrl = self.column_controls[col]
            img_btn = ctrl.get("img_btn")
            if img_btn:
                # 检查该列是否有图片
                has_images = col in self.config.column_images and self.config.column_images[col]
                logger.info(f"[按钮状态] 列 {col+1} 是否有图片: {has_images}")
                
                if has_images:
                    # 有图片：蓝色背景
                    img_btn.setStyleSheet("background-color: #0078D4; border-radius: 4px;")
                    img_btn.setToolTip(f"已添加 {len(self.config.column_images[col])} 张图片")
                    logger.info(f"[按钮状态] 列 {col+1} 设置为蓝色（有 {len(self.config.column_images[col])} 张图片）")
                else:
                    # 无图片：清除样式并恢复默认
                    img_btn.setStyleSheet("background-color: transparent; border-radius: 4px;")
                    img_btn.setToolTip("点击添加图片")
                    img_btn.update()  # 强制刷新
                    logger.info(f"[按钮状态] 列 {col+1} 设置为默认样式（无图片）")
    
    def _bind_image_folder(self, col: int):
        """绑定图片文件夹（已废弃，保留兼容性）"""
        folder = QFileDialog.getExistingDirectory(
            self,
            "选择图片文件夹",
            "",
            QFileDialog.Option.ShowDirsOnly
        )
        
        if folder:
            self.config.set_image_path(col, folder)
            self.config.save_config()  # 保存配置
            logger.info(f"列 {col} 绑定图片文件夹: {folder}")
            
            # Toast 提示
            InfoBar.success(
                title='绑定成功',
                content=f'列 {col+1} 已绑定图片文件夹',
                orient=Qt.Orientation.Horizontal,
                isClosable=False,
                position=InfoBarPosition.BOTTOM_RIGHT,
                duration=2000,
                parent=self.window()
            )
    
    def _on_item_changed(self, item: QTableWidgetItem):
        self.data_changed.emit()
        # 有数据时隐藏空状态提示（仅在空状态可见时检查）
        if self.empty_hint.isVisible():
            if self._has_data():
                self.empty_hint.hide()
                self.table.show()
    
    def _has_data(self) -> bool:
        """检查是否有数据（优化：只检查前几行）"""
        # 只检查前10行，提高性能
        max_check_rows = min(10, self.table.rowCount())
        for row in range(max_check_rows):
            for col in range(self.table.columnCount()):
                item = self.table.item(row, col)
                if item and item.text().strip():
                    return True
        return False
    
    def import_from_excel(self):
        """从 Excel 导入数据"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "选择 Excel 文件",
            "",
            "Excel 文件 (*.xlsx *.xls)"
        )
        
        if not file_path:
            return
        
        try:
            # 显示加载状态
            from PyQt6.QtWidgets import QApplication
            QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
            
            df = FileHandler.read_excel(file_path)
            if df is None:
                QApplication.restoreOverrideCursor()
                InfoBar.error(
                    title='导入失败',
                    content='无法读取 Excel 文件',
                    orient=Qt.Orientation.Horizontal,
                    isClosable=True,
                    position=InfoBarPosition.BOTTOM_RIGHT,
                    duration=3000,
                    parent=self.window()
                )
                return
            
            # 暂停更新以提高性能
            self.table.setUpdatesEnabled(False)
            
            # 调整表格大小
            self.table.setRowCount(len(df))
            self.table.setColumnCount(len(df.columns))
            
            # 设置表头
            self._setup_headers()
            
            # 重新创建列格式下拉框
            self._setup_column_format_combos()
            
            # 填充数据（批量操作）
            for row_idx, row in df.iterrows():
                for col_idx, value in enumerate(row):
                    item = QTableWidgetItem(str(value) if pd.notna(value) else "")
                    self.table.setItem(row_idx, col_idx, item)
            
            # 恢复更新
            self.table.setUpdatesEnabled(True)
            
            # 恢复光标
            QApplication.restoreOverrideCursor()
            
            # 隐藏空状态，显示表格
            self.empty_hint.hide()
            self.table.show()
            
            logger.info(f"从 Excel 导入: {len(df)} 行, {len(df.columns)} 列")
            
            # Toast 提示
            InfoBar.success(
                title='导入成功',
                content=f'已导入 {len(df)} 行数据',
                orient=Qt.Orientation.Horizontal,
                isClosable=False,
                position=InfoBarPosition.BOTTOM_RIGHT,
                duration=2000,
                parent=self.window()
            )
            
        except Exception as e:
            from PyQt6.QtWidgets import QApplication
            QApplication.restoreOverrideCursor()
            logger.error(f"导入 Excel 失败: {e}")
            InfoBar.error(
                title='导入失败',
                content=str(e),
                orient=Qt.Orientation.Horizontal,
                isClosable=True,
                position=InfoBarPosition.BOTTOM_RIGHT,
                duration=3000,
                parent=self.window()
            )
    
    def export_to_excel(self):
        """导出到 Excel"""
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "保存 Excel 文件",
            "",
            "Excel 文件 (*.xlsx)"
        )
        
        if not file_path:
            return
        
        try:
            from PyQt6.QtWidgets import QApplication
            QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
            
            # 收集数据
            data = []
            for row in range(self.table.rowCount()):
                row_data = []
                for col in range(self.table.columnCount()):
                    item = self.table.item(row, col)
                    row_data.append(item.text() if item else "")
                data.append(row_data)
            
            # 创建 DataFrame
            df = pd.DataFrame(data)
            
            # 写入 Excel
            if FileHandler.write_excel(df, file_path):
                QApplication.restoreOverrideCursor()
                InfoBar.success(
                    title='导出成功',
                    content=f'文件已保存到 {file_path}',
                    orient=Qt.Orientation.Horizontal,
                    isClosable=False,
                    position=InfoBarPosition.BOTTOM_RIGHT,
                    duration=2000,
                    parent=self.window()
                )
            else:
                QApplication.restoreOverrideCursor()
                InfoBar.error(
                    title='导出失败',
                    content='无法写入文件',
                    orient=Qt.Orientation.Horizontal,
                    isClosable=True,
                    position=InfoBarPosition.BOTTOM_RIGHT,
                    duration=3000,
                    parent=self.window()
                )
                
        except Exception as e:
            from PyQt6.QtWidgets import QApplication
            QApplication.restoreOverrideCursor()
            logger.error(f"导出 Excel 失败: {e}")
            InfoBar.error(
                title='导出失败',
                content=str(e),
                orient=Qt.Orientation.Horizontal,
                isClosable=True,
                position=InfoBarPosition.BOTTOM_RIGHT,
                duration=3000,
                parent=self.window()
            )
    
    def get_grid_data(self) -> list:
        """获取网格数据"""
        data = []
        for row in range(self.table.rowCount()):
            row_data = []
            for col in range(self.table.columnCount()):
                item = self.table.item(row, col)
                row_data.append(item.text() if item else "")
            # 只添加非空行
            if any(cell.strip() for cell in row_data):
                data.append(row_data)
        return data
    
    def set_grid_data(self, data: list):
        """设置网格数据"""
        if not data:
            return
        
        self.table.setRowCount(len(data))
        self.table.setColumnCount(len(data[0]) if data else 10)
        
        for row_idx, row_data in enumerate(data):
            for col_idx, cell_value in enumerate(row_data):
                item = QTableWidgetItem(str(cell_value))
                self.table.setItem(row_idx, col_idx, item)
        
        # 隐藏空状态
        self.empty_hint.hide()
        self.table.show()
    
    def get_active_row_count(self) -> int:
        """返回包含内容的行数"""
        active_rows = 0
        for row in range(self.table.rowCount()):
            for col in range(self.table.columnCount()):
                item = self.table.item(row, col)
                if item and item.text().strip():
                    active_rows += 1
                    break
        return active_rows
    
    def dragEnterEvent(self, event):
        """拖拽进入事件"""
        if event.mimeData().hasText():
            event.acceptProposedAction()
    
    def dragMoveEvent(self, event):
        """拖拽移动事件 - 高亮目标单元格"""
        if event.mimeData().hasText():
            # 获取鼠标位置对应的单元格
            pos = event.position().toPoint()
            item = self.table.itemAt(pos)
            if item:
                # 高亮显示目标单元格
                item.setBackground(QBrush(QColor(0, 159, 170, 50)))  # 半透明蓝色
            event.acceptProposedAction()
    
    def dropEvent(self, event):
        """拖拽放下事件"""
        if event.mimeData().hasText():
            pos = event.position().toPoint()
            item = self.table.itemAt(pos)
            if item:
                # 恢复背景色
                item.setBackground(QBrush(Qt.GlobalColor.white))
                # 设置文本
                item.setText(event.mimeData().text())
                
                # 隐藏空状态
                self.empty_hint.hide()
                self.table.show()
                
            event.acceptProposedAction()
    
    def clear_all(self):
        """清空所有数据"""
        w = MessageBox("确认清空", "确定要清空工作区的所有内容吗？此操作不可撤销！", self.window())
        if w.exec():
            self.table.clearContents()
            self.empty_hint.show()
            self.table.hide()
            logger.info("工作区已清空")
            
            InfoBar.success(
                title='清空成功',
                content='工作区内容已清空',
                orient=Qt.Orientation.Horizontal,
                isClosable=False,
                position=InfoBarPosition.BOTTOM_RIGHT,
                duration=2000,
                parent=self.window()
            )
    

