@echo off
setlocal

cd /d "%~dp0" || exit /b 1

if not exist "backend\venv\Scripts\activate.bat" (
    echo Backend not initialized. Run setup.bat first.
    exit /b 1
)

if not exist "frontend\node_modules\" (
    echo Frontend not initialized. Run setup.bat first.
    exit /b 1
)

set "LAUNCH_DIR=%CD%"
echo Launching backend window...
start "" cmd /k call "%LAUNCH_DIR%\start-backend.bat"
echo Backend window launched.
timeout /t 2 /nobreak >nul
echo Launching frontend window...
start "" cmd /k call "%LAUNCH_DIR%\start-frontend.bat"
echo Frontend window launched.

echo Backend: http://127.0.0.1:8000
echo Frontend: http://127.0.0.1:8080
echo Close the backend and frontend windows to stop the services.
