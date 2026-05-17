@echo off
title EVAN AI GEN-3 SERVER
color 0B
echo [SYSTEM] Initializing Neural Core...
echo [SYSTEM] Loading Server...
cd /d "%~dp0"

:: Auto-install dependencies
echo [SYSTEM] Checking dependencies...
pip install flask >nul 2>&1

echo [SYSTEM] Booting EvanAI Gen-3...
echo [SYSTEM] Local Link: http://127.0.0.1:5000
echo.
python app.py
pause