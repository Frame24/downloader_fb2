#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Скрипт для проверки целостности книги и выявления пропущенных глав
"""

import os
import re
from ranobe2fb2.client import fetch_chapters_list


def check_book_integrity(book_dir: str):
    """Проверяет целостность книги и выявляет пропущенные главы"""

    print("🔍 Проверяем целостность книги...")

    # Получаем список всех глав с сервера
    print("📋 Получаем список всех глав с сервера...")
    slug = "133676--guangyin-zhi-wai"
    all_chapters = fetch_chapters_list(slug)

    if not all_chapters:
        print("❌ Не удалось получить список глав с сервера!")
        return

    print(f"📊 Всего глав на сервере: {len(all_chapters)}")

    # Получаем список скачанных глав
    downloaded_files = []
    for file in os.listdir(book_dir):
        if file.endswith(".fb2"):
            # Извлекаем номер главы и том из имени файла
            match = re.match(r"(\d+)_Том(\d+)_(.+)\.fb2", file)
            if match:
                chapter_num = int(match.group(1))
                volume = int(match.group(2))
                downloaded_files.append((chapter_num, volume, file))

    if not downloaded_files:
        print("❌ FB2 файлы глав не найдены!")
        return

    print(f"📊 Скачано глав: {len(downloaded_files)}")

    # Сортируем по номеру главы
    downloaded_files.sort(key=lambda x: x[0])

    # Создаем словарь для группировки по томам
    volumes = {}
    for chapter_num, volume, filename in downloaded_files:
        if volume not in volumes:
            volumes[volume] = []
        volumes[volume].append((chapter_num, filename))

    # Проверяем целостность каждого тома
    print("\n📚 Проверка целостности по томам:")

    total_missing = 0
    all_missing_chapters = []

    for volume in sorted(volumes.keys()):
        chapters = sorted(volumes[volume])
        print(f"\n📖 Том {volume}:")

        # Находим диапазон глав в этом томе
        if chapters:
            min_chapter = chapters[0][0]
            max_chapter = chapters[-1][0]
            print(f"   📊 Диапазон: с главы {min_chapter} по главу {max_chapter}")
            print(f"   📊 Найдено глав: {len(chapters)}")

            # Проверяем пропуски
            # Создаем множество всех глав в этом томе
            volume_chapters = set()
            for chapter_num, volume_num in chapters:
                if volume_num == volume:
                    volume_chapters.add(chapter_num)

            # Находим диапазон глав для этого тома
            if volume_chapters:
                min_vol_chapter = min(volume_chapters)
                max_vol_chapter = max(volume_chapters)
                expected_chapters = set(range(min_vol_chapter, max_vol_chapter + 1))
                missing_in_volume = expected_chapters - volume_chapters
            else:
                missing_in_volume = set()

            if missing_in_volume:
                missing_list = sorted(missing_in_volume)
                print(f"   ❌ Пропущенные главы: {missing_list}")
                total_missing += len(missing_list)
                all_missing_chapters.extend([(volume, ch) for ch in missing_list])
            else:
                print(f"   ✅ Все главы в томе присутствуют")

            # Показываем первые и последние главы для проверки
            print(f"   📝 Первые главы: {[f'{ch[0]}' for ch in chapters[:5]]}")
            if len(chapters) > 5:
                print(f"   📝 Последние главы: {[f'{ch[0]}' for ch in chapters[-5:]]}")

    # Проверяем общую целостность
    print(f"\n🔍 Общая проверка целостности:")

    # Получаем все номера глав с сервера для этого slug
    server_chapters = []
    for chapter_num, branch_id, volume in all_chapters:
        server_chapters.append(chapter_num)

    server_chapters = sorted(set(server_chapters))

    # Находим все скачанные номера глав
    downloaded_chapters = sorted(
        set(chapter_num for chapter_num, _, _ in downloaded_files)
    )

    # Проверяем, есть ли главы, которые мы не скачали
    not_downloaded = set(server_chapters) - set(downloaded_chapters)

    if not_downloaded:
        print(f"   ⚠️  Не скачаны главы: {sorted(not_downloaded)[:20]}")
        if len(not_downloaded) > 20:
            print(f"      ... и еще {len(not_downloaded) - 20} глав")

    # Проверяем, есть ли лишние главы
    extra_chapters = set(downloaded_chapters) - set(server_chapters)
    if extra_chapters:
        print(f"   ⚠️  Лишние главы (не на сервере): {sorted(extra_chapters)}")

    # Итоговая статистика
    print(f"\n📊 Итоговая статистика:")
    print(f"   📚 Всего глав на сервере: {len(server_chapters)}")
    print(f"   📥 Скачано глав: {len(downloaded_chapters)}")
    print(f"   ❌ Пропущено глав: {total_missing}")
    print(f"   ⚠️  Не скачано глав: {len(not_downloaded)}")

    if total_missing > 0:
        print(f"\n🔧 Рекомендации:")
        print(f"   📥 Скачайте пропущенные главы: {total_missing} глав")

        # Группируем пропущенные главы по томам для удобства скачивания
        missing_by_volume = {}
        for volume, chapter in all_missing_chapters:
            if volume not in missing_by_volume:
                missing_by_volume[volume] = []
            missing_by_volume[volume].append(chapter)

        print(f"\n📋 Пропущенные главы по томам:")
        for volume in sorted(missing_by_volume.keys()):
            chapters = sorted(missing_by_volume[volume])
            print(f"   Том {volume}: {chapters}")

    return total_missing, all_missing_chapters


def main():
    # Путь к папке с главами
    book_dir = "results_chapters/133676--guangyin-zhi-wai"

    # Проверяем, что папка существует
    if not os.path.exists(book_dir):
        print(f"❌ Папка {book_dir} не найдена!")
        return

    # Проверяем целостность
    try:
        missing_count, missing_chapters = check_book_integrity(book_dir)

        if missing_count == 0:
            print(f"\n🎉 Книга полностью целостна! Все главы на месте.")
        else:
            print(f"\n⚠️  Обнаружены пропуски в книге: {missing_count} глав")

    except Exception as e:
        print(f"❌ Ошибка при проверке целостности: {e}")


if __name__ == "__main__":
    main()
