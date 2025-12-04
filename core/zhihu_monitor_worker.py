"""
知乎监测爬虫核心模块
使用优化的 Selenium 实现安全可靠的知乎问题监控（降低反爬检测率）
"""

import re
import time
import random
from datetime import datetime
from typing import List, Dict, Optional, Tuple
from loguru import logger

# 使用标准 Selenium + 优化配置
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException

from PyQt6.QtCore import QThread, pyqtSignal


class ZhihuMonitorWorker(QThread):
    """知乎监测工作线程"""
    
    # 信号定义
    progress_updated = pyqtSignal(int, int, str)  # (当前进度, 总数, 消息)
    task_completed = pyqtSignal(int, dict)  # (任务ID, 结果数据)
    task_failed = pyqtSignal(int, str)  # (任务ID, 错误信息)
    all_completed = pyqtSignal()  # 所有任务完成
    
    # 扩展的真实 User-Agent 池（从真实浏览器收集，降低指纹识别）
    USER_AGENTS = [
        # Chrome on Windows
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36',
        # Chrome on Mac
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 13_5_0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        # Edge on Windows
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36 Edg/119.0.0.0',
        # Firefox on Windows
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:120.0) Gecko/20100101 Firefox/120.0',
        # Firefox on Mac
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:121.0) Gecko/20100101 Firefox/121.0',
    ]
    
    def __init__(self, tasks: List[Dict], config: Dict, brand_keywords: List[str]):
        """
        初始化监测工作线程
        
        Args:
            tasks: 任务列表 [{'id': 1, 'url': '...', 'target_brand': '...', 'check_range': 20}, ...]
            config: 配置字典 {'cookie': '...', 'delay_min': 2, 'delay_max': 6, ...}
            brand_keywords: 所有品牌关键词列表（用于竞品识别）
        """
        super().__init__()
        self.tasks = tasks
        self.config = config
        self.brand_keywords = brand_keywords
        self.driver = None
        self._stop_flag = False
        
    def run(self):
        """线程主函数"""
        try:
            # 初始化浏览器
            if not self._init_driver():
                self.all_completed.emit()
                return
            
            # 串行处理每个任务
            total = len(self.tasks)
            for index, task in enumerate(self.tasks):
                if self._stop_flag:
                    logger.info("用户请求停止监测")
                    break
                
                task_id = task['id']
                url = task['url']
                target_brand = task['target_brand']
                check_range = task.get('check_range', 20)
                
                self.progress_updated.emit(index + 1, total, f"正在检测: {task.get('title', url)}")
                
                try:
                    # 执行检测
                    result = self._check_question(url, target_brand, check_range)
                    
                    if result:
                        self.task_completed.emit(task_id, result)
                        logger.success(f"任务 {task_id} 完成: {result['question_title']}")
                    else:
                        self.task_failed.emit(task_id, "检测失败，未获取到数据")
                        
                except Exception as e:
                    error_msg = str(e)
                    logger.error(f"任务 {task_id} 失败: {error_msg}")
                    self.task_failed.emit(task_id, error_msg)
                
                # 任务间随机延迟 + 模拟浏览知乎（避免连续访问问题链接）
                if index < total - 1:  # 最后一个任务无需延迟
                    # ✅ 模拟浏览知乎热点（中/高强度模式）
                    anti_detect_level = self.config.get('anti_detect_level', 'medium')
                    if anti_detect_level in ['medium', 'high'] and random.random() < 0.7:
                        self._mimic_browsing_zhihu()
                    
                    # 任务间随机延迟
                    delay = random.uniform(
                        self.config.get('delay_min', 2),
                        self.config.get('delay_max', 6)
                    )
                    logger.info(f"⏳ 等待 {delay:.1f} 秒后继续...")
                    time.sleep(delay)
            
            self.all_completed.emit()
            
        except Exception as e:
            logger.error(f"监测线程异常: {e}")
        finally:
            self._cleanup_driver()
    
    def stop(self):
        """停止线程"""
        self._stop_flag = True
        
    def _init_driver(self) -> bool:
        """
        初始化 Selenium WebDriver（优化配置，降低反爬检测率）
        
        使用精心设计的配置和反检测措施
        
        Returns:
            是否初始化成功
        """
        try:
            # 获取反检测强度配置
            anti_detect_level = self.config.get('anti_detect_level', 'medium')
            logger.info(f"🎯 反检测强度: {anti_detect_level}")
            
            # 获取 ChromeDriver 路径（用户手动配置）
            chromedriver_path = self.config.get('chromedriver_path')
            if not chromedriver_path:
                error_msg = (
                    "❌ 未配置 ChromeDriver 路径！\n\n"
                    "请在\"设置\"中配置 ChromeDriver 可执行文件路径。\n"
                    "下载地址：https://googlechromelabs.github.io/chrome-for-testing/\n"
                    "请确保版本与本机 Chrome 浏览器一致。"
                )
                logger.error(error_msg)
                return False
            
            # 验证 ChromeDriver 路径是否存在
            import os
            if not os.path.exists(chromedriver_path):
                logger.error(f"❌ ChromeDriver 文件不存在: {chromedriver_path}")
                return False
            
            logger.info(f"📂 ChromeDriver 路径: {chromedriver_path}")
            logger.info("🚀 正在启动浏览器...")
            
            # 配置 Chrome 选项（精心设计的反检测配置）
            options = Options()
            
            # 基础配置（保持简洁）
            options.add_argument('--start-maximized')  # 最大化窗口
            options.add_argument('--disable-blink-features=AutomationControlled')  # 移除自动化标识
            
            # 随机 User-Agent
            user_agent = self.config.get('user_agent') or random.choice(self.USER_AGENTS)
            options.add_argument(f'user-agent={user_agent}')
            logger.info(f"🌐 User-Agent: {user_agent[:60]}...")
            
            # 排除自动化特征
            options.add_experimental_option('excludeSwitches', ['enable-automation'])
            options.add_experimental_option('useAutomationExtension', False)
            
            # 禁用一些不必要的功能（提高性能）
            options.add_argument('--disable-extensions')
            options.add_argument('--disable-popup-blocking')
            
            # 创建 Service
            service = Service(executable_path=chromedriver_path)
            
            # 创建 WebDriver
            self.driver = webdriver.Chrome(service=service, options=options)
            logger.success("✅ 浏览器已启动")
            
            # 执行反检测 JavaScript（隐藏 webdriver 属性）
            logger.info("🔧 正在注入反检测脚本...")
            self.driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
                'source': '''
                    Object.defineProperty(navigator, 'webdriver', {
                        get: () => undefined
                    });
                    
                    // 修改 plugins 长度
                    Object.defineProperty(navigator, 'plugins', {
                        get: () => [1, 2, 3, 4, 5]
                    });
                    
                    // 修改 languages
                    Object.defineProperty(navigator, 'languages', {
                        get: () => ['zh-CN', 'zh', 'en']
                    });
                    
                    // 修改 chrome 对象
                    window.chrome = {
                        runtime: {}
                    };
                    
                    // 修改 permissions
                    const originalQuery = window.navigator.permissions.query;
                    window.navigator.permissions.query = (parameters) => (
                        parameters.name === 'notifications' ?
                            Promise.resolve({ state: Notification.permission }) :
                            originalQuery(parameters)
                    );
                '''
            })
            logger.success("✅ 反检测脚本已注入")
            
            # 等待浏览器稳定
            logger.info("⏳ 等待浏览器完全启动...")
            time.sleep(2)
            
            # 测试浏览器是否能正常访问网页
            logger.info("🧪 测试浏览器连接...")
            try:
                self.driver.get('https://www.baidu.com')
                time.sleep(1)
                test_url = self.driver.current_url
                logger.info(f"✅ 浏览器测试成功，当前URL: {test_url}")
            except Exception as e:
                logger.error(f"❌ 浏览器测试失败: {e}")
                logger.error("浏览器可能无法正常工作，请检查网络连接")
                return False
            
            # ✅ Cookie 注入
            cookie = self.config.get('cookie')
            if cookie:
                logger.info("🍪 正在注入 Cookie...")
                
                try:
                    # 访问知乎首页
                    logger.info("🌐 访问知乎首页...")
                    self.driver.get('https://www.zhihu.com')
                    
                    # 等待页面加载
                    wait_time = random.uniform(2.0, 3.0)
                    logger.info(f"⏳ 等待页面加载 {wait_time:.1f} 秒...")
                    time.sleep(wait_time)
                    
                    # 检查页面
                    current_url = self.driver.current_url
                    logger.info(f"📍 当前页面: {current_url}")
                    
                    # 检查是否成功访问知乎
                    if 'zhihu.com' not in current_url:
                        logger.warning(f"⚠️ 未能访问知乎首页，当前URL: {current_url}")
                    
                    # 注入 Cookie
                    cookie_count = 0
                    for cookie_item in cookie.split(';'):
                        cookie_item = cookie_item.strip()
                        if '=' in cookie_item and cookie_item:
                            try:
                                self.driver.execute_script(f'document.cookie = "{cookie_item}";')
                                cookie_count += 1
                            except Exception as e:
                                logger.warning(f"Cookie 注入失败: {e}")
                    
                    logger.success(f"✅ Cookie 已注入（{cookie_count} 条）")
                    
                    # 刷新页面
                    time.sleep(1)
                    self.driver.refresh()
                    time.sleep(2)
                    logger.success("✅ Cookie 注入完成")
                    
                except Exception as e:
                    logger.error(f"❌ Cookie 注入失败: {e}")
                    logger.warning("⚠️ 将继续执行")
            else:
                logger.info("ℹ️ 未配置 Cookie，跳过Cookie注入")
                logger.info("🌐 测试访问知乎...")
                try:
                    self.driver.get('https://www.zhihu.com')
                    time.sleep(2)
                    logger.info(f"📍 当前页面: {self.driver.current_url}")
                except Exception as e:
                    logger.error(f"❌ 访问知乎失败: {e}")
            
            logger.success("✅ WebDriver 初始化成功")
            return True
            
        except Exception as e:
            logger.error(f"❌ 初始化 WebDriver 失败: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return False
    
    def _cleanup_driver(self):
        """清理WebDriver资源"""
        if self.driver:
            try:
                self.driver.quit()
                logger.info("WebDriver已关闭")
            except:
                pass
    
    def _random_small_scroll(self, max_scrolls: int = 10):
        """
        随机小步滚动（模拟真人浏览）
        
        不能直接 scrollTo 底部，改为多次小幅度随机滚动
        
        Args:
            max_scrolls: 最大滚动次数
        """
        anti_detect_level = self.config.get('anti_detect_level', 'medium')
        
        # 根据反检测强度调整参数
        if anti_detect_level == 'low':
            actual_scrolls = random.randint(3, 6)
            scroll_range = (300, 600)
            wait_range = (0.3, 0.8)
        elif anti_detect_level == 'high':
            actual_scrolls = random.randint(10, 15)
            scroll_range = (150, 400)
            wait_range = (1.0, 2.0)
        else:  # medium
            actual_scrolls = random.randint(6, 12)
            scroll_range = (200, 800)
            wait_range = (0.6, 1.4)
        
        logger.info(f"🖱️ 开始随机小步滚动（{actual_scrolls} 次）...")
        
        for i in range(actual_scrolls):
            scroll_y = random.randint(*scroll_range)
            try:
                self.driver.execute_script(f"window.scrollBy(0, {scroll_y});")
                time.sleep(random.uniform(*wait_range))
            except:
                break
        
        logger.info("✅ 随机滚动完成")
    
    def _mimic_human_behavior(self):
        """
        模拟真人行为（鼠标移动、随机停顿）
        
        增加"模拟用户行为"以降低指纹稳定性
        """
        anti_detect_level = self.config.get('anti_detect_level', 'medium')
        
        try:
            # 页面加载后随机停顿
            if anti_detect_level == 'low':
                time.sleep(random.uniform(0.8, 1.5))
            elif anti_detect_level == 'high':
                time.sleep(random.uniform(2.5, 5.0))
            else:  # medium
                time.sleep(random.uniform(1.2, 3.0))
            
            # 随机鼠标移动轨迹（模拟用户扫视页面）
            if anti_detect_level != 'low':
                actions = ActionChains(self.driver)
                for _ in range(random.randint(2, 5)):
                    x_offset = random.randint(50, 400)
                    y_offset = random.randint(50, 400)
                    try:
                        actions.move_by_offset(x_offset, y_offset).perform()
                        time.sleep(random.uniform(0.3, 0.8))
                    except:
                        break
                
                logger.info("✅ 模拟鼠标移动完成")
            
            # 随机点击空白区域（可选，高强度模式）
            if anti_detect_level == 'high' and random.random() < 0.5:
                try:
                    # 点击页面随机位置（body 区域）
                    x = random.randint(100, 800)
                    y = random.randint(100, 600)
                    actions = ActionChains(self.driver)
                    actions.move_by_offset(x, y).click().perform()
                    time.sleep(random.uniform(0.5, 1.0))
                    logger.info("✅ 模拟点击行为")
                except:
                    pass
        
        except Exception as e:
            logger.warning(f"模拟人类行为失败（不影响主流程）: {e}")
    
    def _mimic_browsing_zhihu(self):
        """
        任务间模拟浏览知乎（访问热点页面）
        
        不能直接 get → 抓 → 下一个，需要模拟"浏览知乎"的行为
        """
        anti_detect_level = self.config.get('anti_detect_level', 'medium')
        
        # 低强度模式跳过
        if anti_detect_level == 'low':
            logger.info("ℹ️ 低强度模式，跳过热点浏览")
            return
        
        try:
            logger.info("🔥 模拟浏览知乎热点...")
            
            # 访问知乎热点页面
            self.driver.get("https://www.zhihu.com/hot")
            logger.info(f"📍 已访问热点页面: {self.driver.current_url}")
            
            # 随机停顿
            time.sleep(random.uniform(2.0, 4.0))
            
            # 随机滚动 3-5 次
            scroll_times = random.randint(3, 6)
            logger.info(f"📜 随机滚动 {scroll_times} 次...")
            for i in range(scroll_times):
                scroll_y = random.randint(200, 600)
                self.driver.execute_script(f"window.scrollBy(0, {scroll_y});")
                time.sleep(random.uniform(0.8, 1.8))
            
            # 再次随机停顿
            time.sleep(random.uniform(1.5, 3.5))
            
            logger.success("✅ 热点页面浏览完成")
        
        except Exception as e:
            logger.warning(f"⚠️ 模拟浏览热点失败（不影响主流程）: {e}")
            import traceback
            logger.warning(traceback.format_exc())
    
    def _check_question(self, url: str, target_brand: str, check_range: int) -> Optional[Dict]:
        """
        检测单个知乎问题
        
        Args:
            url: 知乎问题URL
            target_brand: 目标品牌词
            check_range: 检测范围（Top N）
            
        Returns:
            结果字典或None
        """
        try:
            logger.info("="*60)
            logger.info(f"🎯 开始检测: {url}")
            logger.info(f"📌 目标品牌: {target_brand}")
            logger.info(f"📊 检测范围: Top {check_range}")
            logger.info("="*60)
            
            # 访问页面
            logger.info(f"🌐 正在访问页面: {url}")
            
            try:
                self.driver.get(url)
                logger.info("✅ 页面访问命令已发送")
                
                # 等待页面开始加载
                time.sleep(1)
                
                # 检查当前URL
                current_url = self.driver.current_url
                logger.info(f"📍 当前页面URL: {current_url}")
                
                # 检查页面标题
                try:
                    page_title = self.driver.title
                    logger.info(f"📄 页面标题: {page_title}")
                except:
                    logger.warning("⚠️ 无法获取页面标题")
                
            except Exception as e:
                logger.error(f"❌ 访问页面失败: {e}")
                import traceback
                logger.error(traceback.format_exc())
                return None
            
            # ✅ 增加随机等待时间（2-6秒，避免固定节奏）
            anti_detect_level = self.config.get('anti_detect_level', 'medium')
            if anti_detect_level == 'low':
                wait_time = random.uniform(1.5, 3.0)
            elif anti_detect_level == 'high':
                wait_time = random.uniform(4.0, 7.0)
            else:  # medium
                wait_time = random.uniform(2.0, 5.0)
            
            logger.info(f"⏳ 等待页面完全加载 {wait_time:.1f} 秒...")
            time.sleep(wait_time)
            
            # 等待页面关键元素加载
            logger.info("🔍 等待页面关键元素...")
            try:
                wait = WebDriverWait(self.driver, 15)
                wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'QuestionHeader-title')))
                logger.success("✅ 页面关键元素已加载")
            except TimeoutException:
                logger.error("❌ 页面加载超时，未找到问题标题元素")
                logger.error(f"当前URL: {self.driver.current_url}")
                logger.error(f"页面源码（前500字符）: {self.driver.page_source[:500]}")
                return None
            
            # ✅ 模拟真人行为（鼠标移动、随机停顿）
            logger.info("🖱️ 模拟真人行为...")
            self._mimic_human_behavior()
            
            # 提取问题标题 - 尝试多种选择器
            question_title = ""
            try:
                title_elem = self.driver.find_element(By.CLASS_NAME, 'QuestionHeader-title')
                question_title = title_elem.text.strip()
            except:
                try:
                    title_elem = self.driver.find_element(By.CSS_SELECTOR, 'h1.QuestionHeader-title')
                    question_title = title_elem.text.strip()
                except:
                    try:
                        title_elem = self.driver.find_element(By.TAG_NAME, 'h1')
                        question_title = title_elem.text.strip()
                    except:
                        question_title = "未知问题"
            
            logger.info(f"问题标题: {question_title}")
            
            # 提取问题描述（问题补充说明）
            question_detail = ""
            try:
                # 尝试多种选择器
                detail_elem = self.driver.find_element(By.CLASS_NAME, 'QuestionRichText')
                question_detail = detail_elem.text.strip()
            except:
                try:
                    detail_elem = self.driver.find_element(By.CSS_SELECTOR, '.QuestionHeader-detail .RichText')
                    question_detail = detail_elem.text.strip()
                except:
                    try:
                        detail_elem = self.driver.find_element(By.CSS_SELECTOR, 'div[class*="QuestionRichText"]')
                        question_detail = detail_elem.text.strip()
                    except:
                        question_detail = ""
            
            if question_detail:
                logger.info(f"问题描述: {question_detail[:100]}...")
            
            # 提取浏览量和关注数（可选）
            total_views = 0
            total_followers = 0
            try:
                # 知乎的数据结构可能变化，这里做容错处理
                meta_items = self.driver.find_elements(By.CSS_SELECTOR, '.NumberBoard-itemValue')
                if len(meta_items) >= 2:
                    total_followers = self._parse_number(meta_items[0].text)  # 关注者
                    total_views = self._parse_number(meta_items[1].text)  # 被浏览
            except Exception as e:
                logger.warning(f"提取浏览数据失败: {e}")
            
            # ✅ 提取回答列表 - 使用随机小步滚动替代直接 scrollTo 底部
            # 根据反检测强度调整参数
            # ⚠️ 增加滚动次数以确保能加载至少10条回答
            if anti_detect_level == 'low':
                max_scroll_rounds = 5  # 增加（原3）
            elif anti_detect_level == 'high':
                max_scroll_rounds = 10  # 增加（原6）
            else:  # medium
                max_scroll_rounds = 8  # 增加（原5）
            
            # 确保至少滚动到能看到 check_range 或 10 条（取较大值）
            min_answers_needed = max(10, check_range)
            logger.info(f"📜 开始加载回答列表（目标: {min_answers_needed} 条，最多 {max_scroll_rounds} 轮滚动）...")
            
            # 使用随机小步滚动（模拟真人浏览）
            for scroll_round in range(max_scroll_rounds):
                # 随机小步滚动（增加每轮滚动次数）
                self._random_small_scroll(max_scrolls=12)  # 增加（原8）
                
                # 检查是否已加载足够的回答
                answers = self.driver.find_elements(By.CLASS_NAME, 'List-item')
                logger.info(f"第 {scroll_round + 1} 轮滚动完成，已找到 {len(answers)} 个回答")
                
                # 如果已经有足够的回答，继续滚动一轮确保内容完全加载
                if len(answers) >= min_answers_needed:
                    logger.success(f"✅ 已加载足够的回答 ({len(answers)} >= {min_answers_needed})")
                    # 再滚动一轮确保内容完全渲染
                    if scroll_round < max_scroll_rounds - 1:
                        logger.info("继续滚动一轮以确保内容完全加载...")
                        self._random_small_scroll(max_scrolls=6)
                        time.sleep(random.uniform(2.0, 3.0))
                    break
                
                # 等待新内容加载
                time.sleep(random.uniform(2.0, 3.5))
            
            # 最终回答数量
            answers = self.driver.find_elements(By.CLASS_NAME, 'List-item')
            logger.info(f"滚动完成，共找到 {len(answers)} 个回答")
            
            # 扫描前N个回答，并收集Top10详细信息
            found_ranks = []
            top10_details = []  # 存储Top10详细数据
            
            # 确保至少处理10个回答（用于Top10数据）
            scan_count = max(10, min(check_range, len(answers)))
            logger.info(f"将扫描前 {scan_count} 个回答")
            
            for rank in range(1, scan_count + 1):
                try:
                    answer_elem = answers[rank - 1]
                    
                    # 提取回答内容 - 尝试多种选择器
                    content_text = ""
                    try:
                        content_elem = answer_elem.find_element(By.CLASS_NAME, 'RichContent-inner')
                        content_text = content_elem.text
                    except:
                        try:
                            # 备用选择器
                            content_elem = answer_elem.find_element(By.CSS_SELECTOR, '.RichText')
                            content_text = content_elem.text
                        except:
                            # 最后尝试获取整个回答的文本
                            content_text = answer_elem.text
                    
                    if not content_text:
                        logger.warning(f"第 {rank} 个回答内容为空")
                        continue
                    
                    # 输出前100字用于调试
                    logger.info(f"第 {rank} 名回答前100字: {content_text[:100]}")
                    
                    # 检查是否包含目标品牌（不区分大小写）
                    if self._match_brand(content_text, target_brand):
                        found_ranks.append(rank)
                        logger.info(f"在第 {rank} 名发现品牌: {target_brand}")
                    
                    # 收集Top10详细信息（无论是否匹配品牌都要收集）
                    if rank <= 10 and rank <= len(answers):
                        # 滚动到该元素，确保完全加载
                        try:
                            self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", answer_elem)
                            time.sleep(0.5)  # 等待元素完全渲染
                        except:
                            pass
                        
                        # 提取答主信息
                        author = "未知"
                        try:
                            author_elem = answer_elem.find_element(By.CSS_SELECTOR, '.AuthorInfo-name')
                            author = author_elem.text.strip()
                        except:
                            try:
                                author_elem = answer_elem.find_element(By.CSS_SELECTOR, '.UserLink-link')
                                author = author_elem.text.strip()
                            except:
                                try:
                                    # 再尝试其他可能的选择器
                                    author_elem = answer_elem.find_element(By.CSS_SELECTOR, '[itemprop="name"]')
                                    author = author_elem.text.strip()
                                except:
                                    pass
                        
                        # 提取赞同数 - 尝试多种选择器
                        vote_count = 0
                        vote_text = ""
                        try:
                            # 方法1: 标准选择器
                            vote_elem = answer_elem.find_element(By.CSS_SELECTOR, '.VoteButton--up')
                            vote_text = vote_elem.text.strip()
                        except:
                            try:
                                # 方法2: 按钮文本
                                vote_elem = answer_elem.find_element(By.CSS_SELECTOR, 'button[aria-label*="赞同"]')
                                vote_text = vote_elem.text.strip()
                            except:
                                try:
                                    # 方法3: 数据属性
                                    vote_elem = answer_elem.find_element(By.CSS_SELECTOR, '[class*="VoteButton"]')
                                    vote_text = vote_elem.text.strip()
                                except:
                                    pass
                        
                        if vote_text:
                            vote_count = self._parse_vote_count(vote_text)
                            logger.info(f"  第{rank}名 赞同原始文本: '{vote_text}' -> 解析: {vote_count}")
                        else:
                            logger.warning(f"  第{rank}名 未找到赞同数元素")
                        
                        # 提取评论数 - 尝试多种选择器
                        comment_count = 0
                        comment_text = ""
                        try:
                            # 方法1: 标准选择器
                            comment_elem = answer_elem.find_element(By.CSS_SELECTOR, '.Button--comment')
                            comment_text = comment_elem.text.strip()
                        except:
                            try:
                                # 方法2: 按钮文本
                                comment_elem = answer_elem.find_element(By.CSS_SELECTOR, 'button[aria-label*="评论"]')
                                comment_text = comment_elem.text.strip()
                            except:
                                try:
                                    # 方法3: 数据属性
                                    comment_elem = answer_elem.find_element(By.CSS_SELECTOR, 'button[type="button"]')
                                    if '条评论' in comment_elem.text or '评论' in comment_elem.text:
                                        comment_text = comment_elem.text.strip()
                                except:
                                    pass
                        
                        if comment_text:
                            comment_count = self._parse_comment_count(comment_text)
                            logger.info(f"  第{rank}名 评论原始文本: '{comment_text}' -> 解析: {comment_count}")
                        else:
                            logger.warning(f"  第{rank}名 未找到评论数元素")
                        
                        # 品牌归属识别（简化版，只判断目标品牌）
                        mentioned_brand = target_brand if self._match_brand(content_text, target_brand) else "未提及"
                        
                        # 生成摘要
                        summary = content_text[:50] if content_text else ""
                        
                        # 构造Top10数据
                        top10_details.append({
                            'rank': rank,
                            'author': author,
                            'mentioned_brand': mentioned_brand,
                            'vote_count': vote_count,
                            'comment_count': comment_count,
                            'summary': summary
                        })
                        
                        logger.success(f"✅ Top10数据 - 第{rank}名: 作者={author}, 品牌={mentioned_brand}, 赞同={vote_count}, 评论={comment_count}")
                    
                    # 🔧 收起回答（优化滚动性能）
                    self._collapse_answer(answer_elem)
                        
                except Exception as e:
                    logger.warning(f"解析第 {rank} 个回答失败: {e}")
                    continue
            
            # 构造结果（包含Top10详细数据）
            result = {
                'question_title': question_title,
                'question_detail': question_detail,
                'total_views': total_views,
                'total_followers': total_followers,
                'found_ranks': found_ranks,
                'top10_snapshot': {
                    'top10': top10_details,
                    'scan_at': datetime.now().isoformat()
                },
                'status': 'success' if found_ranks else 'not_found',
                'check_at': datetime.now().isoformat()
            }
            
            logger.success(f"检测完成: 找到{len(found_ranks)}个排名, 收集{len(top10_details)}条Top10数据")
            
            return result
            
        except TimeoutException:
            logger.error(f"页面加载超时: {url}")
            return None
        except WebDriverException as e:
            if '403' in str(e) or '429' in str(e):
                logger.error("知乎反爬拦截 (403/429)，任务已停止")
                self._stop_flag = True
            return None
        except Exception as e:
            logger.error(f"检测异常: {e}")
            return None
    
    def _match_brand(self, text: str, brand: str) -> bool:
        """
        匹配品牌词（不区分大小写）
        
        Args:
            text: 待匹配文本
            brand: 品牌词
            
        Returns:
            是否匹配
        """
        # 检查是否是正则表达式
        if brand.startswith('regex:'):
            pattern = brand[6:]  # 去掉'regex:'前缀
            try:
                return bool(re.search(pattern, text, re.IGNORECASE))
            except:
                logger.warning(f"正则表达式无效: {pattern}")
                return False
        else:
            # 精确匹配（不区分大小写）
            return brand.lower() in text.lower()
    
    def _parse_number(self, text: str) -> int:
        """
        解析知乎的数字表示（如 1,234 或 1.2万）
        
        Args:
            text: 数字文本
            
        Returns:
            整数值
        """
        text = text.strip().replace(',', '')
        
        if '万' in text:
            num = float(text.replace('万', ''))
            return int(num * 10000)
        elif '千' in text:
            num = float(text.replace('千', ''))
            return int(num * 1000)
        else:
            try:
                return int(float(text))
            except:
                return 0
    
    def _parse_vote_count(self, vote_text: str) -> int:
        """
        解析赞同数
        
        支持格式: 
        - "赞同 123"
        - "123"
        - "1.2K"
        - "1.2万"
        - "赞同"（无数字）
        """
        if not vote_text:
            return 0
        
        # 去除"赞同"、空格等文字
        vote_text = vote_text.replace('赞同', '').replace(' ', '').strip()
        
        # 如果为空或只有文字，返回0
        if not vote_text or not any(c.isdigit() for c in vote_text):
            return 0
        
        try:
            if 'K' in vote_text.upper():
                # "1.2K" -> 1200
                num_str = vote_text.upper().replace('K', '').strip()
                return int(float(num_str) * 1000)
            elif '万' in vote_text:
                # "1.2万" -> 12000
                num_str = vote_text.replace('万', '').strip()
                return int(float(num_str) * 10000)
            else:
                # "123" 或 "1,234"
                num_str = vote_text.replace(',', '').strip()
                return int(num_str)
        except Exception as e:
            logger.warning(f"解析赞同数失败: '{vote_text}' - {e}")
            return 0
    
    def _parse_comment_count(self, comment_text: str) -> int:
        """
        解析评论数
        
        支持格式:
        - "123 条评论"
        - "添加评论"
        - "评论"
        - "1.2K 条评论"
        """
        if not comment_text:
            return 0
        
        # 移除所有空格
        comment_text = comment_text.replace(' ', '')
        
        # 如果只有"评论"或"添加评论"，返回0
        if comment_text in ['评论', '添加评论', '暂无评论']:
            return 0
        
        try:
            # 尝试匹配 "123K" "1.2万" 等格式
            if 'K' in comment_text.upper():
                match = re.search(r'([\d.]+)K', comment_text.upper())
                if match:
                    return int(float(match.group(1)) * 1000)
            elif '万' in comment_text:
                match = re.search(r'([\d.]+)万', comment_text)
                if match:
                    return int(float(match.group(1)) * 10000)
            
            # 普通数字
            match = re.search(r'(\d+)', comment_text)
            if match:
                return int(match.group(1))
            
            return 0
        except Exception as e:
            logger.warning(f"解析评论数失败: '{comment_text}' - {e}")
            return 0
    
    def _collapse_answer(self, answer_elem):
        """
        收起回答内容（优化滚动性能）
        
        实现策略：
        1. 优先尝试键盘快捷键 'o'（知乎收起回答的快捷键）
        2. 如果快捷键无效，查找并点击"收起"按钮
        3. 失败不抛异常，记录日志后继续
        
        Args:
            answer_elem: 回答元素
        """
        try:
            # 方法1: 优先尝试键盘快捷键 'o'
            try:
                # 先将焦点移到该回答元素上
                answer_elem.click()
                time.sleep(0.1)
                
                # 模拟按下 'o' 键（知乎收起回答的快捷键）
                from selenium.webdriver.common.keys import Keys
                
                actions = ActionChains(self.driver)
                actions.send_keys('o')
                actions.perform()
                
                time.sleep(0.2)  # 等待动画
                logger.debug("✓ 使用快捷键 'o' 收起回答")
                return  # 成功收起，直接返回
                
            except Exception as e:
                logger.debug(f"快捷键收起失败: {e}")
            
            # 方法2: 查找并点击"收起"按钮
            try:
                # 尝试多种选择器查找收起按钮
                collapse_button = None
                
                # 选择器1: 直接查找包含"收起"文本的按钮
                try:
                    buttons = answer_elem.find_elements(By.TAG_NAME, 'button')
                    for btn in buttons:
                        if '收起' in btn.text:
                            collapse_button = btn
                            break
                except:
                    pass
                
                # 选择器2: 查找特定class的收起按钮
                if not collapse_button:
                    try:
                        collapse_button = answer_elem.find_element(
                            By.CSS_SELECTOR, 
                            'button[class*="ContentItem-actions"] button[type="button"]'
                        )
                        if '收起' not in collapse_button.text:
                            collapse_button = None
                    except:
                        pass
                
                # 选择器3: 查找aria-label包含收起的按钮
                if not collapse_button:
                    try:
                        collapse_button = answer_elem.find_element(
                            By.CSS_SELECTOR, 
                            'button[aria-label*="收起"]'
                        )
                    except:
                        pass
                
                # 如果找到收起按钮，执行点击
                if collapse_button:
                    # 滚动到按钮可见
                    self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", collapse_button)
                    time.sleep(0.1)
                    
                    # 点击收起按钮
                    collapse_button.click()
                    time.sleep(0.2)  # 等待动画
                    logger.debug("✓ 点击收起按钮成功")
                else:
                    logger.debug("未找到收起按钮（可能回答未展开或已收起）")
                    
            except Exception as e:
                logger.debug(f"点击收起按钮失败: {e}")
            
        except Exception as e:
            # 任何异常都不影响主流程，仅记录日志
            logger.debug(f"收起回答操作失败（不影响主流程）: {e}")


class ZhihuDetailedWorker(QThread):
    """知乎详情分析工作线程（Phase 2）"""
    
    # 信号定义
    detail_completed = pyqtSignal(dict)  # 详情数据
    detail_failed = pyqtSignal(str)  # 错误信息
    
    # User-Agent池（与主Worker共用）
    USER_AGENTS = ZhihuMonitorWorker.USER_AGENTS
    
    def __init__(self, url: str, config: Dict, brand_keywords: List[Dict]):
        """
        初始化详情分析线程
        
        Args:
            url: 知乎问题URL
            config: 配置字典
            brand_keywords: 品牌关键词列表 [{'name': 'CEWEY', 'type': 'own'}, ...]
        """
        super().__init__()
        self.url = url
        self.config = config
        self.brand_keywords = brand_keywords
        self.driver = None
        
    def run(self):
        """线程主函数"""
        try:
            # 初始化浏览器
            if not self._init_driver():
                self.detail_failed.emit("浏览器初始化失败")
                return
            
            # 执行详细扫描
            result = self._scan_question_detail()
            
            if result:
                self.detail_completed.emit(result)
            else:
                self.detail_failed.emit("未能获取数据")
                
        except Exception as e:
            logger.error(f"详情扫描异常: {e}")
            self.detail_failed.emit(str(e))
        finally:
            self._cleanup_driver()
    
    def _init_driver(self) -> bool:
        """初始化WebDriver（复用主Worker的反检测逻辑）"""
        try:
            # 获取 ChromeDriver 路径
            chromedriver_path = self.config.get('chromedriver_path')
            if not chromedriver_path:
                logger.error("❌ 未配置 ChromeDriver 路径")
                return False
            
            import os
            if not os.path.exists(chromedriver_path):
                logger.error(f"❌ ChromeDriver 文件不存在: {chromedriver_path}")
                return False
            
            logger.info(f"📂 ChromeDriver 路径: {chromedriver_path}")
            logger.info("🚀 正在启动浏览器（详情扫描）...")
            
            # 配置 Chrome 选项
            options = Options()
            options.add_argument('--start-maximized')
            options.add_argument('--disable-blink-features=AutomationControlled')
            
            # 随机 User-Agent
            user_agent = self.config.get('user_agent') or random.choice(self.USER_AGENTS)
            options.add_argument(f'user-agent={user_agent}')
            
            options.add_experimental_option('excludeSwitches', ['enable-automation'])
            options.add_experimental_option('useAutomationExtension', False)
            options.add_argument('--disable-extensions')
            options.add_argument('--disable-popup-blocking')
            
            # 创建 Service 和 WebDriver
            service = Service(executable_path=chromedriver_path)
            self.driver = webdriver.Chrome(service=service, options=options)
            logger.success("✅ 浏览器已启动")
            
            # 注入反检测脚本
            self.driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
                'source': '''
                    Object.defineProperty(navigator, 'webdriver', {
                        get: () => undefined
                    });
                    window.chrome = { runtime: {} };
                '''
            })
            
            time.sleep(1)
            
            # Cookie 注入
            cookie = self.config.get('cookie')
            if cookie:
                logger.info("🍪 正在注入 Cookie（详情扫描）...")
                
                try:
                    self.driver.get('https://www.zhihu.com')
                    time.sleep(2)
                    
                    cookie_count = 0
                    for cookie_item in cookie.split(';'):
                        cookie_item = cookie_item.strip()
                        if '=' in cookie_item and cookie_item:
                            try:
                                self.driver.execute_script(f'document.cookie = "{cookie_item}";')
                                cookie_count += 1
                            except:
                                pass
                    
                    logger.success(f"✅ Cookie 已注入（{cookie_count} 条）")
                    time.sleep(1)
                    self.driver.refresh()
                    time.sleep(2)
                    
                except Exception as e:
                    logger.error(f"❌ Cookie 注入失败: {e}")
            
            logger.success("✅ 详情扫描WebDriver初始化成功")
            return True
            
        except Exception as e:
            logger.error(f"❌ 初始化WebDriver失败: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return False
    
    def _cleanup_driver(self):
        """清理WebDriver资源"""
        if self.driver:
            try:
                self.driver.quit()
            except:
                pass
    
    def _scan_question_detail(self) -> Optional[Dict]:
        """
        扫描问题详情（全量Top 10分析）
        
        Returns:
            详情数据字典
        """
        try:
            logger.info(f"开始详细扫描: {self.url}")
            
            # 访问页面
            self.driver.get(self.url)
            
            # 等待页面加载
            wait = WebDriverWait(self.driver, 10)
            wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'QuestionHeader-title')))
            time.sleep(2)
            
            # 提取问题标题
            title_elem = self.driver.find_element(By.CLASS_NAME, 'QuestionHeader-title')
            question_title = title_elem.text.strip()
            
            # 提取问题描述（问题补充说明）
            question_detail = ""
            try:
                # 尝试多种选择器
                detail_elem = self.driver.find_element(By.CLASS_NAME, 'QuestionRichText')
                question_detail = detail_elem.text.strip()
            except:
                try:
                    detail_elem = self.driver.find_element(By.CSS_SELECTOR, '.QuestionHeader-detail .RichText')
                    question_detail = detail_elem.text.strip()
                except:
                    try:
                        detail_elem = self.driver.find_element(By.CSS_SELECTOR, 'div[class*="QuestionRichText"]')
                        question_detail = detail_elem.text.strip()
                    except:
                        question_detail = ""
                        logger.warning("未找到问题描述")
            
            logger.info(f"问题描述: {question_detail[:100] if question_detail else '(无)'}")
            
            # 提取浏览量和关注数
            total_views = 0
            total_followers = 0
            try:
                meta_items = self.driver.find_elements(By.CSS_SELECTOR, '.NumberBoard-itemValue')
                if len(meta_items) >= 2:
                    total_followers = self._parse_number(meta_items[0].text)
                    total_views = self._parse_number(meta_items[1].text)
            except Exception as e:
                logger.warning(f"提取浏览数据失败: {e}")
            
            # ✅ 滚动加载至少10条回答
            logger.info("📜 滚动加载回答列表（确保至少10条）...")
            for scroll_round in range(6):  # 最多滚动6轮
                # 滚动
                self.driver.execute_script("window.scrollBy(0, 800);")
                time.sleep(1.5)
                
                # 检查回答数量
                answers = self.driver.find_elements(By.CLASS_NAME, 'List-item')
                logger.info(f"滚动 {scroll_round + 1} 轮，已加载 {len(answers)} 条回答")
                
                if len(answers) >= 10:
                    logger.success(f"✅ 已加载足够回答 ({len(answers)} >= 10)")
                    # 再滚动一轮确保元素完全渲染
                    self.driver.execute_script("window.scrollBy(0, 400);")
                    time.sleep(1)
                    break
            
            # 提取Top 10回答详情
            answers = self.driver.find_elements(By.CLASS_NAME, 'List-item')
            logger.info(f"最终获取到 {len(answers)} 条回答，将提取前10条")
            top10_data = []
            
            for rank in range(1, min(11, len(answers) + 1)):
                try:
                    answer_elem = answers[rank - 1]
                    
                    # 滚动到该元素
                    try:
                        self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", answer_elem)
                        time.sleep(0.5)
                    except:
                        pass
                    
                    # 提取答主信息
                    author = "未知"
                    try:
                        author_elem = answer_elem.find_element(By.CSS_SELECTOR, '.AuthorInfo-name')
                        author = author_elem.text.strip()
                    except:
                        try:
                            author_elem = answer_elem.find_element(By.CSS_SELECTOR, '.UserLink-link')
                            author = author_elem.text.strip()
                        except:
                            pass
                    
                    # 提取回答内容
                    content_text = ""
                    try:
                        content_elem = answer_elem.find_element(By.CLASS_NAME, 'RichContent-inner')
                        content_text = content_elem.text
                    except:
                        try:
                            content_elem = answer_elem.find_element(By.CSS_SELECTOR, '.RichText')
                            content_text = content_elem.text
                        except:
                            content_text = answer_elem.text
                    
                    # 提取赞同数 - 尝试多种选择器
                    vote_count = 0
                    vote_text = ""
                    try:
                        vote_elem = answer_elem.find_element(By.CSS_SELECTOR, '.VoteButton--up')
                        vote_text = vote_elem.text.strip()
                    except:
                        try:
                            vote_elem = answer_elem.find_element(By.CSS_SELECTOR, 'button[aria-label*="赞同"]')
                            vote_text = vote_elem.text.strip()
                        except:
                            pass
                    
                    if vote_text:
                        vote_count = self._parse_vote_count(vote_text)
                        logger.info(f"  第{rank}名 赞同: '{vote_text}' -> {vote_count}")
                    else:
                        logger.warning(f"  第{rank}名 未找到赞同数")
                    
                    # 提取评论数 - 尝试多种选择器
                    comment_count = 0
                    comment_text = ""
                    try:
                        comment_elem = answer_elem.find_element(By.CSS_SELECTOR, '.Button--comment')
                        comment_text = comment_elem.text.strip()
                    except:
                        try:
                            comment_elem = answer_elem.find_element(By.CSS_SELECTOR, 'button[aria-label*="评论"]')
                            comment_text = comment_elem.text.strip()
                        except:
                            pass
                    
                    if comment_text:
                        comment_count = self._parse_comment_count(comment_text)
                        logger.info(f"  第{rank}名 评论: '{comment_text}' -> {comment_count}")
                    else:
                        logger.warning(f"  第{rank}名 未找到评论数")
                    
                    # 品牌归属识别
                    mentioned_brand = self._identify_brand(content_text)
                    
                    # 生成摘要
                    summary = content_text[:50] if content_text else ""
                    
                    # 构造回答数据
                    answer_data = {
                        'rank': rank,
                        'author': author,
                        'mentioned_brand': mentioned_brand,
                        'vote_count': vote_count,
                        'comment_count': comment_count,
                        'summary': summary
                    }
                    
                    top10_data.append(answer_data)
                    
                    logger.success(f"✅ 第{rank}名: 作者={author}, 品牌={mentioned_brand}, 赞同={vote_count}, 评论={comment_count}")
                    
                    # 🔧 收起回答（优化滚动性能）
                    self._collapse_answer(answer_elem)
                    
                except Exception as e:
                    logger.warning(f"解析第 {rank} 个回答失败: {e}")
                    continue
            
            # 构造结果
            result = {
                'question_title': question_title,
                'question_detail': question_detail,
                'total_views': total_views,
                'total_followers': total_followers,
                'top10': top10_data,
                'scan_at': datetime.now().isoformat()
            }
            
            logger.success(f"详情扫描完成，获取 {len(top10_data)} 条回答")
            return result
            
        except Exception as e:
            logger.error(f"详情扫描异常: {e}")
            return None
    
    def _identify_brand(self, text: str) -> str:
        """
        识别品牌归属
        
        Args:
            text: 回答文本
            
        Returns:
            品牌名称（我方/竞品/未提及）
        """
        if not text:
            return "未提及"
        
        # 按优先级匹配：我方品牌 > 竞品品牌
        own_brands = [b for b in self.brand_keywords if b['type'] == 'own']
        competitor_brands = [b for b in self.brand_keywords if b['type'] == 'competitor']
        
        # 先匹配我方品牌
        for brand in own_brands:
            brand_name = brand['name']
            if brand_name.lower() in text.lower():
                return brand_name
        
        # 再匹配竞品
        for brand in competitor_brands:
            brand_name = brand['name']
            if brand_name.lower() in text.lower():
                return brand_name
        
        return "未提及"
    
    def _parse_vote_count(self, vote_text: str) -> int:
        """
        解析赞同数
        
        支持格式: 
        - "赞同 123"
        - "123"
        - "1.2K"
        - "1.2万"
        - "赞同"（无数字）
        """
        if not vote_text:
            return 0
        
        # 去除"赞同"、空格等文字
        vote_text = vote_text.replace('赞同', '').replace(' ', '').strip()
        
        # 如果为空或只有文字，返回0
        if not vote_text or not any(c.isdigit() for c in vote_text):
            return 0
        
        try:
            if 'K' in vote_text.upper():
                # "1.2K" -> 1200
                num_str = vote_text.upper().replace('K', '').strip()
                return int(float(num_str) * 1000)
            elif '万' in vote_text:
                # "1.2万" -> 12000
                num_str = vote_text.replace('万', '').strip()
                return int(float(num_str) * 10000)
            else:
                # "123" 或 "1,234"
                num_str = vote_text.replace(',', '').strip()
                return int(num_str)
        except Exception as e:
            logger.warning(f"解析赞同数失败: '{vote_text}' - {e}")
            return 0
    
    def _parse_comment_count(self, comment_text: str) -> int:
        """解析评论数"""
        if not comment_text or '评论' not in comment_text:
            return 0
        
        # 提取数字
        import re
        match = re.search(r'(\d+)', comment_text)
        if match:
            return int(match.group(1))
        return 0
    
    def _parse_number(self, text: str) -> int:
        """
        解析知乎的数字表示（如 1,234 或 1.2万）
        
        Args:
            text: 数字文本
            
        Returns:
            整数值
        """
        text = text.strip().replace(',', '')
        
        if '万' in text:
            num = float(text.replace('万', ''))
            return int(num * 10000)
        elif '千' in text:
            num = float(text.replace('千', ''))
            return int(num * 1000)
        else:
            try:
                return int(float(text))
            except:
                return 0
    
    def _collapse_answer(self, answer_elem):
        """
        收起回答内容（优化滚动性能）
        
        实现策略：
        1. 优先尝试键盘快捷键 'o'（知乎收起回答的快捷键）
        2. 如果快捷键无效，查找并点击"收起"按钮
        3. 失败不抛异常，记录日志后继续
        
        Args:
            answer_elem: 回答元素
        """
        try:
            # 方法1: 优先尝试键盘快捷键 'o'
            try:
                # 先将焦点移到该回答元素上
                answer_elem.click()
                time.sleep(0.1)
                
                # 模拟按下 'o' 键（知乎收起回答的快捷键）
                from selenium.webdriver.common.keys import Keys
                
                actions = ActionChains(self.driver)
                actions.send_keys('o')
                actions.perform()
                
                time.sleep(0.2)  # 等待动画
                logger.debug("✓ 使用快捷键 'o' 收起回答")
                return  # 成功收起，直接返回
                
            except Exception as e:
                logger.debug(f"快捷键收起失败: {e}")
            
            # 方法2: 查找并点击"收起"按钮
            try:
                # 尝试多种选择器查找收起按钮
                collapse_button = None
                
                # 选择器1: 直接查找包含"收起"文本的按钮
                try:
                    buttons = answer_elem.find_elements(By.TAG_NAME, 'button')
                    for btn in buttons:
                        if '收起' in btn.text:
                            collapse_button = btn
                            break
                except:
                    pass
                
                # 选择器2: 查找特定class的收起按钮
                if not collapse_button:
                    try:
                        collapse_button = answer_elem.find_element(
                            By.CSS_SELECTOR, 
                            'button[class*="ContentItem-actions"] button[type="button"]'
                        )
                        if '收起' not in collapse_button.text:
                            collapse_button = None
                    except:
                        pass
                
                # 选择器3: 查找aria-label包含收起的按钮
                if not collapse_button:
                    try:
                        collapse_button = answer_elem.find_element(
                            By.CSS_SELECTOR, 
                            'button[aria-label*="收起"]'
                        )
                    except:
                        pass
                
                # 如果找到收起按钮，执行点击
                if collapse_button:
                    # 滚动到按钮可见
                    self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", collapse_button)
                    time.sleep(0.1)
                    
                    # 点击收起按钮
                    collapse_button.click()
                    time.sleep(0.2)  # 等待动画
                    logger.debug("✓ 点击收起按钮成功")
                else:
                    logger.debug("未找到收起按钮（可能回答未展开或已收起）")
                    
            except Exception as e:
                logger.debug(f"点击收起按钮失败: {e}")
            
        except Exception as e:
            # 任何异常都不影响主流程，仅记录日志
            logger.debug(f"收起回答操作失败（不影响主流程）: {e}")

