#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import time
import re
from ranobe2fb2.client import (
    extract_info,
    fetch_chapters_list,
    fetch_chapter,
    fetch_book_info,
)
from ranobe2fb2.fb2 import build_fb2


def download_missing_chapters(url: str, book_dir: str, max_retries: int = 3):
    """
    Скачивает недостающие главы для книги.
    """
    print(f"Проверяем недостающие главы для: {url}")
    print(f"Папка книги: {book_dir}")
    print("-" * 50)

    try:
        # Извлекаем информацию из URL
        info = extract_info(url)
        slug = info[0]
        print(f"Slug книги: {slug}")

        # Получаем информацию о книге
        print("Получаем информацию о книге...")
        book_info = fetch_book_info(slug, max_retries)
        if book_info:
            print(f"Название книги: {book_info.get('name', 'Неизвестно')}")
            if book_info.get("description"):
                print(f"Описание: {book_info.get('description', '')[:100]}...")
        else:
            print("⚠️ Не удалось получить информацию о книге")
            book_info = {}

        # Получаем список всех доступных глав
        print("\nПолучаем список глав...")
        chapters = fetch_chapters_list(slug, max_retries)
        print(f"Всего глав доступно: {len(chapters)}")

        if not chapters:
            print("❌ Не удалось получить список глав")
            return

        # Получаем список уже скачанных файлов
        existing_files = []
        if os.path.exists(book_dir):
            existing_files = [f for f in os.listdir(book_dir) if f.endswith(".fb2")]
        print(f"Уже скачано файлов: {len(existing_files)}")

        # Определяем какие главы уже есть
        existing_chapters = set()
        for filename in existing_files:
            # Извлекаем номер главы из имени файла
            match = re.search(r"^(\d+)", filename)
            if match:
                existing_chapters.add(int(match.group(1)))

        print(f"Существующие номера глав: {sorted(existing_chapters)}")

        # Определяем недостающие главы
        available_chapters = set(num for num, _, _ in chapters)
        missing_chapters = available_chapters - existing_chapters

        if not missing_chapters:
            print("✅ Все главы уже скачаны!")
            return

        print(f"Недостающие главы: {sorted(missing_chapters)}")
        print(f"Всего недостает: {len(missing_chapters)}")

        # Скачиваем недостающие главы
        for num in sorted(missing_chapters):
            # Находим данные главы
            chapter_data = None
            for ch_num, branch_id, volume in chapters:
                if ch_num == num:
                    chapter_data = (ch_num, branch_id, volume)
                    break

            if not chapter_data:
                print(f"⚠️ Не найдены данные для главы {num}")
                continue

            chapter_num, branch_id, volume = chapter_data
            print(f"\nСкачиваем главу {chapter_num}...")
            print(f"  → Том: {volume}")

            # Пытаемся скачать с повторными попытками
            success = False
            for attempt in range(max_retries):
                try:
                    print(f"  → Попытка {attempt + 1}/{max_retries}...")

                    # Получаем данные главы
                    data = fetch_chapter(
                        slug,
                        branch_id,
                        volume=volume,
                        number=chapter_num,
                        max_retries=1,
                    )

                    if not data:
                        print(f"    → Данные главы не получены")
                        if attempt < max_retries - 1:
                            print(f"    → Ждем 3 секунды перед повторной попыткой...")
                            time.sleep(3)
                        continue

                    # Формируем имя файла
                    chapter_name = data.get("name", f"Глава_{num}")
                    # Очищаем название от недопустимых символов
                    safe_name = "".join(
                        c for c in chapter_name if c.isalnum() or c in " -_"
                    ).rstrip()

                    # Добавляем информацию о томе в имя файла
                    volume_info = data.get("volume", 1)
                    if (
                        volume_info
                        and str(volume_info).isdigit()
                        and int(volume_info) > 1
                    ):
                        filename = f"{num:03d}_Том{volume_info}_{safe_name}.fb2"
                    else:
                        filename = f"{num:03d}_{safe_name}.fb2"

                    filepath = os.path.join(book_dir, filename)

                    # Генерируем FB2 с информацией о книге
                    fb2_content = build_fb2(data, book_info)

                    # Сохраняем файл
                    with open(filepath, "wb") as f:
                        f.write(fb2_content)

                    print(f"    → ✅ Сохранено: {filename}")
                    success = True
                    break

                except Exception as e:
                    print(f"    → Ошибка: {e}")
                    if attempt < max_retries - 1:
                        print(f"    → Ждем 3 секунды перед повторной попыткой...")
                        time.sleep(3)

            if not success:
                print(
                    f"  → ❌ Не удалось скачать главу {chapter_num} после {max_retries} попыток"
                )

        print("\n" + "=" * 50)
        print(f"Скачивание недостающих глав завершено!")

    except Exception as e:
        print(f"❌ Ошибка: {e}")


if __name__ == "__main__":
    # URL книги
    url = "https://ranobelib.me/ru/book/195040--advent-of-the-three-calamities?section=chapters&ui=6052250"

    # Папка с книгой
    book_dir = "results/195040--advent-of-the-three-calamities"

    # Скачиваем недостающие главы
    download_missing_chapters(url, book_dir)
