"""
知乎监测爬虫核心模块
使用 Selenium 实现安全可靠的知乎问题监控
"""

import re
import time
import random
from datetime import datetime
from typing import List, Dict, Optional, Tuple
from loguru import logger

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException
from webdriver_manager.chrome import ChromeDriverManager

from PyQt6.QtCore import QThread, pyqtSignal


class ZhihuMonitorWorker(QThread):
    """知乎监测工作线程"""
    
    # 信号定义
    progress_updated = pyqtSignal(int, int, str)  # (当前进度, 总数, 消息)
    task_completed = pyqtSignal(int, dict)  # (任务ID, 结果数据)
    task_failed = pyqtSignal(int, str)  # (任务ID, 错误信息)
    all_completed = pyqtSignal()  # 所有任务完成
    
    # User-Agent池（轮换使用）
    USER_AGENTS = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0',
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
                
                # 任务间随机延迟（模拟人类行为）
                if index < total - 1:  # 最后一个任务无需延迟
                    delay = random.uniform(
                        self.config.get('delay_min', 2),
                        self.config.get('delay_max', 6)
                    )
                    logger.info(f"等待 {delay:.1f} 秒后继续...")
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
        初始化 Selenium WebDriver
        
        Returns:
            是否初始化成功
        """
        try:
            chrome_options = Options()
            
            # 无头模式（可选，根据需求调整）
            # chrome_options.add_argument('--headless')
            
            # 基础配置
            chrome_options.add_argument('--disable-blink-features=AutomationControlled')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('--window-size=1920,1080')
            
            # 随机User-Agent
            user_agent = self.config.get('user_agent') or random.choice(self.USER_AGENTS)
            chrome_options.add_argument(f'user-agent={user_agent}')
            
            # 禁止图片加载（提速）
            prefs = {
                'profile.managed_default_content_settings.images': 2,
                'permissions.default.stylesheet': 2
            }
            chrome_options.add_experimental_option('prefs', prefs)
            
            # 排除自动化特征
            chrome_options.add_experimental_option('excludeSwitches', ['enable-automation'])
            chrome_options.add_experimental_option('useAutomationExtension', False)
            
            # 创建Driver
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            
            # 修改navigator.webdriver属性
            self.driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
                'source': 'Object.defineProperty(navigator, "webdriver", {get: () => undefined})'
            })
            
            # 设置Cookie（如果有）
            cookie = self.config.get('cookie')
            if cookie:
                self.driver.get('https://www.zhihu.com')
                time.sleep(1)
                
                # 解析并设置Cookie
                for cookie_item in cookie.split(';'):
                    cookie_item = cookie_item.strip()
                    if '=' in cookie_item:
                        name, value = cookie_item.split('=', 1)
                        self.driver.add_cookie({
                            'name': name.strip(),
                            'value': value.strip(),
                            'domain': '.zhihu.com'
                        })
                
                logger.info("已设置知乎Cookie")
            
            logger.success("Selenium WebDriver 初始化成功")
            return True
            
        except Exception as e:
            logger.error(f"初始化WebDriver失败: {e}")
            return False
    
    def _cleanup_driver(self):
        """清理WebDriver资源"""
        if self.driver:
            try:
                self.driver.quit()
                logger.info("WebDriver已关闭")
            except:
                pass
    
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
            logger.info(f"开始检测: {url}")
            
            # 访问页面
            self.driver.get(url)
            
            # 等待页面加载
            wait = WebDriverWait(self.driver, 10)
            wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'QuestionHeader-title')))
            
            # 额外等待内容渲染
            time.sleep(2)
            
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
            
            # 提取回答列表 - 需要滚动加载更多
            # 根据温和模式调整参数
            gentle_mode = self.config.get('gentle_mode', 0)
            if gentle_mode:
                max_scrolls = 3  # 温和模式：最多3次
                scroll_wait = 3.0  # 温和模式：等待3秒
                logger.info("🛡️ 温和模式已启用")
            else:
                max_scrolls = 5  # 正常模式：最多5次
                scroll_wait = 1.5  # 正常模式：等待1.5秒
            
            # 先滚动页面，触发懒加载
            last_height = self.driver.execute_script("return document.body.scrollHeight")
            scroll_attempts = 0
            
            while scroll_attempts < max_scrolls:
                # 滚动到底部
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(scroll_wait)  # 等待加载
                
                # 检查是否加载了新内容
                new_height = self.driver.execute_script("return document.body.scrollHeight")
                answers = self.driver.find_elements(By.CLASS_NAME, 'List-item')
                
                logger.info(f"滚动 {scroll_attempts + 1} 次，找到 {len(answers)} 个回答")
                
                # 如果已经有足够的回答，或者页面不再增长，停止滚动
                if len(answers) >= check_range or new_height == last_height:
                    break
                    
                last_height = new_height
                scroll_attempts += 1
            
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
                        
                        # 提取赞同数
                        vote_count = 0
                        try:
                            vote_elem = answer_elem.find_element(By.CSS_SELECTOR, '.VoteButton--up')
                            vote_text = vote_elem.text.strip()
                            vote_count = self._parse_vote_count(vote_text)
                        except:
                            pass
                        
                        # 提取评论数
                        comment_count = 0
                        try:
                            comment_elem = answer_elem.find_element(By.CSS_SELECTOR, '.Button--comment')
                            comment_text = comment_elem.text.strip()
                            comment_count = self._parse_comment_count(comment_text)
                        except:
                            pass
                        
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
                        
                        logger.info(f"Top10数据 - 第{rank}名: {author}, 品牌:{mentioned_brand}, 赞同:{vote_count}")
                        
                except Exception as e:
                    logger.warning(f"解析第 {rank} 个回答失败: {e}")
                    continue
            
            # 构造结果（包含Top10详细数据）
            result = {
                'question_title': question_title,
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
        """解析赞同数"""
        if not vote_text or vote_text == '赞同':
            return 0
        
        # 去除"赞同"等文字
        vote_text = vote_text.replace('赞同', '').strip()
        
        if 'K' in vote_text.upper():
            return int(float(vote_text.upper().replace('K', '')) * 1000)
        elif '万' in vote_text:
            return int(float(vote_text.replace('万', '')) * 10000)
        else:
            try:
                return int(vote_text.replace(',', ''))
            except:
                return 0
    
    def _parse_comment_count(self, comment_text: str) -> int:
        """解析评论数"""
        if not comment_text or '评论' not in comment_text:
            return 0
        
        # 提取数字
        match = re.search(r'(\d+)', comment_text)
        if match:
            return int(match.group(1))
        return 0


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
        """初始化WebDriver（复用主Worker的逻辑）"""
        try:
            chrome_options = Options()
            chrome_options.add_argument('--disable-blink-features=AutomationControlled')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('--window-size=1920,1080')
            
            user_agent = self.config.get('user_agent') or random.choice(self.USER_AGENTS)
            chrome_options.add_argument(f'user-agent={user_agent}')
            
            prefs = {
                'profile.managed_default_content_settings.images': 2,
                'permissions.default.stylesheet': 2
            }
            chrome_options.add_experimental_option('prefs', prefs)
            chrome_options.add_experimental_option('excludeSwitches', ['enable-automation'])
            chrome_options.add_experimental_option('useAutomationExtension', False)
            
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            
            self.driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
                'source': 'Object.defineProperty(navigator, "webdriver", {get: () => undefined})'
            })
            
            # 设置Cookie
            cookie = self.config.get('cookie')
            if cookie:
                self.driver.get('https://www.zhihu.com')
                time.sleep(1)
                
                for cookie_item in cookie.split(';'):
                    cookie_item = cookie_item.strip()
                    if '=' in cookie_item:
                        name, value = cookie_item.split('=', 1)
                        self.driver.add_cookie({
                            'name': name.strip(),
                            'value': value.strip(),
                            'domain': '.zhihu.com'
                        })
            
            logger.success("详情扫描WebDriver初始化成功")
            return True
            
        except Exception as e:
            logger.error(f"初始化WebDriver失败: {e}")
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
            
            # 提取Top 10回答详情
            answers = self.driver.find_elements(By.CLASS_NAME, 'List-item')
            top10_data = []
            
            for rank in range(1, min(11, len(answers) + 1)):
                try:
                    answer_elem = answers[rank - 1]
                    
                    # 提取答主信息
                    author = "未知"
                    try:
                        author_elem = answer_elem.find_element(By.CSS_SELECTOR, '.AuthorInfo-name')
                        author = author_elem.text.strip()
                    except:
                        pass
                    
                    # 提取回答内容
                    content_text = ""
                    try:
                        content_elem = answer_elem.find_element(By.CLASS_NAME, 'RichContent-inner')
                        content_text = content_elem.text
                    except:
                        pass
                    
                    # 提取赞同数
                    vote_count = 0
                    try:
                        vote_elem = answer_elem.find_element(By.CSS_SELECTOR, '.VoteButton--up')
                        vote_text = vote_elem.text.strip()
                        vote_count = self._parse_vote_count(vote_text)
                    except:
                        pass
                    
                    # 提取评论数
                    comment_count = 0
                    try:
                        comment_elem = answer_elem.find_element(By.CSS_SELECTOR, '.Button--comment')
                        comment_text = comment_elem.text.strip()
                        comment_count = self._parse_comment_count(comment_text)
                    except:
                        pass
                    
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
                    
                    logger.info(f"第 {rank} 名: {author} - 品牌:{mentioned_brand} - 赞同:{vote_count}")
                    
                except Exception as e:
                    logger.warning(f"解析第 {rank} 个回答失败: {e}")
                    continue
            
            # 构造结果
            result = {
                'question_title': question_title,
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
        """解析赞同数"""
        if not vote_text or vote_text == '赞同':
            return 0
        
        # 去除"赞同"等文字
        vote_text = vote_text.replace('赞同', '').strip()
        
        if 'K' in vote_text.upper():
            return int(float(vote_text.upper().replace('K', '')) * 1000)
        elif '万' in vote_text:
            return int(float(vote_text.replace('万', '')) * 10000)
        else:
            try:
                return int(vote_text.replace(',', ''))
            except:
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

