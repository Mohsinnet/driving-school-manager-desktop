@echo off
title Build - Driving School Manager (Windows)
echo ============================================================
echo   Rebuild the app after editing app.py
echo ============================================================
echo.

python --version >nul 2>&1
if errorlevel 1 goto pymiss

python -m PyInstaller --version >nul 2>&1
if errorlevel 1 goto needpyi

python -c "import openpyxl" >nul 2>&1
if errorlevel 1 goto needxl

python -c "import cryptography" >nul 2>&1
if errorlevel 1 goto needcrypto

goto build

:needpyi
echo [INFO] Installing PyInstaller...
python -m pip install --upgrade pyinstaller
goto build

:needxl
echo [INFO] Installing openpyxl (Excel support)...
python -m pip install openpyxl
goto build

:needcrypto
echo [INFO] Installing cryptography (encryption support)...
python -m pip install cryptography

:build
echo.
echo Building... this may take about a minute.
echo.
python -m PyInstaller --noconfirm --onefile --windowed --name DrivingSchoolManager --icon icon.ico --add-data "icon.ico;." --hidden-import openpyxl --hidden-import et_xmlfile --hidden-import PIL --hidden-import PIL.Image --hidden-import cryptography --collect-all ttkbootstrap app.py
if errorlevel 1 goto fail

copy /Y "dist\DrivingSchoolManager.exe" "DrivingSchoolManager.exe" >nul

echo.
echo ============================================================
echo   Build succeeded.
echo   Executable:  %cd%\DrivingSchoolManager.exe
echo.
echo   Copy it anywhere to run it.
echo ============================================================
pause
exit /b 0

:pymiss
echo.
echo [ERROR] Python not found. Install Python 3 from python.org first.
echo.
pause
exit /b 1

:fail
echo.
echo ============================================================
echo   [ERROR] Build failed. See messages above.
echo ============================================================
pause
exit /b 1
