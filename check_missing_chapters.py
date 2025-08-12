#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Скрипт для проверки отсутствующих глав
"""

import os
import re
from ranobe2fb2.client import fetch_chapters_list


def check_missing_chapters():
    """Проверяет, какие главы отсутствуют"""

    slug = "133676--guangyin-zhi-wai"
    book_dir = f"results_chapters/{slug}"

    if not os.path.exists(book_dir):
        print(f"❌ Папка {book_dir} не найдена!")
        return

    # Получаем список всех глав с сервера
    print("📋 Получаем список всех глав с сервера...")
    all_chapters = fetch_chapters_list(slug)
    if not all_chapters:
        print("❌ Не удалось получить список глав!")
        return

    print(f"📊 Всего глав на сервере: {len(all_chapters)}")

    # Получаем список скачанных глав
    downloaded_files = []
    for file in os.listdir(book_dir):
        if file.endswith(".fb2"):
            # Извлекаем номер главы из имени файла
            match = re.match(r"(\d+)", file)
            if match:
                chapter_num = int(match.group(1))
                downloaded_files.append(chapter_num)

    downloaded_files = sorted(set(downloaded_files))  # Убираем дубликаты
    print(f"📊 Скачано глав: {len(downloaded_files)}")

    # Находим отсутствующие главы
    all_chapter_numbers = [num for num, _, _ in all_chapters]
    missing_chapters = []

    for chapter_num, branch_id, volume in all_chapters:
        if chapter_num not in downloaded_files:
            missing_chapters.append((chapter_num, branch_id, volume))

    print(f"📊 Отсутствующих глав: {len(missing_chapters)}")

    if missing_chapters:
        print("\n📝 Отсутствующие главы:")
        for chapter_num, branch_id, volume in missing_chapters[
            :20
        ]:  # Показываем первые 20
            print(f"   Глава {chapter_num} (Том {volume})")

        if len(missing_chapters) > 20:
            print(f"   ... и еще {len(missing_chapters) - 20} глав")

        # Группируем по томам для удобства
        print("\n📚 Группировка по томам:")
        volumes = {}
        for chapter_num, branch_id, volume in missing_chapters:
            if volume not in volumes:
                volumes[volume] = []
            volumes[volume].append(chapter_num)

        for volume in sorted(volumes.keys()):
            chapters = sorted(volumes[volume])
            print(
                f"   Том {volume}: {len(chapters)} глав (с {chapters[0]} по {chapters[-1]})"
            )

    return missing_chapters


if __name__ == "__main__":
    missing = check_missing_chapters()
