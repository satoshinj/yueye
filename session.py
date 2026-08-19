# -*- coding: utf-8 -*-
"""持久化浏览器会话。

用 Playwright 的 persistent context 保存登录态，替代从浏览器 SQLite 解密
Cookie 的做法（新版 Chrome/Edge 启用 App-Bound Encryption 后已不可行）。

用户点一次「登录浏览器」，在真实浏览器里自己完成登录（含扫码/滑块/短信），
关窗后登录态落盘，之后所有抓取自动复用。
"""
from __future__ import annotations

from pathlib import Path

# 登录态目录（与配置同级，便于用户清理）
PROFILE_DIR = Path.home() / ".docsaver" / "browser"

# 反自动化检测 + Edge 启动稳定性参数。
# 后半段是为了解决「Edge 启动后立刻 Target closed」：Edge 首次用新配置目录时
# 会跑首启流程/后台服务，可能自我重启，被 Playwright 判定为浏览器已关闭。
LAUNCH_ARGS = [
    "--disable-blink-features=AutomationControlled",
    "--no-first-run",
    "--no-default-browser-check",
    "--disable-infobars",
    "--no-service-autorun",
    "--disable-sync",
    "--disable-background-networking",
    "--disable-background-timer-throttling",
    "--disable-renderer-backgrounding",
    "--disable-features=msEdgeWelcomePage,EdgeFirstRunExperience,TrackingProtection3pcd",
]

# 覆盖 navigator.webdriver 等自动化指纹
STEALTH_JS = """
Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
Object.defineProperty(navigator, 'languages', {get: () => ['zh-CN', 'zh', 'en']});
window.chrome = window.chrome || {runtime: {}};
"""

DEFAULT_UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
)

# 纯广告/统计域名，抓取时直接拦掉以提速（不含内容资源）
BLOCK_HOSTS = (
    "stat.doc88.com", "png.doc88.com", "face.doc88.com",
    "hm.baidu.com", "google-analytics.com", "googletagmanager.com",
    "cnzz.com", "doubleclick.net",
)


#: 浏览器优先级。系统 Edge 排第一是为了打包：Windows 必装 Edge，
#: 用它就不必随程序分发 Playwright 自带的 Chromium（320 MB），
#: 也不需要用户跑 playwright install。
#: None 表示 Playwright 自带的 Chromium（开发机上有，打包后通常没有）。
BROWSER_CHANNELS = ["msedge", "chrome", None]

#: 记录本次实际用上的浏览器，供日志显示
active_channel: str | None = None


def find_browsers() -> list[tuple[str, str]]:
    """在磁盘上直接找 Edge / Chrome 的 exe，返回 [(名称, 路径)]。

    `channel="chrome"` 这类写法依赖 Playwright 自己的注册表探测，装在非标准
    位置时会报 "distribution not found"。直接给 executable_path 更可靠。
    """
    import os
    found: list[tuple[str, str]] = []
    roots = [
        os.environ.get("PROGRAMFILES(X86)", r"C:\Program Files (x86)"),
        os.environ.get("PROGRAMFILES", r"C:\Program Files"),
        os.environ.get("LOCALAPPDATA", ""),
    ]
    rel = [
        ("Edge", r"Microsoft\Edge\Application\msedge.exe"),
        ("Edge Beta", r"Microsoft\Edge Beta\Application\msedge.exe"),
        ("Chrome", r"Google\Chrome\Application\chrome.exe"),
        ("Chrome Beta", r"Google\Chrome Beta\Application\chrome.exe"),
    ]
    for root in roots:
        if not root:
            continue
        for name, r in rel:
            p = Path(root) / r
            if p.exists() and not any(x[1] == str(p) for x in found):
                found.append((name, str(p)))
    # 注册表 App Paths 兜底（装在自定义目录时）
    try:
        import winreg
        for exe, name in [("msedge.exe", "Edge"), ("chrome.exe", "Chrome")]:
            for hive in (winreg.HKEY_LOCAL_MACHINE, winreg.HKEY_CURRENT_USER):
                try:
                    key = winreg.OpenKey(
                        hive,
                        r"SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\\" + exe)
                    val = winreg.QueryValue(key, None)
                    winreg.CloseKey(key)
                    if val and Path(val).exists() and not any(x[1] == val for x in found):
                        found.append((name + "(注册表)", val))
                except OSError:
                    continue
    except ImportError:
        pass
    return found


def _candidates() -> list[tuple[str, dict]]:
    """生成启动方案候选：先按 channel，再按磁盘上找到的 exe 路径。"""
    cands: list[tuple[str, dict]] = []
    for ch in BROWSER_CHANNELS:
        if ch:
            cands.append((f"channel={ch}", {"channel": ch}))
        else:
            cands.append(("内置 chromium", {}))
    for name, path in find_browsers():
        cands.append((f"{name} 路径", {"executable_path": path}))
    return cands


def _launch(pw, **kwargs):
    """按优先级尝试各方案，返回第一个能启动的 context。

    失败时保留**完整**错误信息 —— 之前截断到 80 字符，导致真正的原因看不到，
    把「Edge 启动后立刻退出」误报成「没装浏览器」。
    """
    global active_channel
    errors: list[str] = []
    profile_retried = False

    for label, extra in _candidates():
        for attempt in range(2):
            try:
                kw = dict(kwargs)
                kw.update(extra)
                if attempt == 1:
                    # 配置目录可能损坏或被占用：换个全新目录再试一次
                    alt = Path(str(kw["user_data_dir"]) + "_alt")
                    alt.mkdir(parents=True, exist_ok=True)
                    kw["user_data_dir"] = str(alt)
                ctx = pw.chromium.launch_persistent_context(**kw)
                active_channel = label + ("（备用配置目录）" if attempt else "")
                return ctx
            except Exception as e:
                msg = str(e).strip()
                errors.append(f"[{label}{'/备用目录' if attempt else ''}] {msg}")
                # 只有"启动后被关闭"才值得换目录重试；找不到浏览器重试没意义
                if "has been closed" not in msg and "Timeout" not in msg:
                    break
                if attempt == 0:
                    profile_retried = True

    # 走到这里说明持久化上下文全挂了。再试一次非持久化（不保存登录态，
    # 但能区分"浏览器有问题"和"配置目录有问题"）
    for label, extra in _candidates():
        try:
            kw = {k: v for k, v in kwargs.items() if k != "user_data_dir"}
            kw.update(extra)
            browser = pw.chromium.launch(
                headless=kw.pop("headless", False),
                args=kw.pop("args", None),
                **{k: v for k, v in extra.items()})
            ctx = browser.new_context(
                user_agent=kw.get("user_agent"),
                viewport=kw.get("viewport"),
                locale=kw.get("locale"), timezone_id=kw.get("timezone_id"))
            active_channel = label + "（临时模式·登录态不保存）"
            return ctx
        except Exception as e:
            errors.append(f"[{label}/非持久化] {str(e).strip()}")

    installed = find_browsers()
    if installed:
        head = ("浏览器已安装但启动失败：\n  " +
                "\n  ".join(f"{n} -> {p}" for n, p in installed) +
                "\n\n常见原因：\n"
                "  1) Edge/Chrome 正在运行 —— 请完全退出浏览器后重试\n"
                "     （注意任务栏右下角，Edge 的「启动增强」会让它常驻后台，\n"
                "      需在 edge://settings/system 里关掉「启动增强」）\n"
                "  2) 杀毒软件/企业策略拦截了以自动化方式启动浏览器\n"
                "  3) 配置目录损坏 —— 删除 %USERPROFILE%\\.docsaver 后重试")
    else:
        head = ("没有在本机找到 Microsoft Edge 或 Google Chrome。\n"
                "请安装其中之一后重试。")
    if profile_retried:
        head += "\n\n（已自动尝试过备用配置目录，仍然失败）"

    raise RuntimeError(head + "\n\n--- 详细错误 ---\n" + "\n".join(errors))


def diagnose() -> str:
    """浏览器环境诊断报告，供界面上的「浏览器诊断」按钮使用。"""
    import platform
    lines = [
        f"系统      : {platform.platform()}",
        f"配置目录  : {PROFILE_DIR}",
        f"目录存在  : {PROFILE_DIR.exists()}",
        "",
        "找到的浏览器:",
    ]
    found = find_browsers()
    if found:
        lines += [f"  [OK] {n}: {p}" for n, p in found]
    else:
        lines.append("  [无] 没找到 Edge / Chrome")

    lines += ["", "实际启动测试:"]
    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as pw:
            try:
                ctx, page = open_context(pw, headless=True, block_ads=False)
                page.set_content("<b>ok</b>")
                ok = page.inner_text("b")
                ctx.close()
                lines.append(f"  [OK] 启动成功，使用 {active_channel}（返回 {ok!r}）")
            except Exception as e:
                lines.append("  [失败]")
                lines += ["    " + ln for ln in str(e).splitlines()]
    except Exception as e:
        lines.append(f"  [失败] Playwright 无法初始化: {e}")
    return "\n".join(lines)


def open_context(pw, headless: bool = False, user_agent: str | None = None,
                 viewport: dict | None = None, block_ads: bool = True):
    """打开持久化浏览器上下文，返回 (context, page)。

    context 关闭即保存登录态，无需显式持久化操作。
    """
    PROFILE_DIR.mkdir(parents=True, exist_ok=True)
    ctx = _launch(
        pw,
        user_data_dir=str(PROFILE_DIR),
        headless=headless,
        args=LAUNCH_ARGS,
        user_agent=user_agent or DEFAULT_UA,
        viewport=viewport or {"width": 1400, "height": 1000},
        locale="zh-CN",
        timezone_id="Asia/Shanghai",
    )
    ctx.add_init_script(STEALTH_JS)

    if block_ads:
        def _route(route):
            url = route.request.url
            if any(h in url for h in BLOCK_HOSTS) or route.request.resource_type == "media":
                try:
                    route.abort()
                    return
                except Exception:
                    pass
            try:
                route.continue_()
            except Exception:
                pass
        try:
            ctx.route("**/*", _route)
        except Exception:
            pass

    page = ctx.pages[0] if ctx.pages else ctx.new_page()
    return ctx, page


def login_flow(url: str, log=print) -> bool:
    """打开有头浏览器让用户手动登录；用户关闭窗口后返回。

    返回是否真的完成了登录流程 —— 浏览器都没起来时必须返回 False，
    不能再报"登录态已保存"（那是假成功，会让用户以为登录好了）。
    """
    from playwright.sync_api import sync_playwright

    log("正在打开登录浏览器，请在窗口中完成登录，登录后直接关闭窗口...")
    with sync_playwright() as pw:
        ctx, page = open_context(pw, headless=False, block_ads=False)
        log(f"浏览器: {active_channel}")
        try:
            page.goto(url, wait_until="domcontentloaded", timeout=60_000)
        except Exception as e:
            log(f"页面加载异常(不影响登录): {e}")
        # 阻塞直到用户关闭浏览器
        try:
            page.wait_for_event("close", timeout=0)
        except Exception:
            pass
        try:
            ctx.close()
        except Exception:
            pass
    log(f"登录态已保存到: {PROFILE_DIR}")
    return True


def profile_exists() -> bool:
    """是否已有保存的登录态。"""
    return (PROFILE_DIR / "Default").exists() or (PROFILE_DIR / "Default" / "Cookies").exists()
