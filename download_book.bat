@echo off
chcp 65001 >nul
title Скачивальщик книг

echo.
echo ================================================
echo           СКАЧИВАЛЬЩИК КНИГ
echo ================================================
echo.

REM Проверяем наличие Python
python --version >nul 2>&1
if errorlevel 1 (
    echo Python не найден! Установите Python 3.8+ и добавьте в PATH
    echo.
    pause
    exit /b 1
)

REM Проверяем наличие файла программы
if not exist "console_downloader.py" (
    echo Файл console_downloader.py не найден!
    echo.
    pause
    exit /b 1
)

REM Активируем виртуальную среду если она есть
if exist ".venv\Scripts\activate.bat" (
    call .venv\Scripts\activate.bat
)

REM Проверяем зависимости
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

REM Выбор режима работы
echo Выберите режим работы:
echo 1. Простой интерфейс (рекомендуется)
echo 2. Командная строка
echo 3. Запустить тесты
echo.
set /p choice="Введите номер (1-3): "

if "%choice%"=="1" (
    echo.
    echo Запускаем простой интерфейс...
    python simple_downloader.py
) else if "%choice%"=="2" (
    echo.
    echo Режим командной строки
    echo Примеры команд:
    echo   python -m src.interface "URL_книги"
    echo   python -m src.interface "URL_книги" --start 15 --end 20
    echo   python -m src.interface "URL_книги" --info-only
    echo.
    set /p command="Введите команду: "
    if "%command%" neq "" (
        %command%
    ) else (
        echo Команда не введена
    )
) else if "%choice%"=="3" (
    echo.
    echo Запускаем тесты...
    call run_tests.bat
) else (
    echo.
    echo Неверный выбор, запускаем простой интерфейс...
    python simple_downloader.py
)

echo.
echo Нажмите любую клавишу для выхода...
pause >nul
