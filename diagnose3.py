# -*- coding: utf-8 -*-
"""验证 doc88: 点 next 翻页后 canvas 内容是否真的变化。"""
import sys, io, hashlib
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
from playwright.sync_api import sync_playwright

URL = "https://www.doc88.com/p-34680749617699.html"

def main():
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(URL, wait_until="domcontentloaded", timeout=60_000)
        page.wait_for_timeout(5000)

        def canvas_hash():
            cvs = page.query_selector_all("canvas")
            hs = []
            for cv in cvs:
                try:
                    shot = cv.screenshot()
                    hs.append(hashlib.md5(shot).hexdigest()[:10])
                except Exception:
                    hs.append("ERR")
            return hs

        print("初始 canvas 哈希:", canvas_hash())

        for i in range(5):
            # 点 next
            try:
                el = page.query_selector(".next") or page.query_selector(".nextskin")
                el.click()
            except Exception as ex:
                print("点击失败", ex)
                break
            page.wait_for_timeout(2500)
            hs = canvas_hash()
            # 看当前页码指示
            try:
                pageinfo = page.query_selector("[class*='page']")
            except Exception:
                pageinfo = None
            print(f"第{i+1}次翻页后 canvas 哈希:", hs)

        browser.close()

if __name__ == "__main__":
    main()