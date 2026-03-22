#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Простой CLI интерфейс
"""

import argparse
from typing import Optional, Dict

from .core.downloader import ChapterDownloader, DownloadConfig
from .client import extract_info
from .utils.cookies import cookies_for_session
from .utils.auth import load_auth_token, save_auth_token


def main():
    """Основная функция CLI"""
    parser = argparse.ArgumentParser(description="Скачивальщик книг")
    parser.add_argument("url", help="URL книги")
    parser.add_argument("--start", type=int, help="Начальная глава (включительно)")
    parser.add_argument("--end", type=int, help="Конечная глава (включительно)")
    parser.add_argument("--full", action="store_true", help="Скачать всю книгу")
    parser.add_argument("--output", default="output", help="Папка для сохранения")
    parser.add_argument(
        "--cookies",
        choices=["chrome", "firefox", "edge", "opera"],
        help="Использовать cookies из браузера для доступа к 18+ главам",
    )
    parser.add_argument("--auth-token", help="Bearer токен для авторизации в API")
    parser.add_argument(
        "--cookies-file",
        help="Файл cookies в формате Netscape (экспорт из браузера)",
    )

    args = parser.parse_args()

    cookies: Optional[Dict[str, str]] = None
    if args.cookies or args.cookies_file:
        cookies = cookies_for_session(
            cookies_file=args.cookies_file,
            browser=args.cookies,
        )
        if not cookies:
            print("Продолжаем без cookies. 18+ может быть недоступен.")

    slug, _, branch_ui, _ = extract_info(args.url)

    auth_token = args.auth_token or load_auth_token()
    if args.auth_token:
        save_auth_token(args.auth_token)

    # Настройки скачивания
    config = DownloadConfig(max_workers=5)
    downloader = ChapterDownloader(
        config, cookies=cookies, auth_token=auth_token, branch_ui=branch_ui
    )

    if args.full:
        # Скачиваем всю книгу
        print(f"Скачиваем полную книгу {slug}")
        successful, failed = downloader.download_full_book(slug, args.output)
    else:
        # Скачиваем диапазон глав
        start = args.start or 1
        end = args.end or 1

        # Валидация диапазона
        if start > end:
            print(f"❌ Ошибка: Начальная глава ({start}) не может быть больше конечной ({end})")
            return

        print(f"Скачиваем главы {start}-{end} (включительно) книги {slug}")
        successful, failed = downloader.download_chapters_range(slug, start, end, args.output)

    print(f"Результат: {successful} успешно, {failed} ошибок")


if __name__ == "__main__":
    main()
