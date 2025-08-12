#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Скрипт для скачивания пропущенных глав
"""

import os
import time
from ranobe2fb2.client import fetch_chapter
from ranobe2fb2.fb2 import build_fb2


def download_missing_chapters():
    """Скачивает пропущенные главы"""

    print("📥 Скачиваем пропущенные главы...")

    # Параметры книги
    slug = "133676--guangyin-zhi-wai"
    branch_id = 20720

    # Пропущенные главы
    missing_chapters = [
        (172, 3),  # Глава 172, Том 3
        (173, 3),  # Глава 173, Том 3
        (0, 1),  # Глава 0, Том 1
        (440, 5),  # Глава 440, Том 5
        (441, 5),  # Глава 441, Том 5
    ]

    # Создаем папку для результатов
    book_dir = f"results_chapters/{slug}"
    if not os.path.exists(book_dir):
        os.makedirs(book_dir)

    # Создаем папку для исходных данных
    html_dir = "results_data"
    if not os.path.exists(html_dir):
        os.makedirs(html_dir)

    successful = 0
    failed = 0

    for chapter_num, volume in missing_chapters:
        print(f"\n📄 Скачиваем главу {chapter_num} (Том {volume})...")

        try:
            # Получаем данные главы
            data = fetch_chapter(slug, branch_id, volume, chapter_num)

            if not data:
                print(f"   ❌ Не удалось получить данные главы {chapter_num}")
                failed += 1
                continue

            # Создаем FB2
            fb2_content = build_fb2(data, chapter_num, volume)

            if not fb2_content:
                print(f"   ❌ Не удалось создать FB2 для главы {chapter_num}")
                failed += 1
                continue

            # Сохраняем FB2
            safe_name = f"Глава_{chapter_num:03d}"
            filename = f"{chapter_num:03d}_Том{volume}_{safe_name}.fb2"
            filepath = os.path.join(book_dir, filename)

            with open(filepath, "w", encoding="utf-8") as f:
                f.write(fb2_content)

            # Сохраняем исходные данные в JSON для отладки
            json_filename = f"{chapter_num:03d}_Том{volume}_{safe_name}.json"
            json_filepath = os.path.join(html_dir, json_filename)

            import json

            with open(json_filepath, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

            # Показываем статистику
            if "content" in data and isinstance(data["content"], dict):
                content = data["content"]
                if "content" in content:
                    paragraph_count = len(
                        [
                            node
                            for node in content["content"]
                            if node.get("type") == "paragraph"
                        ]
                    )
                    print(
                        f"   ✅ Сохранено: {filename} (параграфов: {paragraph_count})"
                    )
                else:
                    print(f"   ✅ Сохранено: {filename}")
            else:
                print(f"   ✅ Сохранено: {filename}")

            successful += 1

            # Небольшая задержка между запросами
            time.sleep(1)

        except Exception as e:
            print(f"   ❌ Ошибка при скачивании главы {chapter_num}: {e}")
            failed += 1
            continue

    print(f"\n📊 Итоговая статистика:")
    print(f"   ✅ Успешно скачано: {successful} глав")
    print(f"   ❌ Ошибок: {failed} глав")

    if successful > 0:
        print(f"\n🎉 Пропущенные главы успешно скачаны!")
        print(f"📁 Файлы сохранены в: {book_dir}")
        print(f"📁 Исходные данные в: {html_dir}")

    return successful, failed


if __name__ == "__main__":
    download_missing_chapters()
