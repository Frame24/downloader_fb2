import xml.etree.ElementTree as ET
import base64
import requests
import re
from datetime import datetime

try:
    # Настройка кодировки для Windows консоли
    from .utils.encoding import setup_console_encoding

    setup_console_encoding()
except Exception:
    pass


FB2_NS = "http://www.gribuser.ru/xml/fictionbook/2.0"
XLINK_NS = "http://www.w3.org/1999/xlink"


def _fb2_root():
    """Корневой FictionBook с пространствами имён, которые ждут читалки."""
    ET.register_namespace("l", XLINK_NS)
    root = ET.Element("FictionBook")
    root.set("xmlns", FB2_NS)
    root.set("xmlns:l", XLINK_NS)
    return root


def _local_tag(el) -> str:
    tag = el.tag if isinstance(el.tag, str) else ""
    return tag.split("}")[-1]


def _serialize_fb2(root) -> bytes:
    """Пишет FB2 без minidom: он подменяет xmlns:l на ns0 и роняет часть читалок."""
    ET.register_namespace("l", XLINK_NS)
    href_clark = f"{{{XLINK_NS}}}href"
    for el in root.iter():
        if href_clark in el.attrib:
            href = el.attrib.pop(href_clark)
            if "l:href" not in el.attrib:
                el.attrib["l:href"] = href
        if _local_tag(el) == "image" and el.text is not None and not el.text.strip():
            el.text = None
        if _local_tag(el) == "binary" and el.text:
            el.text = re.sub(r"\s+", "", el.text)
    try:
        ET.indent(root, space="  ")
    except AttributeError:
        pass
    for el in root.iter():
        if href_clark in el.attrib:
            href = el.attrib.pop(href_clark)
            if "l:href" not in el.attrib:
                el.attrib["l:href"] = href
        if _local_tag(el) == "image" and el.text is not None and not el.text.strip():
            el.text = None
        if _local_tag(el) == "binary" and el.text:
            el.text = re.sub(r"\s+", "", el.text)
    body = ET.tostring(root, encoding="utf-8")
    body = re.sub(rb'\sxmlns:ns\d+="[^"]*"', b"", body)
    return b'<?xml version="1.0" encoding="utf-8"?>\n' + body


def clean_html(html_text):
    """Очищает HTML теги из текста и сохраняет структуру параграфов."""
    if not html_text:
        return ""

    # Заменяем HTML теги параграфов на маркеры
    text = html_text.replace("<p>", "").replace("</p>", "\n\n")
    text = text.replace("<br>", "\n").replace("<br/>", "\n").replace("<br />", "\n")
    text = text.replace("<div>", "").replace("</div>", "\n\n")

    # Обрабатываем заголовки
    text = text.replace("<h1>", "\n\n").replace("</h1>", "\n\n")
    text = text.replace("<h2>", "\n\n").replace("</h2>", "\n\n")
    text = text.replace("<h3>", "\n\n").replace("</h3>", "\n\n")
    text = text.replace("<h4>", "\n\n").replace("</h4>", "\n\n")
    text = text.replace("<h5>", "\n\n").replace("</h5>", "\n\n")
    text = text.replace("<h6>", "\n\n").replace("</h6>", "\n\n")

    # Обрабатываем списки
    text = text.replace("<ul>", "\n").replace("</ul>", "\n")
    text = text.replace("<ol>", "\n").replace("</ol>", "\n")
    text = text.replace("<li>", "\n• ").replace("</li>", "")

    # Обрабатываем блоки кода и цитаты
    text = text.replace("<code>", "`").replace("</code>", "`")
    text = text.replace("<pre>", "\n\n```\n").replace("</pre>", "\n```\n\n")
    text = text.replace("<blockquote>", "\n\n> ").replace("</blockquote>", "\n\n")

    # Обрабатываем горизонтальные линии
    text = text.replace("<hr>", "\n\n" + "-" * 40 + "\n\n")
    text = text.replace("<hr/>", "\n\n" + "-" * 40 + "\n\n")
    text = text.replace("<hr />", "\n\n" + "-" * 40 + "\n\n")

    # Обрабатываем ссылки
    text = re.sub(r'<a[^>]*href="([^"]*)"[^>]*>(.*?)</a>', r"\2 (\1)", text)

    # Обрабатываем изображения (запасной вариант, если тег не вырезали заранее)
    text = re.sub(r'<img[^>]*alt="([^"]*)"[^>]*>', r"[Изображение: \1]", text)
    text = re.sub(r"<img[^>]*>", r"[Изображение]", text)

    # Обрабатываем аббревиатуры и определения
    text = text.replace("<abbr>", "").replace("</abbr>", "")
    text = text.replace("<acronym>", "").replace("</acronym>", "")
    text = text.replace("<dfn>", "").replace("</dfn>", "")

    # Обрабатываем выделение текста
    text = text.replace("<mark>", "**").replace("</mark>", "**")
    text = text.replace("<del>", "~~").replace("</del>", "~~")
    text = text.replace("<ins>", "__").replace("</ins>", "__")

    # Обрабатываем подстрочные и надстрочные индексы
    text = text.replace("<sub>", "₍").replace("</sub>", "₎")
    text = text.replace("<sup>", "⁽").replace("</sup>", "⁾")

    # Обрабатываем цитаты
    text = text.replace("<cite>", '"').replace("</cite>", '"')
    text = text.replace("<q>", '"').replace("</q>", '"')

    # Обрабатываем определения
    text = text.replace("<dt>", "\n• ").replace("</dt>", ":")
    text = text.replace("<dd>", " ").replace("</dd>", "\n")
    text = text.replace("<dl>", "\n").replace("</dl>", "\n")

    # Обрабатываем поля ввода
    text = text.replace("<input>", "[Поле ввода]")
    text = text.replace("<textarea>", "[Текстовая область]")
    text = text.replace("<button>", "[Кнопка]")
    text = text.replace("<select>", "[Выпадающий список]")

    # Обрабатываем метаданные
    text = text.replace("<meta>", "").replace("</meta>", "")
    text = text.replace("<link>", "").replace("</link>", "")
    text = text.replace("<script>", "").replace("</script>", "")
    text = text.replace("<style>", "").replace("</style>", "")

    # Обрабатываем семантические теги
    text = text.replace("<article>", "").replace("</article>", "")
    text = text.replace("<section>", "").replace("</section>", "")
    text = text.replace("<header>", "").replace("</header>", "")
    text = text.replace("<footer>", "").replace("</footer>", "")
    text = text.replace("<nav>", "").replace("</nav>", "")
    text = text.replace("<aside>", "").replace("</aside>", "")
    text = text.replace("<main>", "").replace("</main>", "")

    # Обрабатываем формы
    text = text.replace("<form>", "").replace("</form>", "")
    text = text.replace("<fieldset>", "").replace("</fieldset>", "")
    text = text.replace("<legend>", "").replace("</legend>", "")
    text = text.replace("<label>", "").replace("</label>", "")
    text = text.replace("<optgroup>", "").replace("</optgroup>", "")
    text = text.replace("<option>", "").replace("</option>", "")

    # Обрабатываем мультимедиа
    text = text.replace("<audio>", "[Аудио]").replace("</audio>", "")
    text = text.replace("<video>", "[Видео]").replace("</video>", "")
    text = text.replace("<source>", "").replace("</source>", "")
    text = text.replace("<track>", "").replace("</track>", "")
    text = text.replace("<embed>", "[Встроенный контент]").replace("</embed>", "")
    text = text.replace("<object>", "[Объект]").replace("</object>", "")
    text = text.replace("<param>", "").replace("</param>", "")

    # Обрабатываем интерактивные элементы
    text = text.replace("<details>", "").replace("</details>", "")
    text = text.replace("<summary>", "").replace("</summary>", "")
    text = text.replace("<dialog>", "").replace("</dialog>", "")
    text = text.replace("<menu>", "").replace("</menu>", "")
    text = text.replace("<menuitem>", "").replace("</menuitem>", "")

    # Обрабатываем прогресс и метр
    text = text.replace("<progress>", "[Прогресс]").replace("</progress>", "")
    text = text.replace("<meter>", "[Метр]").replace("</meter>", "")

    # Обрабатываем время и дату
    text = text.replace("<time>", "").replace("</time>", "")
    text = text.replace("<data>", "").replace("</data>", "")

    # Обрабатываем математические элементы
    text = text.replace("<math>", "[Математика]").replace("</math>", "")
    text = text.replace("<svg>", "[SVG]").replace("</svg>", "")
    text = text.replace("<canvas>", "[Canvas]").replace("</canvas>", "")

    # Обрабатываем фреймы
    text = text.replace("<iframe>", "[Встроенная страница]").replace("</iframe>", "")
    text = text.replace("<frame>", "[Фрейм]").replace("</frame>", "")
    text = text.replace("<frameset>", "").replace("</frameset>", "")
    text = text.replace("<noframes>", "").replace("</noframes>", "")

    # Обрабатываем карты изображений
    text = text.replace("<map>", "").replace("</map>", "")
    text = text.replace("<area>", "").replace("</area>", "")

    # Обрабатываем шаблоны
    text = text.replace("<template>", "").replace("</template>", "")
    text = text.replace("<slot>", "").replace("</slot>", "")

    # Обрабатываем веб-компоненты
    text = text.replace("<shadow>", "").replace("</shadow>", "")
    text = text.replace("<content>", "").replace("</content>", "")
    text = text.replace("<element>", "").replace("</element>", "")

    # Обрабатываем микроразметку
    text = text.replace("<microdata>", "").replace("</microdata>", "")
    text = text.replace("<itemscope>", "").replace("</itemscope>", "")
    text = text.replace("<itemtype>", "").replace("</itemtype>", "")
    text = text.replace("<itemprop>", "").replace("</itemprop>", "")

    # Обрабатываем ARIA атрибуты
    text = text.replace("<aria-label>", "").replace("</aria-label>", "")
    text = text.replace("<aria-describedby>", "").replace("</aria-describedby>", "")
    text = text.replace("<aria-hidden>", "").replace("</aria-hidden>", "")

    # Обрабатываем мета-теги
    text = text.replace("<meta charset>", "").replace("</meta>", "")
    text = text.replace("<meta name>", "").replace("</meta>", "")
    text = text.replace("<meta content>", "").replace("</meta>", "")

    # Обрабатываем комментарии
    text = re.sub(r"<!--.*?-->", "", text, flags=re.DOTALL)

    # Обрабатываем CDATA секции
    text = re.sub(r"<!\[CDATA\[.*?\]\]>", "", text, flags=re.DOTALL)

    # Обрабатываем таблицы
    text = text.replace("<table>", "\n\n").replace("</table>", "\n\n")
    text = text.replace("<tr>", "\n").replace("</tr>", "")
    text = text.replace("<td>", " | ").replace("</td>", "")
    text = text.replace("<th>", " | ").replace("</th>", "")

    # Убираем лишние пробелы в таблицах
    text = re.sub(r"\|\s+\|", "| |", text)
    text = re.sub(r"\|\s*$", "|", text, flags=re.MULTILINE)

    # Убираем пустые строки в таблицах
    text = re.sub(r"\n\s*\n\s*\n", "\n\n", text)

    # Убираем остальные HTML теги
    clean = re.compile("<.*?>")
    text = re.sub(clean, "", text)

    # Убираем лишние пробелы, но сохраняем переносы строк
    text = re.sub(r"[ \t]+", " ", text)

    # Убираем пустые строки в начале и конце
    text = text.strip()

    return text


_HARD_BREAK_TYPES = frozenset({"hardBreak", "hard_break"})
_SENTENCE_END_CHARS = ".!?…"
_IMAGE_PREFIX = "__FB2_IMAGE__:"
_IMG_TAG_RE = re.compile(r"<img\b[^>]*>", re.I)
_IMG_SRC_RE = re.compile(
    r"""(?:src|data-src)\s*=\s*['"]([^'"]+)['"]""", re.I
)
_IMAGE_MIME = {
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".png": "image/png",
    ".gif": "image/gif",
    ".webp": "image/webp",
    ".bmp": "image/bmp",
}


def _image_block(ref: str) -> str:
    return f"{_IMAGE_PREFIX}{ref}"


def _is_image_block(block: str) -> bool:
    return isinstance(block, str) and block.startswith(_IMAGE_PREFIX)


def _image_ref(block: str) -> str:
    return block[len(_IMAGE_PREFIX) :] if _is_image_block(block) else ""


def _image_refs_from_pm(node) -> list:
    attrs = node.get("attrs") if isinstance(node.get("attrs"), dict) else {}
    refs = []
    src = attrs.get("src") or node.get("src")
    if src:
        refs.append(str(src))
    images = attrs.get("images") or []
    if isinstance(images, list):
        for item in images:
            if isinstance(item, dict):
                ref = item.get("image") or item.get("src") or item.get("url") or ""
            else:
                ref = str(item or "")
            if ref:
                refs.append(ref)
    return refs


def _html_to_blocks(html_text: str) -> list:
    """Параграфы HTML + картинки на своих местах."""
    urls = []

    def _replace_img(match):
        src_m = _IMG_SRC_RE.search(match.group(0))
        urls.append(src_m.group(1).strip() if src_m else "")
        return f"\n\n{_image_block(str(len(urls) - 1))}\n\n"

    marked = _IMG_TAG_RE.sub(_replace_img, html_text or "")
    clean = clean_html(marked)
    blocks = []
    for part in re.split(r"\n+", clean):
        part = part.strip()
        if not part:
            continue
        if _is_image_block(part):
            try:
                idx = int(_image_ref(part))
            except ValueError:
                continue
            if 0 <= idx < len(urls) and urls[idx]:
                blocks.append(_image_block(urls[idx]))
            continue
        blocks.append(part)
    return blocks


def _attachment_absolute_url(att) -> str:
    url = str((att or {}).get("url") or "").strip()
    if not url:
        return ""
    if url.startswith("//"):
        return "https:" + url
    if url.startswith("/"):
        return "https://ranobelib.me" + url
    if url.startswith(("http://", "https://")):
        return url
    return "https://ranobelib.me/" + url.lstrip("/")


def _resolve_image_url(ref: str, attachments: list) -> str:
    ref = (ref or "").strip()
    if not ref:
        return ""
    key = ref.split("?")[0].rstrip("/").split("/")[-1]
    for att in attachments or []:
        names = {
            str(att.get("name") or ""),
            str(att.get("filename") or ""),
            str(att.get("id") or ""),
            str(att.get("url") or "").split("/")[-1],
        }
        if ref in names or key in names:
            return _attachment_absolute_url(att) or ref
    if ref.startswith("//"):
        return "https:" + ref
    if ref.startswith("/"):
        return "https://ranobelib.me" + ref
    if ref.startswith(("http://", "https://")):
        return ref
    return ""


def _mime_for_url(url: str, content_type: str) -> str:
    ctype = (content_type or "").split(";")[0].strip().lower()
    if ctype.startswith("image/"):
        return ctype
    ext = ""
    path = (url or "").split("?")[0].lower()
    for candidate, mime in _IMAGE_MIME.items():
        if path.endswith(candidate):
            ext = mime
            break
    return ext or "image/jpeg"


def _download_image(url: str):
    """Скачивает картинку. Возвращает (bytes, mime) или None."""
    if not url:
        return None
    try:
        from .client import DEFAULT_API_HEADERS

        headers = dict(DEFAULT_API_HEADERS)
        headers["Accept"] = "image/avif,image/webp,image/apng,image/*,*/*;q=0.8"
        resp = requests.get(url, headers=headers, timeout=30)
        resp.raise_for_status()
        data = resp.content
        mime = _mime_for_url(url, resp.headers.get("content-type", ""))
        if not data or len(data) < 50 or not mime.startswith("image/"):
            return None
        return data, mime
    except Exception:
        return None


def _binary_id(chapter_number, volume, index: int, ref: str) -> str:
    name = ref.split("?")[0].rstrip("/").split("/")[-1] or f"img{index}"
    name = re.sub(r"[^A-Za-z0-9_-]", "_", name)
    ch = re.sub(r"[^A-Za-z0-9_-]", "_", str(chapter_number or "x"))
    vol = re.sub(r"[^A-Za-z0-9_-]", "_", str(volume if volume is not None else "1"))
    return f"img_v{vol}_c{ch}_{index}_{name}"[:120]


def _append_text_chunk(node_text, chunk_text):
    """Добавляет фрагмент текста, восстанавливая пробел на стыке узлов."""
    if not chunk_text:
        return node_text
    if not node_text:
        return chunk_text
    if node_text[-1].isspace() or chunk_text[0].isspace():
        return node_text + chunk_text

    left, right = node_text[-1], chunk_text[0]
    need_space = False
    if left.isalnum() and right.isalnum():
        need_space = True
    elif left in _SENTENCE_END_CHARS and (right.isalnum() or right in "«\"“("):
        need_space = True
    elif left in "»\"”')" and right.isalnum():
        need_space = True

    if need_space:
        return node_text + " " + chunk_text
    return node_text + chunk_text


def _is_hard_break(chunk):
    return isinstance(chunk, dict) and chunk.get("type") in _HARD_BREAK_TYPES


def _inline_text_of(chunk):
    if isinstance(chunk, str):
        return chunk
    if isinstance(chunk, dict):
        chunk_type = chunk.get("type", "")
        if chunk_type == "text" or "text" in chunk:
            return chunk.get("text", "") or ""
    return ""


def _inline_paragraphs(chunks):
    """Режет inline-узлы ProseMirror на абзацы по hardBreak (в т.ч. одиночным)."""
    paragraphs = []
    current = ""
    for chunk in chunks or []:
        if _is_hard_break(chunk):
            text = current.strip()
            if text:
                paragraphs.append(text)
            current = ""
            continue
        if isinstance(chunk, dict) and chunk.get("type") == "image":
            text = current.strip()
            if text:
                paragraphs.append(text)
            current = ""
            for ref in _image_refs_from_pm(chunk):
                paragraphs.append(_image_block(ref))
            continue
        current = _append_text_chunk(current, _inline_text_of(chunk))
    text = current.strip()
    if text:
        paragraphs.append(text)
    return paragraphs


def _extract_inline_text(chunks):
    """Извлекает текст из inline-узлов ProseMirror (paragraph.content)."""
    return "\n".join(_inline_paragraphs(chunks))


def _extract_paragraph_text(node):
    """Извлекает текст из узла paragraph или heading."""
    if "content" in node:
        return _extract_inline_text(node.get("content", []))
    return node.get("text", "")


def _list_item_lines(item):
    """Собирает строки из listItem: параграфы и вложенные блоки."""
    lines = []
    for child in item.get("content", []):
        if not isinstance(child, dict):
            continue
        child_type = child.get("type", "")
        if child_type == "paragraph":
            lines.extend(_inline_paragraphs(child.get("content", [])))
        elif child_type == "image":
            lines.extend(_image_block(ref) for ref in _image_refs_from_pm(child))
        elif child_type in ("bulletList", "orderedList", "blockquote"):
            lines.extend(_blocks_from_node(child))
        else:
            for block in _blocks_from_node(child):
                if block:
                    lines.append(block)
    return lines


def _blocks_from_prefixed_lines(prefix: str, lines: list) -> list:
    """Склеивает текстовые строки списка, картинки оставляет отдельными блоками."""
    blocks = []
    text_lines = []

    def flush():
        if text_lines:
            blocks.append(prefix + "\n".join(text_lines))
            text_lines.clear()

    for line in lines:
        if _is_image_block(line):
            flush()
            blocks.append(line)
        elif line:
            text_lines.append(line)
    flush()
    return blocks


def _blocks_from_node(node):
    """Возвращает список строк-параграфов для одного блочного узла ProseMirror."""
    node_type = node.get("type", "")

    if node_type == "paragraph":
        if "content" in node:
            return _inline_paragraphs(node.get("content", []))
        text = (node.get("text") or "").strip()
        return [text] if text else []

    if node_type == "heading":
        parts = (
            _inline_paragraphs(node.get("content", []))
            if "content" in node
            else [(node.get("text") or "").strip()]
        )
        return [p for p in parts if p]

    if node_type == "image":
        return [_image_block(ref) for ref in _image_refs_from_pm(node)]

    if node_type == "horizontalRule":
        return ["-" * 40]

    if node_type == "bulletList":
        blocks = []
        for item in node.get("content", []):
            if not isinstance(item, dict) or item.get("type") != "listItem":
                continue
            blocks.extend(_blocks_from_prefixed_lines("• ", _list_item_lines(item)))
        return blocks

    if node_type == "orderedList":
        blocks = []
        index = 1
        for item in node.get("content", []):
            if not isinstance(item, dict) or item.get("type") != "listItem":
                continue
            blocks.extend(
                _blocks_from_prefixed_lines(f"{index}. ", _list_item_lines(item))
            )
            index += 1
        return blocks

    if node_type == "blockquote":
        blocks = []
        for child in node.get("content", []):
            blocks.extend(
                _blocks_from_prefixed_lines("> ", _blocks_from_node(child))
            )
        return blocks

    if node_type == "codeBlock":
        text = _extract_paragraph_text(node).strip()
        return [f"```\n{text}\n```"] if text else []

    if "content" in node:
        blocks = []
        for child in node.get("content", []):
            if isinstance(child, dict):
                blocks.extend(_blocks_from_node(child))
        return blocks

    return []


def _blocks_from_prosemirror(content):
    """Извлекает параграфы из ProseMirror-документа (dict с type и content)."""
    if not isinstance(content, dict):
        return []
    blocks = []
    for node in content.get("content", []):
        if isinstance(node, dict):
            blocks.extend(_blocks_from_node(node))
    return blocks


def _is_dotted_number(value) -> bool:
    if value is None or value is False:
        return False
    s = str(value).strip()
    if not s:
        return False
    parts = [p for p in s.split(".") if p != ""]
    return bool(parts) and all(p.isdigit() for p in parts)


def _chapter_heading(volume, chapter_num) -> str:
    """Заголовок секции: «Том X, Глава Y», Y может быть 96.1."""
    has_volume = _is_dotted_number(volume) and float(volume) > 0
    has_chapter = _is_dotted_number(chapter_num)
    if has_chapter:
        # «0.1» оставляем, «0» без дробной части — нет
        parts = [p for p in str(chapter_num).strip().split(".") if p != ""]
        has_chapter = any(int(p) > 0 for p in parts)

    if has_volume and has_chapter:
        return f"Том {volume}, Глава {chapter_num}"
    if has_volume:
        return f"Том {volume}"
    if has_chapter:
        return f"Глава {chapter_num}"
    return "Без названия"


def build_fb2(data, book_info=None, volume=None, chapter_number=None):
    """
    Создает FB2 файл из данных главы.

    Args:
        data: данные главы
        book_info: информация о книге (название, описание и т.д.)
        volume: номер тома (приоритет над data.get("volume"))
        chapter_number: номер главы (приоритет над data.get("number"))
    """
    fb2 = _fb2_root()

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

    # Заголовок главы (Том X, Глава Y) — номер может быть подглавой (96.1)
    title_el = ET.SubElement(main_section, "title")
    title_p = ET.SubElement(title_el, "p")
    title_p.text = _chapter_heading(
        volume if volume is not None else data.get("volume", 1),
        chapter_number if chapter_number is not None else data.get("number", 0),
    )

    # Основной контент главы
    content = data.get("content", "")
    if isinstance(content, str) and content:
        paragraphs = _html_to_blocks(content)
    elif isinstance(content, dict):
        paragraphs = _blocks_from_prosemirror(content)
    else:
        paragraphs = []

    attachments = data.get("attachments") or []
    binaries = []
    seen_urls = set()
    image_index = 0
    volume_info = volume if volume is not None else data.get("volume", 1)
    chapter_num = (
        chapter_number if chapter_number is not None else data.get("number", 0)
    )

    def insert_image(bin_id: str) -> None:
        caption = ET.SubElement(main_section, "p")
        caption.text = "Изображение"
        image_el = ET.SubElement(main_section, "image")
        image_el.set("l:href", f"#{bin_id}")

    def add_image_element(ref: str) -> None:
        nonlocal image_index
        url = _resolve_image_url(ref, attachments)
        if not url:
            return
        if url in seen_urls:
            for bid, stored_url, _mime, _blob in binaries:
                if stored_url == url:
                    insert_image(bid)
                    return
            return
        downloaded = _download_image(url)
        if not downloaded:
            return
        blob, mime = downloaded
        image_index += 1
        bin_id = _binary_id(chapter_num, volume_info, image_index, url)
        seen_urls.add(url)
        binaries.append((bin_id, url, mime, blob))
        insert_image(bin_id)

    for para in paragraphs:
        if not para:
            continue
        if _is_image_block(para):
            add_image_element(_image_ref(para))
            continue
        p = ET.SubElement(main_section, "p")
        p.text = para

    for att in attachments:
        url = _attachment_absolute_url(att)
        if url and url not in seen_urls:
            add_image_element(url)

    for bin_id, _url, mime, blob in binaries:
        bin_el = ET.SubElement(
            fb2,
            "binary",
            {"id": bin_id, "content-type": mime},
        )
        bin_el.text = base64.b64encode(blob).decode("ascii")

    return _serialize_fb2(fb2)


def _find_first(parent, local_name: str):
    for el in parent.iter():
        if _local_tag(el) == local_name:
            return el
    return None


def _find_direct(parent, local_name: str):
    for child in parent:
        if _local_tag(child) == local_name:
            return child
    return None


def deep_copy_element(source_element, target_parent):
    """Рекурсивно копирует элемент и все его дочерние элементы"""
    new_element = ET.SubElement(target_parent, _local_tag(source_element))

    if source_element.text:
        new_element.text = source_element.text

    if source_element.attrib:
        href_clark = f"{{{XLINK_NS}}}href"
        for key, value in source_element.attrib.items():
            local_key = key.split("}")[-1]
            if key == href_clark or local_key == "href" or key == "l:href":
                new_element.attrib["l:href"] = value
            elif local_key in ("xmlns",) or key.startswith("xmlns"):
                continue
            else:
                new_element.attrib[local_key] = value

    if source_element.tail:
        new_element.tail = source_element.tail

    for child in source_element:
        deep_copy_element(child, new_element)

    return new_element


def _copy_section_content(chapter_section, new_section):
    """Копирует секцию и чинит старую разметку картинок/заголовков."""
    for element in chapter_section:
        tag = _local_tag(element)
        if tag == "title" and (element.text or "").strip() and len(list(element)) == 0:
            title_el = ET.SubElement(new_section, "title")
            title_p = ET.SubElement(title_el, "p")
            title_p.text = element.text.strip()
            continue
        if (
            tag == "p"
            and len(list(element)) == 1
            and _local_tag(element[0]) == "image"
            and not (element.text or "").strip()
        ):
            deep_copy_element(element[0], new_section)
            continue
        deep_copy_element(element, new_section)


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

    print(f"\n📚 Объединяем главы в книгу...")

    # Получаем список всех FB2 файлов
    fb2_files = []
    for file in os.listdir(book_dir):
        if file.endswith(".fb2"):
            fb2_files.append(file)

    if not fb2_files:
        print("❌ FB2 файлы глав не найдены!")
        return None

    # Сортируем файлы численно: сначала по тому, затем по номеру главы (с учетом подглав).
    # Имена файлов создаются в формате:
    #   "<safe_chapter_num>_Том<volume>_... .fb2"
    # где safe_chapter_num использует "_" вместо "." (например, "10_2" для "10.2").
    def extract_sort_key(filename: str):
        m = re.match(r"(.+?)_Том(\d+)_", filename)
        if not m:
            return (10**9, 10**9, 10**9, filename)

        chapter_part = m.group(1)
        try:
            volume = int(m.group(2))
        except ValueError:
            volume = 10**9

        chapter_part = chapter_part.replace("_", ".")
        parts = [p for p in chapter_part.split(".") if p != ""]
        nums = []
        for p in parts:
            if p.isdigit():
                nums.append(int(p))
            else:
                # На всякий случай: если номер содержит мусор — оставляем как есть в хвосте.
                return (volume, 10**9, 10**9, filename)

        # Нормализуем длину ключа: (volume, main, sub, subsub, ..., filename)
        # Для обычных глав будет sub=0.
        main = nums[0] if nums else 10**9
        sub = nums[1] if len(nums) > 1 else 0
        sub2 = nums[2] if len(nums) > 2 else 0
        return (volume, main, sub, sub2, filename)

    fb2_files.sort(key=extract_sort_key)
    total_chapters = len(fb2_files)
    print(f"📊 Найдено глав для объединения: {total_chapters}")

    # Генерируем базовое имя выходного файла, если не указано
    if output_file is None:
        from .client import safe_filename as _safe_filename

        book_name = book_info.get("display_name", book_info.get("name", "Книга"))
        safe_name = _safe_filename(book_name)
        results_dir = "results"
        os.makedirs(results_dir, exist_ok=True)
        base_output = os.path.join(results_dir, f"{safe_name}.fb2")
    else:
        base_output = output_file

    # Разбиваем на части по 400 глав максимум
    max_per_book = 400
    chunks = [
        fb2_files[i : i + max_per_book] for i in range(0, total_chapters, max_per_book)
    ]

    created_files = []

    for idx, chunk in enumerate(chunks, start=1):
        # Определяем имя файла для части
        if len(chunks) == 1:
            part_output = base_output
            print("📦 Объединяем в одну книгу (глав ≤ 400)")
        else:
            base, ext = os.path.splitext(base_output)
            part_output = f"{base}_Часть{idx}{ext}"
            print(f"📦 Объединяем часть {idx}/{len(chunks)} (глав: {len(chunk)})")

        root = _fb2_root()

        # Создаем description
        description = ET.SubElement(root, "description")
        title_info = ET.SubElement(description, "title-info")

        # Название книги (если частей несколько — добавляем номер части)
        book_title = ET.SubElement(title_info, "book-title")
        base_title = book_info.get(
            "display_name", book_info.get("name", "Без названия")
        )
        if len(chunks) == 1:
            book_title.text = base_title
        else:
            book_title.text = f"{base_title} (Часть {idx})"

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
            if len(chunks) == 1:
                p.text = book_info.get("description")
            else:
                p.text = f"{book_info.get('description')} (Часть {idx} из {len(chunks)})"

        # Создаем body
        body = ET.SubElement(root, "body")

        # Обрабатываем каждую главу части
        for i, filename in enumerate(chunk, 1):
            print(f"  📄 [{i}/{len(chunk)}] Обрабатываем: {filename}")

            filepath = os.path.join(book_dir, filename)

            try:
                # Парсим FB2 файл главы
                tree = ET.parse(filepath)
                chapter_root = tree.getroot()

                chapter_body = _find_first(chapter_root, "body")
                if chapter_body is not None:
                    chapter_section = _find_direct(chapter_body, "section")
                    if chapter_section is not None:
                        new_section = ET.SubElement(body, "section")
                        _copy_section_content(chapter_section, new_section)

                for bin_el in chapter_root:
                    if _local_tag(bin_el) == "binary":
                        deep_copy_element(bin_el, root)

            except Exception as e:
                print(f"    ❌ Ошибка при обработке {filename}: {e}")
                continue

        print("💾 Сохраняем объединенную книгу...")

        with open(part_output, "wb") as f:
            f.write(_serialize_fb2(root))

        print(f"✅ Объединенная книга сохранена: {part_output}")
        print(f"📊 Всего глав объединено в части: {len(chunk)}")
        created_files.append(part_output)

    # Для обратной совместимости возвращаем первый файл
    return created_files[0] if created_files else None
