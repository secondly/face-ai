@echo off
title AI Face Swap Tool

echo.
echo AI Face Swap Tool - Launcher
echo =============================
echo.

echo Checking conda...
conda --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: conda not found
    echo Please install Anaconda or Miniconda
    pause
    exit /b 1
)

echo Checking face-ai-cuda11 environment...
conda env list | findstr "face-ai-cuda11" >nul
if errorlevel 1 (
    echo ERROR: face-ai-cuda11 environment not found
    echo Please create it first using the setup guide
    pause
    exit /b 1
)

echo Activating environment...
call conda deactivate 2>nul
call conda activate face-ai-cuda11

if errorlevel 1 (
    echo ERROR: Failed to activate environment
    pause
    exit /b 1
)

echo Environment activated successfully
echo Current Python version:
python --version

echo.
echo Starting AI Face Swap Tool...
python main_pyqt.py

if errorlevel 1 (
    echo.
    echo ERROR: Program failed to start
    echo Check dependencies and try again
    pause
)
