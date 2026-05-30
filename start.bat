@echo off
chcp 65001 >nul
cd /d %~dp0
set PYTHONPATH=%~dp0
set PYTHONIOENCODING=utf-8

set PORT=5001

:: Check port
netstat -ano | findstr ":%PORT% " >nul 2>&1
if not errorlevel 1 (
    echo [WARNING] Port %PORT% is already in use.
    echo Maybe the service is already running at http://localhost:%PORT%
    echo.
    choice /c YN /m "Open browser and exit?"
    if errorlevel 2 exit /b
    start http://localhost:%PORT%
    exit /b
)

:: Check waitress
python -c "import waitress" 2>nul
if errorlevel 1 (
    echo [INFO] waitress not found, using dev mode (FLASK_PRODUCTION=false)
    set FLASK_PRODUCTION=false
) else (
    set FLASK_PRODUCTION=true
)

echo Starting movie tool at http://localhost:%PORT%
python web\app.py
pause
