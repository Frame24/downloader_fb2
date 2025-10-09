@echo off
chcp 65001 >nul
title Тесты скачивальщика книг

echo.
echo ================================================
echo           ТЕСТЫ СКАЧИВАЛЬЩИКА КНИГ
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
python -c "import pytest" >nul 2>&1
if errorlevel 1 (
    echo Устанавливаем pytest...
    pip install pytest
)

echo Все готово к тестированию!
echo.

REM Выбор типа тестов
echo Выберите тип тестов:
echo 1. Быстрые тесты (API доступность)
echo 2. Тесты программного API
echo 3. Полные интеграционные тесты
echo 4. Тест конкретной книги
echo.
set /p choice="Введите номер (1-4): "

if "%choice%"=="1" (
    echo.
    echo Запускаем быстрые тесты...
    python -c "from tests.test_main import TestProject; t = TestProject(); t.test_api_accessibility(); t.test_url_parsing(); t.test_book_info_retrieval(); print('✅ Быстрые тесты пройдены!')"
) else if "%choice%"=="2" (
    echo.
    echo Запускаем тесты программного API...
    python -c "from tests.test_interface import TestBookDownloaderAPI; t = TestBookDownloaderAPI(); t.test_get_book_info(t.downloader(t.temp_dir())); t.test_downloader_configuration(); print('✅ Тесты API пройдены!')"
) else if "%choice%"=="3" (
    echo.
    echo Запускаем полные интеграционные тесты...
    python -c "from tests.test_main import TestProject; t = TestProject(); t.test_api_accessibility(); t.test_url_parsing(); t.test_book_info_retrieval(); t.test_chapters_list_retrieval(); print('✅ Интеграционные тесты пройдены!')"
) else if "%choice%"=="4" (
    echo.
    echo Тест конкретной книги
    set /p book_url="Введите URL книги: "
    echo.
    echo Тестируем книгу: %book_url%
    python -c "import sys; sys.path.insert(0, 'src'); from src.interface import BookDownloader; d = BookDownloader(); info = d.get_book_info('%book_url%'); print('Книга:', info.title); print('Глав:', info.total_chapters)"
) else (
    echo.
    echo Неверный выбор, запускаем быстрые тесты...
    python -c "from tests.test_main import TestProject; t = TestProject(); t.test_api_accessibility(); t.test_url_parsing(); t.test_book_info_retrieval(); print('✅ Быстрые тесты пройдены!')"
)

echo.
echo Нажмите любую клавишу для выхода...
pause >nul
