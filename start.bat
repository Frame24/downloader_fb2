@echo off
chcp 65001 >nul
title Скачивальщик книг

python --version >nul 2>&1
if errorlevel 1 (
    echo Python не найден! Установите Python 3.8+ и добавьте в PATH
    echo.
    pause
    exit /b 1
)

if exist ".venv\Scripts\activate.bat" (
    call .venv\Scripts\activate.bat
)

python -c "import requests" >nul 2>&1
if errorlevel 1 (
    echo Устанавливаем зависимости...
    pip install -r requirements.txt
    if errorlevel 1 (
        echo Ошибка установки зависимостей!
        pause
        exit /b 1
    )
)

python simple_downloader.py

echo.
pause >nul
