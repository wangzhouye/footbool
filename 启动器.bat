@echo off
cd /d "%~dp0"
call E:\miniaconda\Scripts\activate.bat E:\miniaconda
start "" pythonw launcher.pyw
