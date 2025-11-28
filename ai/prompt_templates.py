"""
Prompt 模板库
存储各种 AI 任务的 Prompt 模板
"""

from typing import Dict


class PromptTemplate:
    """Prompt 模板管理器"""
    
    # 标题生成模板
    TITLE_GENERATION = {
        "爆款": """请为"{keyword}"生成 {count} 个爆款风格的 SEO 文章标题。

要求：
1. 标题要吸引眼球，激发点击欲望
2. 包含核心关键词"{keyword}"
3. 使用数字、疑问、对比等技巧
4. 长度控制在 25-30 字
5. 每个标题独立一行，不要序号

示例风格：
- {keyword}深度评测：这3个优点让我惊艳！
- 2024年{keyword}选购指南：避坑必看
- {keyword} VS 竞品：谁更值得买？

请开始生成：""",
        
        "专业": """请为"{keyword}"生成 {count} 个专业风格的 SEO 文章标题。

要求：
1. 标题要专业严谨，体现权威性
2. 包含核心关键词"{keyword}"
3. 突出技术细节和专业分析
4. 长度控制在 15-30 字
5. 每个标题独立一行，不要序号

示例风格：
- {keyword}技术解析：核心参数全面对比
- {keyword}行业报告：市场趋势与发展前景
- {keyword}专业评测：性能指标深度分析

请开始生成：""",
        
        "问答": """请为"{keyword}"生成 {count} 个问答风格的 SEO 文章标题。

要求：
1. 标题以疑问句形式呈现
2. 包含核心关键词"{keyword}"
3. 针对用户常见疑问
4. 长度控制在 15-30 字
5. 每个标题独立一行，不要序号

示例风格：
- {keyword}值得买吗？看完这篇你就懂了
- {keyword}怎么选？这些细节别忽略
- {keyword}哪个牌子好？5大品牌横评

请开始生成："""
    }
    
    # 内容改写模板
    CONTENT_REWRITE = {
        "扩写": """请将以下内容进行扩写。

要求：
1. 保持原意不变
2. 增加具体案例、数据和细节描述
3. 字数增加 50% 以上
4. 语言流畅自然

原始内容：
{content}

扩写后的内容：""",
        
        "口语化": """请将以下内容改写得更口语化。

要求：
1. 保持原意不变
2. 使用日常对话的语气和表达
3. 避免生硬的书面语
4. 增加亲和力和可读性

原始内容：
{content}

口语化后的内容：""",
        
        "降重": """请将以下内容进行改写以降低重复率。

要求：
1. 保持核心观点和信息不变
2. 使用不同的表达方式和句式结构
3. 替换同义词，调整语序
4. 确保改写后的内容通顺自然

原始内容：
{content}

降重后的内容：""",
        
        "专业化": """请将以下内容改写得更专业。

要求：
1. 保持原意不变
2. 使用专业术语和行业表达
3. 增加数据支撑和理论依据
4. 提升内容的权威性和可信度

原始内容：
{content}

专业化后的内容："""
    }
    
    # 内容生成模板
    CONTENT_GENERATION = {
        "产品介绍": """请为"{product_name}"撰写一段产品介绍。

要求：
1. 突出产品的核心卖点和优势
2. 包含关键参数和特性
3. 语言生动有吸引力
4. 字数控制在 150-200 字

产品信息：
{product_info}

产品介绍：""",
        
        "痛点分析": """请针对"{scenario}"场景撰写痛点分析。

要求：
1. 列举用户在该场景下的主要痛点
2. 描述痛点带来的具体困扰
3. 语言贴近用户实际体验
4. 字数控制在 100-150 字

痛点分析：""",
        
        "解决方案": """请针对"{problem}"问题提供解决方案。

要求：
1. 给出具体可行的解决步骤
2. 说明方案的优势和效果
3. 语言清晰易懂
4. 字数控制在 150-200 字

解决方案："""
    }
    
    @classmethod
    def get_title_prompt(cls, keyword: str, count: int, style: str = "爆款") -> str:
        """
        获取标题生成 Prompt
        
        Args:
            keyword: 关键词
            count: 数量
            style: 风格
            
        Returns:
            Prompt 文本
        """
        template = cls.TITLE_GENERATION.get(style, cls.TITLE_GENERATION["爆款"])
        return template.format(keyword=keyword, count=count)
    
    @classmethod
    def get_rewrite_prompt(cls, content: str, style: str = "扩写") -> str:
        """
        获取改写 Prompt
        
        Args:
            content: 原始内容
            style: 风格
            
        Returns:
            Prompt 文本
        """
        template = cls.CONTENT_REWRITE.get(style, cls.CONTENT_REWRITE["扩写"])
        return template.format(content=content)
    
    @classmethod
    def get_generation_prompt(cls, template_type: str, **kwargs) -> str:
        """
        获取内容生成 Prompt
        
        Args:
            template_type: 模板类型
            **kwargs: 模板参数
            
        Returns:
            Prompt 文本
        """
        template = cls.CONTENT_GENERATION.get(template_type)
        if template:
            return template.format(**kwargs)
        return ""
    
    @classmethod
    def list_title_styles(cls) -> list:
        """
        列出所有标题风格
        
        Returns:
            风格列表
        """
        return list(cls.TITLE_GENERATION.keys())
    
    @classmethod
    def list_rewrite_styles(cls) -> list:
        """
        列出所有改写风格
        
        Returns:
            风格列表
        """
        return list(cls.CONTENT_REWRITE.keys())


if __name__ == "__main__":
    # 测试代码
    from ..utils.logger import setup_logger
    
    setup_logger()
    
    # 测试标题生成 Prompt
    print("=== 标题生成 Prompt ===")
    prompt = PromptTemplate.get_title_prompt("洗地机", 10, "爆款")
    print(prompt)
    
    print("\n=== 内容改写 Prompt ===")
    prompt = PromptTemplate.get_rewrite_prompt("这是一段测试内容", "口语化")
    print(prompt)
    
    print("\n=== 可用风格 ===")
    print("标题风格:", PromptTemplate.list_title_styles())
    print("改写风格:", PromptTemplate.list_rewrite_styles())

