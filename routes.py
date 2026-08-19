# -*- coding: utf-8 -*-
"""抓取线路（route）：同一个 URL 可能适合不同的抓法，按内容形态选。

- reader  分页阅读器（canvas/图片翻页）  -> 图片型 PDF
- article 普通网页文章（正文在 DOM 里）  -> 文字型 PDF，可选中可搜索
- shot    兜底：整页截图                 -> 图片型 PDF

article 线路质量最高（体积小一个数量级且可搜索），只要正文在 DOM 里就优先走它。
"""
from __future__ import annotations

import json
import re

# 正文容器候选，按可靠性排序
CONTENT_SELECTORS = [
    "article",
    "[role='main']",
    "main",
    "#content", ".content",
    ".article-content", ".article_content", ".articleContent",
    ".post-content", ".post_content", ".entry-content",
    "#article", ".article", ".art_content", ".detail-content",
    "#js_content",            # 微信公众号
    ".rich_media_content",    # 微信公众号
    ".markdown-body",         # GitHub / 掘金
    "#js_article",
]

# 打印时要隐藏的页面杂项
NOISE_SELECTORS = [
    "header", "footer", "nav", "aside",
    ".header", ".footer", ".nav", ".navbar", ".sidebar", ".side-bar",
    ".ad", ".ads", ".advert", ".advertisement", ".recommend", ".related",
    ".comment", ".comments", "#comment", "#comments",
    ".share", ".toolbar", ".breadcrumb", ".pagination",
    ".float", ".fixed-bar", ".back-top", ".qrcode",
]


def find_article(page) -> dict | None:
    """找页面正文容器，返回 {selector, chars, title}；找不到返回 None。

    选文字量最大的候选容器；文字太少视为不是文章页。
    """
    js = """() => {
        const SELS = %s;
        let best = null;
        for (const sel of SELS) {
            let els;
            try { els = document.querySelectorAll(sel); } catch (e) { continue; }
            for (const el of els) {
                const t = (el.innerText || '').trim();
                if (!best || t.length > best.chars) {
                    best = {selector: sel, chars: t.length};
                }
            }
        }
        // 兜底：全文最长的 div
        if (!best || best.chars < 200) {
            let bd = null;
            for (const d of document.querySelectorAll('div, section')) {
                const t = (d.innerText || '').trim();
                // 只要叶子密度高的块，避免选到 body 的包裹层
                if (t.length > 300 && d.querySelectorAll('div, section').length < 30) {
                    if (!bd || t.length > bd.chars) bd = {selector: '', chars: t.length,
                                                          path: d.id ? '#' + d.id : ''};
                }
            }
            if (bd && (!best || bd.chars > best.chars)) best = bd;
        }
        return JSON.stringify({best: best, title: document.title || '',
                               bodyChars: (document.body.innerText || '').length});
    }""" % json.dumps(CONTENT_SELECTORS)
    try:
        raw = page.evaluate(js)
        data = json.loads(raw) if isinstance(raw, str) else None
    except Exception:
        return None
    if not data or not data.get("best"):
        return None
    best = data["best"]
    if best.get("chars", 0) < 200:
        return None
    return {"selector": best.get("selector") or "", "chars": best["chars"],
            "title": data.get("title", ""), "body_chars": data.get("bodyChars", 0)}


def clean_for_print(page, keep_selector: str = "") -> None:
    """注入打印样式：隐藏导航/广告/评论等杂项，只留正文。"""
    css = """
      @page { margin: 14mm 12mm; }
      body { background: #fff !important; }
      %s { display: none !important; }
      * { animation: none !important; transition: none !important; }
      img, table, pre { break-inside: avoid; max-width: 100%% !important; height: auto !important; }
    """ % ", ".join(NOISE_SELECTORS)
    try:
        page.add_style_tag(content=css)
    except Exception:
        pass

    # 有明确正文容器时，把它提升为唯一可见内容，避免打印出整站框架
    if keep_selector:
        js = """(sel) => {
            const el = document.querySelector(sel);
            if (!el) return false;
            let node = el;
            while (node && node !== document.body) {
                for (const sib of Array.from(node.parentElement.children)) {
                    if (sib !== node) sib.style.display = 'none';
                }
                node = node.parentElement;
            }
            document.body.style.display = 'block';
            return true;
        }"""
        try:
            page.evaluate(js, keep_selector)
        except Exception:
            pass


def render_article_pdf(page, keep_selector: str = "") -> bytes | None:
    """把当前页渲染成文字型 PDF（中文原生可选中、可搜索）。"""
    clean_for_print(page, keep_selector)
    page.wait_for_timeout(300)
    try:
        return page.pdf(format="A4", print_background=True,
                        margin={"top": "14mm", "bottom": "14mm",
                                "left": "12mm", "right": "12mm"})
    except Exception:
        return None


def article_text(page, selector: str = "") -> str:
    """提取正文文字，供 txt / markdown 导出。"""
    try:
        if selector:
            el = page.query_selector(selector)
            if el:
                return el.inner_text()
        return page.inner_text("body")
    except Exception:
        return ""


def expand_lazy_content(page, log=lambda m: None, max_rounds: int = 30,
                        pause_ms: int = 350) -> None:
    """滚到底，触发懒加载图片与「加载更多」，直到高度不再增长。

    文章页常见的分段懒加载：不滚到底就只能打印出前一屏。
    """
    last_h = 0
    for i in range(max_rounds):
        h = page.evaluate("() => document.body.scrollHeight") or 0
        if h == last_h and i > 1:
            break
        last_h = h
        page.evaluate("() => window.scrollTo(0, document.body.scrollHeight)")
        page.wait_for_timeout(pause_ms)
        # 点常见的「展开全文 / 加载更多」
        for txt in ["展开全文", "阅读全文", "加载更多", "查看全文"]:
            try:
                el = page.query_selector(f"text={txt}")
                if el and el.is_visible():
                    el.click(timeout=1000)
                    page.wait_for_timeout(600)
            except Exception:
                pass
    # 把懒加载 img 的 data-src 落到 src
    try:
        page.evaluate("""() => {
            for (const img of document.querySelectorAll('img[data-src], img[data-original]')) {
                const s = img.dataset.src || img.dataset.original;
                if (s && !img.src.startsWith('data:') ) img.src = s;
            }
            window.scrollTo(0, 0);
        }""")
    except Exception:
        pass
    page.wait_for_timeout(400)


def full_page_shot(page) -> bytes | None:
    """兜底线路：整页截图。"""
    try:
        return page.screenshot(full_page=True, type="png")
    except Exception:
        return None
