@echo off
setlocal
set "PY=C:\Users\Admin\AppData\Local\Programs\Python\Python312\python.exe"
"%PY%" "%~dp0convert_wordpress_blog_posts.py"
if errorlevel 1 (
    echo.
    echo Conversion failed.
    pause
    exit /b 1
)
echo.
echo Blog conversion complete.
pause
