# -*- coding: utf-8 -*-
"""精确定位 doc88 翻页的正确交互方式。"""
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

        def page_num():
            # 尝试找页码指示
            for sel in ["[class*='pageNum']", "[class*='pagenum']", "[class*='curPage']",
                        "[class*='current']", "[class*='num']", "#pageNum", ".page-num"]:
                try:
                    el = page.query_selector(sel)
                    if el:
                        t = (el.inner_text() or "").strip()
                        if t and len(t) < 10:
                            return f"{sel}={t!r}"
                except Exception:
                    pass
            return "无页码指示"

        def canvas_hash():
            hs = []
            for cv in page.query_selector_all("canvas"):
                cid = cv.get_attribute("id") or ""
                if "postil" in cid:
                    continue
                try:
                    hs.append(hashlib.md5(cv.screenshot()).hexdigest()[:8])
                except Exception:
                    hs.append("ERR")
            return hs

        print("初始:", page_num(), canvas_hash())

        # 连续点 next 5 次，每次看页码和哈希
        for i in range(8):
            try:
                el = None
                for sel in [".next", ".nextskin", "[class*='next']"]:
                    el = page.query_selector(sel)
                    if el and el.is_visible():
                        break
                if el:
                    el.click()
                else:
                    print("找不到 next 按钮")
                    break
            except Exception as ex:
                print("点击失败", ex)
                break
            page.wait_for_timeout(1500)
            print(f"点next {i+1}:", page_num(), canvas_hash())

        browser.close()

if __name__ == "__main__":
    main()