@echo off
rem Gwangdeok school helper - opens the app window (python\app.py)
rem This folder can be moved anywhere: %~dp0 is the folder of this file.
cd /d "%~dp0"
where pythonw >nul 2>nul
if %errorlevel%==0 (
  start "" pythonw python\app.py
) else (
  start "" python python\app.py
)
