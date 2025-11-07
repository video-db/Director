@echo off
setlocal ENABLEEXTENSIONS ENABLEDELAYEDEXPANSION

cd /d "%~dp0frontend" || exit /b 1

where npm >nul 2>&1 || (
    echo npm not found. Install Node.js from https://nodejs.org/ and rerun setup.bat.
    exit /b 1
)

call :ensure_frontend_deps
if errorlevel 1 goto :deps_fail

set "VITE_VERSION="
for /f "usebackq tokens=* delims=" %%v in (`node -p "require('./node_modules/vite/package.json').version" 2^>^&1`) do (
    set "VITE_VERSION=%%v"
    goto :have_vite_version
)
:have_vite_version
if defined VITE_VERSION (
    echo Frontend dependencies ready ^(Vite !VITE_VERSION!^).
) else (
    echo Frontend dependencies ready.
)

echo Frontend: http://127.0.0.1:8080 (Ctrl+C to stop)
call npm run dev
exit /b %errorlevel%

:deps_fail
echo Failed to prepare frontend dependencies. Run setup.bat and review the output.
exit /b 1

:ensure_frontend_deps
if not exist package.json (
    echo Frontend source missing. Run setup.bat first.
    exit /b 1
)

call :ensure_patch_package
if errorlevel 1 exit /b 1

if exist node_modules\vite\package.json (
    if exist node_modules\.bin\vite.cmd goto :deps_ok
    if exist node_modules\.bin\vite.ps1 goto :deps_ok
)

if exist node_modules (
    echo Detected incomplete frontend installation. Cleaning node_modules...
    rmdir /s /q node_modules
)

if exist package-lock.json (
    echo Installing frontend dependencies with npm ci...
    call npm ci || exit /b 1
) else (
    echo Installing frontend dependencies with npm install...
    call npm install || exit /b 1
)

if not exist node_modules\vite\package.json exit /b 1
if not exist node_modules\.bin\vite.cmd (
    if not exist node_modules\.bin\vite.ps1 exit /b 1
)

:deps_ok
exit /b 0

:ensure_patch_package
set "PATCH_PACKAGE_READY="
where patch-package >nul 2>&1 && set "PATCH_PACKAGE_READY=1"
if not defined PATCH_PACKAGE_READY (
    if exist node_modules\.bin\patch-package.cmd set "PATCH_PACKAGE_READY=1"
)
if not defined PATCH_PACKAGE_READY (
    if exist node_modules\.bin\patch-package.ps1 set "PATCH_PACKAGE_READY=1"
)

if not defined PATCH_PACKAGE_READY (
    echo Ensuring patch-package is available for npm lifecycle scripts...
    npm install -g patch-package >nul 2>&1
    if errorlevel 1 (
        echo Failed to install patch-package globally. Run "npm install -g patch-package" manually and rerun the script.
        exit /b 1
    )
    where patch-package >nul 2>&1 && set "PATCH_PACKAGE_READY=1"
    if not defined PATCH_PACKAGE_READY (
        echo patch-package is still unavailable after installation. Ensure your npm global bin directory is on PATH and rerun the script.
        exit /b 1
    )
)

exit /b 0
