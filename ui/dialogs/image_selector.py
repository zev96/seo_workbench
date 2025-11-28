"""
图片选择对话框
"""
from pathlib import Path
from typing import List

from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QPixmap, QIcon
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QListWidget, 
    QListWidgetItem, QFileDialog, QLabel
)
from qfluentwidgets import (
    PushButton, MessageBox, FluentIcon as FIF
)


class ImageSelectorDialog(QDialog):
    """图片选择对话框"""
    
    def __init__(self, parent=None, initial_images: List[str] = None):
        super().__init__(parent)
        # 创建副本，避免直接修改原列表
        self.image_paths: List[str] = list(initial_images) if initial_images else []
        self._init_ui()
        self._load_images()
        
    def _init_ui(self):
        """初始化界面"""
        self.setWindowTitle("选择图片")
        self.setMinimumSize(600, 400)
        
        layout = QVBoxLayout(self)
        
        # 提示文本
        tip_label = QLabel("为该列添加图片组，生成 Word 时会随机选择一张插入")
        tip_label.setStyleSheet("color: gray; padding: 5px;")
        layout.addWidget(tip_label)
        
        # 图片列表
        self.image_list = QListWidget()
        self.image_list.setIconSize(QSize(80, 80))
        self.image_list.setViewMode(QListWidget.ViewMode.IconMode)
        self.image_list.setResizeMode(QListWidget.ResizeMode.Adjust)
        self.image_list.setSpacing(10)
        # 启用多选模式
        self.image_list.setSelectionMode(QListWidget.SelectionMode.ExtendedSelection)
        layout.addWidget(self.image_list)
        
        # 按钮组
        btn_layout = QHBoxLayout()
        
        self.add_btn = PushButton(FIF.ADD, "添加图片")
        self.add_btn.clicked.connect(self._on_add_images)
        btn_layout.addWidget(self.add_btn)
        
        self.remove_btn = PushButton(FIF.DELETE, "删除选中")
        self.remove_btn.clicked.connect(self._on_remove_images)
        btn_layout.addWidget(self.remove_btn)
        
        btn_layout.addStretch()
        
        self.ok_btn = PushButton("确定")
        self.ok_btn.clicked.connect(self.accept)
        btn_layout.addWidget(self.ok_btn)
        
        self.cancel_btn = PushButton("取消")
        self.cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(self.cancel_btn)
        
        layout.addLayout(btn_layout)
        
    def _load_images(self):
        """加载已有图片"""
        self.image_list.clear()
        for img_path in self.image_paths:
            self._add_image_item(img_path)
            
    def _add_image_item(self, img_path: str):
        """添加图片项到列表"""
        path = Path(img_path)
        if not path.exists():
            return
            
        # 创建缩略图
        pixmap = QPixmap(str(path))
        if pixmap.isNull():
            return
            
        # 缩放到合适大小
        pixmap = pixmap.scaled(80, 80, Qt.AspectRatioMode.KeepAspectRatio, 
                               Qt.TransformationMode.SmoothTransformation)
        
        # 创建列表项
        item = QListWidgetItem(QIcon(pixmap), path.name)
        item.setData(Qt.ItemDataRole.UserRole, str(path))
        item.setToolTip(f"{path.name}\n{str(path)}")
        self.image_list.addItem(item)
        
    def _on_add_images(self):
        """添加图片"""
        file_paths, _ = QFileDialog.getOpenFileNames(
            self,
            "选择图片",
            "",
            "图片文件 (*.jpg *.jpeg *.png *.bmp *.gif);;所有文件 (*.*)"
        )
        
        if not file_paths:
            return
            
        for file_path in file_paths:
            if file_path not in self.image_paths:
                self.image_paths.append(file_path)
                self._add_image_item(file_path)
                
    def _on_remove_images(self):
        """删除选中的图片（支持批量删除）"""
        from loguru import logger
        
        selected_items = self.image_list.selectedItems()
        logger.info(f"选中了 {len(selected_items)} 个项目")
        
        if not selected_items:
            MessageBox("提示", "请先选择要删除的图片（可按住 Ctrl 或 Shift 多选）", self).exec()
            return
        
        # 确认删除
        if len(selected_items) > 1:
            w = MessageBox("确认删除", f"确定要删除选中的 {len(selected_items)} 张图片吗？", self)
            if not w.exec():
                logger.info("用户取消了删除操作")
                return
        
        # 收集要删除的路径
        paths_to_remove = []
        for item in selected_items:
            img_path = item.data(Qt.ItemDataRole.UserRole)
            if img_path:
                paths_to_remove.append(img_path)
                logger.info(f"准备删除: {img_path}")
        
        logger.info(f"删除前 image_paths 数量: {len(self.image_paths)}")
        logger.info(f"删除前 image_paths 内容: {self.image_paths}")
        
        # 从列表中删除（统一路径格式，避免 \ 和 / 不匹配）
        for img_path in paths_to_remove:
            # 统一转换为正斜杠格式
            normalized_path = img_path.replace('\\', '/')
            
            # 尝试匹配并删除
            found = False
            for i, existing_path in enumerate(self.image_paths):
                if existing_path.replace('\\', '/') == normalized_path:
                    del self.image_paths[i]
                    logger.info(f"已从 image_paths 中删除: {normalized_path}")
                    found = True
                    break
            
            if not found:
                logger.warning(f"未找到要删除的路径: {normalized_path}")
        
        logger.info(f"删除后 image_paths 数量: {len(self.image_paths)}")
        logger.info(f"删除后 image_paths 内容: {self.image_paths}")
        
        # 刷新界面
        self._load_images()
        
        logger.info(f"成功删除了 {len(paths_to_remove)} 张图片")
            
    def get_image_paths(self) -> List[str]:
        """获取图片路径列表"""
        return self.image_paths

