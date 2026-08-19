# -*- coding: utf-8 -*-
"""抓取引擎的可复现测试（不依赖外网，不敲打真实站点）。

用本地 fixture 页复现 doc88 的阅读器结构与反爬手段：
  - canvas 复用重绘 + 随机渲染延迟
  - 篡改 JSON 序列化（evaluate 返回数组/对象变 null）
  - 超出免费页数后页码仍变但内容不再更新（付费墙）

覆盖三个必须成立的行为：
  T1 全量抓取：12 页一页不漏、一页不重
  T2 付费墙：只抓到有权限的页，且 stopped_reason 说明原因，不静默降级
  T3 导出：PDF 页数与抓取一致
"""
import sys, io, hashlib, time
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from crawler import DocCrawler          # noqa: E402
from sites import Doc88                 # noqa: E402
import exporter as exp                  # noqa: E402

FIXTURE = (Path(__file__).parent / "fixture_reader.html").as_uri()
ARTICLE = (Path(__file__).parent / "fixture_article.html").as_uri()
OUT = Path(__file__).parent / "_out"

_fails = []


def check(name, cond, detail=""):
    print(f"  [{'PASS' if cond else 'FAIL'}] {name}" + (f" — {detail}" if detail else ""))
    if not cond:
        _fails.append(name)


def crawl(url, **kw):
    # fixture 用的就是 doc88 的 DOM 结构，直接复用其适配器
    return DocCrawler(headless=True, adapter=Doc88(), log=lambda m: None,
                      block_ads=False, **kw).crawl(url)


def t1_full():
    print("\nT1 全量抓取（12 页，无限制）")
    t0 = time.time()
    r = crawl(FIXTURE)
    el = time.time() - t0
    check("总页数识别为 12", r.total_pages == 12, f"实际 {r.total_pages}")
    check("抓满 12 页", r.page_count == 12, f"实际 {r.page_count}")
    check("标记为完整", r.complete)
    check("无提前结束", not r.stopped_reason, r.stopped_reason)
    hs = [hashlib.md5(p.screenshot).hexdigest() for p in r.pages if p.screenshot]
    check("页面互不重复", len(hs) == len(set(hs)),
          f"{len(hs)} 页 / {len(set(hs))} 唯一")
    print(f"  耗时 {el:.1f}s ({el / max(r.page_count, 1):.2f}s/页)")
    return r


def t2_paywall():
    print("\nT2 付费墙（免费 4 页 / 共 12 页）")
    r = crawl(FIXTURE + "?free=4")
    check("只抓到 4 页", r.page_count == 4, f"实际 {r.page_count}")
    check("未标记为完整", not r.complete)
    check("有明确的结束原因", bool(r.stopped_reason), r.stopped_reason)
    # 原因里必须带上页面给出的提示原文，便于用户判断是权限问题还是浮层挡住
    check("原因带页面提示原文", "还剩" in r.stopped_reason, r.stopped_reason)
    check("原因说明已重试过", "重试" in r.stopped_reason, r.stopped_reason)
    hs = [hashlib.md5(p.screenshot).hexdigest() for p in r.pages if p.screenshot]
    check("已抓页面互不重复", len(hs) == len(set(hs)))
    return r


def t3_export(r):
    print("\nT3 导出 PDF 并回读")
    OUT.mkdir(exist_ok=True)
    pdf = exp.export(r, "pdf", OUT)[0]
    check("PDF 已生成", pdf.exists() and pdf.stat().st_size > 0,
          f"{pdf.stat().st_size / 1024:.0f} KB")
    try:
        from pypdf import PdfReader
        n = len(PdfReader(str(pdf)).pages)
        check("PDF 页数与抓取一致", n == r.page_count,
              f"PDF {n} / 抓取 {r.page_count}")
    except ImportError:
        print("  (pypdf 未安装, 跳过回读)")


def t4_jseval():
    """jseval 是应对 doc88 篡改结构化序列化的绕过手段。

    真实站点上「evaluate 直接返回数组得 None、返回 JSON 字符串正常」已实测确认；
    该篡改无法在本地 fixture 里如实模拟（能简单写出的版本会连 JSON.stringify
    一起打断），所以这里只验证 jseval 本身的正确性与容错。
    """
    print("\nT4 jseval 辅助函数")
    from playwright.sync_api import sync_playwright
    from sites import jseval
    with sync_playwright() as pw:
        b = pw.chromium.launch(headless=True)
        page = b.new_page()
        page.goto(FIXTURE)
        page.wait_for_timeout(500)
        check("解析 JSON 字符串", jseval(page, "() => JSON.stringify([1,2,3])") == [1, 2, 3])
        check("JS 抛异常时返回默认值",
              jseval(page, "() => { throw new Error('x') }", default="D") == "D")
        check("返回非 JSON 字符串时返回默认值",
              jseval(page, "() => 'not json'", default="D") == "D")
        check("Doc88.total_pages 可用", Doc88().total_pages(page) == 12)
        b.close()


def t5_article():
    """文章线路：输出文字型 PDF，正文可提取，站点杂项被剔除。"""
    print("\nT5 文章线路（文字型 PDF）")
    from crawler import DocCrawler
    r = DocCrawler(headless=True, log=lambda m: None, block_ads=False).crawl(ARTICLE)
    check("自动判定为 article 线路", r.route == "article", f"实际 {r.route!r}")
    check("产出 PDF 字节", bool(r.pdf_bytes), f"{len(r.pdf_bytes or b'') // 1024} KB")
    check("提取到正文文字", "风险辨识" in r.full_text, f"{len(r.full_text)} 字")
    if not r.pdf_bytes:
        return
    OUT.mkdir(exist_ok=True)
    pdf = exp.export(r, "pdf", OUT)[0]
    try:
        from pypdf import PdfReader
        text = "\n".join(pg.extract_text() for pg in PdfReader(str(pdf)).pages)
        check("PDF 中文字可提取(可搜索)", "应急预案修订技术要点" in text)
        check("正文内容在 PDF 里", "三级联动应急演练" in text)
        check("导航被剔除", "站点导航" not in text, "残留了页面导航")
        check("页脚被剔除", "页脚版权信息" not in text, "残留了页脚")
        check("评论被剔除", "评论区内容" not in text, "残留了评论区")
    except ImportError:
        print("  (pypdf 未安装, 跳过文字校验)")
    size_kb = pdf.stat().st_size / 1024
    print(f"  文字型 PDF 体积 {size_kb:.0f} KB")


def t6_autoreader():
    """AutoReader：不靠硬编码选择器，靠试错锁定翻页策略。"""
    print("\nT6 AutoReader 结构探测")
    from sites import AutoReader, pick_adapter
    a = AutoReader()
    r = DocCrawler(headless=True, adapter=a, log=lambda m: None,
                   block_ads=False, route="reader").crawl(FIXTURE)
    check("识别总页数 12", r.total_pages == 12, f"实际 {r.total_pages}")
    check("抓满 12 页", r.page_count == 12, f"实际 {r.page_count}")
    check("锁定了翻页策略", a.nav_name != "未锁定", f"策略: {a.nav_name}")
    hs = [hashlib.md5(p.screenshot).hexdigest() for p in r.pages if p.screenshot]
    check("页面互不重复", len(hs) == len(set(hs)))
    check("book118 选到 AutoReader",
          pick_adapter("https://max.book118.com/html/x.shtm").name == "auto")
    check("doc88 仍用专用适配器",
          pick_adapter("https://www.doc88.com/p-1.html").name == "doc88")

    # 拿掉页码输入框：验证策略试错能自动降级，而不是直接抓瞎
    print("\nT7 翻页策略降级（无页码输入框）")
    a2 = AutoReader()
    r2 = DocCrawler(headless=True, adapter=a2, log=lambda m: None,
                    block_ads=False, route="reader").crawl(FIXTURE + "?noinput=1")
    check("降级到其他策略", a2.nav_name == "下一页按钮", f"策略: {a2.nav_name}")
    check("仍抓满 12 页", r2.page_count == 12, f"实际 {r2.page_count}")
    hs2 = [hashlib.md5(p.screenshot).hexdigest() for p in r2.pages if p.screenshot]
    check("页面互不重复", len(hs2) == len(set(hs2)))


def t8_hint_not_paywall():
    """回归：「还剩 N 页未读」只是引导浮层时，不能据此停止。

    真实故障：同一账号同一文档连抓 7 次，出现该提示的 6 次只抓到 1~5 页，
    唯一没出现的那次抓满 119 页 —— 说明它是异步弹出的引导层，不等于没权限。
    旧逻辑一看到就 break，把有权限的用户挡在门外。
    """
    print("\nT8 引导浮层不应被当成权限墙")
    r = crawl(FIXTURE + "?hint=1")
    check("仍抓满 12 页", r.page_count == 12, f"实际 {r.page_count}")
    check("标记为完整", r.complete)
    check("无提前结束", not r.stopped_reason, r.stopped_reason)
    hs = [hashlib.md5(p.screenshot).hexdigest() for p in r.pages if p.screenshot]
    check("页面互不重复", len(hs) == len(set(hs)))


if __name__ == "__main__":
    full = t1_full()
    part = t2_paywall()
    t3_export(full)
    t4_jseval()
    t5_article()
    t6_autoreader()
    t8_hint_not_paywall()
    print("\n" + "=" * 50)
    if _fails:
        print(f"FAILED ({len(_fails)}): " + ", ".join(_fails))
        sys.exit(1)
    print("全部通过")
