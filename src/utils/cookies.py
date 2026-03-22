#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Утилита для извлечения cookies из браузера
"""

from pathlib import Path
from typing import Optional, Dict
from http.cookiejar import CookieJar, MozillaCookieJar

try:
    import browser_cookie3
except ImportError:
    browser_cookie3 = None


def get_browser_cookies(
    domain: str = "ranobelib.me",
    browser: str = "chrome",
    quiet: bool = False,
) -> Optional[CookieJar]:
    """
    Извлекает cookies из браузера для указанного домена.

    Args:
        domain: Домен, для которого нужны cookies
        browser: Браузер ('chrome', 'firefox', 'edge', 'opera')
        quiet: Не печатать сообщения об успехе / пустом результате

    Returns:
        CookieJar с cookies или None при ошибке
    """
    if browser_cookie3 is None:
        print("❌ Библиотека browser-cookie3 не установлена. Установите: pip install browser-cookie3")
        return None
    
    try:
        browser_lower = browser.lower()
        
        if browser_lower == "chrome":
            cj = browser_cookie3.chrome(domain_name=domain)
        elif browser_lower == "firefox":
            cj = browser_cookie3.firefox(domain_name=domain)
        elif browser_lower == "edge":
            cj = browser_cookie3.edge(domain_name=domain)
        elif browser_lower == "opera":
            cj = browser_cookie3.opera(domain_name=domain)
        else:
            print(f"❌ Неподдерживаемый браузер: {browser}")
            print("   Поддерживаемые: chrome, firefox, edge, opera")
            return None
        
        cookies_count = len(list(cj))
        if cookies_count > 0:
            if not quiet:
                print(f"✅ Найдено {cookies_count} cookies из {browser}")
            return cj
        if not quiet:
            print(f"⚠️  Cookies для {domain} не найдены в {browser}")
            print("   Убедитесь, что вы авторизованы в браузере")
        return None

    except (FileNotFoundError, PermissionError, OSError) as e:
        print(f"❌ Ошибка при извлечении cookies из {browser}: {e}")
        if "sqlite3" in str(e).lower() or "database" in str(e).lower():
            print("   Возможно, браузер открыт. Закройте браузер и попробуйте снова.")
        return None
    except Exception as e:
        print(f"❌ Неожиданная ошибка при извлечении cookies из {browser}: {e}")
        return None


COOKIE_DOMAINS = (
    "ranobelib.me",
    "cdnlibs.org",
    "imglib.info",
    "libs.social",
)


def load_netscape_cookies_file(path: str) -> Optional[Dict[str, str]]:
    p = Path(path)
    if not p.is_file():
        print(f"Файл cookies не найден: {path}")
        return None
    try:
        cj = MozillaCookieJar()
        cj.load(str(p), ignore_discard=True, ignore_expires=True)
    except (OSError, ValueError) as e:
        print(f"Не удалось прочитать cookies: {e}")
        return None
    d = cookies_to_dict(cj)
    if d:
        print(f"Загружено {len(d)} cookies из файла")
    return d if d else None


def get_merged_browser_cookies_dict(browser: str = "chrome") -> Optional[Dict[str, str]]:
    merged: Dict[str, str] = {}
    for domain in COOKIE_DOMAINS:
        jar = get_browser_cookies(domain=domain, browser=browser, quiet=True)
        if jar:
            merged.update(cookies_to_dict(jar))
    if merged:
        print(
            f"Собрано {len(merged)} cookies ({', '.join(COOKIE_DOMAINS)})"
        )
        return merged
    print("Cookies для доменов Lib не найдены в профиле браузера")
    print("Убедитесь, что вы авторизованы на сайте")
    return None


def cookies_for_session(
    cookies_file: Optional[str] = None,
    browser: Optional[str] = None,
) -> Optional[Dict[str, str]]:
    merged: Dict[str, str] = {}
    if cookies_file:
        fd = load_netscape_cookies_file(cookies_file)
        if fd:
            merged.update(fd)
    if browser:
        print(f"Извлекаем cookies из браузера {browser}...")
        bd = get_merged_browser_cookies_dict(browser=browser)
        if bd:
            merged.update(bd)
    return merged if merged else None


def cookies_to_dict(cookie_jar: CookieJar) -> Dict[str, str]:
    """
    Преобразует CookieJar в словарь для использования с requests.
    
    Args:
        cookie_jar: CookieJar с cookies
    
    Returns:
        Словарь с cookies в формате {name: value}
    """
    cookies_dict = {}
    for cookie in cookie_jar:
        cookies_dict[cookie.name] = cookie.value
    return cookies_dict
