"""
AI 标题生成对话框
"""
from typing import List, Optional
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, 
    QLabel, QPlainTextEdit, QWidget
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
        self.setWindowTitle("AI 标题生成")
        self.setMinimumSize(700, 600)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        
        # === 设置区 ===
        settings_widget = QWidget()
        settings_layout = QFormLayout(settings_widget)
        settings_layout.setSpacing(10)
        
        # 核心关键词
        self.keyword_input = LineEdit()
        self.keyword_input.setPlaceholderText("例如：吸尘器、洗地机、扫地机器人...")
        self.keyword_input.setClearButtonEnabled(True)
        settings_layout.addRow("核心关键词:", self.keyword_input)
        
        # 字数限制
        self.word_limit_spin = SpinBox()
        self.word_limit_spin.setRange(10, 100)
        self.word_limit_spin.setValue(25)
        settings_layout.addRow("字数限制:", self.word_limit_spin)
        
        # 生成数量
        self.count_spin = SpinBox()
        self.count_spin.setRange(1, 200)
        self.count_spin.setValue(30)
        settings_layout.addRow("生成数量:", self.count_spin)
        
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
        """开始生成标题"""
        keyword = self.keyword_input.text().strip()
        if not keyword:
            MessageBox("提示", "请输入核心关键词", self).exec()
            return
        
        # 检查 API 配置
        if not self.config.api_config.api_key:
            MessageBox("配置错误", "请先在设置中配置 API Key", self).exec()
            return
        
        # 显示加载状态
        from PyQt6.QtWidgets import QApplication
        QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
        self.generate_btn.setEnabled(False)
        self.generate_btn.setText("生成中...")
        
        try:
            # 构建 Prompt
            prompt_template = self.prompt_edit.toPlainText()
            logger.info(f"准备生成标题: 关键词={keyword}, 数量={self.count_spin.value()}")
            
            prompt = prompt_template.format(
                keyword=keyword,
                count=self.count_spin.value(),
                word_limit=self.word_limit_spin.value()
            )
            
            logger.debug(f"Prompt 已构建，长度: {len(prompt)}")
            
            # 调用 AI API
            ai_client = AIClient(self.config.api_config)
            logger.info("开始调用 AI API...")
            
            titles = ai_client.generate_titles(
                keyword=keyword,
                count=self.count_spin.value(),
                custom_prompt=prompt
            )
            
            logger.info(f"AI API 返回了 {len(titles) if titles else 0} 个标题")
            
            if not titles:
                QApplication.restoreOverrideCursor()
                self.generate_btn.setEnabled(True)
                self.generate_btn.setText("开始生成")
                MessageBox("生成失败", "AI 未返回任何标题，请检查网络或 API 配置", self).exec()
                return
            
            # 显示结果
            self.generated_titles = titles
            self.result_edit.setPlainText("\n".join(titles))
            self.confirm_btn.setEnabled(True)
            
            # 恢复状态
            QApplication.restoreOverrideCursor()
            self.generate_btn.setEnabled(True)
            self.generate_btn.setText("开始生成")
            
            InfoBar.success(
                title='生成完成',
                content=f'成功生成 {len(titles)} 个标题',
                orient=Qt.Orientation.Horizontal,
                isClosable=False,
                position=InfoBarPosition.BOTTOM_RIGHT,
                duration=2000,
                parent=self
            )
            
            logger.info(f"AI 生成了 {len(titles)} 个标题")
            
        except Exception as e:
            QApplication.restoreOverrideCursor()
            self.generate_btn.setEnabled(True)
            self.generate_btn.setText("开始生成")
            
            import traceback
            error_detail = traceback.format_exc()
            logger.error(f"AI 生成标题失败: {e}\n{error_detail}")
            
            MessageBox("生成失败", f"错误: {str(e)}\n\n请检查:\n1. API Key 是否正确\n2. 网络连接是否正常\n3. API 服务是否可用", self).exec()
    
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

