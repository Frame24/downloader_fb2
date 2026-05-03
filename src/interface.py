#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Универсальный интерфейс для скачивальщика книг
Поддерживает как пользовательский, так и программный доступ
"""

import argparse
import sys
from pathlib import Path
from typing import Optional, Tuple, Dict, Any
from dataclasses import dataclass

from .core.downloader import ChapterDownloader, DownloadConfig
from .core.converter import DataConverter
from .client import extract_info, fetch_book_info, fetch_chapters_list
from .utils.cookies import cookies_for_session
from .utils.auth import load_auth_token, save_auth_token


@dataclass
class DownloadResult:
    """Результат скачивания"""
    successful: int
    failed: int
    output_dir: str
    book_title: str
    total_chapters: int


@dataclass
class BookInfo:
    """Информация о книге"""
    title: str
    slug: str
    total_chapters: int
    available_chapters: list


class BookDownloader:
    """Основной класс для скачивания книг"""
    
    def __init__(
        self,
        max_workers: int = 2,
        output_base: str = "output",
        cookies: Optional[Dict[str, str]] = None,
        auth_token: Optional[str] = None,
        skip_existing: bool = True,
    ):
        self.max_workers = max_workers
        self.output_base = output_base
        self.config = DownloadConfig(
            max_workers=max_workers, skip_existing=skip_existing
        )
        self.downloader = ChapterDownloader(
            self.config, cookies=cookies, auth_token=auth_token, branch_ui=None
        )
        self.converter = DataConverter()
        self.cookies = cookies
        self.auth_token = auth_token
    
    def get_book_info(self, url: str) -> BookInfo:
        """Получает информацию о книге"""
        try:
            slug, _, branch_ui, _ = extract_info(url)
            self.downloader.branch_ui = branch_ui
            book_data = fetch_book_info(slug, cookies=self.cookies, auth_token=self.auth_token)
            chapters = fetch_chapters_list(
                slug,
                cookies=self.cookies,
                auth_token=self.auth_token,
                branch_ui=branch_ui,
            )
            
            return BookInfo(
                title=book_data.get("display_name", f"Книга_{slug}"),
                slug=slug,
                total_chapters=book_data.get("chapters_count", 0),
                available_chapters=[ch[0] for ch in chapters]  # Номера глав
            )
        except Exception as e:
            raise ValueError(f"Не удалось получить информацию о книге: {e}")
    
    def download_book(self, url: str, start: Optional[int] = None, 
                     end: Optional[int] = None, title: Optional[str] = None) -> DownloadResult:
        """Скачивает книгу или диапазон глав"""
        # Получаем информацию о книге
        book_info = self.get_book_info(url)
        
        # Определяем диапазон глав
        if start is None:
            start = 1
        if end is None:
            end = book_info.total_chapters
        
        # Создаем папку для сохранения
        book_title = title or book_info.title
        output_dir = f"{self.output_base}/{book_title}"
        
        # Скачиваем главы
        successful, failed = self.downloader.download_chapters_range(
            book_info.slug, start, end, output_dir
        )
        
        return DownloadResult(
            successful=successful,
            failed=failed,
            output_dir=output_dir,
            book_title=book_title,
            total_chapters=book_info.total_chapters
        )
    
    def convert_to_fb2(self, result: DownloadResult, cleanup_individual_files: bool = True) -> bool:
        """Конвертирует скачанные данные в FB2"""
        try:
            # Конвертируем в FB2
            conv_successful, conv_failed = self.converter.convert_raw_to_fb2(
                f"{result.output_dir}/raw_data",
                f"{result.output_dir}/fb2_chapters"
            )
            
            # Объединяем в книгу
            self.converter.convert_fb2_to_merged_book(
                f"{result.output_dir}/fb2_chapters",
                result.output_dir,
                result.book_title,
                cleanup_individual_files
            )
            
            return conv_successful > 0
        except Exception as e:
            print(f"Ошибка конвертации: {e}")
            return False
    
    def full_download(self, url: str, start: Optional[int] = None, 
                     end: Optional[int] = None, title: Optional[str] = None) -> DownloadResult:
        """Полный цикл: скачивание + конвертация"""
        result = self.download_book(url, start, end, title)
        
        if result.successful > 0:
            self.convert_to_fb2(result)
        
        return result


def create_cli_parser() -> argparse.ArgumentParser:
    """Создает парсер командной строки"""
    parser = argparse.ArgumentParser(
        description="Скачивальщик книг с ranobelib.me",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Примеры использования:

  # Скачать всю книгу
  python -m src.interface "https://ranobelib.me/ru/book/197421--naega-geimseog-heukgisaga-doiettda"

  # Скачать главы 15-20 включительно
  python -m src.interface "https://ranobelib.me/ru/book/197421--naega-geimseog-heukgisaga-doiettda" --start 15 --end 20

  # Скачать с кастомным названием
  python -m src.interface "https://ranobelib.me/ru/book/197421--naega-geimseog-heukgisaga-doiettda" --title "Моя книга"

  # Только информация о книге
  python -m src.interface "https://ranobelib.me/ru/book/197421--naega-geimseog-heukgisaga-doiettda" --info-only
        """
    )
    
    parser.add_argument("url", help="URL книги на ranobelib.me")
    parser.add_argument("--start", type=int, help="Начальная глава (включительно)")
    parser.add_argument("--end", type=int, help="Конечная глава (включительно)")
    parser.add_argument("--title", help="Название книги")
    parser.add_argument("--workers", type=int, default=2, help="Количество потоков")
    parser.add_argument("--output", default="output", help="Базовая папка для сохранения")
    parser.add_argument("--info-only", action="store_true", help="Только показать информацию о книге")
    parser.add_argument("--no-convert", action="store_true", help="Не конвертировать в FB2")
    parser.add_argument("--keep-chapters", action="store_true", help="Сохранить отдельные FB2 главы")
    parser.add_argument("--cookies", choices=["chrome", "firefox", "edge", "opera"], 
                       help="Использовать cookies из браузера для доступа к 18+ главам")
    parser.add_argument(
        "--cookies-file",
        help="Файл cookies в формате Netscape (экспорт из браузера)",
    )
    parser.add_argument("--auth-token", help="Bearer токен для авторизации в API")
    parser.add_argument(
        "--redownload",
        action="store_true",
        help="Заново скачать главы с API, даже если JSON уже есть в raw_data",
    )

    return parser


def main():
    """Основная функция CLI"""
    parser = create_cli_parser()
    args = parser.parse_args()
    
    try:
        # Валидация диапазона глав
        if args.start is not None and args.end is not None and args.start > args.end:
            print(f"❌ Ошибка: Начальная глава ({args.start}) не может быть больше конечной ({args.end})")
            sys.exit(1)
        
        cookies = None
        if args.cookies or args.cookies_file:
            cookies = cookies_for_session(
                cookies_file=args.cookies_file,
                browser=args.cookies,
            )
            if not cookies:
                print("Продолжаем без cookies. 18+ может быть недоступен.")

        auth_token = args.auth_token or load_auth_token()
        if args.auth_token:
            save_auth_token(args.auth_token)

        downloader = BookDownloader(
            max_workers=args.workers,
            output_base=args.output,
            cookies=cookies,
            auth_token=auth_token,
            skip_existing=not args.redownload,
        )
        
        if args.info_only:
            # Только информация о книге
            book_info = downloader.get_book_info(args.url)
            print(f"📚 Книга: {book_info.title}")
            print(f"🔗 Slug: {book_info.slug}")
            print(f"📖 Всего глав: {book_info.total_chapters}")
            print(f"📋 Доступные главы: {len(book_info.available_chapters)}")
            return
        
        # Скачивание
        print(f"🚀 Начинаем скачивание...")
        
        if args.no_convert:
            # Только скачивание без конвертации
            result = downloader.download_book(args.url, args.start, args.end, args.title)
        else:
            # Полный цикл с конвертацией
            result = downloader.download_book(args.url, args.start, args.end, args.title)
            if result.successful > 0:
                # Конвертируем с учетом опции keep_chapters
                cleanup = not args.keep_chapters
                downloader.convert_to_fb2(result, cleanup_individual_files=cleanup)
        
        print(f"\n📊 Результат:")
        print(f"✅ Успешно скачано: {result.successful} глав")
        print(f"❌ Ошибок: {result.failed} глав")
        print(f"📁 Папка: {result.output_dir}")
        
        if result.successful > 0:
            print(f"📚 Книга готова: {result.book_title}")
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
