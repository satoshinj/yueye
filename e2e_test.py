# -*- coding: utf-8 -*-
"""端到端测试: 抓取 + 导出，验证页数正确性与速度（无 GUI）。

对**你自己有权查看**的真实页面跑一遍完整链路。URL 由命令行传入，
不内置任何默认目标 —— 避免仓库里出现具体的抓取对象。

    python e2e_test.py <URL> [--headless]

验收标准（不只是"跑通"）：
1. 抓取页数 == 声称总页数，或有明确的 stopped_reason
2. 页面图像两两不重复（重复说明翻页失败被当成了新页）
3. 导出的 PDF 能重新打开，页数与抓取一致

只跑离线用例请用 tests/test_engine.py，它不联网。
"""
import sys, io, time, hashlib
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

from pathlib import Path
from crawler import DocCrawler
import exporter as exp

_args = [a for a in sys.argv[1:] if not a.startswith("--")]
if not _args:
    print(__doc__)
    print("错误: 请传入目标 URL。例如:\n"
          "    python e2e_test.py https://example.com/some-doc --headless")
    sys.exit(2)
URL = _args[0]
HEADLESS = "--headless" in sys.argv
OUT = Path(__file__).parent / "_test_out"


def log(msg):
    print(msg, flush=True)


def main():
    t0 = time.time()
    c = DocCrawler(headless=HEADLESS, log=log,
                   on_progress=lambda cur, tot: None)
    r = c.crawl(URL)
    elapsed = time.time() - t0

    print("\n" + "=" * 60)
    print(f"标题     : {r.title}")
    print(f"抓取页数 : {r.page_count}")
    print(f"总页数   : {r.total_pages}")
    print(f"是否完整 : {r.complete}")
    print(f"提前结束 : {r.stopped_reason or '否'}")
    print(f"总耗时   : {elapsed:.1f}s", end="")
    if r.page_count:
        print(f"  (每页 {elapsed / r.page_count:.2f}s)")
    else:
        print()

    # 校验1: 页面唯一性
    print("\n--- 校验: 页面唯一性 ---")
    hashes = [hashlib.md5(p.screenshot).hexdigest()[:10]
              for p in r.pages if p.screenshot]
    dup = len(hashes) - len(set(hashes))
    print(f"页数 {len(hashes)}, 唯一 {len(set(hashes))}, 重复 {dup}")
    print("PASS" if dup == 0 else "FAIL: 存在重复页, 翻页逻辑有问题")
    if hashes:
        print(f"前5页哈希: {hashes[:5]}")

    # 校验2: 完整性
    print("\n--- 校验: 完整性 ---")
    if r.complete:
        print("PASS: 已抓完全部页面")
    elif r.stopped_reason:
        print(f"部分抓取, 原因明确: {r.stopped_reason}")
    else:
        print("FAIL: 不完整且无原因说明")

    if not r.pages or not any(p.screenshot for p in r.pages):
        print("\n无图像页面, 跳过导出")
        return

    # 校验3: 导出并回读
    print("\n--- 校验: 导出 PDF 并回读 ---")
    OUT.mkdir(exist_ok=True)
    paths = exp.export(r, "pdf", OUT)
    pdf = paths[0]
    size_mb = pdf.stat().st_size / 1024 / 1024
    print(f"已导出: {pdf.name}  ({size_mb:.2f} MB)")
    try:
        from pypdf import PdfReader
        n = len(PdfReader(str(pdf)).pages)
        print(f"回读页数: {n}")
        print("PASS" if n == r.page_count else "FAIL: PDF 页数与抓取不一致")
    except ImportError:
        print("(pypdf 未安装, 跳过回读校验)")

    print(f"\n总耗时(含导出): {time.time() - t0:.1f}s")


if __name__ == "__main__":
    main()
