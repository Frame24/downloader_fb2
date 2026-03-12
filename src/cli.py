#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Простой CLI интерфейс
"""

import argparse
from typing import Optional, Dict

from .core.downloader import ChapterDownloader, DownloadConfig
from .client import extract_info
from .utils.cookies import get_browser_cookies, cookies_to_dict
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

    args = parser.parse_args()

    # Получаем cookies из браузера, если указано
    cookies: Optional[Dict[str, str]] = None
    if args.cookies:
        print(f"🔐 Извлекаем cookies из {args.cookies}...")
        cookie_jar = get_browser_cookies(domain="ranobelib.me", browser=args.cookies)
        if cookie_jar:
            cookies = cookies_to_dict(cookie_jar)
        else:
            print("⚠️  Продолжаем без cookies. 18+ главы могут быть недоступны.")

    # Извлекаем slug из URL
    slug, _, _, _ = extract_info(args.url)

    auth_token = args.auth_token or load_auth_token()
    if args.auth_token:
        save_auth_token(args.auth_token)

    # Настройки скачивания
    config = DownloadConfig(max_workers=5)
    downloader = ChapterDownloader(config, cookies=cookies, auth_token=auth_token)

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
