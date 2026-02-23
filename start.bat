@echo off
chcp 65001 >nul
title Скачивальщик книг

echo.
echo ================================================
echo           СКАЧИВАЛЬЩИК КНИГ
echo ================================================
echo.
echo Диапазон глав: включительный (например, 1-5 скачает главы 1,2,3,4,5)
echo.

REM Проверяем наличие Python
python --version >nul 2>&1
if errorlevel 1 (
    echo Python не найден! Установите Python 3.8+ и добавьте в PATH
    echo.
    pause
    exit /b 1
)

REM Активируем виртуальную среду если она есть
if exist ".venv\Scripts\activate.bat" (
    echo Активируем виртуальную среду...
    call .venv\Scripts\activate.bat
    echo Виртуальная среда активирована!
) else (
    echo Виртуальная среда не найдена, используем системный Python
)

REM Проверяем зависимости
echo Проверяем зависимости...
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

echo Все готово к работе!
echo.

REM Запускаем простой интерфейс
python simple_downloader.py

echo.
echo Нажмите любую клавишу для выхода...
pause >nul
