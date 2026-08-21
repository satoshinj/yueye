# Yueye · 阅页

<p align="center">
  <strong>Turn online documents you already have access to into searchable offline copies.</strong>
</p>

<p align="center">
  <a href="https://yueye.jingzhiacademy.com/"><img src="https://img.shields.io/badge/Website-yueye.jingzhiacademy.com-blue?style=flat-square" alt="Website" /></a>
  <a href="https://github.com/satoshinj/yueye/releases"><img src="https://img.shields.io/github/v/release/satoshinj/yueye?style=flat-square&color=success" alt="Release" /></a>
  <img src="https://img.shields.io/badge/Platform-Windows%2010%20%2F%2011-lightgrey?style=flat-square" alt="Platform" />
  <img src="https://img.shields.io/badge/License-MIT-orange?style=flat-square" alt="License" />
</p>

<p align="center">
  <a href="README.md">简体中文</a> |
  <b>English</b> |
  <a href="README_JA.md">日本語</a> |
  <a href="README_KO.md">한국어</a> |
  <a href="README_ES.md">Español</a> |
  <a href="README_FR.md">Français</a> |
  <a href="README_DE.md">Deutsch</a> |
  <a href="README_RU.md">Русский</a>
</p>

---

> [!IMPORTANT]
> **Compliance & Legal Notice**: This tool is designed solely for personal offline reading of content that you are **authorized and logged in to access**. Target servers stream content based on account permissions; inaccessible pages are never sent. It does not bypass paywalls, crack CAPTCHAs, or solve sliders automatically. See [DISCLAIMER.md](DISCLAIMER.md).

---

## ✨ Key Features

| Feature | Capabilities | Advantages |
|---|---|---|
| **Smart Route Detection** | Automatically chooses Article / Reader / Full Screenshot | Text-based articles produce **searchable text PDFs** (90% smaller size); Canvas readers output original raw pixels |
| **Ultra-Fast Performance** | Native `canvas.toDataURL` pixel dump + hash stability probe | **26 ms/page** image extraction (8x faster than screenshotting), benchmark 0.75s/page, export 100 pages in seconds |
| **Dynamic Page-Turning Trial** | Page Input → Next Button → Scroll Container → Keyboard | **No hardcoded CSS selectors**; runtime exploration determines and locks valid pagination mechanisms |
| **Fault Tolerance & Responsiveness** | Reader warm-up + backoff retry + instant stop | Auto-dismisses overlay popups upon failure; click "Stop" for immediate millisecond-level termination |
| **Broad Browser Compatibility** | Auto-detects Edge, Chrome, 360, QQ Browser, Brave, Cent | Cleans up stale locks (`SingletonLock`), strips automation banners, bypasses enterprise proxy/SSL errors |
| **Multi-Format & Page Range** | PDF (Text/Image) / Word / Markdown / Plain Text / Images | Supports custom page range (e.g. `1-10`); background async export prevents UI freezing |

---

## 🚀 Quick Start

### Option A: Portable Binary (Recommended · No Python Required)

1. Download `Yueye-v1.0.3-win-x64.zip` from [GitHub Releases](https://github.com/satoshinj/yueye/releases) and extract it.
2. Double-click `阅页.exe`:
   - Click **"登录浏览器" (Login Browser)** first: Log in to your target account (session is saved persistently).
   - Paste the document URL, select format and page range, and click **"开始抓取" (Start Crawling)**.

### Option B: CLI Mode (Batch Processing & Automation)

```cmd
# Export entire document to PDF
阅页.exe --url "https://..." --format pdf

# Export pages 1 to 10 as Markdown to a specific folder
阅页.exe --url "https://..." --format markdown --range 1-10 --out ./output

# Use a custom browser executable
阅页.exe --url "https://..." --browser "C:\Path\To\Chrome.exe"
```

### Option C: Run from Source (Developers)

```bash
git clone https://github.com/satoshinj/yueye.git
cd yueye
pip install -r requirements.txt
playwright install chromium
python app.py
```

---

## 📊 Platform Compatibility

| Platform Type | Target Platforms | Strategy | Validation Status |
|---|---|---|---|
| **Dedicated Adapter** | Doc88 (道客巴巴) | Custom reader adapter + annotation layer filter | ✅ Verified with end-to-end tests |
| **Structural Adapter** | RenrenDoc (人人文库) | Dedicated DOM extractor & navigation | ⚠️ Adapter implemented, unverified per-site |
| **Universal Detection** | Book118, Docin, Baidu Wenku, MBA Lib, 360 Doc, Taodocs, etc. | `AutoReader` runtime pagination & canvas probe | ⚠️ Generic detection, results depend on site changes |

> 📌 **Content retrieval strictly depends on your own account permissions.**

---

## 🛠️ Testing & Building

```bash
# Run 11 offline behavioral regression tests (local fixtures, no network needed)
python tests/test_engine.py

# Build portable executable with automated selftest
build.bat
```

---

## 📝 License & Disclaimer

Released under the [MIT License](LICENSE).

Please read **[DISCLAIMER.md](DISCLAIMER.md)** before use. For mandatory national standards, please use official government portals; for academic papers, use institutional subscriptions or DOI open access.
