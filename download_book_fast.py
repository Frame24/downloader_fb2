#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Быстрая версия скачивания книги с параллельной обработкой глав
"""

import os
import time
import argparse
import json
import concurrent.futures
from ranobe2fb2.client import (
    extract_info,
    fetch_chapters_list,
    fetch_chapter,
    fetch_book_info,
)
from ranobe2fb2.fb2 import build_fb2


def download_single_chapter(args):
    """Скачивает одну главу (для параллельной обработки)"""
    slug, branch_id, volume, chapter_num, book_info, book_dir, html_dir, save_html = (
        args
    )

    max_retries = 3
    base_delay = 5  # Базовая задержка при ошибке 429

    for attempt in range(max_retries):
        try:
            # Получаем данные главы
            data = fetch_chapter(slug, branch_id, volume, chapter_num)

            if not data:
                if attempt < max_retries - 1:
                    time.sleep(2)  # Небольшая задержка перед повторной попыткой
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
            if save_html and html_dir:
                json_filename = f"{chapter_num:03d}_Том{volume_info}_{safe_name}.json"
                json_filepath = os.path.join(html_dir, json_filename)

                with open(json_filepath, "w", encoding="utf-8") as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)

            # Показываем статистику данных
            paragraph_count = 0
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

            return (
                chapter_num,
                True,
                f"Сохранено: {filename} (параграфов: {paragraph_count})",
            )

        except Exception as e:
            error_msg = str(e)

            # Проверяем на ошибку 429 (Too Many Requests)
            if "429" in error_msg or "Too Many Requests" in error_msg:
                if attempt < max_retries - 1:
                    # Увеличиваем задержку с каждой попыткой
                    delay = base_delay * (attempt + 1)
                    print(
                        f"      ⏳ Ошибка 429 (Too Many Requests) для главы {chapter_num}. Ждем {delay} секунд..."
                    )
                    time.sleep(delay)
                else:
                    return chapter_num, False, f"Ошибка 429 после {max_retries} попыток"
            else:
                # Для других ошибок небольшая задержка
                if attempt < max_retries - 1:
                    time.sleep(2)

            if attempt == max_retries - 1:
                return (
                    chapter_num,
                    False,
                    f"Ошибка после {max_retries} попыток: {error_msg}",
                )

    return chapter_num, False, "Неизвестная ошибка"


def retry_failed_chapters(
    failed_chapters, slug, book_info, book_dir, html_dir, save_html, max_workers=3
):
    """Повторно пытается скачать неудачные главы"""

    if not failed_chapters:
        print("✅ Нет неудачных глав для повторной попытки")
        return []

    print(f"\n🔄 Повторная попытка скачивания {len(failed_chapters)} неудачных глав...")
    print(f"⚡ Используем {max_workers} потоков для повторной попытки")

    # Подготавливаем аргументы для повторной попытки
    retry_args = [
        (slug, branch_id, volume, chapter_num, book_info, book_dir, html_dir, save_html)
        for chapter_num, branch_id, volume in failed_chapters
    ]

    successful_retries = 0
    still_failed = []

    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Запускаем повторные попытки
        future_to_chapter = {
            executor.submit(download_single_chapter, args): args[3]
            for args in retry_args
        }

        # Обрабатываем результаты
        for future in concurrent.futures.as_completed(future_to_chapter):
            chapter_num = future_to_chapter[future]
            try:
                chapter_num, success, message = future.result()
                if success:
                    print(
                        f"✅ Повторная попытка успешна - Глава {chapter_num}: {message}"
                    )
                    successful_retries += 1
                else:
                    print(
                        f"❌ Повторная попытка неудачна - Глава {chapter_num}: {message}"
                    )
                    # Находим оригинальные данные главы
                    for failed_chapter in failed_chapters:
                        if failed_chapter[0] == chapter_num:
                            still_failed.append(failed_chapter)
                            break
            except Exception as e:
                print(
                    f"❌ Критическая ошибка при повторной попытке главы {chapter_num}: {e}"
                )
                # Находим оригинальные данные главы
                for failed_chapter in failed_chapters:
                    if failed_chapter[0] == chapter_num:
                        still_failed.append(failed_chapter)
                        break

    print(f"\n📊 Результат повторной попытки:")
    print(f"   ✅ Успешно: {successful_retries}")
    print(f"   ❌ Все еще неудачно: {len(still_failed)}")

    return still_failed


def download_book_fast(
    url: str,
    start_chapter: int = 1,
    end_chapter: int = None,
    save_html: bool = True,
    max_workers: int = 5,
    max_retries: int = 2,
):
    """Скачивает книгу быстро с параллельной обработкой глав"""

    print(
        "🚀 Запускаем быстрое скачивание книги с исправленным парсингом параграфов..."
    )
    print(f"⚡ Параллельных потоков: {max_workers}")

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

        # Подготавливаем аргументы для параллельной обработки
        chapter_args = [
            (
                slug,
                branch_id,
                volume,
                chapter_num,
                book_info,
                book_dir,
                html_dir,
                save_html,
            )
            for chapter_num, branch_id, volume in filtered_chapters
        ]

        # Скачиваем главы параллельно
        successful_downloads = 0
        failed_downloads = 0
        failed_chapters = []

        print(f"\n⚡ Начинаем параллельное скачивание {max_workers} потоков...")

        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Запускаем все задачи
            future_to_chapter = {
                executor.submit(download_single_chapter, args): args[3]
                for args in chapter_args
            }

            # Обрабатываем результаты по мере завершения
            for future in concurrent.futures.as_completed(future_to_chapter):
                chapter_num = future_to_chapter[future]
                try:
                    chapter_num, success, message = future.result()
                    if success:
                        print(f"✅ Глава {chapter_num}: {message}")
                        successful_downloads += 1
                    else:
                        print(f"❌ Глава {chapter_num}: {message}")
                        failed_downloads += 1
                        # Сохраняем информацию о неудачной главе для повторной попытки
                        for args in chapter_args:
                            if args[3] == chapter_num:
                                failed_chapters.append((chapter_num, args[1], args[2]))
                                break
                except Exception as e:
                    print(f"❌ Глава {chapter_num}: Критическая ошибка: {e}")
                    failed_downloads += 1
                    # Сохраняем информацию о неудачной главе для повторной попытки
                    for args in chapter_args:
                        if args[3] == chapter_num:
                            failed_chapters.append((chapter_num, args[1], args[2]))
                            break

                # Показываем прогресс
                total_processed = successful_downloads + failed_downloads
                if total_processed % 10 == 0:
                    print(
                        f"📊 Прогресс: {total_processed}/{len(filtered_chapters)} глав обработано"
                    )

        # Итоговая статистика первого прохода
        print(f"\n📊 Результат первого прохода:")
        print(f"   ✅ Успешно: {successful_downloads}")
        print(f"   ❌ Ошибок: {failed_downloads}")

        # Повторная попытка для неудачных глав
        if failed_chapters:
            print(
                f"\n🔄 Начинаем повторную попытку для {len(failed_chapters)} неудачных глав..."
            )

            # Используем меньше потоков для повторной попытки, чтобы не перегружать API
            retry_workers = min(2, max_workers)
            still_failed = retry_failed_chapters(
                failed_chapters,
                slug,
                book_info,
                book_dir,
                html_dir,
                save_html,
                retry_workers,
            )

            # Финальная статистика
            final_successful = successful_downloads + (
                len(failed_chapters) - len(still_failed)
            )
            final_failed = len(still_failed)

            print(f"\n🎉 Финальный результат:")
            print(f"   ✅ Успешно: {final_successful}")
            print(f"   ❌ Ошибок: {final_failed}")

            if still_failed:
                print(
                    f"\n⚠️  Следующие главы не удалось скачать даже после повторной попытки:"
                )
                for chapter_num, branch_id, volume in still_failed[
                    :10
                ]:  # Показываем первые 10
                    print(f"   Глава {chapter_num} (Том {volume})")
                if len(still_failed) > 10:
                    print(f"   ... и еще {len(still_failed) - 10} глав")
        else:
            final_successful = successful_downloads
            final_failed = 0

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
        description="Быстро скачивает книгу с исправленным парсингом параграфов"
    )
    parser.add_argument("--url", required=True, help="URL книги")
    parser.add_argument("--start", type=int, default=1, help="Номер первой главы")
    parser.add_argument("--end", type=int, help="Номер последней главы")
    parser.add_argument("--no-html", action="store_true", help="Не сохранять HTML")
    parser.add_argument(
        "--workers", type=int, default=5, help="Количество параллельных потоков"
    )
    parser.add_argument(
        "--retries", type=int, default=2, help="Количество повторных попыток"
    )

    args = parser.parse_args()

    # Скачиваем книгу
    book_dir = download_book_fast(
        url=args.url,
        start_chapter=args.start,
        end_chapter=args.end,
        save_html=not args.no_html,
        max_workers=args.workers,
        max_retries=args.retries,
    )

    if book_dir:
        print(f"\n🎯 Книга готова! Папка: {book_dir}")


if __name__ == "__main__":
    main()
