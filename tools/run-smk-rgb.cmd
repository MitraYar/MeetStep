@echo off
cd /d "%~dp0"
if not exist .rgb-venv\Scripts\python.exe py -3 -m venv .rgb-venv
if errorlevel 1 goto fail
.rgb-venv\Scripts\python.exe -m pip install mido==1.3.3 python-rtmidi==1.5.8
if errorlevel 1 goto fail
.rgb-venv\Scripts\python.exe smk_rgb.py
:fail
pause
