# 阅页 · Yueye

<p align="center">
  <strong>把你有权阅读的在线文档，收成清晰可搜的离线副本。</strong>
  <br />
  <em>Turn online documents you already have access to into searchable offline copies.</em>
</p>

<p align="center">
  <a href="https://yueye.jingzhiacademy.com/"><img src="https://img.shields.io/badge/官网-yueye.jingzhiacademy.com-blue?style=flat-square" alt="Website" /></a>
  <a href="https://github.com/satoshinj/yueye/releases"><img src="https://img.shields.io/github/v/release/satoshinj/yueye?style=flat-square&color=success" alt="Release" /></a>
  <img src="https://img.shields.io/badge/平台-Windows%2010%20%2F%2011-lightgrey?style=flat-square" alt="Platform" />
  <img src="https://img.shields.io/badge/协议-MIT-orange?style=flat-square" alt="License" />
</p>

<p align="center">
  <b>简体中文</b> |
  <a href="README_EN.md">English</a> |
  <a href="README_JA.md">日本語</a> |
  <a href="README_KO.md">한국어</a> |
  <a href="README_ES.md">Español</a> |
  <a href="README_FR.md">Français</a> |
  <a href="README_DE.md">Deutsch</a> |
  <a href="README_RU.md">Русский</a>
</p>

---

> [!IMPORTANT]
> **合规使用提醒**：本工具仅供个人离线保存**已登录且有权查看**的内容。服务端按权限下发数据，无权限页面不传输。不解密保护、不破解验证码、不代填滑块。详见 [DISCLAIMER.md](DISCLAIMER.md)。

---

## ✨ 核心特性

| 模块 | 核心能力 | 优势说明 |
|---|---|---|
| **智能线路判定** | 网页文章 / 分页阅读器 / 整页截图 自动选择 | DOM 文章优先输出**文字型 PDF**（可选中搜索，体积小 90%）；Canvas 阅读器出原生像素 |
| **极致性能** | `canvas.toDataURL` 读原生像素 + 哈希探针 | **26 ms/页** 取图（比传统截屏快 8 倍），画好即走（基准 0.75s/页），百页秒级导出 |
| **运行时试错** | 输入框 → 下一页按钮 → 滚动容器 → 键盘翻页 | **不硬编码选择器**，自动探测并锁定有效翻页方式，泛化支持各类文库 |
| **抗断与即时响应** | 预热机制 + 退避重试 + 毫秒级停止 | 前页卡顿自动重试与去遮挡；随时点击「停止」即刻退出，不被超时阻塞 |
| **多浏览器兼容** | 自动发现 Edge / Chrome / 360 / QQ / Brave / Cent | 自动清理僵尸锁，彻底去除自动化控制横幅，支持内网 SSL 与网络代理穿透 |
| **多格式与局部截取** | PDF（文字/图像）/ Word / Markdown / 纯文本 / 图片 | 支持指定页码区间（如 `1-10`）；导出在后台线程异步执行，界面不卡顿 |

---

## 🚀 快速开始

### 方式 A：免安装版（推荐 · 无需 Python 环境）

1. 从 [GitHub Releases](https://github.com/satoshinj/yueye/releases) 下载 `Yueye-v1.0.3-win-x64.zip` 并解压。
2. 双击运行 `阅页.exe`：
   - 先点 **「登录浏览器」**：在弹出窗口中登录目标平台账号（一次登录，长期有效）。
   - 粘贴文档链接，选好格式与页码范围，点击 **「开始抓取」** 即可。

### 方式 B：CLI 命令行（脚本化批处理）

```cmd
# 导出整篇文档为 PDF
阅页.exe --url "https://..." --format pdf

# 仅抓取第 1~10 页并导出为 Markdown 到指定目录
阅页.exe --url "https://..." --format markdown --range 1-10 --out ./output

# 指定本地特定浏览器路径运行
阅页.exe --url "https://..." --browser "C:\Path\To\360chrome.exe"
```

### 方式 C：源码运行（开发者）

```bash
git clone https://github.com/satoshinj/yueye.git
cd yueye
pip install -r requirements.txt
playwright install chromium      # 驱动本地 Edge 时无需下载完整内核
python app.py
```

---

## 📊 平台兼容性说明

| 平台类型 | 代表站点 | 支持策略 | 验证程度 |
|---|---|---|---|
| **专用适配** | 道客巴巴 (Doc88) | 专用翻页适配器 + 标注层过滤 | ✅ 逐项实测验证 |
| **结构适配** | 人人文库 (RenrenDoc) | 专用翻页与 DOM 结构提取 | ⚠️ 有适配器，未逐站验收 |
| **通用探测** | 原创力、豆丁、百度文库、MBA智库、360文库、淘豆等 | `AutoReader` 运行时探测翻页与像素 | ⚠️ 通用结构探测，效果视站点改版而定 |

> 📌 **能否获取内容严格取决于账号自身权限**；除道客巴巴外其余站点均为通用结构探测。

---

## 🛠️ 测试与打包

```bash
# 运行 11 组离线核心行为回归测试（本地 fixture，不依赖外网）
python tests/test_engine.py

# 一键打包免安装版并执行 selftest 自动化全链路自检
build.bat
```

---

## 📝 许可证与免责

代码以 [MIT License](LICENSE) 开源。

使用前请完整阅读 **[DISCLAIMER.md](DISCLAIMER.md)**。强制性国家标准请优先通过「国家标准全文公开系统」查阅；学术论文请优先走机构订阅、arXiv、PubMed Central 或按 DOI 查询开放获取版本。
