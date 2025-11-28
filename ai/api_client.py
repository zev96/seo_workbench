"""
AI API 客户端封装
支持 OpenAI 和 DeepSeek API
"""

from typing import List, Optional
import openai
from openai import OpenAI
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from loguru import logger

from ..config.settings import APIConfig


class AIClient:
    """AI API 客户端"""
    
    def __init__(self, config: APIConfig):
        """
        初始化 AI 客户端
        
        Args:
            config: API 配置
        """
        self.config = config
        self.client = OpenAI(
            api_key=config.api_key,
            base_url=config.base_url,
            timeout=config.timeout
        )
        logger.info(f"AI 客户端初始化完成: {config.base_url}, 模型: {config.model}")
    
    def generate_titles(
        self,
        keyword: str,
        count: int = 20,
        style: str = "爆款",
        custom_prompt: str = ""
    ) -> List[str]:
        """
        生成标题列表
        
        Args:
            keyword: 核心关键词
            count: 生成数量
            style: 标题风格
            custom_prompt: 自定义提示词（可选）
            
        Returns:
            标题列表
        """
        try:
            # 如果有自定义 prompt，使用自定义的；否则使用默认模板
            if custom_prompt:
                prompt = f"{custom_prompt}\n\n请为关键词「{keyword}」生成 {count} 个标题，每个标题独立一行，不要添加序号。"
            else:
                prompt = self._build_title_prompt(keyword, count, style)
            
            logger.info(f"正在生成标题: 关键词='{keyword}', 数量={count}")
            logger.debug(f"API 配置: base_url={self.config.base_url}, model={self.config.model}")
            
            response = self.client.chat.completions.create(
                model=self.config.model,
                messages=[
                    {"role": "system", "content": "你是一个专业的 SEO 内容创作专家。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.9,
                max_tokens=2000
            )
            
            logger.info("API 请求成功，开始解析响应")
            
            # 解析响应
            content = response.choices[0].message.content
            logger.debug(f"API 返回内容长度: {len(content) if content else 0}")
            
            if not content:
                logger.warning("API 返回内容为空")
                return []
            
            titles = self._parse_titles(content)
            
            logger.info(f"成功生成 {len(titles)} 个标题")
            return titles[:count]
            
        except Exception as e:
            import traceback
            error_detail = traceback.format_exc()
            logger.error(f"生成标题失败: {e}\n详细错误:\n{error_detail}")
            return []
    
    def rewrite_content(
        self,
        content: str,
        style: str = "扩写"
    ) -> Optional[str]:
        """
        改写内容
        
        Args:
            content: 原始内容
            style: 改写风格（扩写/口语化/降重）
            
        Returns:
            改写后的内容，失败返回 None
        """
        try:
            prompt = self._build_rewrite_prompt(content, style)
            
            logger.info(f"正在改写内容: 风格='{style}', 长度={len(content)}")
            
            response = self.client.chat.completions.create(
                model=self.config.model,
                messages=[
                    {"role": "system", "content": "你是一个专业的内容改写专家。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=1500
            )
            
            rewritten = response.choices[0].message.content.strip()
            logger.info(f"改写完成: {len(content)} -> {len(rewritten)} 字符")
            return rewritten
            
        except Exception as e:
            logger.error(f"改写内容失败: {e}")
            return None
    
    def estimate_tokens(self, text: str) -> int:
        """
        估算文本的 Token 数量（粗略估计）
        
        Args:
            text: 文本内容
            
        Returns:
            Token 数量
        """
        # 中文：约 1.5 字符 = 1 token
        # 英文：约 4 字符 = 1 token
        # 这里简化为：2 字符 = 1 token
        return len(text) // 2
    
    def estimate_cost(self, tokens: int) -> float:
        """
        估算成本（基于 DeepSeek 定价）
        
        Args:
            tokens: Token 数量
            
        Returns:
            预计成本（人民币元）
        """
        # DeepSeek 定价（示例）：
        # 输入：1元/百万tokens，输出：2元/百万tokens
        # 这里简化计算
        cost_per_million = 1.5  # 平均价格
        return (tokens / 1_000_000) * cost_per_million
    
    def _build_title_prompt(self, keyword: str, count: int, style: str) -> str:
        """
        构建标题生成 Prompt
        
        Args:
            keyword: 关键词
            count: 数量
            style: 风格
            
        Returns:
            Prompt 文本
        """
        return f"""请为"{keyword}"生成 {count} 个{style}风格的 SEO 文章标题。

要求：
1. 标题要吸引眼球，包含核心关键词
2. 长度控制在 15-30 字
3. 每个标题独立一行
4. 不要添加序号
5. 标题要符合搜索引擎优化规范

示例格式：
{keyword}深度评测：性能表现如何？
2024年{keyword}选购指南：这些坑千万别踩
{keyword}使用技巧大全，让你的效率翻倍

请开始生成："""
    
    def _build_rewrite_prompt(self, content: str, style: str) -> str:
        """
        构建改写 Prompt
        
        Args:
            content: 原始内容
            style: 风格
            
        Returns:
            Prompt 文本
        """
        style_instructions = {
            "扩写": "将内容扩写得更详细，增加具体案例和细节描述，字数增加 50%",
            "口语化": "将内容改写得更口语化、更接地气，像和朋友聊天一样自然",
            "降重": "保持原意的前提下，用不同的表达方式重新组织内容，降低重复率"
        }
        
        instruction = style_instructions.get(style, style_instructions["扩写"])
        
        return f"""请将以下内容进行改写。

改写要求：{instruction}

原始内容：
{content}

改写后的内容："""
    
    def _parse_titles(self, content: str) -> List[str]:
        """
        解析标题列表
        
        Args:
            content: API 返回的内容
            
        Returns:
            标题列表
        """
        lines = content.strip().split('\n')
        titles = []
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # 移除序号（如 "1. ", "1、", "一、" 等）
            import re
            line = re.sub(r'^[\d一二三四五六七八九十]+[、\.\)）]\s*', '', line)
            
            if line:
                titles.append(line)
        
        return titles
    
    @staticmethod
    def create_retry_session(retries: int = 3, backoff_factor: float = 1.0) -> requests.Session:
        """
        创建带重试机制的 requests session
        
        Args:
            retries: 重试次数
            backoff_factor: 退避因子
            
        Returns:
            Session 对象
        """
        session = requests.Session()
        retry = Retry(
            total=retries,
            read=retries,
            connect=retries,
            backoff_factor=backoff_factor,
            status_forcelist=(500, 502, 503, 504)
        )
        adapter = HTTPAdapter(max_retries=retry)
        session.mount('http://', adapter)
        session.mount('https://', adapter)
        return session
    
    def test_connection(self) -> bool:
        """
        测试 API 连接
        
        Returns:
            是否连接成功
        """
        try:
            logger.info("测试 API 连接...")
            response = self.client.chat.completions.create(
                model=self.config.model,
                messages=[{"role": "user", "content": "Hello"}],
                max_tokens=10
            )
            logger.info("API 连接测试成功")
            return True
        except Exception as e:
            logger.error(f"API 连接测试失败: {e}")
            return False


if __name__ == "__main__":
    # 测试代码
    from ..utils.logger import setup_logger
    from ..config.settings import APIConfig
    
    setup_logger()
    
    # 创建测试配置（需要有效的 API Key）
    config = APIConfig(
        base_url="https://api.deepseek.com",
        api_key="sk-your-api-key-here",  # 替换为实际的 API Key
        model="deepseek-chat"
    )
    
    client = AIClient(config)
    
    # 测试连接（如果有有效 API Key）
    # client.test_connection()
    
    # 测试 Token 估算
    test_text = "这是一段测试文本，用于估算 Token 数量和成本。"
    tokens = client.estimate_tokens(test_text)
    cost = client.estimate_cost(tokens)
    logger.info(f"文本: '{test_text}'")
    logger.info(f"估算 Token: {tokens}, 估算成本: {cost:.6f} 元")

