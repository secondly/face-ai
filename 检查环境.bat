@echo off
title Environment Checker

echo.
echo Environment Information
echo =======================
echo.

echo System: %OS%
echo Computer: %COMPUTERNAME%
echo.

echo Python Check:
python --version 2>nul
if errorlevel 1 (
    echo [FAIL] Python not found
) else (
    echo [OK] Python available
)

echo.
echo Conda Check:
conda --version 2>nul
if errorlevel 1 (
    echo [FAIL] Conda not found
) else (
    echo [OK] Conda available
    echo.
    echo Current environment:
    conda info --envs | findstr "*"
    echo.
    echo All environments:
    conda env list
)

echo.
echo face-ai-cuda11 Check:
conda env list | findstr "face-ai-cuda11" >nul
if errorlevel 1 (
    echo [FAIL] face-ai-cuda11 not found
) else (
    echo [OK] face-ai-cuda11 exists
)

echo.
echo GPU Check:
nvidia-smi >nul 2>&1
if errorlevel 1 (
    echo [FAIL] NVIDIA GPU not detected
) else (
    echo [OK] NVIDIA GPU available
)

echo.
echo =======================
echo To start: run start_face_swap.bat
echo =======================
echo.

pause
