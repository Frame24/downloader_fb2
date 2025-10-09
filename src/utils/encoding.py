#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Утилиты для настройки кодировки в Windows консоли
"""

import sys


import codecs
import io


def setup_console_encoding():
    """
    Настраивает кодировку консоли для корректного отображения русских символов в Windows
    """
    if sys.platform == "win32":
        try:
            if hasattr(sys.stdout, "detach"):
                sys.stdout = codecs.getwriter("utf-8")(sys.stdout.detach())
                sys.stderr = codecs.getwriter("utf-8")(sys.stderr.detach())
            elif hasattr(sys.stdout, "buffer"):
                sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
                sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")
        except (AttributeError, OSError):
            # Если не удается изменить кодировку, продолжаем без изменений
            pass
