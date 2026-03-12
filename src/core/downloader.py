#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Основной класс для скачивания глав
"""

import json
import time
import concurrent.futures
from typing import List, Tuple, Optional, Dict
from dataclasses import dataclass
from pathlib import Path

# Настройка кодировки для Windows консоли
from ..utils.encoding import setup_console_encoding
setup_console_encoding()

# Импортируем функции из существующего модуля
from ..client import fetch_book_info, fetch_chapters_list, fetch_chapter
from ..fb2 import build_fb2


@dataclass
class DownloadConfig:
    """Конфигурация для скачивания"""

    max_workers: int = 5
    retry_delay: int = 5
    max_retries: int = 5  # Увеличиваем количество попыток
    save_raw_data: bool = True
    save_fb2: bool = True
    error_timeout: int = 10  # Таймаут после ошибки в секундах
    exponential_backoff: bool = True  # Экспоненциальная задержка


@dataclass
class ChapterInfo:
    """Информация о главе"""

    chapter_num: str
    volume: int
    branch_id: int
    title: str


class ChapterDownloader:
    """Основной класс для скачивания глав"""

    def __init__(
        self,
        config: DownloadConfig,
        cookies: Optional[Dict[str, str]] = None,
        auth_token: Optional[str] = None,
    ):
        self.config = config
        self.cookies = cookies
        self.auth_token = auth_token
        self.downloaded_chapters: List[ChapterInfo] = []
        self.failed_chapters: List[ChapterInfo] = []

    def _ensure_directories(self, output_dir: str) -> Tuple[str, str]:
        """Создает необходимые директории и возвращает пути"""
        output_path = Path(output_dir)
        raw_dir = output_path / "raw_data"
        fb2_dir = output_path / "fb2_chapters"

        if self.config.save_raw_data:
            raw_dir.mkdir(parents=True, exist_ok=True)
        if self.config.save_fb2:
            fb2_dir.mkdir(parents=True, exist_ok=True)

        return str(raw_dir), str(fb2_dir)

    def _save_raw_data(
        self, data: dict, chapter_info: ChapterInfo, raw_dir: str
    ) -> bool:
        """Сохраняет исходные данные главы"""
        try:
            # Создаем безопасное имя файла из номера главы
            safe_chapter_num = str(chapter_info.chapter_num).replace(".", "_")
            raw_file = (
                Path(raw_dir) / f"{safe_chapter_num}_Том{chapter_info.volume}_"
                f"{chapter_info.title}.json"
            )
            with open(raw_file, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            return True
        except (OSError, IOError, UnicodeEncodeError) as e:
            print(
                f"Ошибка сохранения исходных данных главы {chapter_info.chapter_num}: {e}"
            )
            return False

    def _save_fb2(self, data: dict, chapter_info: ChapterInfo, fb2_dir: str) -> bool:
        """Сохраняет FB2 главу"""
        try:
            fb2_content = build_fb2(
                data,
                chapter_number=chapter_info.chapter_num,
                volume=chapter_info.volume,
            )

            if not fb2_content:
                return False

            # Создаем безопасное имя файла из номера главы
            safe_chapter_num = str(chapter_info.chapter_num).replace(".", "_")
            fb2_file = (
                Path(fb2_dir) / f"{safe_chapter_num}_Том{chapter_info.volume}_"
                f"{chapter_info.title}.fb2"
            )

            if isinstance(fb2_content, bytes):
                with open(fb2_file, "wb") as f:
                    f.write(fb2_content)
            else:
                with open(fb2_file, "w", encoding="utf-8") as f:
                    f.write(fb2_content)

            return True
        except (OSError, IOError, UnicodeEncodeError, ImportError) as e:
            print(f"Ошибка создания FB2 для главы {chapter_info.chapter_num}: {e}")
            return False

    def download_chapter(
        self, chapter_info: ChapterInfo, output_dir: str, slug: str
    ) -> bool:
        """Скачивает одну главу с умными повторными попытками"""
        for attempt in range(self.config.max_retries):
            try:
                # Получаем данные главы
                data = fetch_chapter(
                    slug,
                    chapter_info.volume,
                    chapter_info.chapter_num,
                    cookies=self.cookies,
                    branch_id=chapter_info.branch_id,
                    auth_token=self.auth_token,
                )

                if not data or "content" not in data:
                    if attempt < self.config.max_retries - 1:
                        print(
                            f"Глава {chapter_info.chapter_num}: Нет данных "
                            f"(попытка {attempt + 1}/{self.config.max_retries})"
                        )
                        # Увеличиваем задержку при ошибках
                        delay = (
                            self.config.retry_delay * (2**attempt)
                            if self.config.exponential_backoff
                            else self.config.retry_delay
                        )
                        print(f"   Ждем {delay} секунд перед повторной попыткой...")
                        time.sleep(delay)
                        continue
                    print(
                        f"Глава {chapter_info.chapter_num}: Нет данных после всех попыток"
                    )
                    return False

                raw_dir, fb2_dir = self._ensure_directories(output_dir)

                # Сохраняем исходные данные
                if self.config.save_raw_data:
                    if not self._save_raw_data(data, chapter_info, raw_dir):
                        if attempt < self.config.max_retries - 1:
                            print(
                                f"Глава {chapter_info.chapter_num}: Ошибка сохранения "
                                f"(попытка {attempt + 1}/{self.config.max_retries})"
                            )
                            time.sleep(self.config.error_timeout)
                            continue
                        return False

                # Создаем FB2
                if self.config.save_fb2:
                    if not self._save_fb2(data, chapter_info, fb2_dir):
                        if attempt < self.config.max_retries - 1:
                            print(
                                f"Глава {chapter_info.chapter_num}: Ошибка FB2 "
                                f"(попытка {attempt + 1}/{self.config.max_retries})"
                            )
                            time.sleep(self.config.error_timeout)
                            continue
                        return False

                return True

            except (ValueError, ConnectionError, TimeoutError, KeyError) as e:
                if attempt < self.config.max_retries - 1:
                    print(
                        f"Глава {chapter_info.chapter_num}: Ошибка - {e} "
                        f"(попытка {attempt + 1}/{self.config.max_retries})"
                    )
                    # Увеличиваем задержку при ошибках
                    delay = (
                        self.config.retry_delay * (2**attempt)
                        if self.config.exponential_backoff
                        else self.config.retry_delay
                    )
                    print(f"   Ждем {delay} секунд перед повторной попыткой...")
                    time.sleep(delay)
                    continue
                print(
                    f"Глава {chapter_info.chapter_num}: Ошибка после всех попыток - {e}"
                )
                return False

        return False

    def _get_target_chapters(
        self, slug: str, start_chapter: int = None, end_chapter: int = None
    ) -> List[ChapterInfo]:
        """Получает список глав для скачивания"""
        # Получаем информацию о книге
        book_info = fetch_book_info(slug, cookies=self.cookies, auth_token=self.auth_token)
        if not book_info:
            print("❌ Не удалось получить информацию о книге")
            return []

        # Получаем список глав
        chapters = fetch_chapters_list(slug, cookies=self.cookies, auth_token=self.auth_token)
        if not chapters:
            print("⚠️  Не удалось получить список глав через API")
            # Если указан диапазон глав, создаем список глав напрямую
            if start_chapter is not None and end_chapter is not None:
                print(f"   Пробуем скачать главы {start_chapter}-{end_chapter} напрямую...")
                target_chapters = []
                for chapter_num in range(start_chapter, end_chapter + 1):
                    # Пробуем получить главу для проверки доступности
                    test_data = fetch_chapter(
                        slug,
                        1,
                        str(chapter_num),
                        max_retries=1,
                        cookies=self.cookies,
                        auth_token=self.auth_token,
                    )
                    if test_data and "content" in test_data:
                        target_chapters.append(
                            ChapterInfo(str(chapter_num), 1, None, f"Глава_{chapter_num}")
                        )
                if target_chapters:
                    print(f"   Найдено {len(target_chapters)} доступных глав")
                    return target_chapters
            print("❌ Не удалось получить список глав")
            return []

        # Фильтруем нужные главы
        target_chapters = []
        for chapter_num_str, branch_id, volume in chapters:
            # Парсим номер главы для сравнения
            try:
                if "." in chapter_num_str:
                    # Для подглав типа "1.1" берем основную часть
                    chapter_num = int(chapter_num_str.split(".")[0])
                else:
                    chapter_num = int(chapter_num_str)
            except (ValueError, IndexError):
                continue

            # Включительный диапазон: start_chapter <= chapter_num <= end_chapter
            if (
                start_chapter is None
                or end_chapter is None
                or (start_chapter <= chapter_num <= end_chapter)
            ):
                title = f"Глава_{chapter_num_str}"
                target_chapters.append(
                    ChapterInfo(chapter_num_str, volume, branch_id, title)
                )

        if not target_chapters:
            print("Не найдено глав для скачивания")
            return []

        # Сортируем главы по номеру для правильного порядка
        def sort_key(chapter_info):
            # Парсим номер главы для сортировки
            try:
                if "." in chapter_info.chapter_num:
                    # Для подглав типа "1.1" создаем кортеж (1, 1)
                    parts = chapter_info.chapter_num.split(".")
                    return (int(parts[0]), int(parts[1]) if len(parts) > 1 else 0)
                else:
                    # Для обычных глав типа "105"
                    return (int(chapter_info.chapter_num), 0)
            except (ValueError, IndexError):
                return (0, 0)

        target_chapters.sort(key=sort_key)
        print(f"Найдено глав для скачивания: {len(target_chapters)}")
        return target_chapters

    def download_chapters_parallel(
        self, chapters: List[ChapterInfo], output_dir: str, slug: str
    ) -> Tuple[int, int]:
        """Скачивает главы параллельно"""
        successful = 0
        failed = 0

        with concurrent.futures.ThreadPoolExecutor(
            max_workers=self.config.max_workers
        ) as executor:
            future_to_chapter = {
                executor.submit(
                    self.download_chapter, chapter, output_dir, slug
                ): chapter
                for chapter in chapters
            }

            for future in concurrent.futures.as_completed(future_to_chapter):
                chapter = future_to_chapter[future]
                try:
                    if future.result():
                        successful += 1
                        self.downloaded_chapters.append(chapter)
                    else:
                        failed += 1
                        self.failed_chapters.append(chapter)
                except (ValueError, ConnectionError, TimeoutError) as e:
                    print(f"Критическая ошибка для главы {chapter.chapter_num}: {e}")
                    failed += 1
                    self.failed_chapters.append(chapter)

                # Показываем прогресс
                total = successful + failed
                progress_percent = (total / len(chapters)) * 100
                progress_bar = (
                    "█" * int(progress_percent / 2) +
                    "░" * (50 - int(progress_percent / 2))
                )
                print(
                    f"\r📖 [{progress_bar}] {total}/{len(chapters)} "
                    f"({progress_percent:.1f}%) | ✅ {successful} | ❌ {failed} | "
                    f"Текущая: {chapter.chapter_num}",
                    end="",
                    flush=True,
                )

        # Финальный вывод прогресса
        print(
            f"\nИтоговый прогресс: [{progress_bar}] {total}/{len(chapters)} "
            f"({progress_percent:.1f}%) | Успешно: {successful} | Ошибок: {failed}"
        )
        return successful, failed

    def download_chapters_range(
        self, slug: str, start_chapter: int, end_chapter: int, output_dir: str
    ) -> Tuple[int, int]:
        """Скачивает диапазон глав"""
        print(f"Скачиваем главы с {start_chapter} по {end_chapter} (включительно)")

        target_chapters = self._get_target_chapters(slug, start_chapter, end_chapter)
        if not target_chapters:
            # Если список глав недоступен, пробуем скачать напрямую
            print("⚠️  Список глав недоступен, пробуем скачать главы напрямую...")
            target_chapters = []
            for chapter_num in range(start_chapter, end_chapter + 1):
                target_chapters.append(
                    ChapterInfo(str(chapter_num), 1, None, f"Глава_{chapter_num}")
                )
        
        if not target_chapters:
            return 0, 0

        # Первый проход - скачиваем все главы
        successful, failed = self.download_chapters_parallel(
            target_chapters, output_dir, slug
        )

        # Если есть неудачные главы, пробуем скачать их повторно
        if failed > 0 and self.failed_chapters:
            print(f"\nПовторная попытка скачивания {failed} неудачных глав...")
            print("Список неудачных глав:")
            for chapter in self.failed_chapters:
                print(f"   - Глава {chapter.chapter_num}: {chapter.title}")
            print("Увеличиваем задержки и таймауты для стабильности...")

            # Создаем временную конфигурацию с увеличенными задержками
            retry_config = DownloadConfig(
                max_workers=2,  # Уменьшаем количество потоков для стабильности
                retry_delay=15,  # Увеличиваем базовую задержку
                max_retries=3,  # Уменьшаем количество попыток для повторного прохода
                save_raw_data=self.config.save_raw_data,
                save_fb2=self.config.save_fb2,
                error_timeout=20,  # Увеличиваем таймаут после ошибок
                exponential_backoff=True,
            )

            # Создаем временный загрузчик для повторных попыток
            retry_downloader = ChapterDownloader(
                retry_config,
                cookies=self.cookies,
                auth_token=self.auth_token,
            )
            retry_downloader.downloaded_chapters = self.downloaded_chapters.copy()

            # Пробуем скачать неудачные главы
            retry_chapters = self.failed_chapters.copy()
            self.failed_chapters.clear()  # Очищаем список для нового прохода

            retry_successful, retry_failed = (
                retry_downloader.download_chapters_parallel(
                    retry_chapters, output_dir, slug
                )
            )

            # Обновляем статистику
            successful += retry_successful
            failed = retry_failed

            # Обновляем списки
            self.downloaded_chapters = retry_downloader.downloaded_chapters
            self.failed_chapters = retry_downloader.failed_chapters

            if retry_successful > 0:
                print(
                    f"Повторная попытка успешна! Дополнительно скачано: {retry_successful} глав"
                )
            else:
                print("Повторная попытка не дала результатов")

        return successful, failed

    def download_full_book(self, slug: str, output_dir: str) -> Tuple[int, int]:
        """Скачивает всю книгу"""
        print(f"Скачиваем полную книгу: {slug}")

        target_chapters = self._get_target_chapters(slug)
        if not target_chapters:
            return 0, 0

        # Первый проход - скачиваем все главы
        successful, failed = self.download_chapters_parallel(
            target_chapters, output_dir, slug
        )

        # Если есть неудачные главы, пробуем скачать их повторно
        if failed > 0 and self.failed_chapters:
            print(f"\nПовторная попытка скачивания {failed} неудачных глав...")
            print("Список неудачных глав:")
            for chapter in self.failed_chapters:
                print(f"   - Глава {chapter.chapter_num}: {chapter.title}")
            print("Увеличиваем задержки и таймауты для стабильности...")

            # Создаем временную конфигурацию с увеличенными задержками
            retry_config = DownloadConfig(
                max_workers=2,  # Уменьшаем количество потоков для стабильности
                retry_delay=15,  # Увеличиваем базовую задержку
                max_retries=3,  # Уменьшаем количество попыток для повторного прохода
                save_raw_data=self.config.save_raw_data,
                save_fb2=self.config.save_fb2,
                error_timeout=20,  # Увеличиваем таймаут после ошибок
                exponential_backoff=True,
            )

            # Создаем временный загрузчик для повторных попыток
            retry_downloader = ChapterDownloader(
                retry_config,
                cookies=self.cookies,
                auth_token=self.auth_token,
            )
            retry_downloader.downloaded_chapters = self.downloaded_chapters.copy()

            # Пробуем скачать неудачные главы
            retry_chapters = self.failed_chapters.copy()
            self.failed_chapters.clear()  # Очищаем список для нового прохода

            retry_successful, retry_failed = (
                retry_downloader.download_chapters_parallel(
                    retry_chapters, output_dir, slug
                )
            )

            # Обновляем статистику
            successful += retry_successful
            failed = retry_failed

            # Обновляем списки
            self.downloaded_chapters = retry_downloader.downloaded_chapters
            self.failed_chapters = retry_downloader.failed_chapters

            if retry_successful > 0:
                print(
                    f"Повторная попытка успешна! Дополнительно скачано: {retry_successful} глав"
                )
            else:
                print("Повторная попытка не дала результатов")

        return successful, failed
