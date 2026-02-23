#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Утилита для извлечения cookies из браузера
"""

from typing import Optional, Dict
from http.cookiejar import CookieJar

try:
    import browser_cookie3
except ImportError:
    browser_cookie3 = None


def get_browser_cookies(domain: str = "ranobelib.me", browser: str = "chrome") -> Optional[CookieJar]:
    """
    Извлекает cookies из браузера для указанного домена.
    
    Args:
        domain: Домен, для которого нужны cookies
        browser: Браузер ('chrome', 'firefox', 'edge', 'opera')
    
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
            print(f"✅ Найдено {cookies_count} cookies из {browser}")
            return cj
        else:
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
