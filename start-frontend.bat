@echo off
setlocal

cd /d "%~dp0frontend" || exit /b 1

if not exist "node_modules\" (
    echo Frontend not initialized. Run setup.bat first.
    exit /b 1
)

echo Frontend: http://127.0.0.1:8080 (Ctrl+C to stop)
npm run dev
