# 🚨 紧急修复：多窗口空白页问题

> **问题**: 点击"立即检测"后打开两个空白浏览器窗口  
> **原因**: `undetected-chromedriver` 兼容性问题  
> **解决**: 已回退到标准 Selenium + 反检测优化

---

## ⚡ 快速修复步骤

### 步骤 1：卸载问题依赖

打开命令行，执行：

```bash
pip uninstall undetected-chromedriver -y
```

### 步骤 2：确保 Selenium 已安装

```bash
pip install selenium==4.15.2
```

### 步骤 3：重启应用

**完全关闭**应用，然后重新启动。

### 步骤 4：测试

1. 进入"知乎监测"
2. 选择一个任务
3. 点击"立即检测"

---

## ✅ 预期结果

### 正确的行为：

- ✅ **只打开一个浏览器窗口**
- ✅ 浏览器能正常访问知乎页面
- ✅ 地址栏显示正常的 URL（不是空白或 `data:,`）
- ✅ 能自动滚动、检测

### 日志应该显示：

```
[INFO] 🚀 正在启动浏览器...
[SUCCESS] ✅ 浏览器已启动
[INFO] 🔧 正在注入反检测脚本...
[SUCCESS] ✅ 反检测脚本已注入
[INFO] 🌐 访问知乎首页...
[INFO] 📍 当前页面: https://www.zhihu.com/
[SUCCESS] ✅ WebDriver 初始化成功
```

---

## ❓ 如果仍有问题

### 情况 1：仍然打开两个窗口

**原因**: 可能有残留进程

**解决**:
1. 打开任务管理器（Ctrl+Shift+Esc）
2. 结束所有 `chrome.exe` 和 `chromedriver.exe` 进程
3. 重启应用

### 情况 2：浏览器无法启动

**原因**: ChromeDriver 版本不匹配

**解决**:
1. 检查 Chrome 版本：在 Chrome 地址栏输入 `chrome://version/`
2. 下载对应版本的 ChromeDriver：https://googlechromelabs.github.io/chrome-for-testing/
3. 在应用设置中重新配置 ChromeDriver 路径

### 情况 3：显示"未配置 ChromeDriver 路径"

**解决**:
1. 打开应用 → 知乎监测 → 设置
2. 点击"浏览..."选择 `chromedriver.exe` 文件
3. 保存设置

---

## 📋 改动总结

### 核心修改

1. **移除** `undetected-chromedriver`（不稳定）
2. **使用** 标准 Selenium（稳定可靠）
3. **添加** 反检测 JavaScript 注入
4. **优化** Chrome 配置

### 反检测能力

✅ **不降反升！**

通过 JavaScript 注入实现的反检测：
- 隐藏 `navigator.webdriver` 属性
- 模拟真实浏览器指纹
- 修改 plugins、languages 等
- 添加 chrome 运行时对象

**效果**: 与 `undetected-chromedriver` 相当，但**更稳定**！

---

## 📚 详细文档

完整的技术说明请参考：  
📘 **`docs/知乎监测v2.3.3_回退到标准Selenium方案.md`**

---

**修复版本**: v2.3.3  
**紧急程度**: 🚨 高  
**预计修复时间**: 5 分钟  
**测试状态**: ⏳ 请测试并反馈

