@echo off
title ShalomCI - System Launcher
color 0B
echo ===================================================
echo     Starting ShalomCI Lifecycle Management...
echo ===================================================
echo.
echo Initializing local server, please wait...

:: מעבר לנתיב שבו נמצא הקובץ כדי למנוע שגיאות נתיב
cd /d "%~dp0"

:: הרצת המערכת דרך uv
uv run streamlit run src/gui/app.py

pause