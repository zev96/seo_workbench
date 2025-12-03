"""
知乎品牌词库管理对话框
管理我方品牌和竞品品牌关键词
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QLabel, QLineEdit, QComboBox, QMessageBox, QHeaderView
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor
from qfluentwidgets import (
    PushButton, LineEdit, ComboBox, MessageBox,
    FluentIcon, TableWidget
)
from loguru import logger
from sqlalchemy.orm import Session
from ...database.models import ZhihuBrand


class BrandManagerDialog(QDialog):
    """品牌词库管理对话框"""
    
    brands_updated = pyqtSignal()  # 品牌更新信号
    
    def __init__(self, db_session: Session, parent=None):
        super().__init__(parent)
        self.db_session = db_session
        self.setWindowTitle("品牌词库管理")
        self.resize(800, 600)
        
        self._init_ui()
        self._load_brands()
        
    def _init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        
        # 说明区
        info_label = QLabel(
            "💡 提示：添加品牌关键词后，知乎监测将自动识别竞品在回答中的出现情况。\n"
            "支持正则表达式匹配（在关键词前添加 'regex:' 前缀）。"
        )
        info_label.setStyleSheet("color: #666; padding: 10px; background: #f5f5f5; border-radius: 5px;")
        layout.addWidget(info_label)
        
        # 添加品牌区
        add_layout = QHBoxLayout()
        add_layout.setSpacing(10)
        
        self.brand_name_input = LineEdit()
        self.brand_name_input.setPlaceholderText("输入品牌名称（如 CEWEY）")
        self.brand_name_input.setFixedWidth(250)
        
        self.brand_type_combo = ComboBox()
        self.brand_type_combo.addItems(["我方品牌", "竞品品牌"])
        self.brand_type_combo.setFixedWidth(120)
        
        self.regex_input = LineEdit()
        self.regex_input.setPlaceholderText("正则表达式（可选）")
        self.regex_input.setFixedWidth(200)
        
        self.add_btn = PushButton("添加品牌", self, FluentIcon.ADD)
        self.add_btn.clicked.connect(self._add_brand)
        
        add_layout.addWidget(QLabel("品牌名称:"))
        add_layout.addWidget(self.brand_name_input)
        add_layout.addWidget(QLabel("类型:"))
        add_layout.addWidget(self.brand_type_combo)
        add_layout.addWidget(QLabel("正则:"))
        add_layout.addWidget(self.regex_input)
        add_layout.addWidget(self.add_btn)
        add_layout.addStretch()
        
        layout.addLayout(add_layout)
        
        # 品牌列表表格
        self.table = TableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["品牌名称", "类型", "正则表达式", "操作"])
        
        # 设置列宽
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)
        
        self.table.setColumnWidth(0, 200)
        self.table.setColumnWidth(1, 100)
        self.table.setColumnWidth(3, 100)
        
        layout.addWidget(self.table)
        
        # 底部按钮
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        self.close_btn = PushButton("关闭", self)
        self.close_btn.clicked.connect(self.accept)
        btn_layout.addWidget(self.close_btn)
        
        layout.addLayout(btn_layout)
        
    def _load_brands(self):
        """加载品牌列表"""
        try:
            brands = self.db_session.query(ZhihuBrand).order_by(
                ZhihuBrand.brand_type.desc(),  # 我方品牌在前
                ZhihuBrand.created_at.desc()
            ).all()
            
            self.table.setRowCount(len(brands))
            
            for row, brand in enumerate(brands):
                # 品牌名称
                name_item = QTableWidgetItem(brand.name)
                if brand.brand_type == 'own':
                    name_item.setBackground(QColor(230, 255, 230))  # 淡绿色
                self.table.setItem(row, 0, name_item)
                
                # 类型
                type_text = "我方品牌" if brand.brand_type == 'own' else "竞品品牌"
                type_item = QTableWidgetItem(type_text)
                type_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.table.setItem(row, 1, type_item)
                
                # 正则表达式
                regex_item = QTableWidgetItem(brand.regex_pattern or "-")
                self.table.setItem(row, 2, regex_item)
                
                # 操作按钮
                delete_btn = QPushButton("删除")
                delete_btn.setProperty('brand_id', brand.id)
                delete_btn.clicked.connect(lambda checked, b_id=brand.id: self._delete_brand(b_id))
                delete_btn.setStyleSheet("""
                    QPushButton {
                        background-color: #f44336;
                        color: white;
                        border: none;
                        padding: 5px 15px;
                        border-radius: 3px;
                    }
                    QPushButton:hover {
                        background-color: #da190b;
                    }
                """)
                self.table.setCellWidget(row, 3, delete_btn)
                
            logger.info(f"已加载 {len(brands)} 个品牌")
            
        except Exception as e:
            logger.error(f"加载品牌列表失败: {e}")
            MessageBox("错误", f"加载失败: {e}", self).exec()
    
    def _add_brand(self):
        """添加品牌"""
        name = self.brand_name_input.text().strip()
        if not name:
            MessageBox("提示", "请输入品牌名称", self).exec()
            return
        
        try:
            # 检查是否已存在
            exists = self.db_session.query(ZhihuBrand).filter(
                ZhihuBrand.name == name
            ).first()
            
            if exists:
                MessageBox("提示", f"品牌 '{name}' 已存在", self).exec()
                return
            
            # 添加新品牌
            brand_type = 'own' if self.brand_type_combo.currentIndex() == 0 else 'competitor'
            regex_pattern = self.regex_input.text().strip() or None
            
            new_brand = ZhihuBrand(
                name=name,
                brand_type=brand_type,
                regex_pattern=regex_pattern
            )
            
            self.db_session.add(new_brand)
            self.db_session.commit()
            
            logger.success(f"品牌 '{name}' 添加成功")
            
            # 清空输入
            self.brand_name_input.clear()
            self.regex_input.clear()
            
            # 刷新列表
            self._load_brands()
            
            # 发送更新信号
            self.brands_updated.emit()
            
        except Exception as e:
            self.db_session.rollback()
            logger.error(f"添加品牌失败: {e}")
            MessageBox("错误", f"添加失败: {e}", self).exec()
    
    def _delete_brand(self, brand_id: int):
        """删除品牌"""
        try:
            brand = self.db_session.query(ZhihuBrand).filter(
                ZhihuBrand.id == brand_id
            ).first()
            
            if not brand:
                return
            
            # 确认对话框
            reply = MessageBox(
                "确认删除",
                f"确定要删除品牌 '{brand.name}' 吗？",
                self
            )
            
            if reply.exec():
                self.db_session.delete(brand)
                self.db_session.commit()
                
                logger.success(f"品牌 '{brand.name}' 已删除")
                
                # 刷新列表
                self._load_brands()
                
                # 发送更新信号
                self.brands_updated.emit()
                
        except Exception as e:
            self.db_session.rollback()
            logger.error(f"删除品牌失败: {e}")
            MessageBox("错误", f"删除失败: {e}", self).exec()

