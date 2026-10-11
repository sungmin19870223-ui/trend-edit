@echo off
REM THE TREND EDIT - RSS collector runner (also called by Task Scheduler)
chcp 65001 >nul
cd /d "%~dp0"
python collect.py >> "%~dp0data\collect.log" 2>&1
