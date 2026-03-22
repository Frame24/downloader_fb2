#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Утилиты проекта
"""

from .encoding import setup_console_encoding
from .cookies import (
    get_browser_cookies,
    cookies_to_dict,
    get_merged_browser_cookies_dict,
    load_netscape_cookies_file,
    cookies_for_session,
)

__all__ = [
    "setup_console_encoding",
    "get_browser_cookies",
    "cookies_to_dict",
    "get_merged_browser_cookies_dict",
    "load_netscape_cookies_file",
    "cookies_for_session",
]
