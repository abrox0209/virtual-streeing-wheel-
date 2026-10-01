@echo off
cd /d "%~dp0"
echo ============================================
echo  Virtual Steering - one-time setup
echo ============================================

set PYCMD=
py -3.12 --version >nul 2>nul
if %errorlevel%==0 set PYCMD=py -3.12
if "%PYCMD%"=="" (
    python --version >nul 2>nul
    if %errorlevel%==0 set PYCMD=python
)
if "%PYCMD%"=="" (
    echo ERROR: Python was not found. Install Python 3.12 from https://www.python.org/downloads/
    echo During install, tick "Add python.exe to PATH". Then run setup.bat again.
    pause
    exit /b 1
)
echo Using: %PYCMD%
%PYCMD% --version

if not exist "venv\Scripts\activate.bat" (
    echo Creating virtual environment...
    %PYCMD% -m venv venv
    if errorlevel 1 (
        echo ERROR: Could not create the virtual environment.
        pause
        exit /b 1
    )
) else (
    echo Virtual environment already exists.
)

call venv\Scripts\activate.bat
python -m pip install --upgrade pip
echo Installing requirements - this can take a few minutes...
pip install -r requirements.txt
if errorlevel 1 (
    echo ERROR: Installing requirements failed. Check your internet connection and try again.
    echo If it keeps failing, make sure you use 64-bit Python 3.12.
    pause
    exit /b 1
)

echo Running self-check...
python main.py --check
echo.
echo ============================================
echo  Setup is complete. Double-click run.bat to start.
echo ============================================
pause
