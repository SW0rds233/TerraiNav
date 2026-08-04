@echo off
title TerraiNav Launcher
echo.
echo ============================================================
echo        TerraiNav - One-Click Start
echo ============================================================
echo.

cd /d "%~dp0"

:: Check virtual environment
echo [*] Checking Python venv...
if not exist ".venv\Scripts\python.exe" (
    echo [!] venv not found, creating...
    python -m venv .venv
    if errorlevel 1 (
        echo [X] Failed to create venv. Is Python installed / in PATH?
        pause
        exit /b 1
    )
    echo [OK] venv created
)

:: Activate virtual environment
call .venv\Scripts\activate.bat
if errorlevel 1 (
    echo [X] Failed to activate venv
    pause
    exit /b 1
)
echo [OK] venv activated

:: Check dependencies
echo [*] Checking Python dependencies...
python -c "import flask, numpy, PIL, pandas, scipy, openai" 2>nul
if errorlevel 1 (
    echo [!] Installing dependencies...
    python -m pip install -r backend\requirements.txt -q
    if errorlevel 1 (
        echo [X] Failed to install dependencies
        echo     Run manually: pip install -r backend\requirements.txt
        pause
        exit /b 1
    )
    echo [OK] Dependencies installed
)

:: Launch
echo.
echo [*] Starting backend (port 5000) and frontend (port 5173)...
echo     Ctrl+C to stop all services
echo.

python start_dev.py
pause
