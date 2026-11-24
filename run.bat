@echo off
rem Gwangdeok school helper - runs python\main.py
chcp 65001 > nul
cd /d "%~dp0"
python python\main.py
pause
