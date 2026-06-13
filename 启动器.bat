@echo off
chcp 65001 >nul
title 2026 WC Predictor

cd /d "%~dp0"
call E:\miniaconda\Scripts\activate.bat E:\miniaconda

echo ========================================
echo   2026 WC Predictor
echo ========================================
echo.

echo [1/2] Updating data...
python scheduled_update.py --startup
if errorlevel 1 (
    echo Warning: data update failed
)

echo.
echo [2/2] Starting app...
echo URL: http://localhost:8501
echo Press Ctrl+C to stop
echo ========================================
echo.

python -m streamlit run app.py --server.port 8501 --server.headless true

pause
