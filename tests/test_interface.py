#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Тесты для программного API интерфейса
"""

import sys
import tempfile
import shutil
from pathlib import Path

import pytest

# Добавляем src в путь
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

from src.interface import BookDownloader, BookInfo, DownloadResult


class TestBookDownloaderAPI:
    """Тесты программного API"""

    TEST_URL = "https://ranobelib.me/ru/book/197421--naega-geimseog-heukgisaga-doiettda"
    TEST_SLUG = "197421--naega-geimseog-heukgisaga-doiettda"

    @pytest.fixture
    def temp_dir(self):
        """Временная директория для тестов"""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)

    @pytest.fixture
    def downloader(self, temp_dir):
        """Создает загрузчик с временной папкой"""
        return BookDownloader(max_workers=2, output_base=temp_dir)

    def test_get_book_info(self, downloader):
        """Тест получения информации о книге"""
        book_info = downloader.get_book_info(self.TEST_URL)
        
        assert isinstance(book_info, BookInfo)
        assert book_info.slug == self.TEST_SLUG
        assert book_info.total_chapters > 0
        assert len(book_info.available_chapters) > 0
        assert book_info.title is not None
        
        print(f"✅ Информация о книге получена: {book_info.title}")

    def test_download_single_chapter(self, downloader):
        """Тест скачивания одной главы"""
        result = downloader.download_book(self.TEST_URL, start=1, end=1)
        
        assert isinstance(result, DownloadResult)
        assert result.successful == 1
        assert result.failed == 0
        assert result.total_chapters > 0
        assert Path(result.output_dir).exists()
        
        print(f"✅ Одна глава скачана: {result.successful}")

    def test_download_chapter_range(self, downloader):
        """Тест скачивания диапазона глав"""
        result = downloader.download_book(self.TEST_URL, start=1, end=3)
        
        assert isinstance(result, DownloadResult)
        assert result.successful == 3
        assert result.failed == 0
        assert Path(result.output_dir).exists()
        
        print(f"✅ Диапазон глав скачан: {result.successful}")

    def test_full_download_cycle(self, downloader):
        """Тест полного цикла скачивания"""
        result = downloader.full_download(self.TEST_URL, start=1, end=2)
        
        assert isinstance(result, DownloadResult)
        assert result.successful == 2
        assert result.failed == 0
        
        # Проверяем, что файлы созданы
        raw_dir = Path(result.output_dir) / "raw_data"
        fb2_dir = Path(result.output_dir) / "fb2_chapters"
        
        assert raw_dir.exists()
        assert fb2_dir.exists()
        
        raw_files = list(raw_dir.glob("*.json"))
        fb2_files = list(fb2_dir.glob("*.fb2"))
        
        assert len(raw_files) == 2
        assert len(fb2_files) == 2
        
        print(f"✅ Полный цикл выполнен: {result.successful} глав")

    def test_custom_title(self, downloader):
        """Тест с кастомным названием"""
        custom_title = "Моя тестовая книга"
        result = downloader.download_book(self.TEST_URL, start=1, end=1, title=custom_title)
        
        assert result.book_title == custom_title
        assert custom_title in result.output_dir
        
        print(f"✅ Кастомное название работает: {result.book_title}")

    def test_error_handling_invalid_url(self, downloader):
        """Тест обработки ошибок с неверным URL"""
        with pytest.raises(ValueError):
            downloader.get_book_info("https://invalid-url.com/book/123")

    def test_error_handling_invalid_chapter_range(self, downloader):
        """Тест обработки ошибок с неверным диапазоном глав"""
        # Слишком большой диапазон
        result = downloader.download_book(self.TEST_URL, start=1000, end=2000)
        assert result.successful == 0
        assert result.failed >= 0

    def test_downloader_configuration(self):
        """Тест конфигурации загрузчика"""
        downloader = BookDownloader(max_workers=3, output_base="test_output")
        
        assert downloader.max_workers == 3
        assert downloader.output_base == "test_output"
        assert downloader.config.max_workers == 3

    def test_result_structure(self, downloader):
        """Тест структуры результата"""
        result = downloader.download_book(self.TEST_URL, start=1, end=1)
        
        # Проверяем все поля DownloadResult
        assert hasattr(result, 'successful')
        assert hasattr(result, 'failed')
        assert hasattr(result, 'output_dir')
        assert hasattr(result, 'book_title')
        assert hasattr(result, 'total_chapters')
        
        assert isinstance(result.successful, int)
        assert isinstance(result.failed, int)
        assert isinstance(result.output_dir, str)
        assert isinstance(result.book_title, str)
        assert isinstance(result.total_chapters, int)

    def test_book_info_structure(self, downloader):
        """Тест структуры информации о книге"""
        book_info = downloader.get_book_info(self.TEST_URL)
        
        # Проверяем все поля BookInfo
        assert hasattr(book_info, 'title')
        assert hasattr(book_info, 'slug')
        assert hasattr(book_info, 'total_chapters')
        assert hasattr(book_info, 'available_chapters')
        
        assert isinstance(book_info.title, str)
        assert isinstance(book_info.slug, str)
        assert isinstance(book_info.total_chapters, int)
        assert isinstance(book_info.available_chapters, list)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
