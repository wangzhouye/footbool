@echo off
chcp 65001 >nul
title WC2026 Predictor

cd /d "%~dp0"

echo ========================================
echo   WC2026 Predictor
echo ========================================
echo.

REM Try conda base first
echo [1/2] Updating data...
call E:\miniaconda\Scripts\activate.bat E:\miniaconda
python scheduled_update.py --startup
if errorlevel 1 (
    echo Warning: data update failed, using cached data
)

echo.
echo [2/2] Starting app...
echo URL: http://localhost:8501
echo Press Ctrl+C to stop
echo ========================================

python -m streamlit run app.py --server.port 8501 --server.headless true

pause
