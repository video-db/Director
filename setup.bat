@echo off
setlocal ENABLEEXTENSIONS ENABLEDELAYEDEXPANSION

echo.
echo === Director Setup (Windows) ===
echo.

:: Locate Python
set "PY_CMD="
where py >nul 2>nul && set "PY_CMD=py -3"
if "%PY_CMD%"=="" (
    where python >nul 2>nul && set "PY_CMD=python"
)
if "%PY_CMD%"=="" (
    echo [ERROR] Python 3.9+ not found. Install it from https://www.python.org/downloads/
    goto :fail
)
for /f "tokens=2" %%v in ('%PY_CMD% --version 2^>^&1') do set "PY_VER=%%v"
echo [OK] Python %PY_VER%

:: Locate Node.js and npm
where node >nul 2>nul || (
    echo [ERROR] Node.js not found. Install it from https://nodejs.org/
    goto :fail
)
for /f "tokens=*" %%v in ('node --version 2^>^&1') do set "NODE_VER=%%v"
set "NODE_VER_CLEAN=%NODE_VER%"
if /i "%NODE_VER_CLEAN:~0,1%"=="v" set "NODE_VER_CLEAN=%NODE_VER_CLEAN:~1%"
set "NODE_MAJ="
set "NODE_MIN="
set "NODE_PATCH="
for /f "tokens=1-3 delims=." %%a in ("%NODE_VER_CLEAN%") do (
    set "NODE_MAJ=%%a"
    set "NODE_MIN=%%b"
    set "NODE_PATCH=%%c"
)
if "%NODE_MAJ%"=="" set "NODE_MAJ=0"
if "%NODE_MIN%"=="" set "NODE_MIN=0"
if "%NODE_PATCH%"=="" set "NODE_PATCH=0"
for /f "tokens=1 delims=-" %%p in ("%NODE_MAJ%") do set "NODE_MAJ=%%p"
for /f "tokens=1 delims=-" %%p in ("%NODE_MIN%") do set "NODE_MIN=%%p"
for /f "tokens=1 delims=-" %%p in ("%NODE_PATCH%") do set "NODE_PATCH=%%p"

set /a NODE_REQUIRED=22*10000 + 8*100 + 0 >nul 2>&1
set /a NODE_VALUE=%NODE_MAJ%*10000 + %NODE_MIN%*100 + %NODE_PATCH% >nul 2>&1
if %NODE_VALUE% LSS %NODE_REQUIRED% (
    echo [ERROR] Node.js 22.8.0 or higher required. Detected %NODE_VER%.
    goto :fail
)
echo [OK] Node.js %NODE_VER%

where npm >nul 2>nul || (
    echo [ERROR] npm not found. Reinstall Node.js from https://nodejs.org/
    goto :fail
)
for /f "tokens=*" %%v in ('npm --version 2^>^&1') do set "NPM_VER=%%v"
echo [OK] npm %NPM_VER%

echo.
echo Setting up backend...
pushd backend || goto :fail

if not exist venv (
    echo Creating virtual environment...
    %PY_CMD% -m venv venv || goto :fail_backend
)

call venv\Scripts\activate.bat || goto :fail_backend

echo Installing backend requirements...
pip install --upgrade pip setuptools wheel >nul 2>&1
pip install -r requirements.txt || goto :fail_backend
if exist requirements-dev.txt (
    pip install -r requirements-dev.txt || goto :fail_backend
)

pip check >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Backend dependencies are inconsistent. Resolve pip errors above.
    goto :fail_backend
)

if not exist .env (
    if exist .env.sample (
        copy /y .env.sample .env >nul
        echo DB_TYPE=sqlite >> .env
    ) else (
        (
            echo VIDEO_DB_API_KEY=
            echo.
            echo # Database
            echo DB_TYPE=sqlite
        )> .env
    )
)

echo Initializing SQLite database...
set SQLITE_DB_PATH=director.db
%PY_CMD% director\db\sqlite\initialize.py >nul 2>&1

call venv\Scripts\deactivate.bat >nul 2>&1
popd
echo [OK] Backend ready

echo.
echo Setting up frontend...
pushd frontend || goto :fail

echo Installing frontend dependencies...
set "NPM_LOCK_PRESENT="
if exist package-lock.json set "NPM_LOCK_PRESENT=1"

if defined NPM_LOCK_PRESENT (
    echo Running npm ci ^(clean install^)...
    call npm ci >nul 2>&1
    if errorlevel 1 (
        echo [WARN] npm ci failed. Retrying with npm install...
        call npm install || goto :fail_frontend
    )
) else (
    echo Running npm install...
    call npm install || goto :fail_frontend
)

set "FRONTEND_READY="
for %%R in (1 2) do (
    if not defined FRONTEND_READY (
        if exist node_modules\.bin\vite.cmd set "FRONTEND_READY=1"
    )
    if not defined FRONTEND_READY (
        if exist node_modules\.bin\vite.ps1 set "FRONTEND_READY=1"
    )
    if not defined FRONTEND_READY (
        if exist node_modules\vite\package.json set "FRONTEND_READY=1"
    )

    if not defined FRONTEND_READY (
        if %%R==1 (
            echo [WARN] Frontend dependencies incomplete. Cleaning node_modules and reinstalling...
            if exist node_modules rmdir /s /q node_modules
            if defined NPM_LOCK_PRESENT (
                call npm ci || goto :fail_frontend
            ) else (
                call npm install || goto :fail_frontend
            )
        )
    )
)

:frontend_verified
if not defined FRONTEND_READY (
    echo [ERROR] Unable to verify frontend dependencies.
    goto :fail_frontend
)

set "VITE_VERSION="
for /f "usebackq tokens=* delims=" %%v in (`node -p "require('./node_modules/vite/package.json').version" 2^>^&1`) do (
    set "VITE_VERSION=%%v"
    goto :vite_version_ready
)
:vite_version_ready

if not exist .env (
    (
        echo VITE_APP_BACKEND_URL=http://127.0.0.1:8000
        echo VITE_PORT=8080
        echo VITE_OPEN_BROWSER=true
    )> .env
)

if defined VITE_VERSION (
    echo [OK] Frontend ready ^(Vite !VITE_VERSION!^)
) else (
    echo [OK] Frontend ready
)

echo.
echo Setup complete.
echo Update backend\.env with your VIDEO_DB_API_KEY before running.
echo Use start-all.bat to launch both services.
echo For individual control: start-backend.bat or start-frontend.bat
echo.
exit /b 0

:fail_frontend
popd
goto :fail

:fail_backend
popd

:fail
echo.
echo Setup failed. Review the messages above.
pause
exit /b 1

