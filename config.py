"""配置管理与 Cookie 导入模块。

负责加载/保存用户配置、导入浏览器 Cookie（用户本人已登录、有权查看的内容）。
"""
from __future__ import annotations

import json
import sqlite3
import sys
import tempfile
from dataclasses import dataclass, field, asdict
from pathlib import Path


def app_dir() -> Path:
    """程序所在目录。

    打包后 __file__ 指向 _internal\\ 内部，不能拿它当输出目录——日志和导出的
    PDF 会被写进程序内部。冻结状态下改用 exe 自身所在目录。
    """
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent
    return Path(__file__).parent


# ---------------------------------------------------------------------------
# 配置数据模型
# ---------------------------------------------------------------------------
@dataclass
class Config:
    """工具运行配置。"""
    output_dir: str = ""                 # 留空表示"程序所在目录"，见 load_config
    default_format: str = "pdf"          # pdf / word / markdown / text / images
    scroll_pause: float = 2.0            # 每次滚动暂停秒数
    custom_browser_path: str = ""        # 自定义浏览器路径（留空自动探测）
    user_agent: str = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/131.0.0.0 Safari/537.36"
    )


CONFIG_PATH = Path.home() / ".docsaver" / "config.json"


def load_config() -> Config:
    """加载配置, 不存在则使用默认值。"""
    cfg = Config()
    if CONFIG_PATH.exists():
        try:
            data = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
            cfg = Config(**data)
        except (json.JSONDecodeError, TypeError):
            pass
    if not cfg.output_dir:
        cfg.output_dir = str(app_dir())
    return cfg


def save_config(cfg: Config) -> None:
    """保存配置到磁盘。"""
    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    CONFIG_PATH.write_text(
        json.dumps(asdict(cfg), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


# ---------------------------------------------------------------------------
# Cookie 导入
# ---------------------------------------------------------------------------
def _cookie_db_paths(browser: str) -> list[Path]:
    """返回不同浏览器 Cookie 数据库的候选路径。"""
    home = Path.home()
    base = {
        "chrome": home / "AppData" / "Local" / "Google" / "Chrome" / "User Data",
        "edge": home / "AppData" / "Local" / "Microsoft" / "Edge" / "User Data",
        "brave": home / "AppData" / "Local" / "BraveSoftware" / "Brave-Browser" / "User Data",
    }
    root = base.get(browser)
    if root is None or not root.exists():
        return []
    # 默认 profile 与可能的其他 profile
    paths = [root / "Default" / "Network" / "Cookies"]
    for p in root.glob("Profile *"):
        paths.append(p / "Network" / "Cookies")
    return [p for p in paths if p.exists()]


def import_cookies(browser: str, domains: list[str]) -> list[dict]:
    """从浏览器数据库读取指定域的 Cookie。

    返回 Playwright 可用的 cookie 列表。新版 Chrome 使用 AES 加密，
    无法直接解密时返回空列表（用户可手动在浏览器登录后使用路径登录态）。
    """
    cookies: list[dict] = []
    for db_path in _cookie_db_paths(browser):
        try:
            cookies.extend(_read_sqlite_cookies(db_path, domains))
        except Exception:
            # 数据库被占用或加密无法读取时跳过
            continue
    return _dedupe_cookies(cookies)


def _read_sqlite_cookies(db_path: Path, domains: list[str]) -> list[dict]:
    """从 SQLite Cookie 数据库读取明文 Cookie（仅旧版浏览器或已停用加密）。"""
    # 复制数据库避免锁定问题
    with tempfile.NamedTemporaryFile(suffix=".sqlite", delete=False) as tmp:
        tmp.write(db_path.read_bytes())
        tmp_path = tmp.name

    results: list[dict] = []
    try:
        conn = sqlite3.connect(tmp_path)
        cur = conn.cursor()
        query = (
            "SELECT name, value, host_key, path, expires_utc, is_secure, is_httponly "
            "FROM cookies"
        )
        cur.execute(query)
        for name, value, host_key, path, expires, secure, httponly in cur.fetchall():
            if any(d in host_key for d in domains):
                results.append({
                    "name": name,
                    "value": value,
                    "domain": host_key,
                    "path": path or "/",
                    "expires": expires / 1_000_000 if expires else -1,
                    "secure": bool(secure),
                    "httpOnly": bool(httponly),
                })
        conn.close()
    finally:
        Path(tmp_path).unlink(missing_ok=True)

    return results


def _dedupe_cookies(cookies: list[dict]) -> list[dict]:
    """按 (name, domain, path) 去重, 保留后者。"""
    seen: dict[tuple, dict] = {}
    for c in cookies:
        key = (c["name"], c["domain"], c["path"])
        seen[key] = c
    return list(seen.values())