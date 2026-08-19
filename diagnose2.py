"""精确探查 doc88 翻页按钮 DOM 和点击后的 canvas 变化。"""
from playwright.sync_api import sync_playwright

URL = "https://www.doc88.com/p-34680749617699.html"

def main():
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(URL, wait_until="domcontentloaded", timeout=60_000)
        page.wait_for_timeout(5000)

        # 精确看 next 相关元素的完整外链 HTML
        print("=== next 相关元素 outerHTML ===")
        for sel in ["[class*='next']", ".next", "#next", "[class*='nextsub']"]:
            try:
                els = page.query_selector_all(sel)
                for i, e in enumerate(els[:3]):
                    html = e.evaluate("el => el.outerHTML")
                    print(f"\n--- {sel}[{i}] ---")
                    print(html[:500])
            except Exception as ex:
                print(sel, "err", ex)

        # 尝试点击 next，看 canvas id 是否变化
        print("\n=== 点击 next 前 canvas ids ===")
        ids = page.evaluate("[...document.querySelectorAll('canvas')].map(c=>c.id)")
        print(ids)

        # 尝试多种方式点 next
        clicked = False
        for sel in [".next", "[class*='nextsub']", "[class*='next']", ".nextskin", "#next"]:
            try:
                el = page.query_selector(sel)
                if el and el.is_visible():
                    el.click()
                    clicked = True
                    print(f"点了 {sel}")
                    break
            except Exception as ex:
                print(sel, "点击失败", ex)

        page.wait_for_timeout(4000)
        print("=== 点击 next 后 canvas ids ===")
        ids = page.evaluate("[...document.querySelectorAll('canvas')].map(c=>c.id)")
        print(ids)
        print("canvas 总数:", len(page.query_selector_all("canvas")))

        # 看看是否有 page_2
        p2 = page.query_selector("#page_2")
        print("是否有 #page_2:", p2 is not None)

        browser.close()

if __name__ == "__main__":
    main()