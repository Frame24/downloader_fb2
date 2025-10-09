@echo off
chcp 65001 >nul
title Скачивальщик книг - Быстрый запуск

REM Активируем виртуальную среду если она есть
if exist ".venv\Scripts\activate.bat" (
    call .venv\Scripts\activate.bat
)

REM Запускаем простой интерфейс
python simple_downloader.py

pause
