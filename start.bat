@echo off
cd /d %~dp0
set PYTHONPATH=%~dp0
set PYTHONIOENCODING=utf-8
set FLASK_PRODUCTION=true
echo 启动服务器: http://localhost:5000
python web\app.py
pause
