"""
AI 标题生成对话框
"""
from typing import List, Optional, Dict
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, 
    QLabel, QPlainTextEdit, QWidget, QTableWidget, QTableWidgetItem,
    QHeaderView, QAbstractItemView
)
from PyQt6.QtCore import Qt
from qfluentwidgets import (
    LineEdit, SpinBox, ComboBox, PushButton, PrimaryPushButton,
    PlainTextEdit, MessageBox, InfoBar, InfoBarPosition,
    FluentIcon as FIF
)
from loguru import logger

from ...config.settings import ProfileConfig
from ...ai.api_client import AIClient


class AITitleDialog(QDialog):
    """AI 标题生成对话框"""
    
    def __init__(self, config: ProfileConfig, parent=None):
        super().__init__(parent)
        self.config = config
        self.generated_titles: List[str] = []
        self.title_format = "H1"  # 默认格式
        self._init_ui()
        
    def _init_ui(self):
        """初始化界面"""
        self.setWindowTitle("AI 标题生成（批量模式）")
        self.setMinimumSize(800, 700)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        
        # === 关键词表格区 ===
        keywords_label = QLabel("批量关键词设置（每个关键词独立调用API）:")
        keywords_label.setStyleSheet("font-weight: bold;")
        layout.addWidget(keywords_label)
        
        # 关键词表格
        self.keywords_table = QTableWidget()
        self.keywords_table.setColumnCount(2)
        self.keywords_table.setHorizontalHeaderLabels(["关键词", "生成数量"])
        self.keywords_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.keywords_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)
        self.keywords_table.setColumnWidth(1, 150)  # 增加宽度以完整显示SpinBox
        self.keywords_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.keywords_table.setFixedHeight(200)
        
        # 添加默认的3行示例
        self._add_keyword_row("吸尘器", 30)
        self._add_keyword_row("洗地机", 30)
        self._add_keyword_row("扫地机器人", 30)
        
        layout.addWidget(self.keywords_table)
        
        # 表格操作按钮
        table_btn_layout = QHBoxLayout()
        table_btn_layout.addStretch()
        
        self.add_row_btn = PushButton(FIF.ADD, "添加行")
        self.add_row_btn.clicked.connect(self._on_add_row)
        table_btn_layout.addWidget(self.add_row_btn)
        
        self.remove_row_btn = PushButton(FIF.REMOVE, "删除选中行")
        self.remove_row_btn.clicked.connect(self._on_remove_row)
        table_btn_layout.addWidget(self.remove_row_btn)
        
        layout.addLayout(table_btn_layout)
        
        # === 设置区 ===
        settings_widget = QWidget()
        settings_layout = QFormLayout(settings_widget)
        settings_layout.setSpacing(10)
        
        # 字数限制
        self.word_limit_spin = SpinBox()
        self.word_limit_spin.setRange(10, 100)
        self.word_limit_spin.setValue(25)
        settings_layout.addRow("字数限制:", self.word_limit_spin)
        
        # 格式映射
        self.format_combo = ComboBox()
        self.format_combo.addItems(["标题一 (H1)", "标题二 (H2)", "标题三 (H3)", "标题四 (H4)"])
        self.format_combo.setCurrentIndex(0)
        settings_layout.addRow("Word 格式:", self.format_combo)
        
        layout.addWidget(settings_widget)
        
        # Prompt 模板
        prompt_label = QLabel("Prompt 模板:")
        prompt_label.setStyleSheet("font-weight: bold;")
        layout.addWidget(prompt_label)
        
        self.prompt_edit = PlainTextEdit()
        self.prompt_edit.setPlainText(self._get_default_prompt())
        self.prompt_edit.setFixedHeight(120)
        layout.addWidget(self.prompt_edit)
        
        # 开始生成按钮
        generate_btn_layout = QHBoxLayout()
        generate_btn_layout.addStretch()
        self.generate_btn = PushButton(FIF.SYNC, "开始生成")
        self.generate_btn.clicked.connect(self._on_generate)
        generate_btn_layout.addWidget(self.generate_btn)
        layout.addLayout(generate_btn_layout)
        
        # === 结果预览区 ===
        preview_label = QLabel("生成结果预览（可编辑）:")
        preview_label.setStyleSheet("font-weight: bold;")
        layout.addWidget(preview_label)
        
        self.result_edit = PlainTextEdit()
        self.result_edit.setPlaceholderText("点击【开始生成】后，AI 生成的标题将显示在这里...\n每行一个标题，您可以手动修改。")
        layout.addWidget(self.result_edit)
        
        # === 确认区 ===
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        self.cancel_btn = PushButton("取消")
        self.cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_btn)
        
        self.confirm_btn = PrimaryPushButton("确认并使用")
        self.confirm_btn.clicked.connect(self._on_confirm)
        self.confirm_btn.setEnabled(False)
        button_layout.addWidget(self.confirm_btn)
        
        layout.addLayout(button_layout)
        
    def _add_keyword_row(self, keyword: str = "", count: int = 30):
        """添加一行关键词"""
        row_position = self.keywords_table.rowCount()
        self.keywords_table.insertRow(row_position)
        
        # 关键词列
        keyword_item = QTableWidgetItem(keyword)
        self.keywords_table.setItem(row_position, 0, keyword_item)
        
        # 数量列（使用SpinBox）
        count_spin = SpinBox()
        count_spin.setRange(1, 200)
        count_spin.setValue(count)
        self.keywords_table.setCellWidget(row_position, 1, count_spin)
    
    def _on_add_row(self):
        """添加行"""
        self._add_keyword_row("", 30)
    
    def _on_remove_row(self):
        """删除选中行"""
        selected_rows = self.keywords_table.selectionModel().selectedRows()
        if not selected_rows:
            MessageBox("提示", "请先选择要删除的行", self).exec()
            return
        
        # 从后往前删除，避免索引变化
        for index in sorted(selected_rows, reverse=True):
            self.keywords_table.removeRow(index.row())
    
    def _get_keywords_config(self) -> List[Dict[str, any]]:
        """获取关键词配置列表
        
        Returns:
            [{"keyword": "吸尘器", "count": 30}, ...]
        """
        keywords_config = []
        
        for row in range(self.keywords_table.rowCount()):
            keyword_item = self.keywords_table.item(row, 0)
            count_widget = self.keywords_table.cellWidget(row, 1)
            
            if keyword_item and count_widget:
                keyword = keyword_item.text().strip()
                count = count_widget.value()
                
                # 过滤空关键词
                if keyword:
                    keywords_config.append({
                        "keyword": keyword,
                        "count": count
                    })
        
        return keywords_config
    
    def _get_default_prompt(self) -> str:
        """获取默认 Prompt 模板"""
        return """请为关键词"{keyword}"生成 {count} 个 SEO 优化的文章标题。

要求：
【人设】
你是一名10年SEO软文写作大师，精通软文写作和各个平台（公众号、知乎、今日头条）的文章调性。

【要求】
1. 写符合SEO推广特性的标题党标题，需满足标题党风格、禁用专业术语、保持口语化。
2. 字数限制为28-30字。
3. 必须基于用户提供的【核心关键词】进行创作。
4. 长度控制在 {word_limit} 字以内
5. 每个标题独立一行
6. 不要添加序号、编号或任何前缀

【额外要求】
根据语境语义，标题中随机加入时间节点、震惊体、秘笈体、好奇体、利益体、权威体、认知体、情感共鸣体、疑问词、数字和列表、趋势和热点词等。


【参考风格与结构】
1. 专栏/知乎风：多用品牌、价格、真实体验、避坑、防智商税、全面对比、实测数据，这些词容易让人产生点击欲望。多用“避坑”“内幕”“对比”“性价比”“亲测”“选购建议”等知乎高热词，并用疑问句和感叹句增强吸引力。
   例：【真相揭秘】品牌A、品牌B无线吸尘器横评！哪款最值得买？亲测避坑
2. 长文/媒体风：偏向媒体和杂志风格，强调权威感和内容全面性，常用“横评”“深度测评”“全攻略”“内幕揭秘”“避坑指南”等词，结构复杂，修饰语多。更注重内容体系感、可读性和吸引力，往往结合品牌/年份/痛点+强刺激词+核心主题，吸引订阅或转发。
   例：【2025横评】三大热门无线吸尘器深度对比：全方位实测避坑指南！
3. 导购/推荐风：结构可以灵活变化，例如把场景/利益点前置、数量/痛点突出，结构：时效性+品类聚焦+权威全解+利益直给+数量限定
例：618无线吸尘器避坑全攻略：2025年三款高性价比型号测评推荐
4. 对比/测评风：标题尽量覆盖品牌、品类、内容类型和结果导向
结构：品牌+需求问句+测评类型 或者 品牌关键词+横评+痛点疑问+测评类型
例：品牌A、品牌B、品牌C哪款好？三款爆款机型测评对比！


【标题党常用词组】
1.好奇风：
揭秘
曝光
内幕
真相
独家揭秘
首次曝光
推荐
分享
独家
行业内幕

2.利益风
干货
攻略
指南
教程
懒人包
省钱
方法
技巧
提升
性价比
性价比高
质量好
好用
专业
实用
耐用
便宜
私藏
平价
口碑好

3.权威风
排行榜
Top 10
x万人推荐
专家说
亲测有效
真实评价
大家都在用
好评如潮
用户推荐
真实评价
五星好评
排名
榜单
清单
测评
评测
亲测
PK
横评

4. 制造紧迫风
必看
马上
立即
2025年最新

5.认知
新手
小白
懒人
保姆级
一学就会
手把手
新手必看
必看
必备

6.情感共鸣
踩坑
血泪史
智商税
千万别
感人
扎心了
吐血整理
压箱底

6.疑问词
哪些
哪种
哪个好
哪款
哪个好
怎么样
如何
为什么
是什么
有没有

7.数字和列表
x个理由
x个方法
x种
x大
排行榜
前x名
Top x
x款
盘点
合集

8.趋势和热点
2025年
最新
热门
爆款
新款
618
双十一
618推荐
双十一推荐
618推荐榜单
618购物清单


示例格式：
「真相揭秘」品牌A、品牌B{keyword}横评！哪款最值得买？亲测避坑！
2025横评三大热门{keyword}深度对比：全方位实测避坑指南！
618{keyword}避坑全攻略：2025年三款高性价比牌子测评推荐！
{keyword}怎么选？2025年618三款性价比王者实测横评
2025年618{keyword}最全选购指南：三款高性价比{keyword}测评推荐
品牌A、品牌B、品牌C哪款好？三款爆款{keyword}测评对比！
买吸尘器{keyword}！CEWEY/松下/苏泊尔{keyword}深度对比，谁才是性价比王者？

请开始执行指令：
"""
    
    def _on_generate(self):
        """开始生成标题（批量模式）"""
        # 获取关键词配置
        keywords_config = self._get_keywords_config()
        
        if not keywords_config:
            MessageBox("提示", "请至少添加一个关键词", self).exec()
            return
        
        # 检查 API 配置
        if not self.config.api_config.api_key:
            MessageBox("配置错误", "请先在设置中配置 API Key", self).exec()
            return
        
        # 显示加载状态
        from PyQt6.QtWidgets import QApplication
        QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
        self.generate_btn.setEnabled(False)
        self.generate_btn.setText("批量生成中...")
        
        # 初始化结果
        all_titles = []
        failed_keywords = []
        
        # 获取 Prompt 模板
        prompt_template = self.prompt_edit.toPlainText()
        ai_client = AIClient(self.config.api_config)
        
        total_keywords = len(keywords_config)
        
        try:
            # 遍历每个关键词
            for idx, config in enumerate(keywords_config):
                keyword = config["keyword"]
                count = config["count"]
                
                # 更新按钮文本显示进度
                progress_text = f"生成中 ({idx + 1}/{total_keywords}): {keyword}..."
                self.generate_btn.setText(progress_text)
                logger.info(f"正在处理关键词 {idx + 1}/{total_keywords}: {keyword}, 数量={count}")
                
                try:
                    # 构建 Prompt
                    prompt = prompt_template.format(
                        keyword=keyword,
                        count=count,
                        word_limit=self.word_limit_spin.value()
                    )
                    
                    # 调用 AI API
                    titles = ai_client.generate_titles(
                        keyword=keyword,
                        count=count,
                        custom_prompt=prompt
                    )
                    
                    if titles:
                        all_titles.extend(titles)
                        logger.info(f"✓ 关键词 '{keyword}' 成功生成 {len(titles)} 个标题")
                    else:
                        failed_keywords.append(f"{keyword}（未返回标题）")
                        logger.warning(f"✗ 关键词 '{keyword}' 未返回任何标题")
                
                except Exception as e:
                    failed_keywords.append(f"{keyword}（{str(e)}）")
                    logger.error(f"✗ 关键词 '{keyword}' 生成失败: {e}")
            
            # 恢复状态
            QApplication.restoreOverrideCursor()
            self.generate_btn.setEnabled(True)
            self.generate_btn.setText("开始生成")
            
            # 显示结果
            if all_titles:
                self.generated_titles = all_titles
                self.result_edit.setPlainText("\n".join(all_titles))
                self.confirm_btn.setEnabled(True)
                
                # 成功提示
                success_msg = f'成功生成 {len(all_titles)} 个标题'
                if failed_keywords:
                    success_msg += f'\n失败 {len(failed_keywords)} 个关键词'
                
                InfoBar.success(
                    title='批量生成完成',
                    content=success_msg,
                    orient=Qt.Orientation.Horizontal,
                    isClosable=True,
                    position=InfoBarPosition.BOTTOM_RIGHT,
                    duration=3000,
                    parent=self
                )
                
                logger.info(f"批量生成完成: 总计 {len(all_titles)} 个标题，失败 {len(failed_keywords)} 个关键词")
                
                # 如果有失败的，显示详细信息
                if failed_keywords:
                    MessageBox(
                        "部分关键词生成失败", 
                        f"以下关键词生成失败：\n\n" + "\n".join(failed_keywords) + "\n\n已保留成功生成的标题。",
                        self
                    ).exec()
            else:
                # 全部失败
                MessageBox("生成失败", "所有关键词都未能成功生成标题，请检查:\n1. API Key 是否正确\n2. 网络连接是否正常\n3. API 服务是否可用", self).exec()
            
        except Exception as e:
            QApplication.restoreOverrideCursor()
            self.generate_btn.setEnabled(True)
            self.generate_btn.setText("开始生成")
            
            import traceback
            error_detail = traceback.format_exc()
            logger.error(f"批量生成标题失败: {e}\n{error_detail}")
            
            MessageBox("生成失败", f"错误: {str(e)}", self).exec()
    
    def _on_confirm(self):
        """确认并使用"""
        # 从预览框获取最终标题（用户可能编辑过）
        text = self.result_edit.toPlainText().strip()
        if not text:
            MessageBox("提示", "没有可用的标题", self).exec()
            return
        
        # 按行分割，过滤空行
        self.generated_titles = [line.strip() for line in text.split('\n') if line.strip()]
        
        if not self.generated_titles:
            MessageBox("提示", "没有可用的标题", self).exec()
            return
        
        # 获取选中的格式
        format_index = self.format_combo.currentIndex()
        format_map = {0: "H1", 1: "H2", 2: "H3", 3: "H4"}
        self.title_format = format_map[format_index]
        
        logger.info(f"用户确认使用 {len(self.generated_titles)} 个标题，格式: {self.title_format}")
        self.accept()
    
    def get_titles(self) -> List[str]:
        """获取生成的标题列表"""
        return self.generated_titles
    
    def get_title_format(self) -> str:
        """获取标题格式"""
        return self.title_format

