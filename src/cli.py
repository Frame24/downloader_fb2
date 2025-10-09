#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Простой CLI интерфейс
"""

import argparse

from .core.downloader import ChapterDownloader, DownloadConfig
from .client import extract_info


def main():
    """Основная функция CLI"""
    parser = argparse.ArgumentParser(description="Скачивальщик книг")
    parser.add_argument("url", help="URL книги")
    parser.add_argument("--start", type=int, help="Начальная глава")
    parser.add_argument("--end", type=int, help="Конечная глава")
    parser.add_argument("--output", default="output", help="Папка для сохранения")

    args = parser.parse_args()

    # Извлекаем slug из URL
    slug, _, _, _ = extract_info(args.url)

    # Настройки скачивания
    config = DownloadConfig(max_workers=5)
    downloader = ChapterDownloader(config)

    # Скачиваем главы
    start = args.start or 1
    end = args.end or 1

    print(f"Скачиваем главы {start}-{end} книги {slug}")
    successful, failed = downloader.download_chapters_range(slug, start, end, args.output)

    print(f"Результат: {successful} успешно, {failed} ошибок")


if __name__ == "__main__":
    main()
