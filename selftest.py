# -*- coding: utf-8 -*-
"""打包后的自检：验证 Playwright driver 在冻结环境里能否真正驱动浏览器。

这是打包最容易翻车的地方 —— GUI 能启动不代表能抓取，node driver 的路径
在冻结后会变。打成控制台 exe 单独跑一次，看到"自检通过"才算打包成功。

    pyinstaller selftest.spec --noconfirm
    dist\\selftest\\selftest.exe
"""
import sys
import io
import time
import traceback
from pathlib import Path

if hasattr(sys.stdout, "buffer"):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")


def base_dir() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent
    return Path(__file__).parent


def main() -> int:
    print("=" * 56)
    print("打包自检")
    print("=" * 56)
    print(f"冻结状态 : {getattr(sys, 'frozen', False)}")
    print(f"程序目录 : {base_dir()}")

    # 1. 依赖能否导入
    try:
        import playwright, img2pdf, docx           # noqa: F401
        from PIL import Image                      # noqa: F401
        import crawler, sites, routes, session, exporter, config   # noqa: F401
        print("[OK] 依赖导入")
    except Exception:
        print("[FAIL] 依赖导入"); traceback.print_exc(); return 1

    # 2. Playwright driver 能否启动浏览器（打包最容易挂的一步）
    import session as sess
    try:
        from playwright.sync_api import sync_playwright
        t0 = time.time()
        with sync_playwright() as pw:
            ctx, page = sess.open_context(pw, headless=True, block_ads=False)
            page.set_content("<h1>ok</h1>")
            got = page.inner_text("h1")
            ctx.close()
        assert got == "ok", got
        print(f"[OK] 浏览器启动 — 使用 {sess.active_channel}，耗时 {time.time()-t0:.1f}s")
    except Exception:
        print("[FAIL] 浏览器启动"); traceback.print_exc()
        print("\n请确认已安装 Microsoft Edge 或 Google Chrome。")
        return 1

    # 3. 端到端：抓取本地测试页 -> 导出 PDF
    fixture = base_dir() / "tests" / "fixture_reader.html"
    if not fixture.exists():
        print(f"[跳过] 端到端测试（缺 {fixture}）")
        print("\n自检通过（未含端到端）")
        return 0
    try:
        from crawler import DocCrawler
        from sites import Doc88
        import exporter as exp
        r = DocCrawler(headless=True, adapter=Doc88(), log=lambda m: None,
                       block_ads=False).crawl(fixture.resolve().as_uri())
        assert r.page_count == 12, f"应抓 12 页，实得 {r.page_count}"
        out = base_dir() / "_selftest_out"
        pdf = exp.export(r, "pdf", out)[0]
        size = pdf.stat().st_size
        assert size > 10000, f"PDF 太小: {size}"
        print(f"[OK] 端到端 — 抓取 {r.page_count} 页，导出 PDF {size//1024} KB")

        # Word 导出单独验：python-docx 依赖 lxml，漏打包时只有这一步会炸
        docx_path = exp.export(r, "word", out)[0]
        assert docx_path.stat().st_size > 10000, "docx 太小"
        print(f"[OK] Word 导出 — {docx_path.stat().st_size//1024} KB")

        for f in out.iterdir():
            f.unlink()
        out.rmdir()
    except Exception:
        print("[FAIL] 端到端"); traceback.print_exc(); return 1

    print("\n自检通过：打包正常，可以分发。")
    return 0


if __name__ == "__main__":
    code = main()
    try:
        if sys.stdin and sys.stdin.isatty():
            input("\n按回车退出...")
    except (EOFError, OSError):
        pass
    sys.exit(code)
