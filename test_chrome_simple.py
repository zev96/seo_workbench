"""
简单的 ChromeDriver 测试脚本
用于验证 ChromeDriver 是否能正常工作
"""

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
import time

# ⚠️ 请修改为你的 ChromeDriver 路径
CHROMEDRIVER_PATH = r"E:\chromedriver\chromedriver.exe"

print("="*60)
print("🧪 ChromeDriver 测试脚本")
print("="*60)

try:
    print("\n步骤 1: 创建浏览器配置...")
    options = Options()
    options.add_argument('--start-maximized')
    options.add_argument('--disable-blink-features=AutomationControlled')
    print("  ✅ 配置创建成功")
    
    print("\n步骤 2: 启动浏览器...")
    print(f"  ChromeDriver 路径: {CHROMEDRIVER_PATH}")
    service = Service(executable_path=CHROMEDRIVER_PATH)
    driver = webdriver.Chrome(service=service, options=options)
    print("  ✅ 浏览器已启动")
    
    time.sleep(2)
    
    print("\n步骤 3: 注入反检测脚本...")
    driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
        'source': '''
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
        '''
    })
    print("  ✅ 反检测脚本已注入")
    
    print("\n步骤 4: 测试访问百度...")
    driver.get('https://www.baidu.com')
    time.sleep(2)
    print(f"  当前URL: {driver.current_url}")
    print(f"  页面标题: {driver.title}")
    
    if 'baidu.com' in driver.current_url:
        print("  ✅ 百度访问成功")
    else:
        print(f"  ⚠️ 百度访问异常，当前URL: {driver.current_url}")
    
    print("\n步骤 5: 测试访问知乎...")
    driver.get('https://www.zhihu.com')
    time.sleep(3)
    print(f"  当前URL: {driver.current_url}")
    print(f"  页面标题: {driver.title}")
    
    if 'zhihu.com' in driver.current_url:
        print("  ✅ 知乎访问成功")
    else:
        print(f"  ⚠️ 知乎访问异常，当前URL: {driver.current_url}")
    
    print("\n步骤 6: 测试访问知乎问题...")
    test_url = 'https://www.zhihu.com/question/19550225'
    driver.get(test_url)
    time.sleep(3)
    print(f"  当前URL: {driver.current_url}")
    print(f"  页面标题: {driver.title}")
    
    if 'question' in driver.current_url:
        print("  ✅ 知乎问题页访问成功")
    else:
        print(f"  ⚠️ 知乎问题页访问异常，当前URL: {driver.current_url}")
    
    print("\n" + "="*60)
    print("🎉 所有测试通过！")
    print("="*60)
    print("\n✅ ChromeDriver 配置正确")
    print("✅ 网络连接正常")
    print("✅ 知乎可以访问")
    print("\n如果应用仍然无法工作，问题可能在应用代码逻辑中。")
    print("请运行应用并复制完整的日志输出。")
    
    print("\n浏览器将在 5 秒后关闭...")
    time.sleep(5)
    driver.quit()
    print("✅ 测试完成")
    
except Exception as e:
    print(f"\n" + "="*60)
    print("❌ 测试失败")
    print("="*60)
    print(f"\n错误信息: {e}")
    print("\n完整错误堆栈:")
    import traceback
    traceback.print_exc()
    print("\n可能的原因:")
    print("  1. ChromeDriver 版本与 Chrome 浏览器版本不匹配")
    print("  2. ChromeDriver 路径不正确")
    print("  3. 网络连接问题")
    print("  4. 防火墙阻止")
    
    input("\n按回车键退出...")

