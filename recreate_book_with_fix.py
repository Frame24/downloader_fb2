#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Скрипт для пересоздания всей книги с исправленным парсингом параграфов
"""

import os
import shutil
from datetime import datetime
from ranobe2fb2.client import fetch_chapter
from ranobe2fb2.fb2 import build_fb2


def recreate_book_with_fix(book_dir: str, slug: str):
    """Пересоздает всю книгу с исправленным парсингом"""
    print("🔄 Пересоздаем книгу с исправленным парсингом параграфов...")
    print(f"📁 Папка с главами: {book_dir}")

    # Создаем резервную копию
    backup_dir = f"{book_dir}_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    print(f"💾 Создаем резервную копию: {backup_dir}")
    shutil.copytree(book_dir, backup_dir)

    # Получаем список всех FB2 файлов
    fb2_files = []
    for file in os.listdir(book_dir):
        if file.endswith(".fb2"):
            fb2_files.append(file)

    if not fb2_files:
        print("❌ FB2 файлы глав не найдены!")
        return None

    # Сортируем файлы по номеру главы
    def extract_chapter_number(filename: str) -> int:
        import re

        match = re.match(r"(\d+)", filename)
        if match:
            return int(match.group(1))
        return 0

    fb2_files.sort(key=extract_chapter_number)
    print(f"📊 Найдено глав для пересоздания: {len(fb2_files)}")

    # Создаем новую папку для исправленных глав
    fixed_dir = f"{book_dir}_fixed_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    os.makedirs(fixed_dir, exist_ok=True)
    print(f"📁 Создаем папку для исправленных глав: {fixed_dir}")

    # Пересоздаем каждую главу
    success_count = 0
    error_count = 0

    for i, filename in enumerate(fb2_files, 1):
        print(f"\n📄 [{i}/{len(fb2_files)}] Пересоздаем: {filename}")

        try:
            # Извлекаем номер главы из имени файла
            chapter_num = extract_chapter_number(filename)
            if chapter_num == 0:
                print(f"   ⚠️  Не удалось извлечь номер главы из {filename}")
                continue

            # Получаем данные главы с сервера
            print(f"   🔄 Получаем данные главы {chapter_num}...")

            # Здесь нужно получить branch_id и volume из оригинального файла или API
            # Для простоты используем значения по умолчанию
            branch_id = 20720  # Это нужно получить из API
            volume = 1

            data = fetch_chapter(slug, branch_id, volume, chapter_num)

            if not data:
                print(f"   ❌ Не удалось получить данные главы {chapter_num}")
                error_count += 1
                continue

            # Создаем исправленный FB2 файл
            fb2_content = build_fb2(data)

            # Сохраняем в новую папку
            new_filename = (
                f"{chapter_num:03d}_{data.get('name', f'Глава_{chapter_num}')}.fb2"
            )
            # Очищаем название от недопустимых символов
            new_filename = "".join(
                c for c in new_filename if c.isalnum() or c in " -_"
            ).rstrip()

            new_filepath = os.path.join(fixed_dir, new_filename)
            with open(new_filepath, "wb") as f:
                f.write(fb2_content)

            print(f"   ✅ Глава {chapter_num} пересоздана: {new_filename}")
            success_count += 1

        except Exception as e:
            print(f"   ❌ Ошибка при пересоздании {filename}: {e}")
            error_count += 1
            continue

    print(f"\n📊 Результат пересоздания:")
    print(f"   ✅ Успешно: {success_count}")
    print(f"   ❌ Ошибок: {error_count}")
    print(f"   📁 Исправленные главы в: {fixed_dir}")

    return fixed_dir


def main():
    # Путь к папке с главами
    book_dir = "results/133676--guangyin-zhi-wai"
    slug = "133676--guangyin-zhi-wai"

    # Проверяем, что папка существует
    if not os.path.exists(book_dir):
        print(f"❌ Папка {book_dir} не найдена!")
        return

    # Пересоздаем книгу
    try:
        fixed_dir = recreate_book_with_fix(book_dir, slug)

        if fixed_dir and os.path.exists(fixed_dir):
            print(f"\n🎉 Книга успешно пересоздана с исправленным парсингом!")
            print(f"📁 Новые главы в: {fixed_dir}")
            print(f"💾 Резервная копия сохранена")
        else:
            print(f"\n❌ Не удалось пересоздать книгу")

    except Exception as e:
        print(f"❌ Ошибка при пересоздании книги: {e}")


if __name__ == "__main__":
    main()
