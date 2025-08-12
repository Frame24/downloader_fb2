#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Скрипт для исправления существующих FB2 файлов с проблемами параграфов
"""

import os
import re
import xml.etree.ElementTree as ET
from xml.dom import minidom
from ranobe2fb2.fb2 import clean_html


def fix_fb2_file(filepath):
    """Исправляет FB2 файл, разбивая длинные параграфы на более короткие"""
    print(f"🔧 Исправляем файл: {os.path.basename(filepath)}")

    try:
        # Парсим XML
        tree = ET.parse(filepath)
        root = tree.getroot()

        # Находим все параграфы
        paragraphs = root.findall(".//p")

        if not paragraphs:
            print("   ⚠️  Параграфы не найдены")
            return False

        print(f"   📝 Найдено параграфов: {len(paragraphs)}")

        # Проверяем каждый параграф
        fixed = False
        for i, p in enumerate(paragraphs):
            if p.text and len(p.text) > 500:  # Если параграф слишком длинный
                print(f"   📏 Параграф {i+1} слишком длинный ({len(p.text)} символов)")

                # Разбиваем длинный параграф на предложения
                sentences = re.split(r"(?<=[.!?])\s+", p.text)

                if len(sentences) > 1:
                    # Группируем предложения в параграфы по 3-5 предложений
                    new_paragraphs = []
                    current_para = ""

                    for j, sentence in enumerate(sentences):
                        current_para += sentence + " "
                        if (j + 1) % 4 == 0 or j == len(sentences) - 1:
                            new_paragraphs.append(current_para.strip())
                            current_para = ""

                    if len(new_paragraphs) > 1:
                        # Заменяем длинный параграф на несколько коротких
                        # Находим родительский элемент
                        parent = None
                        for elem in root.iter():
                            if p in list(elem):
                                parent = elem
                                break

                        if parent is not None:
                            # Удаляем старый параграф
                            parent.remove(p)

                            # Добавляем новые параграфы
                            for new_text in new_paragraphs:
                                new_p = ET.SubElement(parent, "p")
                                new_p.text = new_text

                            fixed = True
                            print(
                                f"      ✅ Разбит на {len(new_paragraphs)} параграфов"
                            )
                        else:
                            print("      ❌ Не удалось найти родительский элемент")
                    else:
                        print("      ⚠️  Не удалось разбить на параграфы")

        if fixed:
            # Сохраняем исправленный файл
            raw = ET.tostring(root, encoding="utf-8")
            pretty = minidom.parseString(raw)
            pretty_xml = pretty.toprettyxml(indent="  ", encoding="utf-8")

            with open(filepath, "wb") as f:
                f.write(pretty_xml)

            print(f"   💾 Файл исправлен и сохранен")
            return True
        else:
            print(f"   ✅ Файл не требует исправлений")
            return False

    except Exception as e:
        print(f"   ❌ Ошибка при исправлении: {e}")
        return False


def fix_all_fb2_in_directory(directory):
    """Исправляет все FB2 файлы в указанной директории"""
    print(f"📁 Обрабатываем директорию: {directory}")

    if not os.path.exists(directory):
        print(f"❌ Директория не существует: {directory}")
        return

    # Получаем список всех FB2 файлов
    fb2_files = []
    for file in os.listdir(directory):
        if file.endswith(".fb2"):
            fb2_files.append(os.path.join(directory, file))

    if not fb2_files:
        print("❌ FB2 файлы не найдены")
        return

    print(f"📊 Найдено FB2 файлов: {len(fb2_files)}")

    # Сортируем файлы по имени
    fb2_files.sort()

    # Обрабатываем каждый файл
    fixed_count = 0
    for filepath in fb2_files:
        if fix_fb2_file(filepath):
            fixed_count += 1
        print()  # Пустая строка для разделения

    print(f"🎯 Обработка завершена!")
    print(f"📊 Всего файлов: {len(fb2_files)}")
    print(f"🔧 Исправлено файлов: {fixed_count}")


def main():
    """Основная функция"""
    print("🚀 Скрипт исправления FB2 файлов")
    print("=" * 50)

    # Проверяем, есть ли аргументы командной строки
    import sys

    if len(sys.argv) > 1:
        target_dir = sys.argv[1]
    else:
        # По умолчанию обрабатываем папку results
        target_dir = "results"

    if os.path.isdir(target_dir):
        fix_all_fb2_in_directory(target_dir)
    elif os.path.isfile(target_dir) and target_dir.endswith(".fb2"):
        # Если указан конкретный файл
        fix_fb2_file(target_dir)
    else:
        print(f"❌ Указанный путь не существует: {target_dir}")
        print("💡 Использование:")
        print("   python fix_existing_fb2.py [путь_к_папке_или_файлу]")
        print("   По умолчанию обрабатывается папка 'results'")


if __name__ == "__main__":
    main()
