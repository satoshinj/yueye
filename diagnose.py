"""诊断 doc88 页面结构: 找出翻页按钮和 canvas 加载机制。"""
import sys
from playwright.sync_api import sync_playwright

URL = "https://www.doc88.com/p-34680749617699.html"

def main():
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(URL, wait_until="domcontentloaded", timeout=60_000)
        page.wait_for_timeout(5000)

        print("=== title ===")
        print(page.title())

        print("\n=== canvas count ===")
        print(len(page.query_selector_all("canvas")))

        print("\n=== 试探翻页按钮选择器 ===")
        selectors = [
            "[class*='next']",
            "[class*='page']",
            "[class*='turn']",
            "[class*='prev']",
            "[class*='arrow']",
            "[class*='btn']",
            "[onclick*='next']",
            "button",
            "a[class*='page']",
        ]
        for sel in selectors:
            try:
                els = page.query_selector_all(sel)
                if els:
                    info = []
                    for e in els[:5]:
                        try:
                            cls = e.get_attribute("class") or ""
                            txt = (e.inner_text() or "").strip()[:20]
                            info.append(f"{cls}={txt!r}")
                        except Exception:
                            pass
                    print(f"{sel}: {len(els)}个 -> {info}")
            except Exception as ex:
                print(f"{sel}: 错误 {ex}")

        print("\n=== 所有 canvas 的 class/id ===")
        for i, cv in enumerate(page.query_selector_all("canvas")):
            try:
                cls = cv.get_attribute("class") or ""
                cid = cv.get_attribute("id") or ""
                print(f"canvas[{i}] class={cls!r} id={cid!r}")
            except Exception:
                pass

        print("\n=== 页面里包含 'page' 的元素 (前30) ===")
        try:
            els = page.eval_on_selector_all(
                "*[class*='page'], *[id*='page']",
                "els => els.slice(0,30).map(e => ({tag:e.tagName, cls:e.className, id:e.id, txt:(e.innerText||'').slice(0,15)}))"
            )
            for e in els:
                print(e)
        except Exception as ex:
            print("err", ex)

        browser.close()

if __name__ == "__main__":
    main()