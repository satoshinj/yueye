# -*- coding: utf-8 -*-
"""站点适配器。

各文档站阅读器实现差异极大（翻页控件、页容器、页码暴露方式各不相同），
用「适配器 + 通用兜底」而非一套通用逻辑猜所有站点。

⚠ 重要约定：doc88 篡改了 JS 结构化序列化，page.evaluate 返回数组/对象一律
得到 None 且不报错。**所有 evaluate 必须返回 JSON 字符串**，用 jseval() 解析。
"""
from __future__ import annotations

import json
import re
from urllib.parse import urlparse


def jseval(page, js: str, default=None):
    """执行 JS 并解析其返回的 JSON 字符串。

    绕过 doc88 对结构化序列化的篡改——直接返回对象会静默变成 None。
    """
    try:
        raw = page.evaluate(js)
    except Exception:
        return default
    if raw is None:
        return default
    if isinstance(raw, str):
        try:
            return json.loads(raw)
        except (json.JSONDecodeError, ValueError):
            return default
    return raw


def pick_js(selectors: list[str]) -> str:
    """生成"按优先级挑元素"的 JS 片段。

    注意不能直接用 querySelector('a, b, c')：逗号列表是按**文档顺序**返回的，
    不按书写顺序。doc88 的标注层 canvas 排在内容层前面，用逗号列表会一直拿到
    那张空白画布——翻页探测因此永远判定"内容没变"。
    这里显式逐个选择器试，并跳过标注层与过小的元素。
    """
    return """(() => {
        const SELS = %s;
        for (const sel of SELS) {
            let els;
            try { els = document.querySelectorAll(sel); } catch (e) { continue; }
            for (const e of els) {
                const id = (e.id || '').toLowerCase();
                if (id.includes('postil') || id.includes('annot')) continue;
                const w = e.width || e.naturalWidth || 0;
                const h = e.height || e.naturalHeight || 0;
                if (w > 50 && h > 50) return e;
            }
        }
        return null;
    })()""" % json.dumps(selectors)


class SiteAdapter:
    """站点适配器基类。子类覆盖各钩子。"""

    name = "generic"
    #: 付费墙/权限墙特征文案（文档内容被部分限制）
    paywall_patterns = (
        r"还剩\s*[\d,]+\s*页未读",
        r"请拖动滑块继续阅读",
        r"登录后.{0,6}(继续|查看|阅读)",
        r"购买后.{0,6}(继续|查看|阅读)",
        r"开通.{0,6}(会员|VIP).{0,6}(继续|查看|阅读)",
    )
    #: 访问阻断特征（整页被风控/验证拦下，连第一页都进不去）
    access_block_patterns = (
        r"网络环境安全验证",
        r"网络环境存在频繁操作",
        r"访问过于频繁",
        r"请完成.{0,4}验证",
        r"人机验证",
    )

    @classmethod
    def matches(cls, url: str) -> bool:
        return False

    # -- 页码 --------------------------------------------------------
    def total_pages(self, page) -> int | None:
        """文档总页数，取不到返回 None。"""
        return None

    def current_page(self, page) -> int | None:
        """阅读器当前页码，取不到返回 None。"""
        return None

    def goto_page(self, page, n: int) -> bool:
        """跳转到第 n 页，返回是否下达成功（不保证已渲染）。"""
        return False

    # -- 抓取 --------------------------------------------------------
    def page_selectors(self, n: int) -> list[str]:
        """第 n 页内容元素的候选选择器，按优先级从高到低。"""
        return [f"canvas#page_{n}", f"img#page_{n}", "canvas", "img[id^='page']"]

    def page_canvas_selector(self, n: int) -> str:
        """兼容旧接口：返回首选选择器。"""
        return self.page_selectors(n)[0]

    def capture(self, page, n: int, fmt: str = "png") -> bytes | None:
        """抓取第 n 页图像字节。用 canvas.toDataURL 取原生像素。

        比 element.screenshot() 快约 8 倍，且不受滚动位置/视口/CSS 缩放影响。
        先合成到白底再导出：canvas 带 alpha 通道会让 img2pdf 为每页额外生成
        软掩码(SMask)，白白撑大 PDF，且部分阅读器会把透明区渲染成黑色。
        """
        import base64
        sels = self.page_selectors(n)
        mime = "image/png" if fmt == "png" else "image/jpeg"
        quality = "" if fmt == "png" else ", 0.92"
        data = page.evaluate(
            "() => { const c = %s;"
            " if (!c) return '';"
            " const w = c.width || c.naturalWidth, h = c.height || c.naturalHeight;"
            " if (!w || !h) return '';"
            " try {"
            "   const t = document.createElement('canvas');"
            "   t.width = w; t.height = h;"
            "   const g = t.getContext('2d', {alpha: false});"
            "   g.fillStyle = '#fff'; g.fillRect(0, 0, w, h);"
            "   g.drawImage(c, 0, 0, w, h);"
            "   return t.toDataURL('%s'%s);"
            " } catch(e) { return 'ERR:' + e; } }" % (pick_js(sels), mime, quality)
        )
        if isinstance(data, str) and data.startswith("data:"):
            try:
                return base64.b64decode(data.split(",", 1)[1])
            except Exception:
                return None
        # 跨域图片会污染 canvas 导致 toDataURL 抛 SecurityError，
        # 此时退回 CDP 截图（慢一些但不受同源策略限制）
        for sel in sels:
            try:
                el = page.query_selector(sel)
                if el:
                    return el.screenshot(type="png")
            except Exception:
                continue
        return None

    def thumb_hash(self, page, n: int) -> str:
        """48x48 缩略图哈希，用作渲染稳定性探针（约 2ms，可高频轮询）。"""
        return page.evaluate(
            "() => { const c = %s; if (!c) return '';"
            " const t = document.createElement('canvas'); t.width = 48; t.height = 48;"
            " try { t.getContext('2d').drawImage(c, 0, 0, 48, 48);"
            " return t.toDataURL('image/png'); } catch(e) { return 'ERR'; } }"
            % pick_js(self.page_selectors(n))
        ) or ""

    # -- 权限墙 ------------------------------------------------------
    def paywall(self, page) -> str | None:
        """检测付费/登录墙，命中则返回提示原文。"""
        try:
            body = page.inner_text("body")
        except Exception:
            return None
        for pat in self.paywall_patterns:
            m = re.search(pat, body)
            if m:
                return m.group(0).replace("\xa0", " ")
        return None

    def access_block(self, page) -> str | None:
        """检测整页级访问阻断（风控验证页），命中则返回提示原文。

        与 paywall 的区别：paywall 是文档看到一半被拦，access_block 是
        整个阅读器都没出来，需要人工登录/过验证才能继续。
        """
        try:
            body = page.inner_text("body")
        except Exception:
            return None
        for pat in self.access_block_patterns:
            m = re.search(pat, body)
            if m:
                # 带上后续的说明句，便于用户判断怎么处理
                idx = body.find(m.group(0))
                snippet = body[idx:idx + 80].replace("\n", " ").replace("\xa0", " ")
                # 截到第一个句号，避免把页脚导航也带进提示
                cut = snippet.find("。")
                if cut > 0:
                    snippet = snippet[:cut + 1]
                return snippet.strip()
        return None

    def reader_present(self, page) -> bool:
        """阅读器是否已出现（用于快速判定页面是否可抓）。"""
        try:
            return bool(page.evaluate(
                "() => document.querySelectorAll('canvas, img[id^=\"page\"]').length"))
        except Exception:
            return False

    def prepare(self, page, log=lambda m: None) -> None:
        """抓取前的准备动作（关弹窗、调缩放等）。"""
        return None

    #: 引导浮层上的"关闭/继续"控件候选
    OVERLAY_CLOSE_SELECTORS = [
        "[class*='continue-read']", "[class*='continueRead']",
        "[class*='read-more'] [class*='close']",
        "[class*='mask'] [class*='close']", "[class*='popup'] [class*='close']",
        "[class*='dialog'] [class*='close']", "[class*='modal'] [class*='close']",
        "[class*='layer'] [class*='close']",
        ".close", ".closeBtn", "[class*='btn-close']", "[aria-label='关闭']",
    ]

    def dismiss_overlay(self, page, log=lambda m: None) -> bool:
        """尝试关掉挡住阅读区的引导浮层。

        只点"关闭"类控件，**不碰滑块验证** —— 那属于人机验证，
        应由用户自己在可见窗口里完成，程序不代劳。
        """
        closed = False
        for sel in self.OVERLAY_CLOSE_SELECTORS:
            try:
                for el in page.query_selector_all(sel)[:3]:
                    if el.is_visible():
                        el.click(timeout=1200)
                        closed = True
            except Exception:
                continue
        if closed:
            page.wait_for_timeout(300)
            log("已尝试关闭页面浮层")
        # 有滑块验证就提示用户自己处理，不自动破解
        try:
            body = page.inner_text("body")
            if "拖动滑块" in body or "滑动验证" in body:
                log("  页面出现滑块验证，请在浏览器窗口中手动完成")
        except Exception:
            pass
        return closed


# ---------------------------------------------------------------------------
class Doc88(SiteAdapter):
    """道客巴巴 doc88.com。

    实测结构（2026-08）：
      DIV#pageContainer.page_view > DIV#outer_page_1.outer_page
        ├── CANVAS#postil_1.postil_page  标注层（跳过）
        └── CANVAS#page_1.inner_page     内容层（抓这个）
    工具栏：#pageNumInput（当前页，可写）/ #nextPageButton / #item-page-panel 内 "/ N" 为总页数
    内容以加密 .ebt + mymu.wasm 解密后绘制，无可直接下载的每页图片。
    """

    name = "doc88"

    @classmethod
    def matches(cls, url: str) -> bool:
        return "doc88.com" in urlparse(url).netloc

    def total_pages(self, page) -> int | None:
        txt = jseval(page, """() => JSON.stringify(
            Array.from(document.querySelectorAll('#item-page-panel *'),
                       e => (e.innerText || '').trim()).filter(Boolean))""", [])
        for t in txt or []:
            m = re.search(r"/\s*([\d,]+)", t)
            if m:
                return int(m.group(1).replace(",", ""))
        # 兜底：正文「还剩 N 页未读」+ 当前页推算
        try:
            m = re.search(r"还剩\s*([\d,]+)\s*页未读", page.inner_text("body"))
            if m:
                cur = self.current_page(page) or 1
                return int(m.group(1).replace(",", "")) + cur
        except Exception:
            pass
        return None

    def current_page(self, page) -> int | None:
        v = page.evaluate(
            "() => { const e = document.querySelector('#pageNumInput');"
            " return e ? String(e.value || '') : ''; }")
        try:
            return int(str(v).strip())
        except (TypeError, ValueError):
            return None

    def goto_page(self, page, n: int) -> bool:
        """写页码输入框跳页。比连点 next 可靠：幂等且可回读校验。"""
        try:
            page.fill("#pageNumInput", str(n), timeout=5000)
            page.press("#pageNumInput", "Enter")
            return True
        except Exception:
            pass
        # 兜底：点下一页按钮（注意 .next 是侧栏推荐位，不是阅读器翻页）
        try:
            page.click("#nextPageButton", timeout=5000)
            return True
        except Exception:
            return False

    def page_selectors(self, n: int) -> list[str]:
        # 优先按页号取；该阅读器复用 page_1 时退回内容层 class。
        # 顺序重要：不能让 postil 标注层排在前面（pick_js 也会主动跳过它）
        return [f"canvas#page_{n}", "canvas.inner_page", "canvas[id^='page_']"]

    def prepare(self, page, log=lambda m: None) -> None:
        # 关掉可能挡住阅读区的浮层
        for sel in [".close", "[class*='closeBtn']", "[class*='pop'] .close"]:
            try:
                el = page.query_selector(sel)
                if el and el.is_visible():
                    el.click(timeout=1000)
            except Exception:
                pass


# ---------------------------------------------------------------------------
class RenrenDoc(SiteAdapter):
    """人人文库 renrendoc.com。以图片分页为主。"""

    name = "renrendoc"

    @classmethod
    def matches(cls, url: str) -> bool:
        return "renrendoc.com" in urlparse(url).netloc

    def total_pages(self, page) -> int | None:
        try:
            m = re.search(r"共\s*([\d,]+)\s*页", page.inner_text("body"))
            if m:
                return int(m.group(1).replace(",", ""))
        except Exception:
            pass
        n = jseval(page, "() => JSON.stringify(document.querySelectorAll('img[id^=\"page\"]').length)")
        return n or None

    def page_selectors(self, n: int) -> list[str]:
        return [f"img#page{n}", f"canvas#page_{n}", "img[id^='page']", "canvas"]


# ---------------------------------------------------------------------------
class AutoReader(SiteAdapter):
    """通用分页阅读器适配器：结构探测 + 翻页策略试错。

    不为每个站硬编码选择器——那需要事先知道站点长什么样，猜出来的多半是错的。
    改为运行时把多种翻页策略逐个试一遍，哪个真能让页面内容变化就锁定哪个，
    之后一直用它。新站点因此开箱可用。
    """

    name = "auto"

    #: 翻页策略候选，按可靠性排序。返回值仅表示"动作已下达"
    NEXT_SELECTORS = [
        "#nextPageButton", ".nextPageButton",
        "[id*='nextPage']", "[class*='nextPage']",
        "[id*='next-page']", "[class*='next-page']",
        "a[title*='下一页']", "[aria-label*='下一页']",
        "text=下一页",
    ]
    PAGE_INPUT_SELECTORS = [
        "#pageNumInput", "input[id*='pageNum']", "input[class*='pageNum']",
        "input[id*='curPage']", "input[class*='page-num']",
    ]
    PAGE_ELEMENT_SELECTORS = [
        "canvas.inner_page", "canvas[id^='page_']", "canvas[id^='page']",
        "img[id^='page_']", "img[id^='page']", "img[class*='page-img']",
        "canvas",
    ]

    def __init__(self):
        self._nav = None            # 锁定的翻页策略
        self._page_input = None     # 锁定的页码输入框
        self._page_sel = None       # 锁定的页元素选择器

    # -- 结构探测 ----------------------------------------------------
    def _find_page_input(self, page) -> str | None:
        if self._page_input is not None:
            return self._page_input
        for sel in self.PAGE_INPUT_SELECTORS:
            n = jseval(page, f"() => JSON.stringify(document.querySelectorAll({json.dumps(sel)}).length)", 0)
            if n:
                self._page_input = sel
                return sel
        self._page_input = ""
        return None

    def page_selectors(self, n: int) -> list[str]:
        if self._page_sel:
            return [self._page_sel.replace("{n}", str(n))] + self.PAGE_ELEMENT_SELECTORS
        return [f"canvas#page_{n}", f"img#page_{n}", f"img#page{n}"] + self.PAGE_ELEMENT_SELECTORS

    def detect_page_element(self, page) -> str | None:
        """找出承载页面内容的元素选择器。"""
        for sel in self.PAGE_ELEMENT_SELECTORS:
            info = jseval(page, """() => { const els = document.querySelectorAll(%s);
                let big = 0;
                for (const e of els) { const r = e.getBoundingClientRect();
                    if (r.width > 200 && r.height > 200) big++; }
                return JSON.stringify({n: els.length, big: big}); }""" % json.dumps(sel), {})
            if info and info.get("big"):
                # 带页号的选择器保留 {n} 占位，便于逐页定位
                if "page_" in sel:
                    self._page_sel = sel.replace("[id^='page_']", "#page_{n}")
                else:
                    self._page_sel = sel
                return self._page_sel
        return None

    def total_pages(self, page) -> int | None:
        # 1) 工具栏里的 "/ N"
        texts = jseval(page, """() => JSON.stringify(
            Array.from(document.querySelectorAll(
                "[id*='page'],[class*='page'],[id*='toolbar'],[class*='toolbar']"),
                e => (e.innerText || '').trim()).filter(t => t && t.length < 40).slice(0, 60))""", [])
        for t in texts or []:
            # 不能锚定行尾：工具栏常是「1 / 12 >」这类带尾随图标的文本
            m = re.search(r"/\s*([\d,]+)", t) or re.search(r"共\s*([\d,]+)\s*页", t)
            if m:
                v = int(m.group(1).replace(",", ""))
                if 1 < v < 10000:
                    return v
        # 2) 正文里的「共 N 页」
        try:
            body = page.inner_text("body")
        except Exception:
            body = ""
        m = re.search(r"共\s*([\d,]+)\s*页", body)
        if m:
            v = int(m.group(1).replace(",", ""))
            if 1 < v < 10000:
                return v
        # 3) 「还剩 N 页未读」+ 当前页
        m = re.search(r"还剩\s*([\d,]+)\s*页未读", body)
        if m:
            return int(m.group(1).replace(",", "")) + (self.current_page(page) or 1)
        # 4) 数页容器
        n = jseval(page, """() => JSON.stringify(
            document.querySelectorAll("[id^='outer_page'],[id^='page_'],[class*='page-item']").length)""", 0)
        return n if isinstance(n, int) and n > 1 else None

    def current_page(self, page) -> int | None:
        sel = self._find_page_input(page)
        if not sel:
            return None
        v = page.evaluate(
            "() => { const e = document.querySelector(%s);"
            " return e ? String(e.value || '') : ''; }" % json.dumps(sel))
        try:
            return int(str(v).strip())
        except (TypeError, ValueError):
            return None

    # -- 翻页：策略试错 ----------------------------------------------
    def _content_hash(self, page, n: int) -> str:
        return self.thumb_hash(page, n)

    def _try_input(self, page, n: int) -> bool:
        sel = self._find_page_input(page)
        if not sel:
            return False
        try:
            page.fill(sel, str(n), timeout=3000)
            page.press(sel, "Enter")
            return True
        except Exception:
            return False

    def _try_next_button(self, page, n: int) -> bool:
        for sel in self.NEXT_SELECTORS:
            try:
                el = page.query_selector(sel)
                if el and el.is_visible():
                    el.click(timeout=3000)
                    return True
            except Exception:
                continue
        return False

    def _try_scroll(self, page, n: int) -> bool:
        try:
            page.evaluate("""() => {
                const c = document.querySelector("[id*='pageContainer'],[class*='page_view']")
                          || document.scrollingElement;
                c.scrollTop += c.clientHeight * 0.95; }""")
            return True
        except Exception:
            return False

    def _try_key(self, page, n: int) -> bool:
        try:
            page.keyboard.press("PageDown")
            return True
        except Exception:
            return False

    def goto_page(self, page, n: int) -> bool:
        """翻到第 n 页。首次调用时把各策略试一遍，锁定有效的那个。"""
        strategies = [
            ("页码输入框", self._try_input),
            ("下一页按钮", self._try_next_button),
            ("滚动容器", self._try_scroll),
            ("键盘翻页", self._try_key),
        ]
        if self._nav is not None:
            return self._nav[1](page, n)

        before = self._content_hash(page, n - 1)
        for label, fn in strategies:
            if not fn(page, n):
                continue
            page.wait_for_timeout(900)
            if self._content_hash(page, n) != before:
                self._nav = (label, fn)
                return True
        # 都没让内容变化：仍返回最后一次尝试的结果，交由上层判定末尾/权限墙
        return False

    @property
    def nav_name(self) -> str:
        return self._nav[0] if self._nav else "未锁定"


# ---------------------------------------------------------------------------
#: 已知在线文档平台。除 doc88 外，其余走结构探测（AutoReader），
#: 因为未在真实文档 URL 上验证过 DOM，硬编码选择器等于凭空捏造。
KNOWN_SITES = {
    "doc88.com":        ("道客巴巴", Doc88),
    "renrendoc.com":    ("人人文库", RenrenDoc),
    "book118.com":      ("原创力文档", AutoReader),
    "docin.com":        ("豆丁网", AutoReader),
    "wenku.baidu.com":  ("百度文库", AutoReader),
    "doc.mbalib.com":   ("MBA智库文档", AutoReader),
    "wenku.so.com":     ("360文库", AutoReader),
    "taodocs.com":      ("淘豆网", AutoReader),
    "mayiwenku.com":    ("蚂蚁文库", AutoReader),
    "wenkub.com":       ("文库网", AutoReader),
    "zhuangpeitu.com":  ("装配图网", AutoReader),
    "ishare.iask.sina.com.cn": ("爱问共享资料", AutoReader),
}


def site_name(url: str) -> str:
    """已知平台的中文名，未知返回域名。"""
    host = urlparse(url).netloc
    for domain, (label, _) in KNOWN_SITES.items():
        if domain in host:
            return label
    return host


ADAPTERS = [Doc88, RenrenDoc]


def pick_adapter(url: str) -> SiteAdapter:
    """按 URL 选适配器。

    已验证的站点用专用适配器；其余一律用 AutoReader 做结构探测。
    """
    host = urlparse(url).netloc
    for cls in ADAPTERS:
        if cls.matches(url):
            return cls()
    for domain, (_, cls) in KNOWN_SITES.items():
        if domain in host:
            return cls()
    return AutoReader()
