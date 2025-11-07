@echo off
setlocal ENABLEEXTENSIONS ENABLEDELAYEDEXPANSION

cd /d "%~dp0backend" || exit /b 1

if not exist "venv\Scripts\activate.bat" (
    echo Backend not initialized. Run setup.bat first.
    exit /b 1
)

echo Backend: http://127.0.0.1:8000 (Ctrl+C to stop)
call venv\Scripts\activate.bat
set SQLITE_DB_PATH=director.db
pip check >nul 2>&1
if errorlevel 1 (
    echo Backend dependencies incomplete. Reinstalling requirements...
    pip install --upgrade pip setuptools wheel >nul 2>&1
    pip install -r requirements.txt || goto :deps_fail
    if exist requirements-dev.txt (
        pip install -r requirements-dev.txt || goto :deps_fail
    )
    pip check || goto :deps_fail
)
python director\db\sqlite\initialize.py >nul 2>&1
if errorlevel 1 (
    echo SQLite initialization failed.
    exit /b 1
)
python director\entrypoint\api\server.py
exit /b %errorlevel%

:deps_fail
echo Failed to reinstall backend dependencies. Review the messages above.
exit /b 1
