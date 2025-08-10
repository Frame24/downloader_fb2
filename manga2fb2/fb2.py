import xml.etree.ElementTree as ET
from xml.dom import minidom
import base64
import requests
import re


def clean_html(html_text):
    """
    Извлекает чистый текст из HTML-разметки.
    """
    if not html_text:
        return ""

    # Убираем HTML-теги, оставляя только текст
    # Заменяем <p> на переносы строк
    text = re.sub(r"<p[^>]*>", "\n", html_text)
    # Убираем все остальные HTML-теги
    text = re.sub(r"<[^>]+>", "", text)
    # Убираем лишние пробелы и переносы
    text = re.sub(r"\n\s*\n", "\n\n", text)
    text = text.strip()

    return text


def build_fb2(data: dict) -> bytes:
    """
    Собирает FB2-документ из JSON 'data' главы.
    Возвращает байты XML.
    """
    fb2 = ET.Element("FictionBook", {"xmlns:l": "http://www.w3.org/1999/xlink"})

    # — description —
    desc = ET.SubElement(fb2, "description")
    ti = ET.SubElement(desc, "title-info")
    ET.SubElement(ti, "genre").text = "manga"
    ET.SubElement(ti, "book-title").text = (
        data.get("name") or f"Chapter {data['number']}"
    )
    ET.SubElement(ti, "date").text = data.get("created_at", "")[:10]
    ET.SubElement(ti, "lang").text = "ru"

    # — body —
    body = ET.SubElement(fb2, "body")
    sec = ET.SubElement(body, "section")
    title = ET.SubElement(sec, "title")
    ET.SubElement(title, "p").text = (
        f"Volume {data.get('volume')}, Chapter {data.get('number')}"
    )

    # Обрабатываем content - может быть строкой или словарем
    content = data.get("content", {})
    if isinstance(content, str):
        # Если content - HTML-строка, извлекаем чистый текст
        clean_text = clean_html(content)
        # Разбиваем на параграфы по переносам строк
        paragraphs = clean_text.split("\n")
        for para in paragraphs:
            if para.strip():
                p = ET.SubElement(sec, "p")
                p.text = para.strip()
    elif isinstance(content, dict):
        # Если content - словарь, обрабатываем структурированно
        for node in content.get("content", []):
            if node.get("type") == "paragraph":
                p = ET.SubElement(sec, "p")
                p.text = "".join(
                    chunk.get("text", "") for chunk in node.get("content", [])
                )

    # — attachments —
    for att in data.get("attachments", []):
        url = att.get("url")
        if not url:
            continue
        img_data = requests.get(url).content
        bin_el = ET.SubElement(
            fb2,
            "binary",
            {
                "id": str(att.get("id")),
                "content-type": att.get("mime_type", "image/jpeg"),
            },
        )
        bin_el.text = base64.b64encode(img_data).decode("ascii")

    raw = ET.tostring(fb2, encoding="utf-8")
    pretty = minidom.parseString(raw)
    return pretty.toprettyxml(indent="  ", encoding="utf-8")
