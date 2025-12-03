"""
指纹库管理对话框
提供查看统计、清理旧数据、清空指纹库等功能
"""

from PyQt6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QGridLayout
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from qfluentwidgets import (
    CardWidget, BodyLabel, StrongBodyLabel, PrimaryPushButton, PushButton,
    InfoBar, InfoBarPosition, MessageBox, ProgressRing, TransparentToolButton,
    FluentIcon as FIF
)
from loguru import logger

from ...database.db_manager import DatabaseManager
from ...database.fingerprint_manager import FingerprintManager
from ...config.settings import ProfileConfig


class CleanupWorker(QThread):
    """清理旧指纹的工作线程"""
    
    finished = pyqtSignal(int)  # 删除的记录数
    error = pyqtSignal(str)  # 错误信息
    
    def __init__(self, fp_manager: FingerprintManager, days: int):
        super().__init__()
        self.fp_manager = fp_manager
        self.days = days
    
    def run(self):
        try:
            count = self.fp_manager.clean_old_fingerprints(self.days)
            self.finished.emit(count)
        except Exception as e:
            self.error.emit(str(e))


class FingerprintManagerDialog(QDialog):
    """指纹库管理对话框"""
    
    def __init__(self, config: ProfileConfig, parent=None):
        super().__init__(parent)
        self.config = config
        
        # 初始化数据库管理器
        self.db_manager = DatabaseManager()
        self.fp_manager = FingerprintManager(self.db_manager)
        
        self._init_ui()
        self._load_statistics()
    
    def _init_ui(self):
        """初始化UI"""
        self.setWindowTitle("指纹库管理")
        self.setMinimumWidth(600)
        self.setMinimumHeight(500)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(24, 24, 24, 24)
        
        # 标题
        title_label = StrongBodyLabel("内容指纹库统计", self)
        title_label.setStyleSheet("font-size: 18px; font-weight: bold;")
        layout.addWidget(title_label)
        
        # 统计卡片
        self.stats_card = CardWidget(self)
        stats_layout = QGridLayout(self.stats_card)
        stats_layout.setContentsMargins(20, 20, 20, 20)
        stats_layout.setSpacing(16)
        
        # 总记录数
        self.total_label = self._create_stat_item("📊 总记录数", "0 条")
        stats_layout.addWidget(self.total_label, 0, 0)
        
        # 近7天新增
        self.recent_label = self._create_stat_item("📈 近7天新增", "0 条")
        stats_layout.addWidget(self.recent_label, 0, 1)
        
        # 最早记录
        self.first_label = self._create_stat_item("🕐 最早记录", "无")
        stats_layout.addWidget(self.first_label, 1, 0)
        
        # 最新记录
        self.last_label = self._create_stat_item("🕑 最新记录", "无")
        stats_layout.addWidget(self.last_label, 1, 1)
        
        layout.addWidget(self.stats_card)
        
        # 项目分布卡片
        self.project_card = CardWidget(self)
        project_layout = QVBoxLayout(self.project_card)
        project_layout.setContentsMargins(16, 16, 16, 16)
        project_layout.setSpacing(12)
        
        project_title = StrongBodyLabel("📁 项目分布", self)
        project_layout.addWidget(project_title)
        
        self.project_breakdown_label = BodyLabel("加载中...", self)
        self.project_breakdown_label.setWordWrap(True)
        project_layout.addWidget(self.project_breakdown_label)
        
        layout.addWidget(self.project_card)
        
        # 操作按钮组
        actions_card = CardWidget(self)
        actions_layout = QVBoxLayout(actions_card)
        actions_layout.setContentsMargins(16, 16, 16, 16)
        actions_layout.setSpacing(12)
        
        actions_title = StrongBodyLabel("🛠️ 管理操作", self)
        actions_layout.addWidget(actions_title)
        
        # 刷新按钮
        refresh_layout = QHBoxLayout()
        self.refresh_btn = PushButton("刷新统计", self, FIF.SYNC)
        self.refresh_btn.clicked.connect(self._load_statistics)
        refresh_layout.addWidget(self.refresh_btn)
        refresh_layout.addStretch()
        actions_layout.addLayout(refresh_layout)
        
        # 清理旧数据按钮
        clean_layout = QHBoxLayout()
        self.clean_btn = PushButton("清理旧数据", self, FIF.DELETE)
        self.clean_btn.clicked.connect(self._clean_old_fingerprints)
        clean_layout.addWidget(self.clean_btn)
        
        clean_tip = BodyLabel(f"（清理 {self.config.dedup_retention_days} 天前的数据）", self)
        clean_tip.setStyleSheet("color: #909090; font-size: 12px;")
        clean_layout.addWidget(clean_tip)
        clean_layout.addStretch()
        actions_layout.addLayout(clean_layout)
        
        # 清空指纹库按钮（危险操作）
        clear_layout = QHBoxLayout()
        self.clear_all_btn = PushButton("清空指纹库", self, FIF.CANCEL)
        self.clear_all_btn.clicked.connect(self._clear_all_fingerprints)
        self.clear_all_btn.setStyleSheet("""
            QPushButton {
                background-color: #FF4D4F;
                color: white;
            }
            QPushButton:hover {
                background-color: #FF7875;
            }
        """)
        clear_layout.addWidget(self.clear_all_btn)
        
        clear_tip = BodyLabel("⚠ 危险操作，不可恢复", self)
        clear_tip.setStyleSheet("color: #FF4D4F; font-size: 12px; font-weight: bold;")
        clear_layout.addWidget(clear_tip)
        clear_layout.addStretch()
        actions_layout.addLayout(clear_layout)
        
        layout.addWidget(actions_card)
        
        layout.addStretch()
        
        # 关闭按钮
        close_layout = QHBoxLayout()
        close_layout.addStretch()
        
        self.close_btn = PrimaryPushButton("关闭", self)
        self.close_btn.clicked.connect(self.accept)
        close_layout.addWidget(self.close_btn)
        
        layout.addLayout(close_layout)
    
    def _create_stat_item(self, label_text: str, value_text: str) -> CardWidget:
        """创建统计项卡片"""
        card = CardWidget(self)
        card.setFixedHeight(80)
        
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(12, 12, 12, 12)
        card_layout.setSpacing(8)
        
        label = BodyLabel(label_text, self)
        label.setStyleSheet("color: #606060; font-size: 13px;")
        
        value = StrongBodyLabel(value_text, self)
        value.setStyleSheet("font-size: 24px; font-weight: bold; color: #1890ff;")
        value.setObjectName(f"value_{label_text}")  # 用于后续更新
        
        card_layout.addWidget(label)
        card_layout.addWidget(value)
        
        # 保存引用
        setattr(card, 'value_label', value)
        
        return card
    
    def _load_statistics(self):
        """加载统计信息"""
        try:
            stats = self.fp_manager.get_statistics()
            
            # 更新总记录数
            self.total_label.value_label.setText(f"{stats['total_count']} 条")
            
            # 更新近7天新增
            self.recent_label.value_label.setText(f"{stats['recent_week_count']} 条")
            
            # 更新最早记录
            if stats['first_created']:
                first_date = stats['first_created'].split('T')[0]
                self.first_label.value_label.setText(first_date)
            else:
                self.first_label.value_label.setText("无")
            
            # 更新最新记录
            if stats['last_created']:
                last_date = stats['last_created'].split('T')[0]
                self.last_label.value_label.setText(last_date)
            else:
                self.last_label.value_label.setText("无")
            
            # 更新项目分布
            project_breakdown = stats.get('project_breakdown', {})
            if project_breakdown:
                breakdown_text = "\n".join([
                    f"• {project}: {count} 条"
                    for project, count in project_breakdown.items()
                ])
            else:
                breakdown_text = "暂无数据"
            
            self.project_breakdown_label.setText(breakdown_text)
            
            logger.info("指纹库统计已刷新")
            
        except Exception as e:
            logger.error(f"加载统计信息失败: {e}")
            InfoBar.error(
                title="加载失败",
                content=f"无法加载统计信息: {str(e)}",
                duration=3000,
                position=InfoBarPosition.TOP,
                parent=self
            )
    
    def _clean_old_fingerprints(self):
        """清理旧指纹"""
        days = self.config.dedup_retention_days
        
        # 确认对话框
        msg_box = MessageBox(
            "确认清理",
            f"将删除 {days} 天前的所有指纹记录，是否继续？",
            self
        )
        
        if msg_box.exec():
            try:
                # 禁用按钮
                self.clean_btn.setEnabled(False)
                self.clean_btn.setText("清理中...")
                
                # 创建工作线程
                self.cleanup_worker = CleanupWorker(self.fp_manager, days)
                self.cleanup_worker.finished.connect(self._on_cleanup_finished)
                self.cleanup_worker.error.connect(self._on_cleanup_error)
                self.cleanup_worker.start()
                
            except Exception as e:
                logger.error(f"清理失败: {e}")
                self._on_cleanup_error(str(e))
    
    def _on_cleanup_finished(self, count: int):
        """清理完成"""
        self.clean_btn.setEnabled(True)
        self.clean_btn.setText("清理旧数据")
        
        InfoBar.success(
            title="清理完成",
            content=f"成功删除 {count} 条旧记录",
            duration=3000,
            position=InfoBarPosition.TOP,
            parent=self
        )
        
        # 刷新统计
        self._load_statistics()
        
        logger.info(f"清理旧指纹完成: 删除 {count} 条")
    
    def _on_cleanup_error(self, error_msg: str):
        """清理出错"""
        self.clean_btn.setEnabled(True)
        self.clean_btn.setText("清理旧数据")
        
        InfoBar.error(
            title="清理失败",
            content=f"清理过程出错: {error_msg}",
            duration=3000,
            position=InfoBarPosition.TOP,
            parent=self
        )
        
        logger.error(f"清理旧指纹失败: {error_msg}")
    
    def _clear_all_fingerprints(self):
        """清空所有指纹（危险操作）"""
        # 二次确认
        msg_box = MessageBox(
            "⚠ 危险操作",
            "此操作将删除所有历史指纹记录，不可恢复！\n\n是否确认清空指纹库？",
            self
        )
        msg_box.yesButton.setText("确认清空")
        msg_box.cancelButton.setText("取消")
        
        if msg_box.exec():
            try:
                # 获取项目名称
                project_name = self.config.get_dedup_project_name()
                
                # 清空指纹库
                count = self.fp_manager.clear_all_fingerprints(source_project=project_name)
                
                InfoBar.warning(
                    title="已清空",
                    content=f"成功删除 {count} 条指纹记录",
                    duration=3000,
                    position=InfoBarPosition.TOP,
                    parent=self
                )
                
                # 刷新统计
                self._load_statistics()
                
                logger.warning(f"指纹库已清空: 删除 {count} 条")
                
            except Exception as e:
                logger.error(f"清空指纹库失败: {e}")
                InfoBar.error(
                    title="清空失败",
                    content=f"操作失败: {str(e)}",
                    duration=3000,
                    position=InfoBarPosition.TOP,
                    parent=self
                )


if __name__ == "__main__":
    from PyQt6.QtWidgets import QApplication
    import sys
    
    app = QApplication(sys.argv)
    
    # 测试配置
    from ...config.settings import ProfileConfig
    config = ProfileConfig()
    
    dialog = FingerprintManagerDialog(config)
    dialog.show()
    
    sys.exit(app.exec())

