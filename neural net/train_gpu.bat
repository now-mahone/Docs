@echo off
REM ============================================================
REM   KERNE NEURAL NET - GPU TRAINER
REM   Double-click this file to train the model on your GPU
REM ============================================================

echo.
echo ============================================================
echo   KERNE NEURAL NET - GPU TRAINER
echo ============================================================
echo.

REM Check for NVIDIA GPU
echo Checking for GPU...
nvidia-smi --query-gpu=name,memory.total --format=csv,noheader 2>nul
if errorlevel 1 (
    echo.
    echo [WARNING] No NVIDIA GPU detected or drivers not installed.
    echo Training will use CPU (slower).
    echo.
) else (
    echo.
    echo [OK] GPU Detected!
    echo.
)

cd /d "%~dp0"

REM Check Python
python --version 2>nul
if errorlevel 1 (
    echo [ERROR] Python not found. Please install Python 3.10+
    pause
    exit /b 1
)

REM Check dependencies
echo Checking dependencies...
pip show torch 2>nul | findstr "Name" >nul
if errorlevel 1 (
    echo Installing dependencies...
    pip install torch numpy pandas requests tqdm scikit-learn xgboost --quiet
)

echo.
echo Starting GPU Trainer...
echo This will:
echo   1. Fetch latest yield data from DeFiLlama
echo   2. Train the model on your GPU
echo   3. Save the trained model
echo.
echo Press Ctrl+C to stop at any time.
echo.

REM Run the GPU trainer with 50 epochs
python gpu_trainer.py --epochs 50

echo.
echo ============================================================
echo Training complete! Press any key to exit.
echo ============================================================
pause
