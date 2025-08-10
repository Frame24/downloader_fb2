import xml.etree.ElementTree as ET
from xml.dom import minidom
import base64
import requests
import re


def clean_html(html_text):
    """Очищает HTML теги из текста."""
    # Убираем HTML теги
    clean = re.compile("<.*?>")
    text = re.sub(clean, "", html_text)
    # Убираем лишние пробелы и переносы строк
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def build_fb2(data, book_info=None, volume=None, chapter_number=None):
    """
    Создает FB2 файл из данных главы.

    Args:
        data: данные главы
        book_info: информация о книге (название, описание и т.д.)
        volume: номер тома (приоритет над data.get("volume"))
        chapter_number: номер главы (приоритет над data.get("number"))
    """
    fb2 = ET.Element("FictionBook")
    fb2.set("xmlns:l", "http://www.w3.org/1999/xlink")

    # — description —
    description = ET.SubElement(fb2, "description")
    title_info = ET.SubElement(description, "title-info")

    # Жанр
    genre = ET.SubElement(title_info, "genre")
    genre.text = "ranobe"

    # Название книги (берем из book_info, если есть, иначе из названия главы)
    book_title = ET.SubElement(title_info, "book-title")
    if book_info and book_info.get("display_name"):
        book_title.text = book_info.get("display_name")
    elif book_info and book_info.get("name"):
        book_title.text = book_info.get("name")
    else:
        book_title.text = data.get("name", "Без названия")

    # Дата
    date = ET.SubElement(title_info, "date")
    date.text = "2025-07-10"

    # Язык
    lang = ET.SubElement(title_info, "lang")
    lang.text = "ru"

    # Описание книги (если есть)
    if book_info and book_info.get("description"):
        annotation = ET.SubElement(title_info, "annotation")
        p = ET.SubElement(annotation, "p")
        p.text = book_info.get("description")

    # — body —
    body = ET.SubElement(fb2, "body")

    # Создаем основную секцию
    main_section = ET.SubElement(body, "section")

    # Заголовок главы (Том X, Глава Y)
    title_info = ET.SubElement(main_section, "title")

    # Формируем заголовок как "Том X, Глава Y"
    # Используем переданные параметры, если они есть, иначе берем из data
    volume_info = volume if volume is not None else data.get("volume", 1)
    chapter_num = (
        chapter_number if chapter_number is not None else data.get("number", 0)
    )

    if volume_info and str(volume_info).isdigit() and int(volume_info) > 0:
        if chapter_num and str(chapter_num).isdigit() and int(chapter_num) > 0:
            title_info.text = f"Том {volume_info}, Глава {chapter_num}"
        else:
            title_info.text = f"Том {volume_info}"
    elif chapter_num and str(chapter_num).isdigit() and int(chapter_num) > 0:
        title_info.text = f"Глава {chapter_num}"
    else:
        title_info.text = "Без названия"

    # Основной контент главы
    content = data.get("content", "")
    if content:
        if isinstance(content, str):
            # Если контент - строка, очищаем HTML
            clean_content = clean_html(content)
            # Разбиваем контент на параграфы
            paragraphs = clean_content.split("\n\n")
        elif isinstance(content, dict):
            # Если контент - словарь, извлекаем текст
            clean_content = ""
            if "content" in content:
                for node in content["content"]:
                    if node.get("type") == "paragraph":
                        node_text = ""
                        for chunk in node.get("content", []):
                            node_text += chunk.get("text", "")
                        clean_content += node_text + "\n\n"
            paragraphs = clean_content.split("\n\n")
        else:
            paragraphs = []

        for para in paragraphs:
            para = para.strip()
            if para:
                p = ET.SubElement(main_section, "p")
                p.text = para

    # — attachments —
    for att in data.get("attachments", []):
        url = att.get("url")
        if not url:
            continue

        # Проверяем и исправляем URL изображения
        if url.startswith("/"):
            # Если URL относительный, добавляем базовый домен
            url = "https://ranobelib.me" + url
        elif not url.startswith(("http://", "https://")):
            # Если URL без схемы, пропускаем
            continue

        try:
            img_data = requests.get(url, timeout=30).content
            bin_el = ET.SubElement(
                fb2,
                "binary",
                {
                    "id": str(att.get("id")),
                    "content-type": att.get("mime_type", "image/jpeg"),
                },
            )
            bin_el.text = base64.b64encode(img_data).decode("ascii")
        except Exception as e:
            # Если не удалось загрузить изображение, пропускаем его
            print(f"    → Предупреждение: не удалось загрузить изображение {url}: {e}")
            continue

    raw = ET.tostring(fb2, encoding="utf-8")
    pretty = minidom.parseString(raw)
    return pretty.toprettyxml(indent="  ", encoding="utf-8")
