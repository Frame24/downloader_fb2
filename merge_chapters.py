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
    print(f"Найдено файлов глав: {len(fb2_files)}")

    # Создаем корневой элемент
    root = ET.Element("FictionBook")
    root.set("xmlns:l", "http://www.w3.org/1999/xlink")

    # Создаем описание книги
    description = ET.SubElement(root, "description")
    title_info = ET.SubElement(description, "title-info")

    # Извлекаем название книги из имени папки
    book_name = os.path.basename(book_dir)
    book_title = ET.SubElement(title_info, "book-title")
    book_title.text = book_name.replace("--", " - ").replace("-", " ")

    genre = ET.SubElement(title_info, "genre")
    genre.text = "ranobe"

    lang = ET.SubElement(title_info, "lang")
    lang.text = "ru"

    # Создаем тело книги
    body = ET.SubElement(root, "body")

    # Обрабатываем каждую главу
    for i, filename in enumerate(fb2_files, 1):
        print(f"[{i}/{len(fb2_files)}] Обрабатываем: {filename}")

        filepath = os.path.join(book_dir, filename)

        try:
            # Парсим FB2 файл главы
            tree = ET.parse(filepath)
            chapter_root = tree.getroot()

            # Ищем секцию с контентом
            chapter_body = chapter_root.find(".//body")
            if chapter_body is not None:
                # Копируем все секции из главы
                for section in chapter_body.findall("section"):
                    # Создаем новую секцию в основном файле
                    new_section = ET.SubElement(body, "section")

                    # Копируем заголовок
                    title = section.find("title")
                    if title is not None:
                        new_title = ET.SubElement(new_section, "title")
                        # Копируем содержимое заголовка
                        for child in title:
                            new_child = ET.SubElement(new_title, child.tag)
                            if child.text:
                                new_child.text = child.text
                            if child.attrib:
                                new_child.attrib.update(child.attrib)

                    # Копируем все параграфы и другие элементы
                    for element in section:
                        if (
                            element.tag != "title"
                        ):  # Пропускаем заголовок, так как уже обработали
                            new_element = ET.SubElement(new_section, element.tag)
                            if element.text:
                                new_element.text = element.text
                            if element.attrib:
                                new_element.attrib.update(element.attrib)
                            # Рекурсивно копируем вложенные элементы
                            for child in element:
                                new_child = ET.SubElement(new_element, child.tag)
                                if child.text:
                                    new_child.text = child.text
                                if child.attrib:
                                    new_child.attrib.update(child.attrib)

        except Exception as e:
            print(f"  → Ошибка при обработке {filename}: {e}")
            continue

    # Форматируем и сохраняем объединенный файл
    print("Сохраняем объединенный файл...")

    # Создаем красивый XML
    rough_string = ET.tostring(root, encoding="utf-8")
    reparsed = minidom.parseString(rough_string)
    pretty_xml = reparsed.toprettyxml(indent="  ", encoding="utf-8")

    # Убираем лишние пустые строки
    pretty_xml = pretty_xml.replace(b"\n\n", b"\n")

    with open(output_file, "wb") as f:
        f.write(pretty_xml)

    print(f"✅ Объединенный файл сохранен: {output_file}")


if __name__ == "__main__":
    book_dir = "results/195040--advent-of-the-three-calamities"
    output_file = "results/195040--advent-of-the-three-calamities_полная_книга.fb2"

    merge_fb2_files(book_dir, output_file)
