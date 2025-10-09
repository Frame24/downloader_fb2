#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Основной файл для запуска проекта
"""

import sys
from pathlib import Path

# Настройка кодировки для Windows консоли
try:
    from src.utils.encoding import setup_console_encoding
    setup_console_encoding()
except ImportError:
    # Если модуль недоступен, продолжаем без настройки кодировки
    pass

# Добавляем src в путь
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

from src.cli import main

if __name__ == "__main__":
    main()
