@echo off
cd /d "%~dp0"
set "PY=C:\Users\user\AppData\Local\Programs\Python\Python312\python.exe"

if not exist "%PY%" (
    echo [ERROR] Python not found: %PY%
    pause
    exit /b 1
)

"%PY%" -c "import PySide6, playwright, PIL" 2>nul
if %errorlevel% neq 0 (
    echo [INFO] Installing dependencies...
    "%PY%" -m pip install -r requirements.txt
    if %errorlevel% neq 0 (
        echo [ERROR] Install failed.
        pause
        exit /b 1
    )
)

"%PY%" app.py
set CODE=%errorlevel%
echo.
if %CODE% neq 0 (
    echo [ERROR] App exited with code %CODE%. See crash.log if present.
)
pause