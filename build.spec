# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller 打包配置：生成单目录免安装版。

关键取舍：**不打包 Playwright 自带的 Chromium（320 MB）**，改用系统已有的
Edge / Chrome（见 session.BROWSER_CHANNELS）。Windows 必装 Edge，所以这个
取舍几乎没有代价，却让成品从 ~500 MB 降到 ~150 MB，也省掉了用户跑
`playwright install` 这一步。

Playwright 的 node driver（约 76 MB）必须打进去，它是驱动浏览器的本体。

打包:  pyinstaller build.spec --noconfirm
产物:  dist/阅页/阅页.exe
"""
import os
from pathlib import Path
from PyInstaller.utils.hooks import collect_data_files

import playwright

# Playwright 的 node driver 必须整个带上
PW_ROOT = Path(playwright.__file__).parent
datas = [(str(PW_ROOT / "driver"), "playwright/driver")]

# 用不到的 Qt 模块全部排除，能显著减小体积
excludes = [
    "PySide6.QtWebEngineCore", "PySide6.QtWebEngineWidgets", "PySide6.QtWebEngineQuick",
    "PySide6.QtQuick", "PySide6.QtQuick3D", "PySide6.QtQml", "PySide6.QtQuickWidgets",
    "PySide6.Qt3DCore", "PySide6.Qt3DRender", "PySide6.Qt3DAnimation", "PySide6.Qt3DExtras",
    "PySide6.QtCharts", "PySide6.QtDataVisualization", "PySide6.QtMultimedia",
    "PySide6.QtMultimediaWidgets", "PySide6.QtBluetooth", "PySide6.QtNfc",
    "PySide6.QtPositioning", "PySide6.QtLocation", "PySide6.QtSerialPort",
    "PySide6.QtSql", "PySide6.QtTest", "PySide6.QtDesigner", "PySide6.QtHelp",
    "PySide6.QtOpenGL", "PySide6.QtOpenGLWidgets", "PySide6.QtSvgWidgets",
    "PySide6.QtPdf", "PySide6.QtPdfWidgets", "PySide6.QtNetworkAuth",
    "PySide6.QtRemoteObjects", "PySide6.QtScxml", "PySide6.QtSensors",
    "PySide6.QtStateMachine", "PySide6.QtTextToSpeech", "PySide6.QtUiTools",
    "PySide6.QtWebChannel", "PySide6.QtWebSockets",
    # 科学计算栈从未被引用，误收进来会白白撑大体积
    "numpy", "scipy", "pandas", "matplotlib", "tkinter",
    "PyQt5", "PyQt6", "notebook", "IPython",
    # 代码里已无调用点，却会被间接收进来
    "pymupdf", "fitz",        # 本机 wheel 缺 MSVC 运行库，且已改用 pypdf
    "reportlab", "bs4",
    "pypdf",                  # 只在测试里用
    # ⚠ 不要排除 lxml：python-docx 依赖它，排掉后 Word 导出会 ModuleNotFoundError。
    #   这个坑由 selftest.exe 抓到 —— GUI 启动时不会暴露，要等用户点导出才炸。
]

a = Analysis(
    ["app.py"],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=["playwright", "playwright.sync_api", "docx", "img2pdf", "PIL"],
    hookspath=[],
    runtime_hooks=[],
    excludes=excludes,
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="阅页",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,          # 不弹黑框
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name="阅页",
)
