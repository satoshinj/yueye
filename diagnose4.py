# -*- coding: utf-8 -*-
"""测试 doc88 各种翻页方式: 键盘、滚动、点击。"""
import sys, io, hashlib
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
from playwright.sync_api import sync_playwright

URL = "https://www.doc88.com/p-34680749617699.html"

def canvas_hash(page):
    hs = []
    for cv in page.query_selector_all("canvas"):
        try:
            hs.append(hashlib.md5(cv.screenshot()).hexdigest()[:8])
        except Exception:
            hs.append("ERR")
    return hs

def main():
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(URL, wait_until="domcontentloaded", timeout=60_000)
        page.wait_for_timeout(5000)

        print("初始:", canvas_hash(page))

        # 方法1: 点 canvas 下方的翻页区域 (可能是整个页面区域)
        # 方法2: 键盘 PageDown
        print("\n--- 测试键盘 PageDown ---")
        for i in range(3):
            page.keyboard.press("PageDown")
            page.wait_for_timeout(2000)
            print(f"PageDown {i+1}:", canvas_hash(page))

        # 方法3: 滚轮滚动
        print("\n--- 测试鼠标滚轮滚动 ---")
        for i in range(5):
            page.mouse.wheel(0, 800)
            page.wait_for_timeout(1500)
            print(f"wheel {i+1}:", canvas_hash(page))

        # 方法4: 检查是否有页码输入框或跳页
        print("\n--- 查找页码相关元素 ---")
        for sel in ["input", "[class*='pageNum']", "[class*='jump']", "[class*='go']", "[class*='current']"]:
            try:
                els = page.query_selector_all(sel)
                for e in els[:3]:
                    cid = e.get_attribute("id") or ""
                    cls = e.get_attribute("class") or ""
                    print(f"{sel}: id={cid!r} cls={cls!r}")
            except Exception:
                pass

        browser.close()

if __name__ == "__main__":
    main()