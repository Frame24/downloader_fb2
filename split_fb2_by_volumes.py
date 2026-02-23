#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Разбор уже собранной FB2-книги по томам и частям (максимум 400 глав в файле).

Использование:

  python split_fb2_by_volumes.py "output/Книга_177465--changjiacmul-sogro/Книга_177465--changjiacmul-sogro_2026-01-17_14-17-29.fb2"
"""

import sys
import re
from pathlib import Path
import xml.etree.ElementTree as ET
from xml.dom import minidom
from datetime import datetime


def deep_copy_element(source_element: ET.Element, target_parent: ET.Element) -> ET.Element:
    """Рекурсивно копирует элемент и все его дочерние элементы."""
    new_element = ET.SubElement(target_parent, source_element.tag, source_element.attrib)
    new_element.text = source_element.text
    new_element.tail = source_element.tail
    for child in source_element:
        deep_copy_element(child, new_element)
    return new_element


def extract_volume_and_chapter(section: ET.Element) -> tuple[int | None, str | None]:
    """
    Пытается вытащить (том, глава) из текста title внутри <section>.
    Ожидаемый формат: "Том X, Глава Y" (как генерирует build_fb2).
    """
    title_el = section.find("title")
    if title_el is None:
        return None, None

    # Текст может лежать или в самом <title>, или в первом <p> внутри.
    text = title_el.text or ""
    if not text:
        first_p = title_el.find("p")
        if first_p is not None and first_p.text:
            text = first_p.text

    if not text:
        return None, None

    m = re.search(r"Том\s+(\d+)\s*,\s*Глава\s+([\d\.]+)", text)
    if not m:
        return None, None

    try:
        vol = int(m.group(1))
    except ValueError:
        vol = None
    chapter = m.group(2)
    return vol, chapter


def pretty_xml_bytes(root: ET.Element) -> bytes:
    """Форматирует XML и убирает лишние пустые строки между <p>."""
    rough = ET.tostring(root, encoding="utf-8")
    dom = minidom.parseString(rough)
    pretty = dom.toprettyxml(indent="  ", encoding="utf-8")

    # Убираем лишние пустые строки, как в fb2.py
    if isinstance(pretty, bytes):
        pretty = re.sub(rb"</p>\s*\n\s*\n+(\s*)<p>", rb"</p>\n\1<p>", pretty)
        pretty = re.sub(rb">\s*\n\s*\n+(\s*)<p>", rb">\n\1<p>", pretty)
        while b"\n\n\n" in pretty:
            pretty = pretty.replace(b"\n\n\n", b"\n\n")
    return pretty


def split_fb2_by_volumes(input_path: Path) -> None:
    """Основная логика разбора одной FB2 по томам и частям."""
    if not input_path.exists():
        print(f"Файл не найден: {input_path}")
        return

    print(f"Разбираем книгу: {input_path}")

    tree = ET.parse(str(input_path))
    root = tree.getroot()

    body = root.find("body")
    if body is None:
        print("В файле нет <body>")
        return

    sections = list(body.findall("section"))
    if not sections:
        print("В файле нет секций глав (<section>)")
        return

    print(f"Найдено секций (глав): {len(sections)}")

    # Группируем по томам
    volumes: dict[int, list[ET.Element]] = {}
    unknown_sections: list[ET.Element] = []

    for sec in sections:
        vol, chap = extract_volume_and_chapter(sec)
        if vol is None:
            unknown_sections.append(sec)
            continue
        volumes.setdefault(vol, []).append(sec)

    if unknown_sections:
        print(f"Секций без распознанного тома: {len(unknown_sections)} (будут проигнорированы)")

    # Базовое имя и директория для сохранения
    out_dir = input_path.parent
    base_name = input_path.stem  # без .fb2

    # Достаём описание книги из оригинального description/title-info, если есть
    description_el = root.find("description")
    title_info_el = description_el.find("title-info") if description_el is not None else None
    base_title = None
    base_annotation = None
    if title_info_el is not None:
        bt = title_info_el.find("book-title")
        if bt is not None and bt.text:
            base_title = bt.text
        ann = title_info_el.find("annotation")
        if ann is not None:
            # Берём текст из первого <p>, если есть
            p = ann.find("p")
            if p is not None and p.text:
                base_annotation = p.text

    if not base_title:
        base_title = base_name

    max_per_book = 400

    for vol_num in sorted(volumes.keys()):
        vol_sections = volumes[vol_num]
        print(f"Том {vol_num}: глав {len(vol_sections)}")

        # Разбиваем том на части по 400 глав
        chunks = [
            vol_sections[i : i + max_per_book]
            for i in range(0, len(vol_sections), max_per_book)
        ]

        for idx, chunk in enumerate(chunks, start=1):
            # Имя файла
            safe_title = "".join(c for c in base_title if c.isalnum() or c in " -_").rstrip()

            # Если том один и часть одна — максимально простой суффикс
            if len(volumes) == 1 and len(chunks) == 1:
                out_name = f"{safe_title}.fb2"
            else:
                if len(chunks) == 1:
                    out_name = f"{safe_title}_Том{vol_num}.fb2"
                else:
                    out_name = f"{safe_title}_Том{vol_num}_Часть{idx}.fb2"

            out_file = out_dir / out_name

            print(
                f"  Том {vol_num}, часть {idx}/{len(chunks)} "
                f"(глав: {len(chunk)}) -> {out_file.name}"
            )

            # Собираем новый FictionBook для этой части
            new_root = ET.Element("FictionBook")
            new_root.set("xmlns:l", "http://www.w3.org/1999/xlink")

            # description/title-info
            new_desc = ET.SubElement(new_root, "description")
            new_title_info = ET.SubElement(new_desc, "title-info")

            bt_el = ET.SubElement(new_title_info, "book-title")
            if len(chunks) == 1:
                bt_el.text = f"{base_title} – Том {vol_num}"
            else:
                bt_el.text = f"{base_title} – Том {vol_num}, Часть {idx}"

            genre_el = ET.SubElement(new_title_info, "genre")
            genre_el.text = "ranobe"

            date_el = ET.SubElement(new_title_info, "date")
            date_el.text = datetime.now().strftime("%Y-%m-%d")

            lang_el = ET.SubElement(new_title_info, "lang")
            lang_el.text = "ru"

            if base_annotation:
                ann_el = ET.SubElement(new_title_info, "annotation")
                p_el = ET.SubElement(ann_el, "p")
                if len(chunks) == 1:
                    p_el.text = base_annotation
                else:
                    p_el.text = f"{base_annotation} (Том {vol_num}, часть {idx})"

            # body
            new_body = ET.SubElement(new_root, "body")
            for sec in chunk:
                new_section = ET.SubElement(new_body, "section")
                for child in sec:
                    deep_copy_element(child, new_section)

            # Сохраняем
            xml_bytes = pretty_xml_bytes(new_root)
            with open(out_file, "wb") as f:
                f.write(xml_bytes)

            print(f"    Сохранено: {out_file}")

    print("Разбор по томам завершён.")


def main() -> None:
    if len(sys.argv) < 2:
        print(
            "Использование:\n"
            "  python split_fb2_by_volumes.py \"path/to/book.fb2\""
        )
        sys.exit(1)

    input_path = Path(sys.argv[1])
    split_fb2_by_volumes(input_path)


if __name__ == "__main__":
    main()

