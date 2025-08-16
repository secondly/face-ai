@echo off
title AI Face Swap Tool
cd /d "%~dp0"

echo.
echo AI Face Swap Tool - Launcher
echo =============================
echo Current directory: %CD%
echo.

echo Step 1: Checking conda...
where conda >nul 2>&1
if errorlevel 1 (
    echo ERROR: conda command not found in PATH
    echo Please install Anaconda or Miniconda and restart terminal
    echo.
    pause
    exit /b 1
)
echo OK: conda found

echo.
echo Step 2: Checking face-ai-cuda11 environment...
conda env list | findstr "face-ai-cuda11" >nul 2>&1
if errorlevel 1 (
    echo ERROR: face-ai-cuda11 environment not found
    echo Please create it first using the setup guide
    echo.
    pause
    exit /b 1
)
echo OK: face-ai-cuda11 environment exists

echo.
echo Step 3: Activating environment...
call conda activate face-ai-cuda11
if errorlevel 1 (
    echo ERROR: Failed to activate environment
    echo.
    pause
    exit /b 1
)
echo OK: Environment activated

echo Environment activated successfully
echo Current Python version:
python --version

echo.
echo Starting AI Face Swap Tool...
echo Please wait for the GUI to load...
echo.

python main_pyqt.py

if errorlevel 1 (
    echo.
    echo ERROR: Program failed to start
    echo Check dependencies and try again
    echo.
    pause
) else (
    echo.
    echo Program closed normally
    pause
)
