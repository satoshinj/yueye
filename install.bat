@echo off
chcp 65001 >nul
echo ============================================
echo   在线文档阅读与离线保存助手 - 一键安装
echo ============================================
echo.

where python >nul 2>nul
if %errorlevel% neq 0 (
    echo [错误] 未检测到 Python，请先安装 Python 3.10+ 并勾选 "Add to PATH"
    echo 下载地址: https://www.python.org/downloads/
    pause
    exit /b 1
)

echo [1/3] 升级 pip...
python -m pip install --upgrade pip

echo.
echo [2/3] 安装依赖（这一步会下载较多文件，请耐心等待）...
python -m pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo [错误] 依赖安装失败，请检查网络后重试。
    pause
    exit /b 1
)

echo.
echo [3/3] 安装 Playwright 浏览器内核（可选，但推荐）...
python -m playwright install chromium
if %errorlevel% neq 0 (
    echo [提示] 浏览器内核安装失败不影响运行，可在工具里选择系统已装的 Chrome/Edge。
)

echo.
echo ============================================
echo   安装完成！
echo   运行方式：双击运行 run.bat，或执行 python app.py
echo ============================================
pause