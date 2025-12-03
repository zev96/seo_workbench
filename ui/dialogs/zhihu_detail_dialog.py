"""
知乎详情分析对话框
展示问题的Top 10回答竞争格局
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QWidget,
    QTableWidget, QTableWidgetItem, QHeaderView, QGroupBox
)
from PyQt6.QtCore import Qt, QUrl
from PyQt6.QtGui import QColor, QDesktopServices
from qfluentwidgets import (
    PushButton, FluentIcon, MessageBox
)
from loguru import logger
from sqlalchemy.orm import Session

from ...database.models import ZhihuMonitorTask, ZhihuBrand
from ...core.zhihu_monitor_worker import ZhihuDetailedWorker


class ZhihuDetailDialog(QDialog):
    """知乎详情分析对话框"""
    
    def __init__(self, task_id: int, db_session: Session, parent=None):
        super().__init__(parent)
        self.task_id = task_id
        self.db_session = db_session
        self.task = None
        self.worker = None
        
        self.setWindowTitle("知乎问题详情分析")
        self.resize(1000, 700)
        
        self._load_task()
        self._init_ui()
        self._load_snapshot()
        
    def _load_task(self):
        """加载任务数据"""
        try:
            self.task = self.db_session.query(ZhihuMonitorTask).filter(
                ZhihuMonitorTask.id == self.task_id
            ).first()
            
            if not self.task:
                logger.error(f"未找到任务: {self.task_id}")
                
        except Exception as e:
            logger.error(f"加载任务失败: {e}")
    
    def _init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # 区域 A: 流量概览
        overview_group = self._create_overview_section()
        layout.addWidget(overview_group)
        
        # 区域 B: Top 10 排名透视表
        ranking_group = self._create_ranking_section()
        layout.addWidget(ranking_group)
        
        # 底部按钮
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        self.refresh_btn = PushButton("🔄 刷新数据", self, FluentIcon.SYNC)
        self.refresh_btn.clicked.connect(self._refresh_data)
        btn_layout.addWidget(self.refresh_btn)
        
        self.close_btn = PushButton("关闭", self)
        self.close_btn.clicked.connect(self.accept)
        btn_layout.addWidget(self.close_btn)
        
        layout.addLayout(btn_layout)
    
    def _create_overview_section(self) -> QGroupBox:
        """创建流量概览区"""
        group = QGroupBox("📊 流量概览")
        layout = QVBoxLayout()
        
        if not self.task:
            no_data = QLabel("⚠️ 数据加载失败")
            layout.addWidget(no_data)
            group.setLayout(layout)
            return group
        
        # 问题标题（可点击）
        title_layout = QHBoxLayout()
        title_label = QLabel(f"<b>问题:</b> {self.task.question_title or '未知'}")
        title_label.setWordWrap(True)
        title_label.setStyleSheet("font-size: 14px; padding: 5px;")
        title_layout.addWidget(title_label)
        
        open_btn = PushButton("🔗 打开链接", self, FluentIcon.LINK)
        open_btn.clicked.connect(self._open_url)
        open_btn.setFixedWidth(120)
        title_layout.addWidget(open_btn)
        
        layout.addLayout(title_layout)
        
        # 核心数据
        stats_layout = QHBoxLayout()
        
        # 浏览量
        views_box = self._create_stat_box(
            "👁️ 浏览量",
            self._format_number(self.task.total_views),
            "#4CAF50"
        )
        stats_layout.addWidget(views_box)
        
        # 关注者
        followers_box = self._create_stat_box(
            "⭐ 关注者",
            self._format_number(self.task.total_followers),
            "#2196F3"
        )
        stats_layout.addWidget(followers_box)
        
        # 我方排名
        ranks = self.task.get_result_list()
        rank_text = f"第 {', '.join(map(str, ranks))} 名" if ranks else "未上榜"
        rank_color = "#4CAF50" if ranks else "#f44336"
        rank_box = self._create_stat_box(
            "🎯 我方品牌",
            rank_text,
            rank_color
        )
        stats_layout.addWidget(rank_box)
        
        # 更新时间
        update_time = self.task.last_check_at or self.task.created_at
        time_text = update_time.strftime("%Y-%m-%d %H:%M") if update_time else "从未"
        time_box = self._create_stat_box(
            "🕒 最后更新",
            time_text,
            "#9E9E9E"
        )
        stats_layout.addWidget(time_box)
        
        layout.addLayout(stats_layout)
        
        group.setLayout(layout)
        return group
    
    def _create_stat_box(self, title: str, value: str, color: str) -> QWidget:
        """创建统计卡片"""
        from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel
        
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(5)
        layout.setContentsMargins(10, 10, 10, 10)
        
        title_label = QLabel(title)
        title_label.setStyleSheet("color: #666; font-size: 12px;")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        value_label = QLabel(value)
        value_label.setStyleSheet(f"color: {color}; font-size: 18px; font-weight: bold;")
        value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        layout.addWidget(title_label)
        layout.addWidget(value_label)
        
        widget.setStyleSheet("""
            QWidget {
                background: #f5f5f5;
                border-radius: 8px;
                border: 1px solid #e0e0e0;
            }
        """)
        
        return widget
    
    def _create_ranking_section(self) -> QGroupBox:
        """创建排名透视表区"""
        group = QGroupBox("🏆 Top 10 排名透视")
        layout = QVBoxLayout()
        
        # 提示信息
        info_label = QLabel(
            "💡 说明：绿色高亮表示我方品牌，加粗表示竞品品牌"
        )
        info_label.setStyleSheet("color: #666; padding: 5px; background: #f5f5f5; border-radius: 3px;")
        layout.addWidget(info_label)
        
        # 表格
        self.ranking_table = QTableWidget()
        self.ranking_table.setColumnCount(5)
        self.ranking_table.setHorizontalHeaderLabels([
            "排名", "提及品牌", "赞同数", "评论数", "答主/摘要"
        ])
        
        # 设置列宽
        header = self.ranking_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)
        
        self.ranking_table.setColumnWidth(0, 80)
        self.ranking_table.setColumnWidth(1, 150)
        self.ranking_table.setColumnWidth(2, 100)
        self.ranking_table.setColumnWidth(3, 100)
        
        layout.addWidget(self.ranking_table)
        
        group.setLayout(layout)
        return group
    
    def _load_snapshot(self):
        """加载快照数据"""
        if not self.task:
            return
        
        snapshot = self.task.get_snapshot()
        
        if not snapshot or 'top10' not in snapshot:
            # 显示空数据提示
            self.ranking_table.setRowCount(1)
            empty_item = QTableWidgetItem("暂无数据，请点击 '刷新数据' 重新抓取")
            empty_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.ranking_table.setSpan(0, 0, 1, 5)
            self.ranking_table.setItem(0, 0, empty_item)
            return
        
        top10_data = snapshot['top10']
        self.ranking_table.setRowCount(len(top10_data))
        
        # 加载品牌列表
        own_brands = self._load_own_brands()
        competitor_brands = self._load_competitor_brands()
        
        for row, answer_data in enumerate(top10_data):
            # 排名
            rank_item = QTableWidgetItem(str(answer_data.get('rank', row + 1)))
            rank_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            
            # 判断是否是我方品牌
            mentioned_brand = answer_data.get('mentioned_brand', '未提及')
            if mentioned_brand in own_brands:
                rank_item.setBackground(QColor(230, 255, 230))  # 淡绿色
            
            self.ranking_table.setItem(row, 0, rank_item)
            
            # 提及品牌
            brand_item = QTableWidgetItem(mentioned_brand)
            brand_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            
            if mentioned_brand in own_brands:
                brand_item.setBackground(QColor(230, 255, 230))
                brand_item.setForeground(QColor(0, 128, 0))
            elif mentioned_brand in competitor_brands:
                font = brand_item.font()
                font.setBold(True)
                brand_item.setFont(font)
            
            self.ranking_table.setItem(row, 1, brand_item)
            
            # 赞同数
            votes = answer_data.get('vote_count', 0)
            votes_item = QTableWidgetItem(self._format_number(votes))
            votes_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            if mentioned_brand in own_brands:
                votes_item.setBackground(QColor(230, 255, 230))
            self.ranking_table.setItem(row, 2, votes_item)
            
            # 评论数
            comments = answer_data.get('comment_count', 0)
            comments_item = QTableWidgetItem(self._format_number(comments))
            comments_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            if mentioned_brand in own_brands:
                comments_item.setBackground(QColor(230, 255, 230))
            self.ranking_table.setItem(row, 3, comments_item)
            
            # 答主/摘要
            author = answer_data.get('author', '未知')
            summary = answer_data.get('summary', '')
            display_text = f"{author} - {summary[:30]}..." if summary else author
            summary_item = QTableWidgetItem(display_text)
            if mentioned_brand in own_brands:
                summary_item.setBackground(QColor(230, 255, 230))
            self.ranking_table.setItem(row, 4, summary_item)
        
        logger.info(f"已加载 {len(top10_data)} 条排名数据")
    
    def _load_own_brands(self) -> list:
        """加载我方品牌列表"""
        try:
            brands = self.db_session.query(ZhihuBrand).filter(
                ZhihuBrand.brand_type == 'own'
            ).all()
            return [b.name for b in brands]
        except:
            return []
    
    def _load_competitor_brands(self) -> list:
        """加载竞品品牌列表"""
        try:
            brands = self.db_session.query(ZhihuBrand).filter(
                ZhihuBrand.brand_type == 'competitor'
            ).all()
            return [b.name for b in brands]
        except:
            return []
    
    def _format_number(self, num: int) -> str:
        """格式化数字显示"""
        if num >= 10000:
            return f"{num / 10000:.1f}万"
        elif num >= 1000:
            return f"{num / 1000:.1f}k"
        else:
            return str(num)
    
    def _open_url(self):
        """打开知乎链接"""
        if self.task and self.task.question_url:
            QDesktopServices.openUrl(QUrl(self.task.question_url))
            logger.info(f"打开链接: {self.task.question_url}")
    
    def _refresh_data(self):
        """刷新数据（重新爬取）"""
        if not self.task:
            return
        
        # 获取配置
        from .zhihu_settings_dialog import ZhihuSettingsDialog
        settings_dialog = ZhihuSettingsDialog(self.db_session, self)
        config = settings_dialog.get_config_dict()
        
        # 获取品牌关键词
        brands = self.db_session.query(ZhihuBrand).all()
        brand_keywords = [{'name': b.name, 'type': b.brand_type} for b in brands]
        
        # 创建详情工作线程
        self.worker = ZhihuDetailedWorker(
            self.task.question_url,
            config,
            brand_keywords
        )
        
        self.worker.detail_completed.connect(self._on_refresh_completed)
        self.worker.detail_failed.connect(self._on_refresh_failed)
        
        # 禁用按钮
        self.refresh_btn.setEnabled(False)
        self.refresh_btn.setText("正在刷新...")
        
        # 启动线程
        self.worker.start()
        
        logger.info("开始刷新详情数据")
    
    def _on_refresh_completed(self, detail_data: dict):
        """刷新完成"""
        try:
            # 更新数据库
            self.task.set_snapshot(detail_data)
            self.task.total_views = detail_data.get('total_views', 0)
            self.task.total_followers = detail_data.get('total_followers', 0)
            self.db_session.commit()
            
            # 重新加载UI
            self._load_snapshot()
            
            MessageBox("成功", "数据已刷新", self).exec()
            logger.success("详情数据刷新成功")
            
        except Exception as e:
            self.db_session.rollback()
            logger.error(f"保存数据失败: {e}")
            MessageBox("错误", f"保存失败: {e}", self).exec()
        finally:
            self.refresh_btn.setEnabled(True)
            self.refresh_btn.setText("🔄 刷新数据")
    
    def _on_refresh_failed(self, error: str):
        """刷新失败"""
        MessageBox("失败", f"刷新失败: {error}", self).exec()
        logger.error(f"刷新详情失败: {error}")
        
        self.refresh_btn.setEnabled(True)
        self.refresh_btn.setText("🔄 刷新数据")

