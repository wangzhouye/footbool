@echo off
chcp 65001 >nul
title WC2026 Predictor

cd /d "%~dp0"
python scheduled_update.py --startup
streamlit run app.py --server.port 8501 --server.headless true
