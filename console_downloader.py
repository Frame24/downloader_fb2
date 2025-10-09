#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Простой консольный интерфейс для скачивания книг
"""

import sys
from pathlib import Path
from datetime import datetime

# Настройка кодировки для Windows консоли
try:
    from src.utils.encoding import setup_console_encoding
    setup_console_encoding()
except ImportError:
    pass

# Добавляем src в путь
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

from src.core.downloader import ChapterDownloader, DownloadConfig
from src.core.converter import DataConverter
from src.client import extract_info, fetch_book_info


def main():
    """Основная функция"""
    print("СКАЧИВАЛЬЩИК КНИГ")
    print("=" * 50)
    print("Вставьте ссылку на книгу или главу:")
    print("Пример: https://ranobelib.me/ru/book/197421--naega-geimseog-heukgisaga-doiettda")
    print("=" * 50)
    
    url = input("\nВведите URL: ").strip()
    if not url:
        print("❌ URL не может быть пустым")
        return
    
    # Извлекаем slug
    try:
        slug, _, _, _ = extract_info(url)
    except ValueError as e:
        print(f"❌ Ошибка разбора URL: {e}")
        return
    
    # Получаем информацию о книге
    try:
        book_info = fetch_book_info(slug)
        book_title = book_info.get("display_name", f"Книга_{slug}")
        chapters_count = book_info.get("chapters_count", 0)
        print(f"Название книги: {book_title}")
        print(f"Количество глав: {chapters_count}")
    except Exception as e:
        print(f"❌ Не удалось получить информацию о книге: {e}")
        return
    
    # Создаем папку для сохранения
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    output_dir = f"output/{book_title}_{timestamp}"
    
    print(f"\nПапка для сохранения: {output_dir}")
    print("\nНачинаем скачивание...")
    
    # Настройки скачивания
    config = DownloadConfig(max_workers=5)
    downloader = ChapterDownloader(config)
    
    # Скачиваем всю книгу
    successful, failed = downloader.download_full_book(slug, output_dir)
    
    print(f"\nРезультат скачивания:")
    print(f"Успешно скачано: {successful} глав")
    print(f"Ошибок: {failed} глав")
    
    if successful > 0:
        # Конвертируем в FB2
        print("\nКонвертируем в FB2...")
        converter = DataConverter()
        conv_successful, conv_failed = converter.convert_raw_to_fb2(
            f"{output_dir}/raw_data", f"{output_dir}/fb2_chapters"
        )
        print(f"Конвертировано в FB2: {conv_successful} глав")
        
        # Объединяем в книгу
        print("\nОбъединяем главы в книгу...")
        try:
            converter.convert_fb2_to_merged_book(
                f"{output_dir}/fb2_chapters", output_dir, book_title
            )
            print(f"✅ Книга создана: {output_dir}/{book_title}.fb2")
        except Exception as e:
            print(f"❌ Ошибка при создании книги: {e}")
    
    print(f"\nВсе файлы сохранены в: {output_dir}")


if __name__ == "__main__":
    main()