#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Класс для конвертации данных в различные форматы
"""

import json
import re
import shutil
import sys
from typing import Dict, Any, Optional, Tuple
from pathlib import Path

# Настройка кодировки для Windows консоли
from ..utils.encoding import setup_console_encoding
setup_console_encoding()

from ..fb2 import build_fb2, merge_chapters_to_book


class DataConverter:
    """Класс для конвертации данных"""

    def __init__(self):
        self.converted_count = 0
        self.failed_count = 0

    def _parse_filename(self, filename: str) -> Optional[Tuple[int, int, str]]:
        """Парсит имя файла и извлекает номер главы, том и название"""
        match = re.match(r"(\d+)_Том(\d+)_(.+)\.(json|fb2)", filename)
        if not match:
            return None

        chapter_num = int(match.group(1))
        volume = int(match.group(2))
        chapter_name = match.group(3)
        return chapter_num, volume, chapter_name

    def _ensure_output_dir(self, output_dir: str, subdir: str) -> Path:
        """Создает выходную директорию"""
        output_path = Path(output_dir) / subdir
        output_path.mkdir(parents=True, exist_ok=True)
        return output_path

    def _save_fb2_file(self, fb2_content: bytes | str, fb2_path: Path) -> bool:
        """Сохраняет FB2 файл"""
        try:
            if isinstance(fb2_content, bytes):
                with open(fb2_path, "wb") as f:
                    f.write(fb2_content)
            else:
                with open(fb2_path, "w", encoding="utf-8") as f:
                    f.write(fb2_content)
            return True
        except (OSError, IOError, UnicodeEncodeError) as e:
            print(f"   ❌ Ошибка сохранения {fb2_path.name}: {e}")
            return False

    def convert_raw_to_fb2(self, raw_data_dir: str, output_dir: str) -> Tuple[int, int]:
        """Конвертирует исходные JSON данные в FB2"""
        print("🔄 Конвертируем исходные данные в FB2...")

        raw_path = Path(raw_data_dir)
        if not raw_path.exists():
            print(f"❌ Папка с исходными данными не найдена: {raw_data_dir}")
            return 0, 0

        # Создаем папку для FB2
        fb2_dir = self._ensure_output_dir(output_dir, "fb2_chapters")

        # Получаем список JSON файлов
        json_files = list(raw_path.glob("*.json"))

        if not json_files:
            print("❌ JSON файлы не найдены!")
            return 0, 0

        print(f"📊 Найдено JSON файлов: {len(json_files)}")

        for json_file in json_files:
            try:
                # Извлекаем информацию из имени файла
                parsed = self._parse_filename(json_file.name)
                if not parsed:
                    print(
                        f"   ⚠️  Пропускаем файл с неправильным именем: {json_file.name}"
                    )
                    continue

                chapter_num, volume, chapter_name = parsed

                print(
                    f"📄 [{self.converted_count + self.failed_count + 1}/{len(json_files)}] "
                    f"Конвертируем главу {chapter_num} (Том {volume})..."
                )

                # Читаем JSON данные
                with open(json_file, "r", encoding="utf-8") as f:
                    data = json.load(f)

                # Создаем FB2
                fb2_content = build_fb2(data, chapter_number=chapter_num, volume=volume)

                if not fb2_content:
                    print(f"   ❌ Не удалось создать FB2 для главы {chapter_num}")
                    self.failed_count += 1
                    continue

                # Сохраняем FB2
                fb2_filename = f"{chapter_num:03d}_Том{volume}_{chapter_name}.fb2"
                fb2_path = fb2_dir / fb2_filename

                if self._save_fb2_file(fb2_content, fb2_path):
                    print(f"   ✅ Сохранено: {fb2_filename}")
                    self.converted_count += 1
                else:
                    self.failed_count += 1

            except (ValueError, KeyError, OSError, IOError) as e:
                print(f"   ❌ Ошибка при конвертации {json_file.name}: {e}")
                self.failed_count += 1
                continue

        self._print_conversion_stats()
        return self.converted_count, self.failed_count

    def convert_fb2_to_merged_book(
        self, fb2_chapters_dir: str, output_dir: str, book_title: str
    ) -> bool:
        """Объединяет отдельные FB2 главы в одну книгу"""
        print(f"📚 Объединяем главы в книгу: {book_title}")

        fb2_path = Path(fb2_chapters_dir)
        if not fb2_path.exists():
            print(f"❌ Папка с FB2 главами не найдена: {fb2_chapters_dir}")
            return False

        # Получаем список FB2 файлов
        fb2_files = sorted(list(fb2_path.glob("*.fb2")))

        if not fb2_files:
            print("❌ FB2 файлы не найдены!")
            return False

        print(f"📊 Найдено FB2 глав: {len(fb2_files)}")

        try:
            # Создаем информацию о книге
            book_info = {
                "display_name": book_title,
                "name": book_title,
                "description": f"Книга '{book_title}' - объединенные главы",
            }

            # Объединяем главы
            output_file = merge_chapters_to_book(str(fb2_path), book_info)

            # Перемещаем файл в output_dir если нужно
            if output_file and output_dir:
                final_path = Path(output_dir) / Path(output_file).name
                shutil.move(output_file, final_path)
                output_file = str(final_path)

            if output_file:
                print(f"✅ Книга успешно создана: {output_file}")
                return True
            print("❌ Не удалось создать объединенную книгу")
            return False

        except (ValueError, KeyError, OSError, IOError) as e:
            print(f"❌ Ошибка при создании объединенной книги: {e}")
            return False

    def validate_data_integrity(
        self, raw_data_dir: str, fb2_chapters_dir: str
    ) -> Dict[str, Any]:
        """Проверяет целостность данных"""
        print("🔍 Проверяем целостность данных...")

        raw_path = Path(raw_data_dir)
        fb2_path = Path(fb2_chapters_dir)

        raw_files = list(raw_path.glob("*.json")) if raw_path.exists() else []
        fb2_files = list(fb2_path.glob("*.fb2")) if fb2_path.exists() else []

        # Анализируем файлы
        raw_chapters = set()
        fb2_chapters = set()

        for raw_file in raw_files:
            parsed = self._parse_filename(raw_file.name)
            if parsed:
                chapter_num, volume, _ = parsed
                raw_chapters.add((chapter_num, volume))

        for fb2_file in fb2_files:
            parsed = self._parse_filename(fb2_file.name)
            if parsed:
                chapter_num, volume, _ = parsed
                fb2_chapters.add((chapter_num, volume))

        # Находим различия
        missing_fb2 = raw_chapters - fb2_chapters
        extra_fb2 = fb2_chapters - raw_chapters

        result = {
            "raw_chapters_count": len(raw_chapters),
            "fb2_chapters_count": len(fb2_chapters),
            "missing_fb2": sorted(list(missing_fb2)),
            "extra_fb2": sorted(list(extra_fb2)),
            "integrity_score": (
                len(fb2_chapters) / len(raw_chapters) if raw_chapters else 0
            ),
        }

        self._print_integrity_stats(result)
        return result

    def _print_conversion_stats(self):
        """Выводит статистику конвертации"""
        print("\n📊 Итоговая статистика:")
        print(f"   ✅ Успешно конвертировано: {self.converted_count} глав")
        print(f"   ❌ Ошибок: {self.failed_count} глав")

    def _print_integrity_stats(self, result: dict):
        """Выводит статистику целостности"""
        print("📊 Результаты проверки:")
        print(f"   📁 Исходных глав: {result['raw_chapters_count']}")
        print(f"   📚 FB2 глав: {result['fb2_chapters_count']}")
        print(f"   ❌ Отсутствуют FB2: {len(result['missing_fb2'])}")
        print(f"   ⚠️  Лишние FB2: {len(result['extra_fb2'])}")
        print(f"   📈 Целостность: {result['integrity_score']:.1%}")
