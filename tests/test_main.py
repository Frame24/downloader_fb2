#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Основные тесты проекта
"""

import sys
import tempfile
import shutil
import time
from pathlib import Path

import pytest

# Добавляем src в путь для импорта
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

from src.core.downloader import ChapterDownloader, DownloadConfig
from src.core.converter import DataConverter
from src.client import extract_info, fetch_book_info, fetch_chapters_list, fetch_chapter


class TestProject:
    """Основные тесты проекта"""

    # Тестовые данные
    TEST_BOOK_URL = "https://ranobelib.me/ru/book/197421--naega-geimseog-heukgisaga-doiettda"
    TEST_BOOK_SLUG = "197421--naega-geimseog-heukgisaga-doiettda"

    @pytest.fixture
    def temp_dir(self):
        """Создает временную директорию для тестов"""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)

    @pytest.fixture
    def download_config(self):
        """Конфигурация для скачивания"""
        return DownloadConfig(max_workers=2, retry_delay=1, max_retries=2)

    def test_api_accessibility(self):
        """Тест доступности API"""
        import requests  # pylint: disable=import-outside-toplevel

        try:
            response = requests.get(
                f"https://api.cdnlibs.org/api/manga/{self.TEST_BOOK_SLUG}/chapters",
                timeout=10
            )
            assert response.status_code == 200
            data = response.json()
            assert "data" in data
            print("✅ API доступен")
        except requests.exceptions.RequestException as e:
            pytest.fail(f"❌ API недоступен: {e}")

    def test_url_parsing(self):
        """Тест парсинга URL"""
        try:
            slug, book_type, _, _ = extract_info(self.TEST_BOOK_URL)
            assert slug == self.TEST_BOOK_SLUG
            assert book_type == "list"
            print(f"✅ URL парсится корректно: {slug}")
        except (ValueError, KeyError) as e:
            pytest.fail(f"❌ Ошибка парсинга URL: {e}")

    def test_book_info_retrieval(self):
        """Тест получения информации о книге"""
        try:
            book_info = fetch_book_info(self.TEST_BOOK_SLUG)
            assert book_info is not None
            assert "display_name" in book_info
            assert "chapters_count" in book_info
            assert book_info["chapters_count"] > 0
            print(f"✅ Информация о книге получена: {book_info['chapters_count']} глав")
        except (ValueError, KeyError, ConnectionError) as e:
            pytest.fail(f"❌ Ошибка получения информации о книге: {e}")

    def test_chapters_list_retrieval(self):
        """Тест получения списка глав"""
        try:
            chapters = fetch_chapters_list(self.TEST_BOOK_SLUG)
            assert chapters is not None
            assert len(chapters) > 0
            first_chapter = chapters[0]
            assert len(first_chapter) == 3
            print(f"✅ Список глав получен: {len(chapters)} глав")
        except (ValueError, KeyError, ConnectionError) as e:
            pytest.fail(f"❌ Ошибка получения списка глав: {e}")

    def test_single_chapter_download(self, temp_dir, download_config):
        """Тест скачивания одной главы"""
        try:
            downloader = ChapterDownloader(download_config)
            successful, failed = downloader.download_chapters_range(
                self.TEST_BOOK_SLUG, 1, 1, temp_dir
            )

            assert successful == 1
            assert failed == 0

            # Проверяем файлы
            raw_dir = Path(temp_dir) / "raw_data"
            fb2_dir = Path(temp_dir) / "fb2_chapters"

            assert raw_dir.exists()
            assert fb2_dir.exists()

            raw_files = list(raw_dir.glob("*.json"))
            fb2_files = list(fb2_dir.glob("*.fb2"))

            assert len(raw_files) == 1
            assert len(fb2_files) == 1

            print("✅ Глава скачана успешно")
        except (ValueError, ConnectionError, OSError) as e:
            pytest.fail(f"❌ Ошибка скачивания главы: {e}")

    def test_chapter_range_download(self, temp_dir, download_config):
        """Тест скачивания диапазона глав"""
        try:
            downloader = ChapterDownloader(download_config)
            successful, failed = downloader.download_chapters_range(
                self.TEST_BOOK_SLUG, 1, 3, temp_dir
            )

            assert successful == 3
            assert failed == 0

            print(f"✅ Диапазон глав скачан: {successful} глав")
        except (ValueError, ConnectionError, OSError) as e:
            pytest.fail(f"❌ Ошибка скачивания диапазона глав: {e}")

    def test_converter(self, temp_dir, download_config):
        """Тест конвертера"""
        try:
            # Сначала скачиваем главу
            downloader = ChapterDownloader(download_config)
            downloader.download_chapters_range(self.TEST_BOOK_SLUG, 1, 1, temp_dir)

            # Тестируем конвертер
            converter = DataConverter()
            successful, failed = converter.convert_raw_to_fb2(
                f"{temp_dir}/raw_data", f"{temp_dir}/fb2_chapters"
            )

            assert successful == 1
            assert failed == 0

            print("✅ Конвертер работает корректно")
        except (ValueError, ConnectionError, OSError) as e:
            pytest.fail(f"❌ Ошибка конвертера: {e}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
