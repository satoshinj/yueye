# -*- coding: utf-8 -*-
"""阅页 Yueye · GUI 主程序。

输入文档分享平台 URL, 抓取你有权查看的内容, 导出为
PDF/Word/Markdown/文本/图片合集。

登录态用持久化浏览器上下文保存（「登录浏览器」按钮），不再解密浏览器 Cookie
数据库——新版 Chrome/Edge 启用 App-Bound Encryption 后那条路已不可行。
"""
from __future__ import annotations

import os
import sys
import threading
import traceback
from datetime import datetime
from pathlib import Path

from PySide6.QtCore import Qt, QMetaObject, Q_ARG, Slot
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLineEdit, QPushButton, QComboBox, QLabel, QPlainTextEdit,
    QProgressBar, QFileDialog, QCheckBox, QGroupBox, QMessageBox,
)

from config import Config, load_config, app_dir
from crawler import DocCrawler
import session as sess
import exporter as exp


# 日志文件固定放在工具目录下
LOG_PATH = app_dir() / "run.log"


def write_log(msg: str) -> None:
    """写入日志文件（追加），即使 GUI 崩了也能查。"""
    try:
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(LOG_PATH, "a", encoding="utf-8") as f:
            f.write(f"[{ts}] {msg}\n")
    except Exception:
        pass


class MainWindow(QMainWindow):
    def __init__(self, cfg: Config):
        super().__init__()
        self.cfg = cfg
        self.setWindowTitle("阅页 Yueye · 在线文档离线保存")
        self.resize(900, 640)

        self._result = None
        self._pending_result = None
        self._pending_error = None
        self._stop_flag = False

        # 确保输出目录存在
        Path(self.cfg.output_dir).mkdir(parents=True, exist_ok=True)

        self._build_ui()
        self._load_cfg_to_ui()
        self._log(f"输出目录: {self.cfg.output_dir}")
        self._log(f"登录态: {'已保存' if sess.profile_exists() else '未登录（如需全文请先点「登录浏览器」）'}")

    # ------------------------------------------------------------------
    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)

        # URL 输入行
        row_url = QHBoxLayout()
        self.url_edit = QLineEdit()
        self.url_edit.setPlaceholderText("粘贴文档分享平台 URL, 如 https://...")
        self.btn_login = QPushButton("登录浏览器")
        self.btn_login.setToolTip("打开真实浏览器手动登录，登录态长期保存；这是抓取全文的前提")
        self.btn_login.clicked.connect(self.on_login)
        self.btn_fetch = QPushButton("开始抓取")
        self.btn_fetch.clicked.connect(self.on_fetch)
        self.btn_stop = QPushButton("停止")
        self.btn_stop.setEnabled(False)
        self.btn_stop.clicked.connect(self.on_stop)
        row_url.addWidget(self.url_edit, stretch=1)
        row_url.addWidget(self.btn_login)
        row_url.addWidget(self.btn_fetch)
        row_url.addWidget(self.btn_stop)
        root.addLayout(row_url)

        # 设置 group
        grp = QGroupBox("设置")
        grp_layout = QHBoxLayout(grp)

        grp_layout.addWidget(QLabel("输出格式:"))
        self.fmt_combo = QComboBox()
        for f, label in [("pdf", "PDF"), ("word", "Word(docx)"),
                         ("markdown", "Markdown"), ("text", "纯文本"),
                         ("images", "图片合集")]:
            self.fmt_combo.addItem(label, f)
        grp_layout.addWidget(self.fmt_combo)

        grp_layout.addWidget(QLabel("线路:"))
        self.route_combo = QComboBox()
        for r, label, tip in [
            ("", "自动判定", "按页面形态自动选择线路（推荐）"),
            ("article", "网页文章", "正文在 DOM 里：输出文字型 PDF，可选中可搜索，体积小"),
            ("reader", "分页阅读器", "canvas/图片翻页的文库类阅读器：逐页抓图"),
            ("shot", "整页截图", "兜底：整页截一张长图"),
        ]:
            self.route_combo.addItem(label, r)
            self.route_combo.setItemData(self.route_combo.count() - 1, tip, Qt.ToolTipRole)
        grp_layout.addWidget(self.route_combo)

        grp_layout.addWidget(QLabel("图像:"))
        self.img_combo = QComboBox()
        self.img_combo.addItem("PNG(无损)", "png")
        self.img_combo.addItem("JPEG(体积小)", "jpeg")
        grp_layout.addWidget(self.img_combo)

        # 有头是默认: 站点对 headless 有降级投喂, 且滑块验证需人工完成
        self.headless_check = QCheckBox("无头模式")
        self.headless_check.setChecked(False)
        self.headless_check.setToolTip("不建议勾选：目标站点会识别无头浏览器并降级投喂内容")
        grp_layout.addWidget(self.headless_check)

        self.block_ads_check = QCheckBox("拦截广告/统计")
        self.block_ads_check.setChecked(True)
        self.block_ads_check.setToolTip("拦掉纯广告与统计域名以提速，不影响正文内容")
        grp_layout.addWidget(self.block_ads_check)

        self.auto_export_check = QCheckBox("抓完自动导出")
        self.auto_export_check.setChecked(True)
        grp_layout.addWidget(self.auto_export_check)

        grp_layout.addStretch(1)
        root.addWidget(grp)

        # 预览/日志区
        self.log_view = QPlainTextEdit()
        self.log_view.setReadOnly(True)
        self.log_view.setFont(QFont("Consolas", 10))
        root.addWidget(self.log_view, stretch=1)

        # 进度条
        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        self.progress.setFormat("%v / %m 页")
        root.addWidget(self.progress)

        # 底部按钮
        row_btn = QHBoxLayout()
        self.btn_export = QPushButton("导出到...")
        self.btn_export.setEnabled(False)
        self.btn_export.clicked.connect(self.on_export)
        self.btn_open_dir = QPushButton("打开输出目录")
        self.btn_open_dir.clicked.connect(self.on_open_dir)
        self.btn_open_log = QPushButton("打开日志")
        self.btn_open_log.clicked.connect(self.on_open_log)
        self.btn_diag = QPushButton("浏览器诊断")
        self.btn_diag.setToolTip("检测本机 Edge/Chrome 并实际启动一次，输出完整报告")
        self.btn_diag.clicked.connect(self.on_diagnose)
        row_btn.addWidget(self.btn_export)
        row_btn.addWidget(self.btn_open_dir)
        row_btn.addWidget(self.btn_open_log)
        row_btn.addWidget(self.btn_diag)
        row_btn.addStretch(1)
        root.addLayout(row_btn)

    def _load_cfg_to_ui(self):
        for i in range(self.fmt_combo.count()):
            if self.fmt_combo.itemData(i) == self.cfg.default_format:
                self.fmt_combo.setCurrentIndex(i)
                break

    # ------------------------------------------------------------------
    def _log(self, msg: str):
        """同时写到界面和文件。"""
        self.log_view.appendPlainText(msg)
        write_log(msg)

    def _log_safe(self, msg: str):
        """从子线程安全地追加日志到界面。"""
        QMetaObject.invokeMethod(
            self.log_view, "appendPlainText", Qt.QueuedConnection, Q_ARG(str, msg),
        )
        write_log(msg)

    def _progress_safe(self, cur: int, total: int):
        """从子线程安全地更新进度。"""
        QMetaObject.invokeMethod(
            self, "_set_progress", Qt.QueuedConnection,
            Q_ARG(int, cur), Q_ARG(int, total),
        )

    @Slot(int, int)
    def _set_progress(self, cur: int, total: int):
        if total > 0:
            self.progress.setRange(0, total)
            self.progress.setValue(cur)
        else:
            self.progress.setRange(0, 0)

    # ------------------------------------------------------------------
    def on_login(self):
        """打开有头浏览器让用户手动登录。"""
        url = self.url_edit.text().strip()
        if not url.startswith(("http://", "https://")):
            url = "https://www.doc88.com/"
            self._log("URL 为空，打开 doc88 首页登录")

        self.btn_login.setEnabled(False)
        self.btn_fetch.setEnabled(False)

        def task():
            ok = False
            try:
                ok = bool(sess.login_flow(url, log=self._log_safe))
            except Exception as e:
                write_log(traceback.format_exc())
                self._log_safe(f"登录失败: {e}")
                self._pending_error = str(e)
            finally:
                self._login_ok = ok
                QMetaObject.invokeMethod(self, "_on_login_done", Qt.QueuedConnection)

        threading.Thread(target=task, daemon=True).start()

    @Slot()
    def _on_login_done(self):
        self.btn_login.setEnabled(True)
        self.btn_fetch.setEnabled(True)
        if getattr(self, "_login_ok", False):
            self._log("登录窗口已关闭，登录态已保存")
        else:
            # 浏览器根本没起来时不能报"已保存"，那是假成功
            self._log("[!] 登录未完成：浏览器没能启动")
            QMessageBox.critical(
                self, "浏览器启动失败",
                (self._pending_error or "未知错误")
                + "\n\n可点「浏览器诊断」查看详细排查信息。")

    def on_stop(self):
        self._stop_flag = True
        self._log("正在停止...")
        self.btn_stop.setEnabled(False)

    def on_fetch(self):
        url = self.url_edit.text().strip()
        if not url.startswith(("http://", "https://")):
            self._log("请输入合法的 http/https URL")
            return

        headless = self.headless_check.isChecked()
        img_fmt = self.img_combo.currentData()
        block_ads = self.block_ads_check.isChecked()
        route = self.route_combo.currentData()

        self._stop_flag = False
        self.btn_fetch.setEnabled(False)
        self.btn_login.setEnabled(False)
        self.btn_stop.setEnabled(True)
        self.progress.setRange(0, 0)  # 忙碌动画, 拿到总页数后转为真实进度

        def task():
            try:
                crawler = DocCrawler(
                    headless=headless,
                    log=self._log_safe,
                    image_format=img_fmt,
                    block_ads=block_ads,
                    route=route,
                    should_stop=lambda: self._stop_flag,
                    on_progress=self._progress_safe,
                )
                self._pending_result = crawler.crawl(url)
                QMetaObject.invokeMethod(
                    self, "_on_worker_done", Qt.QueuedConnection,
                )
            except Exception as e:
                tb = traceback.format_exc()
                write_log(tb)
                self._pending_error = f"{e}\n\n详情见 run.log"
                QMetaObject.invokeMethod(
                    self, "_on_worker_error", Qt.QueuedConnection,
                )

        threading.Thread(target=task, daemon=True).start()

    @Slot()
    def _on_worker_done(self):
        result = self._pending_result
        if result is None:
            return
        self._result = result
        self._reset_buttons()

        if result.total_pages:
            self.progress.setRange(0, result.total_pages)
            self.progress.setValue(result.page_count)
            self._log(f"完成! 抓取 {result.page_count}/{result.total_pages} 页, "
                      f"标题: {result.title}")
        else:
            self.progress.setRange(0, 100)
            self.progress.setValue(100)
            self._log(f"完成! 共 {result.page_count} 页, 标题: {result.title}")
        if result.route == "article" and result.pdf_bytes:
            self._log("输出为文字型 PDF（可选中/可搜索）")

        # 不完整时明确告知，绝不让用户误以为拿到了全文
        if result.stopped_reason and not result.complete:
            missing = (result.total_pages - result.page_count) if result.total_pages else None
            tip = f"只抓到 {result.page_count} 页"
            if missing:
                tip += f"，还差 {missing} 页"
            tip += f"。\n\n原因: {result.stopped_reason}"
            if "权限墙" in result.stopped_reason:
                tip += ("\n\n剩余内容由服务端按账号权限下发，客户端无法绕过。"
                        "\n请点「登录浏览器」登录有权限的账号后重试。")
            self._log(f"[!] {tip}")
            QMessageBox.warning(self, "内容不完整", tip)

        if result.page_count == 0:
            QMessageBox.critical(self, "抓取失败", "没有抓到任何页面，详情见日志。")
            return

        self.btn_export.setEnabled(True)
        if self.auto_export_check.isChecked():
            self._do_export(auto_open=True)

    @Slot()
    def _on_worker_error(self):
        msg = self._pending_error or "未知错误"
        self._log(f"错误: {msg}")
        self._reset_buttons()
        self.progress.setRange(0, 100)
        self.progress.setValue(0)
        QMessageBox.critical(self, "抓取失败", msg)

    def _reset_buttons(self):
        self.btn_fetch.setEnabled(True)
        self.btn_login.setEnabled(True)
        self.btn_stop.setEnabled(False)

    # ------------------------------------------------------------------
    def _do_export(self, auto_open: bool = False):
        """执行导出, 返回生成的文件路径列表。"""
        if self._result is None:
            return []
        fmt = self.fmt_combo.currentData()
        out_dir = Path(self.cfg.output_dir)
        try:
            paths = exp.export(self._result, fmt, out_dir)
            for p in paths:
                self._log(f"已导出: {p}")
            if paths and auto_open:
                self._open_in_explorer(paths[0])
            return paths
        except Exception as e:
            write_log(traceback.format_exc())
            self._log(f"导出失败: {e}")
            QMessageBox.critical(self, "导出失败", str(e))
            return []

    def on_export(self):
        if self._result is None:
            return
        out_dir = QFileDialog.getExistingDirectory(
            self, "选择输出目录", self.cfg.output_dir)
        if not out_dir:
            return
        fmt = self.fmt_combo.currentData()
        try:
            paths = exp.export(self._result, fmt, Path(out_dir))
            for p in paths:
                self._log(f"已导出: {p}")
            if paths:
                self._open_in_explorer(paths[0])
        except Exception as e:
            write_log(traceback.format_exc())
            self._log(f"导出失败: {e}")
            QMessageBox.critical(self, "导出失败", str(e))

    @staticmethod
    def _open_in_explorer(path: Path):
        """在资源管理器中打开所在目录。"""
        try:
            os.startfile(path.parent)
        except Exception:
            try:
                os.startfile(str(path))
            except Exception:
                pass

    def on_open_dir(self):
        try:
            os.startfile(self.cfg.output_dir)
        except Exception as e:
            self._log(f"打开目录失败: {e}")

    def on_open_log(self):
        try:
            os.startfile(str(LOG_PATH))
        except Exception:
            self._log(f"日志文件不存在: {LOG_PATH}")

    def on_diagnose(self):
        """浏览器环境诊断：结果写进日志区和 run.log，方便截图/发回排查。"""
        self.btn_diag.setEnabled(False)
        self._log("正在诊断浏览器环境，请稍候...")

        def task():
            try:
                report = sess.diagnose()
            except Exception:
                report = "诊断过程本身出错:\n" + traceback.format_exc()
            self._log_safe("=" * 46)
            for line in report.splitlines():
                self._log_safe(line)
            self._log_safe("=" * 46)
            self._log_safe("以上内容已写入 run.log，可点「打开日志」复制发出")
            QMetaObject.invokeMethod(self, "_on_diag_done", Qt.QueuedConnection)

        threading.Thread(target=task, daemon=True).start()

    @Slot()
    def _on_diag_done(self):
        self.btn_diag.setEnabled(True)


def main():
    try:
        cfg = load_config()
        write_log("=" * 40)
        write_log("工具启动")

        app = QApplication(sys.argv)
        win = MainWindow(cfg)
        win.show()
        sys.exit(app.exec())
    except SystemExit:
        raise
    except Exception:
        # 任何未捕获异常都写进 crash.log，便于排查闪退
        tb = traceback.format_exc()
        write_log("启动崩溃:\n" + tb)
        try:
            with open(app_dir() / "crash.log", "w", encoding="utf-8") as f:
                f.write(tb)
        except Exception:
            pass
        # 注意: 这里必须用别的变量名, 若写 app = ... 会让上面的 app 变成
        # 局部变量而在赋值前被引用 (原 UnboundLocalError 崩溃的根因)
        try:
            qapp = QApplication.instance() or QApplication(sys.argv)  # noqa: F841
            QMessageBox.critical(None, "启动失败", tb)
        except Exception:
            pass
        print(tb)
        sys.exit(1)


if __name__ == "__main__":
    main()
