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
from src.utils.auth import (
    BROWSER_TOKEN_JS,
    clear_auth_token,
    load_auth_token,
    save_auth_token,
    token_status_label,
)


def show_menu():
    """Показывает главное меню"""
    print("\n" + "=" * 50)
    print("           СКАЧИВАЛЬЩИК КНИГ")
    print("=" * 50)
    print("1. Скачать всю книгу")
    print("2. Скачать определенные главы")
    print("3. Информация о книге")
    print("4. Вставить токен авторизации")
    print("5. Настройки")
    print("0. Выход")
    print("=" * 50)
    print(f"🔐 Токен: {token_status_label()}")
    print("=" * 50)


def download_full_book():
    """Скачивает всю книгу"""
    url = input("\n📖 Введите URL книги: ").strip()
    if not url:
        print("❌ URL не может быть пустым")
        return
    
    try:
        auth_token = load_auth_token()
        downloader = BookDownloader(auth_token=auth_token)
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
        end = int(input("📖 Конечная глава (включительно): "))
        
        if start > end:
            print("❌ Начальная глава не может быть больше конечной")
            return
        
        auth_token = load_auth_token()
        downloader = BookDownloader(auth_token=auth_token)
        print(f"🚀 Скачиваем главы {start}-{end} (включительно)...")
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
        auth_token = load_auth_token()
        downloader = BookDownloader(auth_token=auth_token)
        book_info = downloader.get_book_info(url)
        
        print(f"\n📚 Информация о книге:")
        print(f"📖 Название: {book_info.title}")
        print(f"🔗 Slug: {book_info.slug}")
        print(f"📋 Всего глав: {book_info.total_chapters}")
        print(f"📄 Доступные главы: {len(book_info.available_chapters)}")
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")


def insert_auth_token():
    """Показывает JS для получения токена и сохраняет вставленный Bearer."""
    print("\n" + "=" * 50)
    print("        ВСТАВКА ТОКЕНА АВТОРИЗАЦИИ")
    print("=" * 50)
    print(f"Текущий токен: {token_status_label()}")
    print()
    print("Как получить токен:")
    print("  1. Откройте страницу тайтла на ranobelib.me (будучи авторизованы)")
    print("  2. Нажмите F12 → вкладка Console (Консоль)")
    print("  3. Вставьте код ниже и нажмите Enter")
    print("  4. Токен скопируется в буфер — вставьте его сюда")
    print()
    print("-" * 50)
    print("JavaScript (скопируйте целиком):")
    print("-" * 50)
    print(BROWSER_TOKEN_JS)
    print("-" * 50)
    print()
    print("Вставьте Bearer-токен (или оставьте пустым, чтобы отменить):")
    new_token = input("> ").strip()
    if not new_token:
        print("Отменено, токен не изменён.")
        return

    save_auth_token(new_token)
    if load_auth_token():
        print(f"✅ Токен сохранён. Статус: {token_status_label()}")
    else:
        print("❌ Не удалось распознать JWT в вставленном тексте. Попробуйте снова.")


def show_settings():
    """Показывает настройки и управление токеном"""
    print("\n⚙️ Настройки:")
    print("📁 Папка сохранения: output/")
    print("🔄 Потоков скачивания: 5")
    print("📚 Формат: FB2")
    print(f"🔐 Токен авторизации: {token_status_label()}")
    print()
    print("1. Вставить / обновить токен")
    print("2. Удалить токен")
    print("0. Назад")

    choice = input("\nВыберите действие (0-2): ").strip()
    if choice == "1":
        insert_auth_token()
    elif choice == "2":
        if load_auth_token():
            clear_auth_token()
            print("✅ Токен удалён.")
        else:
            print("Токен и так не задан.")
    elif choice == "0":
        return
    else:
        print("❌ Неверный выбор")


def main():
    """Основная функция"""
    while True:
        show_menu()
        choice = input("\nВыберите действие (0-5): ").strip()
        
        if choice == "1":
            download_full_book()
        elif choice == "2":
            download_chapters()
        elif choice == "3":
            show_book_info()
        elif choice == "4":
            insert_auth_token()
        elif choice == "5":
            show_settings()
        elif choice == "0":
            print("👋 До свидания!")
            break
        else:
            print("❌ Неверный выбор, попробуйте снова")
        
        input("\nНажмите Enter для продолжения...")


if __name__ == "__main__":
    main()
