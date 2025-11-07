@echo off
setlocal ENABLEEXTENSIONS ENABLEDELAYEDEXPANSION

cd /d "%~dp0frontend" || exit /b 1

where npm >nul 2>&1 || (
    echo npm not found. Install Node.js from https://nodejs.org/ and rerun setup.bat.
    exit /b 1
)

call :ensure_frontend_deps
if errorlevel 1 goto :deps_fail

call :configure_frontend_runtime
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

if not defined VITE_PORT set "VITE_PORT=8080"
if not defined VITE_BIND_HOST set "VITE_BIND_HOST=0.0.0.0"

if /i "%VITE_BIND_HOST%"=="0.0.0.0" (
    echo Frontend: http://127.0.0.1:%VITE_PORT% (Ctrl+C to stop)
) else (
    echo Frontend: http://%VITE_BIND_HOST%:%VITE_PORT% (Ctrl+C to stop)
)

call npm run dev -- --host %VITE_BIND_HOST% --port %VITE_PORT%
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

:configure_frontend_runtime
set "ENV_FILE=.env"
if not exist "%ENV_FILE%" (
    if exist .env.sample (
        copy /y .env.sample .env >nul
    ) else (
        (
            echo VITE_APP_BACKEND_URL=http://127.0.0.1:8000
            echo VITE_PORT=8080
            echo VITE_OPEN_BROWSER=true
        )> "%ENV_FILE%"
    )
)

set "REQUESTED_PORT="
if exist "%ENV_FILE%" (
    for /f "tokens=2 delims==" %%P in ('findstr /R "^VITE_PORT=" "%ENV_FILE%"') do (
        set "REQUESTED_PORT=%%P"
    )
)
if defined REQUESTED_PORT (
    for /f "tokens=1" %%Q in ("!REQUESTED_PORT!") do set "REQUESTED_PORT=%%Q"
) else (
    set "REQUESTED_PORT=8080"
)
set "ORIGINAL_PORT=%REQUESTED_PORT%"

set "PORT_CANDIDATES=%REQUESTED_PORT% 8080 5173 8081 8000 3000 3001 9000 5500"
call :find_available_port %PORT_CANDIDATES%
if errorlevel 1 (
    echo Unable to find an available port for the frontend dev server.
    exit /b 1
)

set "VITE_PORT=%RESOLVED_PORT%"
set "VITE_BIND_HOST=%RESOLVED_HOST%"
if not defined VITE_BIND_HOST set "VITE_BIND_HOST=0.0.0.0"

call :set_env_value "%ENV_FILE%" "VITE_PORT" "%VITE_PORT%"

if /i "%VITE_BIND_HOST%"=="127.0.0.1" (
    echo Binding dev server to loopback because listening on 0.0.0.0 was blocked.
)
if "%VITE_PORT%" NEQ "%ORIGINAL_PORT%" (
    echo Using port %VITE_PORT% for the dev server (requested %ORIGINAL_PORT% was unavailable).
)

exit /b 0

:find_available_port
set "RESOLVED_PORT="
set "RESOLVED_HOST="
for %%P in (%*) do (
    if not defined RESOLVED_PORT (
        call :probe_port %%P
        if not errorlevel 1 (
            set "RESOLVED_PORT=%%P"
            set "RESOLVED_HOST=!PROBED_HOST!"
        )
    )
)
if not defined RESOLVED_PORT exit /b 1
exit /b 0

:probe_port
set "PROBED_HOST="
powershell -NoProfile -Command "try { $listener = [System.Net.Sockets.TcpListener]::new([System.Net.IPAddress]::Any,%~1); $listener.Start(); $listener.Stop(); exit 0 } catch { try { $listener = [System.Net.Sockets.TcpListener]::new([System.Net.IPAddress]::Loopback,%~1); $listener.Start(); $listener.Stop(); exit 2 } catch { exit 1 } }" >nul 2>&1
set "PS_EXIT=%ERRORLEVEL%"
if "%PS_EXIT%"=="0" (
    set "PROBED_HOST=0.0.0.0"
    exit /b 0
)
if "%PS_EXIT%"=="2" (
    set "PROBED_HOST=127.0.0.1"
    exit /b 0
)
exit /b 1

:set_env_value
setlocal ENABLEDELAYEDEXPANSION
set "ENV_FILE=%~1"
set "ENV_KEY=%~2"
set "ENV_VALUE=%~3"

if not exist "%ENV_FILE%" (
    >"%ENV_FILE%" echo %ENV_KEY%=%ENV_VALUE%
    endlocal & exit /b 0
)

set "TEMP_FILE=%ENV_FILE%.tmp"
set "VAR_WRITTEN="
(
    for /f "usebackq delims=" %%L in ("%ENV_FILE%") do (
        set "LINE=%%L"
        set "WRITE_LINE=1"
        for /f "tokens=1* delims==" %%K in ("!LINE!") do (
            set "KEY=%%K"
            if /i "!KEY!"=="%ENV_KEY%" (
                if not defined VAR_WRITTEN (
                    echo %ENV_KEY%=%ENV_VALUE%
                    set "VAR_WRITTEN=1"
                )
                set "WRITE_LINE="
            )
        )
        if defined WRITE_LINE (
            echo !LINE!
        )
    )
    if not defined VAR_WRITTEN (
        echo %ENV_KEY%=%ENV_VALUE%
    )
) >"%TEMP_FILE%"
move /Y "%TEMP_FILE%" "%ENV_FILE%" >nul
endlocal & exit /b 0

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
