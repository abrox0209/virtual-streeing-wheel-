@echo off
cd /d "%~dp0"
if not exist "venv\Scripts\activate.bat" (
    echo The virtual environment was not found. Running setup first...
    call setup.bat
)
call venv\Scripts\activate.bat
python main.py
echo.
pause
