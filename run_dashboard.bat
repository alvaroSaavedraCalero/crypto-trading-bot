@echo off
set PYTHONPATH=%CD%
if not exist ".venv" (
    echo Virtual environment not found. Please run 'python -m venv .venv' first.
    pause
    exit /b
)
call .venv\Scripts\activate.bat
python cli_dashboard.py
pause
