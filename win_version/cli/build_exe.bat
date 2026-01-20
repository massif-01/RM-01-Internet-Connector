@echo off
REM RM-01 Internet Connector - Windows CLI Build Script
REM Builds standalone executable using PyInstaller

echo ========================================
echo RM-01 CLI - Build Executable
echo ========================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.8 or later from python.org
    pause
    exit /b 1
)

echo [1/4] Installing dependencies...
pip install -r requirements.txt
if errorlevel 1 (
    echo ERROR: Failed to install dependencies
    pause
    exit /b 1
)

echo.
echo [2/4] Installing PyInstaller...
pip install pyinstaller
if errorlevel 1 (
    echo ERROR: Failed to install PyInstaller
    pause
    exit /b 1
)

echo.
echo [3/4] Building executable...

REM Check if icon exists
set ICON_PATH=..\..\icons\icon.png
if not exist "%ICON_PATH%" (
    echo Warning: Icon file not found at %ICON_PATH%
    set ICON_PARAM=
) else (
    set ICON_PARAM=--icon=%ICON_PATH%
)

REM Build with PyInstaller
pyinstaller --onefile ^
    --name rm01-cli ^
    %ICON_PARAM% ^
    --console ^
    --clean ^
    --noupx ^
    --add-data "network_service_windows.py;." ^
    cli.py

if errorlevel 1 (
    echo ERROR: PyInstaller build failed
    pause
    exit /b 1
)

echo.
echo [4/4] Build complete!
echo.
echo Executable location: dist\rm01-cli.exe
echo.
echo Usage:
echo   dist\rm01-cli.exe status      - Show connection status
echo   dist\rm01-cli.exe detect      - Detect RM-01 adapter  
echo   dist\rm01-cli.exe connect     - Enable internet sharing
echo   dist\rm01-cli.exe disconnect  - Disable internet sharing
echo.
echo Note: Run as Administrator for network configuration
echo.

pause
