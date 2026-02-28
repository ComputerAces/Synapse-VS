@echo off
setlocal EnableDelayedExpansion
set "PYTHONPATH=%~dp0"
echo Setting PYTHONPATH to %PYTHONPATH%

REM Check if environment folder exists
if exist "environment" goto :SKIP_SETUP

echo Creating virtual environment...
python -m venv environment

echo Upgrading pip...
environment\Scripts\python.exe -m pip install --upgrade pip

echo.
echo ========================================================
echo               SYNAPSE VS - FIRST TIME SETUP
echo ========================================================
echo.
echo Select installation mode:
echo [1] Minimal (Online Hot-Loading) - fast, installs setup\requirements_min.txt
echo [2] Full (Offline Capable) - slower, installs setup\requirements_max.txt + browsers
echo.
set /p "install_choice=Enter selection (1 or 2) [Default: 2]: "

if "!install_choice!"=="1" (
    echo Installing MINIMAL requirements...
    environment\Scripts\pip install -r setup\requirements_min.txt
) else (
    echo Installing FULL requirements...
    environment\Scripts\pip install -r setup\requirements_max.txt
    echo Installing Playwright Browsers...
    environment\Scripts\playwright install
)

:SKIP_SETUP

REM Activate the virtual environment
call environment\Scripts\activate.bat

REM Run the Synapse Architect GUI
if exist "synapse\gui\main_window.py" (
    echo Launching Synapse VS Architect...
    python "synapse\gui\main_window.py" %*
) else (
    echo Error: synapse\gui\main_window.py not found.
)
