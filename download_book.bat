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

REM Выбор режима работы
echo Выберите режим работы:
echo 1. Интерактивный режим (ввод URL)
echo 2. Скачать определенные главы
echo 3. Запустить тесты
echo.
set /p choice="Введите номер (1-3): "

if "%choice%"=="1" (
    echo.
    echo Запускаем интерактивный режим...
    python console_downloader.py
) else if "%choice%"=="2" (
    echo.
    echo Режим скачивания определенных глав
    set /p book_url="Введите URL книги: "
    set /p start_chapter="Введите номер начальной главы: "
    set /p end_chapter="Введите номер конечной главы: "
    set /p output_dir="Введите папку для сохранения (или нажмите Enter для output/): "
    
    if "%output_dir%"=="" set output_dir=output
    
    echo.
    echo Скачиваем главы %start_chapter%-%end_chapter%...
    python main.py download-range --slug %book_url% --start %start_chapter% --end %end_chapter% --output %output_dir%/
) else if "%choice%"=="3" (
    echo.
    echo Запускаем тесты...
    python -m pytest tests/test_ranobelib_integration.py -v -s
) else (
    echo.
    echo Неверный выбор, запускаем интерактивный режим...
    python console_downloader.py
)

echo.
echo Нажмите любую клавишу для выхода...
pause >nul
