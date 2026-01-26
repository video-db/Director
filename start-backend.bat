@echo off
setlocal ENABLEEXTENSIONS ENABLEDELAYEDEXPANSION

cd /d "%~dp0backend" || exit /b 1

if not exist "venv\Scripts\activate.bat" (
    echo Backend not initialized. Run setup.bat first.
    exit /b 1
)

call :ensure_backend_env
if errorlevel 1 exit /b 1

echo Backend: http://127.0.0.1:8000 (Ctrl+C to stop)
call venv\Scripts\activate.bat
set "DB_TYPE=sqlite"
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

:ensure_backend_env
set "ENV_FILE=.env"
if not exist "%ENV_FILE%" (
    if exist .env.sample (
        copy /y .env.sample .env >nul
    ) else (
        (
            echo VIDEO_DB_API_KEY=
            echo.
            echo # Database
        )> "%ENV_FILE%"
    )
)

call :set_env_value "%ENV_FILE%" "DB_TYPE" "sqlite"
exit /b %errorlevel%

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

:deps_fail
echo Failed to reinstall backend dependencies. Review the messages above.
exit /b 1
