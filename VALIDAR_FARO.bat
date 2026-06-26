@echo off
title FARO v5.3 - Validar
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

%PYTHON_CMD% -m py_compile faro.py
if %errorlevel% neq 0 (
    echo Validacion fallida en faro.py
    pause
    exit /b
)

%PYTHON_CMD% -m py_compile faro_dependency_check.py
if %errorlevel% neq 0 (
    echo Validacion fallida en faro_dependency_check.py
    pause
    exit /b
)

%PYTHON_CMD% faro_dependency_check.py
if %errorlevel% neq 0 (
    echo Revision de dependencias fallida.
    pause
    exit /b
)

echo FARO v5.3 validado correctamente.
pause
