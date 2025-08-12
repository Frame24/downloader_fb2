#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Скрипт для объединения всех скачанных глав в одну итоговую книгу
"""

import os
import re
import xml.etree.ElementTree as ET
from datetime import datetime


def merge_complete_book(book_dir: str, output_filename: str = None):
    """Объединяет все главы в одну книгу"""

    print("📚 Объединяем все главы в одну итоговую книгу...")

    # Получаем список всех FB2 файлов
    fb2_files = []
    for file in os.listdir(book_dir):
        if file.endswith(".fb2"):
            fb2_files.append(file)

    if not fb2_files:
        print("❌ FB2 файлы глав не найдены!")
        return None

    print(f"📊 Найдено глав: {len(fb2_files)}")

    # Сортируем файлы по номеру главы и тому
    def extract_sort_key(filename: str):
        # Извлекаем номер главы и том для сортировки
        match = re.match(r"(\d+)_Том(\d+)_(.+)\.fb2", filename)
        if match:
            chapter_num = int(match.group(1))
            volume = int(match.group(2))
            return (volume, chapter_num)
        return (999, 999)  # Для файлов без номера

    fb2_files.sort(key=extract_sort_key)

    # Создаем структуру итоговой книги
    root = ET.Element("FictionBook")
    root.set("xmlns:l", "http://www.w3.org/1999/xlink")

    # Добавляем описание
    description = ET.SubElement(root, "description")
    title_info = ET.SubElement(description, "title-info")

    # Заголовок книги
    book_title = ET.SubElement(title_info, "book-title")
    book_title.text = "За гранью времени (Новелла)"

    # Жанр
    genre = ET.SubElement(title_info, "genre")
    genre.text = "ranobe"

    # Дата
    date = ET.SubElement(title_info, "date")
    date.text = datetime.now().strftime("%Y-%m-%d")

    # Язык
    lang = ET.SubElement(title_info, "lang")
    lang.text = "ru"

    # Создаем тело книги
    body = ET.SubElement(root, "body")

    # Добавляем заголовок книги
    book_section = ET.SubElement(body, "section")
    book_title_elem = ET.SubElement(book_section, "title")
    book_title_elem.text = "За гранью времени (Новелла)"

    # Обрабатываем каждую главу
    total_paragraphs = 0
    successful_chapters = 0

    for i, filename in enumerate(fb2_files, 1):
        print(f"📄 [{i}/{len(fb2_files)}] Обрабатываем: {filename}")

        try:
            # Парсим FB2 файл главы
            filepath = os.path.join(book_dir, filename)
            tree = ET.parse(filepath)
            chapter_root = tree.getroot()

            # Извлекаем название главы
            chapter_name = filename.replace(".fb2", "")
            chapter_name = re.sub(r"^\d+_Том\d+_", "", chapter_name)

            # Создаем секцию для главы
            chapter_section = ET.SubElement(body, "section")

            # Заголовок главы
            chapter_title = ET.SubElement(chapter_section, "title")
            chapter_title.text = f"Глава {i}: {chapter_name}"

            # Ищем все параграфы в главе
            paragraphs = chapter_root.findall(".//p")

            if paragraphs:
                # Добавляем параграфы в главу
                for p in paragraphs:
                    if p.text and p.text.strip():
                        new_p = ET.SubElement(chapter_section, "p")
                        new_p.text = p.text.strip()
                        total_paragraphs += 1

                successful_chapters += 1
                print(f"   ✅ Добавлено параграфов: {len(paragraphs)}")
            else:
                print(f"   ⚠️  Параграфы не найдены")

        except Exception as e:
            print(f"   ❌ Ошибка при обработке {filename}: {e}")
            continue

    # Создаем итоговый файл
    if output_filename is None:
        output_filename = f"За_гранью_времени_полная_книга_{datetime.now().strftime('%Y%m%d_%H%M%S')}.fb2"

    # Форматируем XML
    xml_str = ET.tostring(root, encoding="utf-8", xml_declaration=True)

    # Добавляем отступы для читаемости
    from xml.dom import minidom

    dom = minidom.parseString(xml_str)
    pretty_xml = dom.toprettyxml(indent="  ", encoding="utf-8")

    # Сохраняем итоговую книгу
    with open(output_filename, "wb") as f:
        f.write(pretty_xml)

    print(f"\n🎉 Итоговая книга создана!")
    print(f"📊 Статистика:")
    print(f"   📚 Глав обработано: {successful_chapters}")
    print(f"   📝 Всего параграфов: {total_paragraphs}")
    print(f"📁 Файл: {output_filename}")

    # Показываем размер файла
    file_size = os.path.getsize(output_filename)
    if file_size > 1024 * 1024:
        size_mb = file_size / (1024 * 1024)
        print(f"💾 Размер: {size_mb:.1f} МБ")
    else:
        size_kb = file_size / 1024
        print(f"💾 Размер: {size_kb:.1f} КБ")

    return output_filename


def main():
    # Путь к папке с главами
    book_dir = "results_chapters/133676--guangyin-zhi-wai"

    # Проверяем, что папка существует
    if not os.path.exists(book_dir):
        print(f"❌ Папка {book_dir} не найдена!")
        return

    # Объединяем книгу
    try:
        output_file = merge_complete_book(book_dir)

        if output_file:
            print(f"\n🎯 Полная книга готова!")
            print(f"📁 Файл: {output_file}")
        else:
            print(f"\n❌ Не удалось создать итоговую книгу")

    except Exception as e:
        print(f"❌ Ошибка при объединении книги: {e}")


if __name__ == "__main__":
    main()
