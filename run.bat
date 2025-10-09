@echo off
chcp 65001 >nul
title Скачивальщик книг

REM Активируем виртуальную среду если она есть
if exist ".venv\Scripts\activate.bat" (
    call .venv\Scripts\activate.bat
)

echo.
echo ================================================
echo           СКАЧИВАЛЬЩИК КНИГ
echo ================================================
echo.
echo Выберите режим:
echo 1. Простой интерфейс
echo 2. Командная строка
echo 3. Тесты
echo.
set /p choice="Введите номер (1-3): "

if "%choice%"=="1" (
    echo.
    echo Запускаем простой интерфейс...
    python simple_downloader.py
) else if "%choice%"=="2" (
    echo.
    echo Запускаем командную строку...
    call cmd_interface.bat
) else if "%choice%"=="3" (
    echo.
    echo Запускаем тесты...
    call run_tests.bat
) else (
    echo.
    echo Неверный выбор, запускаем командную строку...
    call cmd_interface.bat
)

pause
