# Скачивальщик книг

Простой инструмент для скачивания книг с ranobelib.me в формате FB2.

## Возможности

- Скачивание книг с ranobelib.me
- Конвертация в формат FB2
- Скачивание отдельных глав или диапазонов
- Многопоточное скачивание
- Автоматическое создание структуры папок

## Установка

1. Клонируйте репозиторий
2. Установите зависимости: `pip install -r requirements.txt`

## Использование

### Простой способ (рекомендуется)

Запустите `download_book.bat` и следуйте инструкциям.

### Командная строка

```bash
# Скачать всю книгу
python console_downloader.py

# Скачать определенные главы
python main.py "https://ranobelib.me/ru/book/197421--naega-geimseog-heukgisaga-doiettda" --start 1 --end 10 --output output/
```

### Тестирование

```bash
# Запустить тесты
python -m pytest tests/test_main.py -v

# Или через батник
run_tests.bat
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

## Лицензия

MIT