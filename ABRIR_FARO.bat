@echo off
title FARO v5.3
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
    echo Instale Python desde python.org y vuelva a intentar.
    pause
    exit /b
)

echo.
echo [FARO] Revisando dependencias...
%PYTHON_CMD% faro_dependency_check.py
if %errorlevel% neq 0 (
    echo.
    echo [FARO] No se pudo completar la revision de dependencias.
    echo Revise faro_data\dependency_check.log
    pause
    exit /b
)

echo.
echo [FARO] Abriendo aplicacion...
%PYTHON_CMD% faro.py
pause
