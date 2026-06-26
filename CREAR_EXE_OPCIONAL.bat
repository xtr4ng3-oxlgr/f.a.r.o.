@echo off
title FARO v4 - Crear EXE opcional
color 1F
chcp 65001 >nul
cd /d "%~dp0"

set PYTHON_CMD=
where py >nul 2>nul
if %errorlevel%==0 set PYTHON_CMD=py -3
if "%PYTHON_CMD%"=="" (
    where python >nul 2>nul
    if %errorlevel%==0 set PYTHON_CMD=python
)
if "%PYTHON_CMD%"=="" (
    echo Python no encontrado.
    pause
    exit /b
)

%PYTHON_CMD% -m pip install --upgrade pip
%PYTHON_CMD% -m pip install pyinstaller
%PYTHON_CMD% -m PyInstaller --onefile --windowed --name FARO faro.py

echo.
echo EXE creado en dist\FARO.exe
pause
