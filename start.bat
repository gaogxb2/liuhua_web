@echo off
cd /d %~dp0
pip install -r requirements.txt
REM --reload：修改 .py 等代码后自动重启，保存后刷新网页即可，无需手动 Ctrl+C
uvicorn api.main:app --host 0.0.0.0 --port 8001 --reload
