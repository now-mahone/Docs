@echo off
REM ============================================================
REM   KERNE NEURAL NET - Build GUI Trainer as .exe
REM   Run this once to produce:
REM     neural net/dist/KerneTrainer/KerneTrainer.exe
REM ============================================================

echo.
echo ============================================================
echo   KERNE TRAINER - EXE Builder
echo ============================================================
echo.

cd /d "%~dp0"

REM Install / upgrade PyInstaller
echo Installing PyInstaller...
pip install pyinstaller --quiet
if errorlevel 1 (
    echo [ERROR] Failed to install PyInstaller.
    pause
    exit /b 1
)

REM Ensure GUI dependencies are present
echo Installing GUI dependencies...
pip install matplotlib --quiet

echo.
echo Building KerneTrainer.exe ...
echo This will take 1-3 minutes on first run.
echo.

pyinstaller ^
  --name "KerneTrainer" ^
  --onedir ^
  --windowed ^
  --clean ^
  --noconfirm ^
  --add-data "src;src" ^
  --hidden-import=matplotlib.backends.backend_tkagg ^
  --hidden-import=tkinter ^
  --hidden-import=tkinter.ttk ^
  --hidden-import=tkinter.scrolledtext ^
  --hidden-import=tkinter.messagebox ^
  --hidden-import=torch ^
  --hidden-import=numpy ^
  --hidden-import=pandas ^
  --hidden-import=requests ^
  --hidden-import=tqdm ^
  gui_trainer.py

if errorlevel 1 (
    echo.
    echo [ERROR] Build failed. See output above.
    pause
    exit /b 1
)

echo.
echo ============================================================
echo   BUILD COMPLETE!
echo   Executable: dist\KerneTrainer\KerneTrainer.exe
echo   Double-click it to launch the Kerne Trainer GUI.
echo ============================================================
pause