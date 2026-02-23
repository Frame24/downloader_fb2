# Скачивальщик книг

Простой инструмент для скачивания книг с ranobelib.me в формате FB2.

## Возможности

- Скачивание книг с ranobelib.me
- Конвертация в формат FB2
- Скачивание отдельных глав или диапазонов
- Многопоточное скачивание
- Автоматическое создание структуры папок
- Поддержка 18+ глав через cookies из браузера

## Установка

1. Клонируйте репозиторий
2. Установите зависимости: `pip install -r requirements.txt`

## Использование

### 🎯 Простой способ (рекомендуется)

**Быстрый запуск:**
- `start.bat` - полная проверка + простой интерфейс
- `quick_start.bat` - быстрый запуск интерфейса
- `cmd_interface.bat` - командная строка

**Или через основной батник:**
- `download_book.bat` - выбор режима работы

### 💻 Командная строка

```bash
# Скачать всю книгу
python -m src.interface "https://ranobelib.me/ru/book/197421--naega-geimseog-heukgisaga-doiettda"

# Скачать главы 15-20
python -m src.interface "https://ranobelib.me/ru/book/197421--naega-geimseog-heukgisaga-doiettda" --start 15 --end 20

# Скачать с использованием cookies из Chrome (для 18+ глав)
python -m src.interface "https://ranobelib.me/ru/book/177465--changjiacmul-sogro" --cookies chrome

# Только информация о книге
python -m src.interface "https://ranobelib.me/ru/book/197421--naega-geimseog-heukgisaga-doiettda" --info-only

# С кастомным названием
python -m src.interface "https://ranobelib.me/ru/book/197421--naega-geimseog-heukgisaga-doiettda" --title "Моя книга"
```

### 🧪 Тестирование

```bash
# Запустить тесты
run_tests.bat

# Или напрямую
python -c "from tests.test_main import TestProject; t = TestProject(); t.test_api_accessibility()"
```

### 🔧 Программный API

```python
from src.interface import BookDownloader

# Создаем загрузчик
downloader = BookDownloader(max_workers=5)

# Получаем информацию о книге
info = downloader.get_book_info("https://ranobelib.me/ru/book/197421--naega-geimseog-heukgisaga-doiettda")
print(f"Книга: {info.title}, глав: {info.total_chapters}")

# Скачиваем главы 1-5
result = downloader.full_download("https://ranobelib.me/ru/book/197421--naega-geimseog-heukgisaga-doiettda", start=1, end=5)
print(f"Скачано: {result.successful} глав")
```

## Структура проекта

```
src/
├── client.py          # API клиент для ranobelib.me
├── fb2.py            # Генерация FB2 файлов
├── cli.py            # Командный интерфейс
├── core/
│   ├── downloader.py # Скачивание глав
│   └── converter.py  # Конвертация данных
└── utils/
    └── encoding.py   # Настройка кодировки
```

## Требования

- Python 3.8+
- requests
- click
- browser-cookie3 (для поддержки 18+ глав через cookies)

## Поддержка 18+ глав

Для скачивания 18+ глав необходимо использовать cookies из браузера, где вы уже авторизованы:

```bash
# Использовать cookies из Chrome
python -m src.interface "URL_книги" --cookies chrome

# Использовать cookies из Firefox
python -m src.interface "URL_книги" --cookies firefox

# Использовать cookies из Edge
python -m src.interface "URL_книги" --cookies edge

# Использовать cookies из Opera
python -m src.interface "URL_книги" --cookies opera
```

**Важно:** Перед использованием убедитесь, что вы авторизованы в браузере на сайте ranobelib.me. Браузер должен быть закрыт во время извлечения cookies.

## Лицензия

MIT