@echo off
REM Easy Windows launcher for the Supply Chain MAS prototype
cd /d "%~dp0"
echo === Supply Chain Multi-Agent System ===
if not exist venv (
  echo Creating virtual environment...
  python -m venv venv
)
call venv\Scripts\activate
echo Installing dependencies...
pip install -r requirements.txt
echo Starting backend + dashboard at http://127.0.0.1:8000 ...
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000
