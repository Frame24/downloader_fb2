import xml.etree.ElementTree as ET
from xml.dom import minidom
import base64
import requests
import re
from datetime import datetime


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
    current_time = datetime.now()
    date.text = current_time.strftime("%Y-%m-%d")

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


def merge_chapters_to_book(book_dir: str, book_info: dict, output_file: str = None):
    """
    Объединяет все FB2 файлы глав в один файл книги.

    Args:
        book_dir: папка с главами
        book_info: информация о книге
        output_file: путь к выходному файлу (если None, генерируется автоматически)

    Returns:
        str: путь к созданному файлу
    """
    import os
    import re
    from xml.dom import minidom

    print(f"\n📚 Объединяем главы в книгу...")

    # Получаем список всех FB2 файлов
    fb2_files = []
    for file in os.listdir(book_dir):
        if file.endswith(".fb2"):
            fb2_files.append(file)

    if not fb2_files:
        print("❌ FB2 файлы глав не найдены!")
        return None

    # Сортируем файлы по номеру главы
    def extract_chapter_number(filename: str) -> int:
        match = re.match(r"(\d+)", filename)
        if match:
            return int(match.group(1))
        return 0

    fb2_files.sort(key=extract_chapter_number)
    print(f"📊 Найдено глав для объединения: {len(fb2_files)}")

    # Генерируем имя выходного файла, если не указано
    if output_file is None:
        book_name = book_info.get("display_name", book_info.get("name", "Книга"))
        # Очищаем название от недопустимых символов для имени файла
        safe_name = "".join(c for c in book_name if c.isalnum() or c in " -_").rstrip()

        # Добавляем дату и время скачивания
        current_time = datetime.now()
        time_str = current_time.strftime("%Y-%m-%d_%H-%M-%S")

        # Сохраняем в папку results/ вместо book_dir
        results_dir = "results"
        os.makedirs(results_dir, exist_ok=True)
        output_file = os.path.join(results_dir, f"{safe_name}_{time_str}.fb2")

    # Создаем корневой элемент
    root = ET.Element("FictionBook")
    root.set("xmlns:l", "http://www.w3.org/1999/xlink")

    # Создаем description
    description = ET.SubElement(root, "description")
    title_info = ET.SubElement(description, "title-info")

    # Название книги
    book_title = ET.SubElement(title_info, "book-title")
    book_title.text = book_info.get(
        "display_name", book_info.get("name", "Без названия")
    )

    # Жанр
    genre = ET.SubElement(title_info, "genre")
    genre.text = "ranobe"

    # Дата
    date = ET.SubElement(title_info, "date")
    current_time = datetime.now()
    date.text = current_time.strftime("%Y-%m-%d")

    # Язык
    lang = ET.SubElement(title_info, "lang")
    lang.text = "ru"

    # Описание книги (если есть)
    if book_info.get("description"):
        annotation = ET.SubElement(title_info, "annotation")
        p = ET.SubElement(annotation, "p")
        p.text = book_info.get("description")

    # Создаем body
    body = ET.SubElement(root, "body")

    # Обрабатываем каждую главу
    for i, filename in enumerate(fb2_files, 1):
        print(f"  📄 [{i}/{len(fb2_files)}] Обрабатываем: {filename}")

        filepath = os.path.join(book_dir, filename)

        try:
            # Парсим FB2 файл главы
            tree = ET.parse(filepath)
            chapter_root = tree.getroot()

            # Находим секцию с контентом
            chapter_body = chapter_root.find(".//body")
            if chapter_body is not None:
                chapter_section = chapter_body.find("section")
                if chapter_section is not None:
                    # Копируем section в новый body
                    new_section = ET.SubElement(body, "section")

                    # Копируем все элементы из секции главы
                    for element in chapter_section:
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

                    # Добавляем разделитель между главами (кроме последней)
                    if i < len(fb2_files):
                        separator = ET.SubElement(body, "section")
                        separator.set("id", f"separator_{i}")

                        # Добавляем пустую строку как разделитель
                        empty_p = ET.SubElement(separator, "p")
                        empty_p.text = ""

        except Exception as e:
            print(f"    ❌ Ошибка при обработке {filename}: {e}")
            continue

    # Форматируем и сохраняем объединенный файл
    print("💾 Сохраняем объединенную книгу...")

    # Создаем красивый XML
    rough_string = ET.tostring(root, encoding="utf-8")
    reparsed = minidom.parseString(rough_string)
    pretty_xml = reparsed.toprettyxml(indent="  ", encoding="utf-8")

    # Убираем лишние пустые строки
    pretty_xml = pretty_xml.replace(b"\n\n", b"\n")

    with open(output_file, "wb") as f:
        f.write(pretty_xml)

    print(f"✅ Объединенная книга сохранена: {output_file}")
    print(f"📊 Всего глав объединено: {len(fb2_files)}")

    return output_file
