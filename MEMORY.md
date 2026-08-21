# MEMORY.md · 阅页 Yueye

记录跨会话有用的事实：踩过的坑、外部入口、非显而易见的决策。
**不记**代码里能查到的结构，**不记**任何凭据值。

---

## 外部入口

| 项 | 位置 |
|---|---|
| 仓库 | `https://github.com/bitcoinjohnny/yueye` · **public** · 分支 `master` |
| Release | 当前 **v1.0.3** · 上一版 v1.0.2、v1.0.1、v1.0.0 保留。
| 官网 / 主页 | `https://yueye.jingzhiacademy.com/` | |
| 登录态 | `%USERPROFILE%\.docsaver\browser`（持久化浏览器上下文，**不在**发布包里） |

---

## 关键决策与原因

### 用系统 Edge，不打包 Chromium
Playwright 自带的 Chromium 有 320 MB。改用 `session.BROWSER_CHANNELS` 降级链
`msedge → chrome → 内置 chromium`，安装包省 320 MB，用户也不用跑 `playwright install`。
Windows 必装 Edge，代价几乎为零。

### 登录态用持久化上下文，不解密 Cookie
新版 Chrome/Edge 启用 App-Bound Encryption 后，从 SQLite 读 Cookie 已不可行。
`config.py` 里的 Cookie 读取代码仍在但主路径不用。

### 「还剩 N 页未读」是软信号
2026-08-19 实测：同一账号同一文档连抓 7 次，出现该提示的 6 次只抓到 1~5 页，
**唯一没出现该提示的那次抓满了 119 页**。证明它是异步引导浮层，不等于没权限。
旧逻辑一看到就 `break`，把有权限的用户挡在门外。已改为软信号 + 退避重试。
→ 回归测试 `T8 引导浮层不应被当成权限墙` 守这条。

### 名字
产品名 **阅页 Yueye**。2026-08-19 曾考虑「标准下载助手」，否决——
「标准」把国标获取这个最敏感的用途写进产品名，且「下载」不准确
（程序是渲染后存 PDF，不是拉原文件）。

---

## 踩过的坑（都很难查，别再踩）

### 1. 目标站篡改 JS 结构化序列化 ★最隐蔽
`page.evaluate` 返回**数组/对象一律得 `None`，且不报错**；返回 `JSON.stringify(...)` 字符串正常。
早期 6 个 `diagnose*.py` 全部「什么都探不到」就是这个原因，静默失败。
→ 一律用 `sites.jseval()`。

### 2. `querySelector('a, b, c')` 不表达优先级
逗号列表按**文档顺序**返回。doc88 的标注层 canvas 排在内容层前面，
用逗号列表会一直拿到空白画布 → 翻页探测永远判定「内容没变」。
→ 用 `sites.pick_js([...])` 逐个试，并跳过 id 含 `postil`/`annot` 的元素。

### 3. `_crawl_paginated()` 缺 `return`（已修）
旧版恒返回 `None`，导致永远走 `_crawl_single`（滚动截图）。
产出的 PDF「看起来成功」实际内容全错。**这是不静默降级原则的由来。**

### 4. `.next` 选择器点到推荐位轮播
doc88 侧栏推荐位也叫 `.next`。点它触发 `doc.php?act=moredoc&page=N`，与正文无关。
真正的翻页控件是 `#nextPageButton`（在 `#toolbar` 内）。

### 5. `QApplication` 作用域崩溃（已修）
`main()` 的 `except` 块里写 `app = QApplication.instance() or ...`，
赋值让 `QApplication` 在整个函数变成局部变量 → `try` 里首次使用即 `UnboundLocalError`。

### 6. 打包排除 `lxml` 会让 Word 导出崩
`python-docx` 依赖 `lxml`。排掉后 **GUI 启动完全正常**，要等用户点导出才炸。
→ 由 `selftest.exe` 抓到。`build.spec` 里有注释标注，别再排。

### 7. 冻结后 `Path(__file__).parent` 指向 `_internal\`
日志和导出的 PDF 会被写进程序内部目录。→ 用 `config.app_dir()`。

### 8. PyMuPDF 本机 wheel 缺 MSVC 运行库
`import fitz` 直接 DLL 报错。→ 已全部改用 `pypdf`（纯 Python）。

### 9. Playwright 版本落后会让 Edge 启动即关闭
1.44（2024）配 Edge 151（2026）表现为 `Target page, context or browser has been closed`，
容易被误判成「没装浏览器」。→ 已升到 1.62，requirements 钉 `>=1.62.0`。
**教训**：错误信息不要截断（早期 `[:80]` 截断掩盖了真因）。

### 10. `canvas.toDataURL` 固定输出 RGBA
`getContext('2d', {alpha:false})` 改不了 PNG 色彩类型。带 alpha 会让 img2pdf
为每页生成 SMask 撑大 PDF。→ 在 `exporter._strip_alpha()` 里剥离。

---

## 性能基线（本地 fixture，可公开引用）

| 项 | 数值 |
|---|---|
| 分页阅读器线路 | 约 0.75 秒/页 |
| `canvas.toDataURL` | 26 ms/页 |
| `element.screenshot()` | 211 ms/页（慢 8 倍） |
| 48×48 缩略哈希探针 | 约 2 ms |
| 文字型 PDF vs 图片型 | 73 KB 可搜索 vs 881 KB 不可搜索 |
