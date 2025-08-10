#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import time
import argparse
from ranobe2fb2.client import (
    extract_info,
    fetch_chapters_list,
    fetch_chapter,
    fetch_book_info,
)
from ranobe2fb2.fb2 import build_fb2


def get_user_input():
    """
    Получает от пользователя URL книги и параметры загрузки.
    """
    print("🚀 Загрузчик ранобэ в FB2")
    print("=" * 50)

    # Получаем URL
    while True:
        url = input("Введите URL книги с ranobelib.me: ").strip()
        if url and "ranobelib.me" in url:
            break
        print("❌ Пожалуйста, введите корректный URL с ranobelib.me")

    # Получаем начальную главу
    while True:
        try:
            start_input = input(
                "С какой главы начать? (Enter для начала с 1): "
            ).strip()
            if not start_input:
                start_chapter = 1
                break
            start_chapter = int(start_input)
            if start_chapter > 0:
                break
            print("❌ Номер главы должен быть положительным числом")
        except ValueError:
            print("❌ Пожалуйста, введите число")

    # Получаем количество глав для загрузки
    while True:
        try:
            count_input = input(
                "Сколько глав скачать? (Enter для всех доступных): "
            ).strip()
            if not count_input:
                chapters_count = None
                break
            chapters_count = int(count_input)
            if chapters_count > 0:
                break
            print("❌ Количество глав должно быть положительным числом")
        except ValueError:
            print("❌ Пожалуйста, введите число")

    return url, start_chapter, chapters_count


def download_chapters(
    url: str,
    book_dir: str,
    start_chapter: int = 1,
    chapters_count: int = None,
    max_retries: int = 3,
    volume_filter: str = None,
    args=None,
):
    """
    Скачивает главы с указанными параметрами.
    """
    print(f"\n📚 Скачиваем главы для: {url}")
    print(f"📁 Папка книги: {book_dir}")
    print(f"🎯 Начинаем с главы: {start_chapter}")
    if chapters_count:
        print(f"📊 Количество глав для загрузки: {chapters_count}")
    else:
        print(f"📊 Загружаем все доступные главы")
    print("-" * 50)

    try:
        # Извлекаем информацию из URL
        info = extract_info(url)
        slug = info[0]
        print(f"🔍 Slug книги: {slug}")

        # Получаем информацию о книге
        print("📖 Получаем информацию о книге...")
        book_info = fetch_book_info(slug, max_retries)
        if book_info:
            print(
                f"📖 Название книги: {book_info.get('display_name', book_info.get('name', 'Неизвестно'))}"
            )
            if book_info.get("description"):
                desc = book_info.get("description", "")[:100]
                print(f"📝 Описание: {desc}...")
        else:
            print("⚠️ Не удалось получить информацию о книге")
            book_info = {}

        # Получаем список всех доступных глав
        print("\n📋 Получаем список глав...")
        chapters = fetch_chapters_list(slug, max_retries)
        print(f"📊 Всего глав доступно: {len(chapters)}")

        if not chapters:
            print("❌ Не удалось получить список глав")
            return

        # Фильтруем главы согласно параметрам
        filtered_chapters = [
            (num, branch_id, volume)
            for num, branch_id, volume in chapters
            if num >= start_chapter
            and (volume_filter is None or volume == volume_filter)
        ]

        if chapters_count:
            filtered_chapters = filtered_chapters[:chapters_count]

        print(f"🎯 Глав для скачивания: {len(filtered_chapters)}")
        if filtered_chapters:
            print(
                f"   От главы {filtered_chapters[0][0]} до главы {filtered_chapters[-1][0]}"
            )

        if not filtered_chapters:
            print("❌ Нет глав для скачивания с указанными параметрами")
            return

        # Создаем папку для книги, если её нет
        os.makedirs(book_dir, exist_ok=True)

        # Скачиваем главы
        successful_downloads = 0
        failed_chapters = []  # Список неудачных скачиваний для повторных попыток

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
                        slug,
                        branch_id,
                        volume=volume,
                        number=chapter_num,
                        max_retries=1,
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
                        filename = f"{chapter_num:03d}_Том{volume_info}_{safe_name}.fb2"
                    else:
                        filename = f"{chapter_num:03d}_{safe_name}.fb2"

                    filepath = os.path.join(book_dir, filename)

                    # Генерируем FB2 с информацией о книге
                    # Передаем правильные номера тома и главы из списка глав
                    fb2_content = build_fb2(
                        data, book_info, volume=volume, chapter_number=chapter_num
                    )

                    # Сохраняем файл
                    with open(filepath, "wb") as f:
                        f.write(fb2_content)

                    print(f"      ✅ Сохранено: {filename}")
                    successful_downloads += 1
                    success = True
                    break

                except Exception as e:
                    print(f"      ❌ Ошибка: {e}")
                    if attempt < max_retries - 1:
                        print(f"      ⏳ Ждем 3 секунды перед повторной попыткой...")
                        time.sleep(3)

            if not success:
                print(
                    f"   ❌ Не удалось скачать главу {chapter_num} после {max_retries} попыток"
                )
                failed_chapters.append((chapter_num, branch_id, volume))

        # Если есть неудачные скачивания, пытаемся их повторить
        if failed_chapters:
            print(
                f"\n🔄 Повторная попытка скачивания {len(failed_chapters)} неудачных глав..."
            )
            retry_successful = 0

            for chapter_num, branch_id, volume in failed_chapters:
                print(f"\n🔄 Повторное скачивание главы {chapter_num}...")

                # Увеличиваем количество попыток для повторного скачивания
                for attempt in range(5):  # 5 попыток для повторного скачивания
                    try:
                        print(f"   🔄 Попытка {attempt + 1}/5...")

                        data = fetch_chapter(
                            slug,
                            branch_id,
                            volume=volume,
                            number=chapter_num,
                            max_retries=1,
                        )

                        if not data:
                            if attempt < 4:
                                print(
                                    f"      ⏳ Ждем 5 секунд перед повторной попыткой..."
                                )
                                time.sleep(5)
                            continue

                        # Формируем имя файла
                        chapter_name = data.get("name", f"Глава_{chapter_num}")
                        safe_name = "".join(
                            c for c in chapter_name if c.isalnum() or c in " -_"
                        ).rstrip()

                        volume_info = data.get("volume", 1)
                        if (
                            volume_info
                            and str(volume_info).isdigit()
                            and int(volume_info) > 1
                        ):
                            filename = (
                                f"{chapter_num:03d}_Том{volume_info}_{safe_name}.fb2"
                            )
                        else:
                            filename = f"{chapter_num:03d}_{safe_name}.fb2"

                        filepath = os.path.join(book_dir, filename)

                        fb2_content = build_fb2(
                            data, book_info, volume=volume, chapter_number=chapter_num
                        )

                        with open(filepath, "wb") as f:
                            f.write(fb2_content)

                        print(f"      ✅ Успешно сохранено: {filename}")
                        successful_downloads += 1
                        retry_successful += 1
                        break

                    except Exception as e:
                        print(f"      ❌ Ошибка: {e}")
                        if attempt < 4:
                            print(f"      ⏳ Ждем 5 секунд перед повторной попыткой...")
                            time.sleep(5)
                else:
                    print(
                        f"   ❌ Не удалось скачать главу {chapter_num} после 5 повторных попыток"
                    )

            if retry_successful > 0:
                print(
                    f"\n✅ Дополнительно скачано {retry_successful} глав при повторных попытках"
                )

        print("\n" + "=" * 50)
        print(f"🎉 Скачивание завершено!")
        print(
            f"✅ Успешно скачано: {successful_downloads}/{len(filtered_chapters)} глав"
        )
        if (
            len(failed_chapters)
            - (retry_successful if "retry_successful" in locals() else 0)
            > 0
        ):
            remaining_failed = len(failed_chapters) - (
                retry_successful if "retry_successful" in locals() else 0
            )
            print(f"❌ Не удалось скачать: {remaining_failed} глав")
        print(f"📁 Файлы сохранены в: {book_dir}")

        # Автоматически объединяем главы в книгу
        if successful_downloads > 0 and not getattr(args, "no_merge", False):
            try:
                from ranobe2fb2.fb2 import merge_chapters_to_book

                merged_file = merge_chapters_to_book(book_dir, book_info)
                if merged_file:
                    print(f"📚 Книга объединена в: {merged_file}")
            except Exception as e:
                print(f"⚠️ Предупреждение: Не удалось объединить главы в книгу: {e}")
                print("   Главы остались в отдельных файлах")
        elif getattr(args, "no_merge", False):
            print("📝 Объединение глав отключено (используйте --no-merge)")

    except Exception as e:
        print(f"❌ Критическая ошибка: {e}")


def download_chapters_from_267(
    url: str, book_dir: str, start_chapter: int = 267, max_retries: int = 3
):
    """
    Скачивает главы начиная с указанного номера (для обратной совместимости).
    """
    download_chapters(url, book_dir, start_chapter, None, max_retries)


def parse_arguments():
    """
    Парсит аргументы командной строки.
    """
    parser = argparse.ArgumentParser(
        description="🚀 Загрузчик ранобэ в FB2 формат",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Примеры использования:
  python download_new_book.py                    # Интерактивный режим
  python download_new_book.py --url "URL"       # Загрузить все главы с 1
  python download_new_book.py --url "URL" --start 10 --count 5  # Главы 10-14
  python download_new_book.py --url "URL" --start 100            # С главы 100 до конца
  python download_new_book.py --url "URL" --start 47 --volume 2 # Главу 47 из тома 2
  python download_new_book.py --url "URL" --no-merge            # Без объединения в книгу
        """,
    )

    parser.add_argument("--url", type=str, help="URL книги с ranobelib.me")
    parser.add_argument(
        "--start", type=int, default=1, help="Номер начальной главы (по умолчанию: 1)"
    )
    parser.add_argument(
        "--volume", type=str, help="Номер тома для фильтрации (например: 2)"
    )
    parser.add_argument(
        "--count",
        type=int,
        help="Количество глав для загрузки (по умолчанию: все доступные)",
    )
    parser.add_argument(
        "--no-merge",
        action="store_true",
        help="Не объединять главы в книгу после загрузки",
    )
    parser.add_argument(
        "--retries",
        type=int,
        default=3,
        help="Количество повторных попыток при ошибке (по умолчанию: 3)",
    )
    parser.add_argument(
        "--output", type=str, help="Папка для сохранения (по умолчанию: results/SLUG)"
    )

    return parser.parse_args()


if __name__ == "__main__":
    try:
        args = parse_arguments()

        # Если указан URL в аргументах, используем неинтерактивный режим
        if args.url:
            if not args.url or "ranobelib.me" not in args.url:
                print("❌ Пожалуйста, укажите корректный URL с ranobelib.me")
                sys.exit(1)

            # Создаем имя папки из slug
            info = extract_info(args.url)
            slug = info[0]
            book_dir = args.output or f"results/{slug}"

            # Запускаем загрузку
            download_chapters(
                args.url,
                book_dir,
                args.start,
                args.count,
                args.retries,
                args.volume,
                args,
            )
        else:
            # Интерактивный режим
            url, start_chapter, chapters_count = get_user_input()

            # Создаем имя папки из slug
            info = extract_info(url)
            slug = info[0]
            book_dir = f"results/{slug}"

            # Запускаем загрузку
            download_chapters(url, book_dir, start_chapter, chapters_count, args=args)

    except KeyboardInterrupt:
        print("\n\n❌ Загрузка прервана пользователем")
        sys.exit(1)
    except SystemExit:
        # argparse уже вызвал sys.exit(), просто выходим
        pass
    except Exception as e:
        print(f"\n❌ Неожиданная ошибка: {e}")
        sys.exit(1)
