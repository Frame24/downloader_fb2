#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Утилиты проекта
"""

from .encoding import setup_console_encoding
from .cookies import get_browser_cookies, cookies_to_dict

__all__ = ["setup_console_encoding", "get_browser_cookies", "cookies_to_dict"]
