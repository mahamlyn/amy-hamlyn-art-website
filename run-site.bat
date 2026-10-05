@echo off
setlocal

cd /d "%~dp0"

set PYTHON="C:\Users\Admin\AppData\Local\Programs\Python\Python312\python.exe"

if not exist "%PYTHON%" (
    echo Python not found at %PYTHON%
    echo Install Python 3.12 from https://www.python.org/downloads/
    pause
    exit /b 1
)

if not exist ".venv\Scripts\python.exe" (
    echo Creating virtual environment...
    "%PYTHON%" -m venv .venv
)

call ".venv\Scripts\activate.bat"
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python app.py

endlocal
