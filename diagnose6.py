# -*- coding: utf-8 -*-
"""检查 doc88 页面上的付费/登录提示，判断免费预览上限。"""
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
from playwright.sync_api import sync_playwright

URL = "https://www.doc88.com/p-34680749617699.html"

def main():
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(URL, wait_until="domcontentloaded", timeout=60_000)
        page.wait_for_timeout(5000)

        # 抓取所有可能包含关键提示的文字
        body = page.inner_text("body")
        keywords = ["登录", "付费", "预览", "查看更多", "下载", "阅读全文",
                    "剩余", "页", "会员", "积分", "券", "继续"]
        lines = body.split("\n")
        print("=== 含关键字的行 ===")
        for ln in lines:
            ln = ln.strip()
            if not ln:
                continue
            if any(k in ln for k in keywords):
                print(repr(ln))

        print("\n=== 侧边栏页码信息 ===")
        for sel in ["[class*='side-page']", "[class*='pages']"]:
            try:
                els = page.query_selector_all(sel)
                for e in els[:10]:
                    print(repr(e.inner_text()))
            except Exception:
                pass

        browser.close()

if __name__ == "__main__":
    main()