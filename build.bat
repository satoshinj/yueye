@echo off
chcp 65001 >nul
setlocal
cd /d "%~dp0"

echo ============================================
echo   打包「阅页」为免安装版
echo ============================================
echo.

where python >nul 2>nul
if errorlevel 1 (
    echo [错误] 找不到 python，请先安装 Python 3.10+
    pause & exit /b 1
)

echo [1/4] 安装打包依赖...
python -m pip install -q -r requirements.txt pyinstaller
if errorlevel 1 ( echo [错误] 依赖安装失败 & pause & exit /b 1 )

echo [2/4] 打包主程序...
python -m PyInstaller build.spec --noconfirm --clean >build.log 2>&1
if errorlevel 1 ( echo [错误] 打包失败，详见 build.log & pause & exit /b 1 )

echo [3/4] 打包自检程序...
python -m PyInstaller selftest.spec --noconfirm >>build.log 2>&1
if errorlevel 1 ( echo [错误] 自检程序打包失败，详见 build.log & pause & exit /b 1 )

echo [4/4] 运行自检（验证打包后浏览器驱动可用）...
mkdir "dist\selftest\tests" 2>nul
copy /y "tests\fixture_reader.html" "dist\selftest\tests\" >nul
"dist\selftest\selftest.exe"
if errorlevel 1 (
    echo.
    echo [错误] 自检未通过，产物可能不可用。
    pause & exit /b 1
)

echo.
echo ============================================
echo   打包完成
echo ============================================
echo   产物: dist\阅页\
echo   运行: dist\阅页\阅页.exe
echo.
echo   整个 dist\阅页 文件夹可直接拷给别人用，
echo   对方电脑不需要装 Python，也不需要装依赖，
echo   只要有 Microsoft Edge 或 Chrome 即可。
echo ============================================
pause
