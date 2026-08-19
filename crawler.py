# -*- coding: utf-8 -*-
"""文档抓取引擎。

只抓取「用户本人已登录、有权查看」的内容：命中付费墙/权限墙时明确停止
并如实告知，绝不静默降级成整页滚动截图冒充成功。

设计要点（均经实测确定）：
- 用 canvas.toDataURL 取原生像素，比 element.screenshot() 快约 8 倍
- 48x48 缩略哈希做渲染稳定探针（约 2ms），替代固定 sleep
- 跳页后回读页码校验，失败重试
- 单页失败按退避重试 max_retries 次才放弃：阅读器常常只是还没渲染好，
  立刻放弃会把本来能抓全的文档丢掉
- 「还剩 N 页未读」这类提示只当**软信号**：实测同一账号同一文档连抓 7 次，
  出现该提示的 6 次只抓到 1~5 页，唯一没出现的那次抓满 119 页 ——
  它是异步引导浮层，不等于没权限，不能据此停止
"""
from __future__ import annotations

import hashlib
import time
from dataclasses import dataclass, field
from urllib.parse import urlparse

from playwright.sync_api import sync_playwright

import routes
import session as sess
from sites import pick_adapter, site_name


@dataclass
class PageData:
    """单页抽取结果。"""
    index: int
    screenshot: bytes | None = None
    text: str = ""


@dataclass
class CrawlResult:
    """一次抓取任务的完整结果。"""
    title: str = ""
    url: str = ""
    pages: list[PageData] = field(default_factory=list)
    full_text: str = ""
    total_pages: int | None = None      # 文档声称的总页数
    stopped_reason: str = ""            # 提前结束的原因（付费墙等）
    route: str = ""                     # 实际使用的抓取线路
    pdf_bytes: bytes | None = None      # 文章线路直接产出的文字型 PDF

    @property
    def page_count(self) -> int:
        return len(self.pages)

    @property
    def complete(self) -> bool:
        if self.route == "article":
            return bool(self.pdf_bytes) and not self.stopped_reason
        return bool(self.total_pages) and self.page_count >= self.total_pages


class DocCrawler:
    """文档抓取器。"""

    def __init__(self, headless: bool = False, cookies=None, user_agent: str | None = None,
                 log=None, image_format: str = "png", max_pages: int = 2000,
                 render_timeout: float = 8.0, poll_interval: float = 0.08,
                 should_stop=None, on_progress=None, block_ads: bool = True,
                 block_wait: float = 180.0, adapter=None, route: str = "",
                 max_retries: int = 4, **_ignored):
        # 有头是默认：doc88 等站点对 headless 有降级投喂，且滑块验证需人工完成
        self.headless = headless
        self.user_agent = user_agent
        self.log = log or (lambda msg: None)
        self.image_format = image_format
        self.max_pages = max_pages
        self.render_timeout = render_timeout
        self.poll_interval = poll_interval
        self.should_stop = should_stop or (lambda: False)
        self.on_progress = on_progress or (lambda cur, total: None)
        self.block_ads = block_ads
        # 有头模式下遇到风控验证页，留给用户手动处理的时间
        self.block_wait = block_wait
        # 显式指定适配器（测试用；正常按 URL 自动选）
        self.adapter = adapter
        # 强制线路: reader / article / shot；留空则自动判定
        self.route = route
        # 单页最多重试几次再放弃（阅读器常常只是还没渲染好）
        self.max_retries = max_retries

    # ------------------------------------------------------------------
    def crawl(self, url: str) -> CrawlResult:
        """打开 URL 并抓取有权查看的每一页。"""
        self.log(f"开始抓取: {url}")
        adapter = self.adapter or pick_adapter(url)
        self.log(f"站点: {site_name(url)} / 适配器: {adapter.name}")

        result = CrawlResult(url=url)
        with sync_playwright() as pw:
            ctx, page = sess.open_context(
                pw, headless=self.headless, user_agent=self.user_agent,
                block_ads=self.block_ads)
            self.log(f"浏览器: {sess.active_channel}")
            try:
                self._run(page, adapter, url, result)
            finally:
                try:
                    ctx.close()
                except Exception:
                    pass

        result.full_text = "\n\n".join(p.text for p in result.pages if p.text)
        done = result.page_count
        if result.total_pages:
            self.log(f"抓取完成: {done}/{result.total_pages} 页")
        else:
            self.log(f"抓取完成: 共 {done} 页")
        if result.stopped_reason:
            self.log(f"提前结束: {result.stopped_reason}")
        return result

    # ------------------------------------------------------------------
    def _run(self, page, adapter, url: str, result: CrawlResult) -> None:
        t0 = time.time()
        page.goto(url, wait_until="domcontentloaded", timeout=60_000)
        page.wait_for_timeout(1500)

        # 风控验证页：有头模式下等用户手动处理，无头直接失败
        if not self._clear_access_block(page, adapter, result):
            return

        # 等阅读器把首页画出来（而不是死等固定秒数）
        self._wait_reader_ready(page, adapter)
        self.log(f"页面就绪, 耗时 {time.time() - t0:.1f}s")

        result.title = (page.title() or "未命名文档").strip()
        self.log(f"页面标题: {result.title}")
        adapter.prepare(page, self.log)

        # 选线路：阅读器 / 文章 / 整页截图
        route = self.route or self._detect_route(page, adapter)
        result.route = route
        self.log(f"抓取线路: {self._ROUTE_LABEL.get(route, route)}")
        if route == "article":
            self._run_article(page, result)
            return
        if route == "shot":
            self._run_shot(page, result)
            return

        total = adapter.total_pages(page)
        result.total_pages = total
        self.log(f"文档总页数: {total if total else '未知'}")

        # 权限墙提示只作为**软信号**，不据此停止。
        # 实测同一账号同一文档连抓 7 次：出现「还剩 N 页未读」的 6 次都只抓到
        # 1~5 页，唯一没出现该提示的那次抓满了 119 页 —— 说明它是异步弹出的
        # 引导浮层，不等于真的没权限。据此立即停止会把有权限的用户挡在门外。
        wall_hint = adapter.paywall(page)
        if wall_hint:
            self.log(f"[!] 页面提示「{wall_hint}」—— 可能只是引导浮层，继续尝试")
            adapter.dismiss_overlay(page, self.log)

        # 先预热：阅读器刚打开时往往还没缓存好，直接开抓容易前几页就卡住
        if (total or 0) > 1:
            self._warm_up(page, adapter)

        limit = min(total or self.max_pages, self.max_pages)
        seen: dict[str, int] = {}
        seen_thumbs: set[str] = set()
        self._at_end = False

        n = 1
        fails = 0
        while n <= limit:
            if self.should_stop():
                result.stopped_reason = "用户已停止"
                self.log("收到停止请求")
                break

            # --- 翻页 ---
            if n > 1 and not self._turn_to(page, adapter, n, seen_thumbs):
                fails += 1
                if self._at_end or fails >= self.max_retries:
                    result.stopped_reason = self._diagnose_stall(page, adapter, n)
                    break
                self._retry_wait(page, adapter, n, fails, "翻页未生效")
                continue

            # --- 取图 ---
            img = adapter.capture(page, n, self.image_format)
            if not img:
                fails += 1
                if fails >= self.max_retries:
                    result.stopped_reason = f"第 {n} 页取图失败"
                    self.log(f"[!] {result.stopped_reason}")
                    break
                self._retry_wait(page, adapter, n, fails, "取图失败")
                continue

            # --- 去重：内容没推进就重试，而不是立刻放弃 ---
            digest = hashlib.md5(img).hexdigest()
            if digest in seen:
                fails += 1
                if fails >= self.max_retries:
                    result.stopped_reason = self._diagnose_stall(
                        page, adapter, n, dup_of=seen[digest])
                    break
                self._retry_wait(page, adapter, n, fails,
                                 f"内容与第 {seen[digest]} 页相同")
                continue

            # --- 成功 ---
            fails = 0
            seen[digest] = n
            seen_thumbs.add(adapter.thumb_hash(page, n))
            result.pages.append(PageData(index=n - 1, screenshot=img))
            self.on_progress(n, total or 0)
            if n == 1 or n % 5 == 0 or n == limit:
                self.log(f"已抓 {n}" + (f"/{total}" if total else "") + " 页")
            n += 1

        # 文字层：canvas 型阅读器提取不到，如实留空
        try:
            body = page.inner_text("body")
            if len(body) > 200 and not result.pages:
                result.pages.append(PageData(index=0, text=body))
        except Exception:
            pass

    # ------------------------------------------------------------------
    _ROUTE_LABEL = {
        "reader": "分页阅读器（图片型 PDF）",
        "article": "网页文章（文字型 PDF，可选中可搜索）",
        "shot": "整页截图（兜底）",
    }

    def _detect_route(self, page, adapter) -> str:
        """按内容形态自动选线路。

        文章线路质量最高（体积小一个数量级且文字可搜索），只要正文在 DOM 里
        就优先走它；页面是 canvas/图片分页阅读器才走 reader。
        """
        if adapter.reader_present(page):
            n = adapter.total_pages(page)
            if n and n > 1:
                return "reader"
            # 只有一页 canvas 且正文文字很少，仍按阅读器处理
            art = routes.find_article(page)
            if not art:
                return "reader"
        art = routes.find_article(page)
        if art:
            self.log(f"识别到正文容器 {art['selector'] or '(最长文本块)'}，"
                     f"约 {art['chars']} 字")
            return "article"
        if adapter.reader_present(page):
            return "reader"
        return "shot"

    def _run_article(self, page, result) -> None:
        """文章线路：展开懒加载 -> 清理杂项 -> 渲染文字型 PDF。"""
        art = routes.find_article(page) or {}
        sel = art.get("selector", "")
        self.log("展开懒加载内容...")
        routes.expand_lazy_content(page, self.log)

        # 展开后正文可能变长，重新定位一次
        art2 = routes.find_article(page)
        if art2:
            sel = art2.get("selector", sel)
            self.log(f"正文约 {art2['chars']} 字")

        text = routes.article_text(page, sel)
        if text.strip():
            result.pages.append(PageData(index=0, text=text))

        self.on_progress(1, 1)
        pdf = routes.render_article_pdf(page, sel)
        if pdf:
            result.pdf_bytes = pdf
            result.total_pages = 1
            self.log(f"已生成文字型 PDF ({len(pdf) // 1024} KB)")
        else:
            result.stopped_reason = "文字型 PDF 生成失败，已退回整页截图"
            self.log(f"[!] {result.stopped_reason}")
            self._run_shot(page, result)
            result.route = "shot"

    def _run_shot(self, page, result) -> None:
        """兜底线路：展开懒加载后整页截图。"""
        routes.expand_lazy_content(page, self.log)
        try:
            result.pages.append(PageData(index=0, text=page.inner_text("body")))
        except Exception:
            pass
        shot = routes.full_page_shot(page)
        if shot:
            if result.pages:
                result.pages[0].screenshot = shot
            else:
                result.pages.append(PageData(index=0, screenshot=shot))
            result.total_pages = 1
            self.on_progress(1, 1)
            self.log(f"整页截图完成 ({len(shot) // 1024} KB)")
        else:
            result.stopped_reason = "整页截图失败"
            self.log(f"[!] {result.stopped_reason}")

    # ------------------------------------------------------------------
    def _clear_access_block(self, page, adapter, result) -> bool:
        """处理风控验证页。返回 True 表示可以继续抓取。

        有头模式下浏览器窗口是可见的，用户可以直接在窗口里登录/过验证；
        这里轮询等待其消失，而不是直接判失败。
        """
        block = adapter.access_block(page)
        if not block:
            return True

        self.log(f"[!] 访问被拦截: {block}")
        if self.headless:
            msg = f"访问被拦截（无头模式无法人工处理）: {block}"
            result.stopped_reason = msg
            self.log("  -> 请取消勾选「无头模式」，在可见浏览器窗口中登录后重试")
            return False

        self.log(f"  -> 请在弹出的浏览器窗口中登录或完成验证，"
                 f"最长等待 {int(self.block_wait)} 秒...")
        deadline = time.time() + self.block_wait
        while time.time() < deadline:
            if self.should_stop():
                result.stopped_reason = "用户已停止"
                return False
            page.wait_for_timeout(1000)
            if not adapter.access_block(page):
                self.log("验证已通过，继续抓取")
                page.wait_for_timeout(1500)
                return True
            remain = int(deadline - time.time())
            if remain % 15 == 0 and remain > 0:
                self.log(f"  等待人工处理中... 剩余 {remain}s")

        msg = f"访问被拦截且未在 {int(self.block_wait)} 秒内解除: {block}"
        result.stopped_reason = msg
        self.log(f"[!] {msg}")
        return False

    def _warm_up(self, page, adapter) -> None:
        """预热阅读器：来回翻一次页，逼它把资源加载/初始化完。

        实测症状：刚打开就开始逐页抓，头几页常常翻不动或抓到重复内容
        （阅读器还没缓存出来）；先翻到第 2 页再回到第 1 页，后续就顺了。
        """
        try:
            cur = adapter.current_page(page)
            if cur is None:
                return
            adapter.goto_page(page, 2)
            page.wait_for_timeout(1200)
            adapter.dismiss_overlay(page, self.log)
            adapter.goto_page(page, 1)
            page.wait_for_timeout(900)
            self.log("阅读器预热完成")
        except Exception:
            pass

    def _wait_reader_ready(self, page, adapter, timeout: float = 15.0) -> None:
        """轮询等待阅读器首页绘制完成，取代固定 sleep。"""
        deadline = time.time() + timeout
        last = ""
        stable = 0
        while time.time() < deadline:
            h = adapter.thumb_hash(page, 1)
            if h and h != "ERR" and h == last:
                stable += 1
                if stable >= 2:
                    return
            else:
                stable = 0
            last = h
            page.wait_for_timeout(int(self.poll_interval * 1000))

    def _retry_wait(self, page, adapter, n: int, fails: int, why: str) -> None:
        """一次失败后的退避重试准备：等一会儿、关掉浮层、回到第 n 页。

        阅读器常常只是还没缓存/渲染好（尤其头几页），立刻放弃会白白丢掉
        本来能抓全的文档。
        """
        wait = 1.2 * fails          # 1.2s / 2.4s / 3.6s ...
        self.log(f"第 {n} 页{why}，{wait:.1f}s 后重试（{fails}/{self.max_retries}）")
        page.wait_for_timeout(int(wait * 1000))
        adapter.dismiss_overlay(page, self.log)
        # 重新下达一次跳页，把阅读器拉回目标页
        try:
            adapter.goto_page(page, n)
            page.wait_for_timeout(600)
        except Exception:
            pass

    def _turn_to(self, page, adapter, n: int, seen_thumbs: set) -> bool:
        """跳到第 n 页并等渲染稳定；带页码回读校验与重试。"""
        # 第一次翻页时阅读器往往还在初始化，给双倍时间
        timeout = self.render_timeout * (2 if n == 2 else 1)
        for attempt in range(3):
            if not adapter.goto_page(page, n):
                page.wait_for_timeout(300)
                continue
            # 先看页码认不认这次跳转：阅读器根本不接受（停在上一页）说明
            # 已经到末尾，此时再等满渲染超时纯属浪费
            page.wait_for_timeout(150)
            cur = adapter.current_page(page)
            if cur is not None and cur < n:
                # 只有确认不是被浮层挡住，才判定到末尾
                adapter.dismiss_overlay(page, self.log)
                page.wait_for_timeout(300)
                cur2 = adapter.current_page(page)
                if cur2 is not None and cur2 < n and attempt == 2:
                    self._at_end = True
                    return False
            if self._wait_render(page, adapter, n, seen_thumbs, timeout):
                cur = adapter.current_page(page)
                if cur is None or cur == n:
                    return True
                # 页码没跟上，重试
            if attempt < 2:
                page.wait_for_timeout(400)
        return False

    def _wait_render(self, page, adapter, n: int, seen_thumbs: set,
                     timeout: float | None = None) -> bool:
        """等待第 n 页绘制稳定。

        判据：缩略哈希连续两次相同，且**不在任何已抓过的页面里**。
        只跟"上一页"比是不够的 —— 阅读器被浮层打断时常常回退到第 1 页，
        那样也满足"和上一页不同"，会被误判成渲染完成。
        """
        deadline = time.time() + (timeout or self.render_timeout)
        last = ""
        while time.time() < deadline:
            page.wait_for_timeout(int(self.poll_interval * 1000))
            h = adapter.thumb_hash(page, n)
            if not h or h == "ERR":
                continue
            if h == last and h not in seen_thumbs:
                return True
            last = h
        # 超时：内容可能确实没变（权限墙），交给上层判定
        return False

    def _diagnose_stall(self, page, adapter, n: int, dup_of: int | None = None) -> str:
        """内容不再推进时，判断到底是到末尾、权限墙还是卡住。"""
        # 已到最后一页是正常结束，不该报成错误
        if getattr(self, "_at_end", False) and not adapter.paywall(page):
            self.log(f"已到最后一页（第 {n - 1} 页）")
            return ""
        wall = adapter.paywall(page)
        if wall:
            msg = (f"第 {n} 页起翻不动了（重试 {self.max_retries} 次无效），"
                   f"页面提示：{wall}")
            self.log(f"[!] {msg}")
            self.log("  -> 可能是权限不足，也可能是页面弹出了引导层/滑块验证。")
            self.log("  -> 请在浏览器窗口里手动翻到该页看看：能翻就再抓一次；"
                     "要求登录/购买就换有权限的账号。")
            return msg
        if dup_of:
            msg = f"第 {n} 页与第 {dup_of} 页内容相同，判定内容未推进"
        else:
            msg = f"第 {n} 页渲染超时或翻页失败"
        self.log(f"[!] {msg}")
        return msg


# ---------------------------------------------------------------------------
def check_robots(url: str) -> bool:
    """极简 robots 检查, 返回是否允许默认爬取。仅作提示, 不强制。"""
    try:
        from urllib.robotparser import RobotFileParser
        parsed = urlparse(url)
        rp = RobotFileParser()
        rp.set_url(f"{parsed.scheme}://{parsed.netloc}/robots.txt")
        rp.read()
        return rp.can_fetch("*", url)
    except Exception:
        return True
