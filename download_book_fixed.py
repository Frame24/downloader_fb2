#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Улучшенный скрипт для скачивания книги с исправленным парсингом параграфов
"""

import os
import time
import argparse
from ranobe2fb2.client import (
    extract_info,
    fetch_chapters_list,
    fetch_chapter,
    fetch_book_info,
)
from ranobe2fb2.fb2 import build_fb2
import json


def download_book_fixed(
    url: str,
    start_chapter: int = 1,
    end_chapter: int = None,
    save_html: bool = True,
    max_retries: int = 3,
):
    """Скачивает книгу с исправленным парсингом параграфов"""

    print("🚀 Запускаем скачивание книги с исправленным парсингом параграфов...")

    try:
        # Извлекаем информацию из URL
        slug, mode, bid, chap = extract_info(url)
        print(f"📚 Слаг книги: {slug}")
        print(f"🎯 Режим: {mode}")

        if mode == "single":
            print("❌ Одиночные главы не поддерживаются в этом режиме")
            return

        # Получаем информацию о книге
        print("\n📖 Получаем информацию о книге...")
        book_info = fetch_book_info(slug)
        if book_info:
            print(f"✅ Название: {book_info.get('display_name', 'Неизвестно')}")
            print(
                f"📝 Описание: {book_info.get('description', 'Нет описания')[:100]}..."
            )
        else:
            book_info = {"display_name": slug, "name": slug}

        # Получаем список всех глав
        print("\n📋 Получаем список глав...")
        all_chapters = fetch_chapters_list(slug)
        if not all_chapters:
            print("❌ Не удалось получить список глав!")
            return

        print(f"📊 Всего глав найдено: {len(all_chapters)}")

        # Фильтруем главы по диапазону
        if end_chapter is None:
            end_chapter = len(all_chapters)

        filtered_chapters = [
            (num, branch_id, volume)
            for num, branch_id, volume in all_chapters
            if start_chapter <= num <= end_chapter
        ]

        print(f"🎯 Скачиваем главы с {start_chapter} по {end_chapter}")
        print(f"📊 Количество глав для скачивания: {len(filtered_chapters)}")

        # Создаем папку для книги
        book_dir = f"results_chapters/{slug}"
        os.makedirs(book_dir, exist_ok=True)

        # Создаем папку для HTML если нужно
        html_dir = None
        if save_html:
                    html_dir = f"results_data/{slug}"
                    os.makedirs(html_dir, exist_ok=True)
            print(f"📁 HTML будет сохраняться в: {html_dir}")

        print(f"📁 Главы будут сохраняться в: {book_dir}")

        # Скачиваем главы
        successful_downloads = 0
        failed_downloads = 0

        for i, (chapter_num, branch_id, volume) in enumerate(filtered_chapters, 1):
            print(
                f"\n📥 Скачиваем главу {chapter_num} ({i}/{len(filtered_chapters)})..."
            )
            print(f"   📚 Том: {volume}")

            # Пытаемся скачать с повторными попытками
            success = False
            for attempt in range(max_retries):
                try:
                    print(f"   🔄 Попытка {attempt + 1}/{max_retries}...")

                    # Получаем данные главы
                    data = fetch_chapter(
                        slug, branch_id, volume=volume, number=chapter_num
                    )

                    if not data:
                        print(f"      ❌ Данные главы не получены")
                        if attempt < max_retries - 1:
                            print(
                                f"      ⏳ Ждем 3 секунды перед повторной попыткой..."
                            )
                            time.sleep(3)
                        continue

                    # Формируем имя файла
                    chapter_name = data.get("name", f"Глава_{chapter_num}")
                    safe_name = "".join(
                        c for c in chapter_name if c.isalnum() or c in " -_"
                    ).rstrip()

                    # Добавляем информацию о томе в имя файла
                    volume_info = data.get("volume", volume)
                    filename = f"{chapter_num:03d}_Том{volume_info}_{safe_name}.fb2"
                    filepath = os.path.join(book_dir, filename)

                    # Создаем FB2 файл с исправленным парсингом
                    fb2_content = build_fb2(data, book_info, volume_info, chapter_num)

                    # Сохраняем FB2 файл
                    with open(filepath, "wb") as f:
                        f.write(fb2_content)

                    # Сохраняем исходные данные в JSON для отладки
                    if save_html:
                        json_filename = (
                            f"{chapter_num:03d}_Том{volume_info}_{safe_name}.json"
                        )
                        json_filepath = os.path.join(html_dir, json_filename)

                        with open(json_filepath, "w", encoding="utf-8") as f:
                            json.dump(data, f, ensure_ascii=False, indent=2)

                        # Показываем статистику данных
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
                                print(f"      📊 JSON параграфов: {paragraph_count}")

                    print(f"      ✅ Сохранено: {filename}")
                    successful_downloads += 1
                    success = True
                    break

                except Exception as e:
                    print(f"      ❌ Ошибка при попытке {attempt + 1}: {e}")
                    if attempt < max_retries - 1:
                        print(f"      ⏳ Ждем 1 секунду перед повторной попыткой...")
                        time.sleep(1)

            if not success:
                print(
                    f"   ❌ Не удалось скачать главу {chapter_num} после {max_retries} попыток"
                )
                failed_downloads += 1

            # Минимальная задержка между главами (убрали лишние 2 секунды)
            time.sleep(0.5)

        # Итоговая статистика
        print(f"\n🎉 Скачивание завершено!")
        print(f"📊 Результат:")
        print(f"   ✅ Успешно: {successful_downloads}")
        print(f"   ❌ Ошибок: {failed_downloads}")
        print(f"📁 Файлы сохранены в: {book_dir}")

        if save_html:
            print(f"📁 HTML файлы в: {html_dir}")

        return book_dir

    except Exception as e:
        print(f"❌ Критическая ошибка: {e}")
        import traceback

        traceback.print_exc()
        return None


def main():
    parser = argparse.ArgumentParser(
        description="Скачивает книгу с исправленным парсингом параграфов"
    )
    parser.add_argument("--url", required=True, help="URL книги")
    parser.add_argument("--start", type=int, default=1, help="Номер первой главы")
    parser.add_argument("--end", type=int, help="Номер последней главы")
    parser.add_argument("--no-html", action="store_true", help="Не сохранять HTML")
    parser.add_argument(
        "--retries", type=int, default=3, help="Количество повторных попыток"
    )

    args = parser.parse_args()

    # Скачиваем книгу
    book_dir = download_book_fixed(
        url=args.url,
        start_chapter=args.start,
        end_chapter=args.end,
        save_html=not args.no_html,
        max_retries=args.retries,
    )

    if book_dir:
        print(f"\n🎯 Книга готова! Папка: {book_dir}")


if __name__ == "__main__":
    main()
