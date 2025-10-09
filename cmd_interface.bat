@echo off
chcp 65001 >nul
title Скачивальщик книг - Командная строка

REM Активируем виртуальную среду если она есть
if exist ".venv\Scripts\activate.bat" (
    call .venv\Scripts\activate.bat
)

echo.
echo ================================================
echo        СКАЧИВАЛЬЩИК КНИГ - КОМАНДНАЯ СТРОКА
echo ================================================
echo.
echo Примеры команд:
echo   python -m src.interface "URL_книги"
echo   python -m src.interface "URL_книги" --start 15 --end 20
echo   python -m src.interface "URL_книги" --info-only
echo   python -m src.interface "URL_книги" --title "Моя книга"
echo.
echo Для выхода введите: exit
echo.

:loop
set /p command="Введите команду: "
if "%command%"=="exit" goto end
if "%command%" neq "" (
    %command%
) else (
    echo Команда не введена
)
echo.
goto loop

:end
echo До свидания!
pause
