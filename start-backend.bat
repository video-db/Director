@echo off
setlocal

cd /d "%~dp0backend" || exit /b 1

if not exist "venv\Scripts\activate.bat" (
    echo Backend not initialized. Run setup.bat first.
    exit /b 1
)

echo Backend: http://127.0.0.1:8000 (Ctrl+C to stop)
call venv\Scripts\activate.bat
set SQLITE_DB_PATH=director.db
python director\db\sqlite\initialize.py >nul 2>&1
if errorlevel 1 (
    echo SQLite initialization failed.
    exit /b 1
)
python director\entrypoint\api\server.py
