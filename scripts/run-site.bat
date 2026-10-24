@echo off
setlocal

cd /d "%~dp0.."
if errorlevel 1 goto :error

if not exist ".venv\Scripts\python.exe" (
    echo Creating virtual environment...
    where py >nul 2>&1
    if not errorlevel 1 (
        py -3 -m venv .venv
    ) else (
        python -m venv .venv
    )
    if errorlevel 1 goto :error
)

if not exist ".venv\Scripts\python.exe" goto :error

".venv\Scripts\python.exe" -m pip install -r requirements.txt
if errorlevel 1 goto :error

".venv\Scripts\python.exe" app.py
exit /b %ERRORLEVEL%

:error
echo Could not prepare or start the website. Check that Python 3 is installed and available as py or python.
pause
exit /b 1