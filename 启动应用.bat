@echo off
chcp 65001 >nul
title 2026 WC Predictor

echo ========================================
echo   2026 WC Predictor
echo ========================================
echo.

cd /d "%~dp0"

REM Activate conda base environment
call E:\miniaconda\Scripts\activate.bat E:\miniaconda

echo [1/3] Checking Python...
python --version
if errorlevel 1 (
    echo Error: Python not found
    pause
    exit /b 1
)
echo Python OK

echo.
echo [2/3] Updating data...
python scheduled_update.py --startup
if errorlevel 1 (
    echo Warning: data update failed
)

echo.
echo [3/3] Starting app...
echo URL: http://localhost:8501
echo Press Ctrl+C to stop
echo ========================================
echo.

python -m streamlit run app.py --server.port 8501 --server.headless true

pause
