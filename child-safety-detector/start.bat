@echo off
REM ==================================================================
REM  start.bat
REM  One-click launcher for Guardian Lens on Windows.
REM  Runs everything in THIS one window (no separate spawned window).
REM ==================================================================

title Guardian Lens - AI Child Screen Safety Detector
setlocal
cd /d "%~dp0"

echo ============================================================
echo   Guardian Lens - AI Child Screen Safety Detector
echo   Working folder: %cd%
echo ============================================================
echo.

REM ---- Step 1: Find a working Python command ----
set PYCMD=
where python >nul 2>nul
if not errorlevel 1 (
    set PYCMD=python
) else (
    where py >nul 2>nul
    if not errorlevel 1 set PYCMD=py
)

if "%PYCMD%"=="" (
    echo [ERROR] Python was not found on your PATH.
    echo Install Python 3 from https://www.python.org/downloads/
    echo and make sure "Add Python to PATH" is checked during install.
    echo.
    pause
    exit /b 1
)
echo [1/5] Using Python command: %PYCMD%

REM ---- Step 2: Create the virtual environment if needed ----
set VENV_PY=venv\Scripts\python.exe
if exist "%VENV_PY%" (
    echo [2/5] Virtual environment found.
) else (
    echo [2/5] Creating virtual environment...
    %PYCMD% -m venv venv
    if not exist "%VENV_PY%" (
        echo [ERROR] Failed to create the virtual environment.
        pause
        exit /b 1
    )
)

REM ---- Step 3: Install required packages ----
echo [3/5] Installing required packages (this may take a minute the first time)...
"%VENV_PY%" -m pip install -r requirements.txt
if errorlevel 1 (
    echo.
    echo [ERROR] pip install failed. See the error messages above.
    echo   - Make sure you have internet access
    echo   - Delete the "venv" folder and re-run this file for a clean retry
    echo.
    pause
    exit /b 1
)

REM ---- Step 4: Verify Flask imports correctly ----
echo [4/5] Verifying Flask is installed correctly...
"%VENV_PY%" -c "import flask; print('Flask', flask.__version__, 'OK')"
if errorlevel 1 (
    echo.
    echo [ERROR] Flask does not import even after installing.
    echo Try deleting the "venv" folder and re-running this file.
    echo.
    pause
    exit /b 1
)

REM ---- Step 5: Open the browser and start the server (in this window) ----
echo [5/5] Starting Guardian Lens...
echo.
echo Opening your browser to http://127.0.0.1:5000
echo The server log will print below. Press CTRL+C to stop the app.
echo ------------------------------------------------------------
echo.

start "" http://127.0.0.1:5000
"%VENV_PY%" app.py

echo.
echo ------------------------------------------------------------
echo The server has stopped. If that was unexpected, scroll up to
echo read the error message above.
pause
