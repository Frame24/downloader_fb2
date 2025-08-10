#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import xml.etree.ElementTree as ET
from xml.dom import minidom
import re


def extract_chapter_number(filename: str) -> int:
    """
    Извлекает номер главы из имени файла.
    """
    match = re.match(r"(\d+)", filename)
    if match:
        return int(match.group(1))
    return 0


def merge_fb2_files(book_dir: str, output_file: str):
    """
    Объединяет все FB2 файлы глав в один файл.
    """
    print(f"Объединяем главы из папки: {book_dir}")

    # Получаем список всех FB2 файлов
    fb2_files = []
    for file in os.listdir(book_dir):
        if file.endswith(".fb2"):
            fb2_files.append(file)

    if not fb2_files:
        print("FB2 файлы не найдены!")
        return

    # Сортируем файлы по номеру главы
    fb2_files.sort(key=extract_chapter_number)
    print(f"Найдено {len(fb2_files)} глав для объединения")

    # Читаем первый файл для получения базовой структуры
    first_file = os.path.join(book_dir, fb2_files[0])
    print(f"Базовый файл: {fb2_files[0]}")

    try:
        tree = ET.parse(first_file)
        root = tree.getroot()

        # Создаем новый корневой элемент
        new_root = ET.Element("FictionBook")
        new_root.set("xmlns:l", "http://www.w3.org/1999/xlink")

        # Копируем description из первого файла
        description = root.find("description")
        if description is not None:
            new_root.append(description)

        # Создаем body
        body = ET.SubElement(new_root, "body")

        # Обрабатываем каждый файл
        for i, filename in enumerate(fb2_files):
            print(f"Обрабатываем {filename}...")

            filepath = os.path.join(book_dir, filename)
            try:
                chapter_tree = ET.parse(filepath)
                chapter_root = chapter_tree.getroot()

                # Находим body и section
                chapter_body = chapter_root.find("body")
                if chapter_body is not None:
                    chapter_section = chapter_body.find("section")
                    if chapter_section is not None:
                        # Копируем section в новый body
                        body.append(chapter_section)

                        # Добавляем разделитель между главами (кроме последней)
                        if i < len(fb2_files) - 1:
                            separator = ET.SubElement(body, "section")
                            separator.set("id", f"separator_{i}")
                            separator.set("name", "Разделитель")

                            # Добавляем пустую строку как разделитель
                            empty_p = ET.SubElement(separator, "p")
                            empty_p.text = ""

            except Exception as e:
                print(f"  → Ошибка при обработке {filename}: {e}")
                continue

        # Создаем красивый XML
        xml_str = ET.tostring(new_root, encoding="unicode")
        dom = minidom.parseString(xml_str)
        pretty_xml = dom.toprettyxml(indent="  ", encoding="utf-8")

        # Сохраняем объединенный файл
        with open(output_file, "wb") as f:
            f.write(pretty_xml)

        print(f"\n✅ Объединение завершено!")
        print(f"📁 Файл сохранен: {output_file}")

        # Показываем статистику
        print(f"📊 Всего глав объединено: {len(fb2_files)}")

    except Exception as e:
        print(f"❌ Ошибка при объединении: {e}")


if __name__ == "__main__":
    book_dir = "results/116902--is-this-hero-for-real"
    output_file = "results/116902--is-this-hero-for-real_полная_книга.fb2"

    merge_fb2_files(book_dir, output_file)
