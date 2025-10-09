#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Простой пользовательский интерфейс для скачивания книг
"""

import sys
from pathlib import Path

# Настройка кодировки
try:
    from src.utils.encoding import setup_console_encoding
    setup_console_encoding()
except ImportError:
    pass

# Добавляем src в путь
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

from src.interface import BookDownloader


def show_menu():
    """Показывает главное меню"""
    print("\n" + "="*50)
    print("           СКАЧИВАЛЬЩИК КНИГ")
    print("="*50)
    print("1. Скачать всю книгу")
    print("2. Скачать определенные главы")
    print("3. Информация о книге")
    print("4. Настройки")
    print("0. Выход")
    print("="*50)


def download_full_book():
    """Скачивает всю книгу"""
    url = input("\n📖 Введите URL книги: ").strip()
    if not url:
        print("❌ URL не может быть пустым")
        return
    
    try:
        downloader = BookDownloader()
        print("🚀 Скачиваем всю книгу...")
        result = downloader.full_download(url)
        
        print(f"\n✅ Готово!")
        print(f"📚 Книга: {result.book_title}")
        print(f"📖 Скачано глав: {result.successful}")
        print(f"📁 Папка: {result.output_dir}")
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")


def download_chapters():
    """Скачивает определенные главы"""
    url = input("\n📖 Введите URL книги: ").strip()
    if not url:
        print("❌ URL не может быть пустым")
        return
    
    try:
        start = int(input("📖 Начальная глава: "))
        end = int(input("📖 Конечная глава: "))
        
        downloader = BookDownloader()
        print(f"🚀 Скачиваем главы {start}-{end}...")
        result = downloader.full_download(url, start, end)
        
        print(f"\n✅ Готово!")
        print(f"📚 Книга: {result.book_title}")
        print(f"📖 Скачано глав: {result.successful}")
        print(f"📁 Папка: {result.output_dir}")
        
    except ValueError:
        print("❌ Введите корректные номера глав")
    except Exception as e:
        print(f"❌ Ошибка: {e}")


def show_book_info():
    """Показывает информацию о книге"""
    url = input("\n📖 Введите URL книги: ").strip()
    if not url:
        print("❌ URL не может быть пустым")
        return
    
    try:
        downloader = BookDownloader()
        book_info = downloader.get_book_info(url)
        
        print(f"\n📚 Информация о книге:")
        print(f"📖 Название: {book_info.title}")
        print(f"🔗 Slug: {book_info.slug}")
        print(f"📋 Всего глав: {book_info.total_chapters}")
        print(f"📄 Доступные главы: {len(book_info.available_chapters)}")
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")


def show_settings():
    """Показывает настройки"""
    print("\n⚙️ Настройки:")
    print("📁 Папка сохранения: output/")
    print("🔄 Потоков скачивания: 5")
    print("📚 Формат: FB2")
    print("\n💡 Для изменения настроек используйте командную строку")


def main():
    """Основная функция"""
    while True:
        show_menu()
        choice = input("\nВыберите действие (0-4): ").strip()
        
        if choice == "1":
            download_full_book()
        elif choice == "2":
            download_chapters()
        elif choice == "3":
            show_book_info()
        elif choice == "4":
            show_settings()
        elif choice == "0":
            print("👋 До свидания!")
            break
        else:
            print("❌ Неверный выбор, попробуйте снова")
        
        input("\nНажмите Enter для продолжения...")


if __name__ == "__main__":
    main()
