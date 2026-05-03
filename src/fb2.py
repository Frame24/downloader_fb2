import xml.etree.ElementTree as ET
from xml.dom import minidom
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

    # Обрабатываем изображения
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
            # Разбиваем контент на параграфы по двойным переносам строк
            paragraphs = [p.strip() for p in clean_content.split("\n\n") if p.strip()]
        elif isinstance(content, dict):
            # Если контент - словарь, извлекаем текст более надежно
            clean_content = ""
            if "content" in content:
                for node in content["content"]:
                    if node.get("type") == "paragraph":
                        node_text = ""
                        if "content" in node:
                            for chunk in node.get("content", []):
                                if isinstance(chunk, dict) and "text" in chunk:
                                    chunk_text = chunk.get("text", "")
                                    if chunk_text:
                                        # Иногда API присылает текст кусками (из-за разметки/маркеров),
                                        # и пробел может "потеряться" на границе чанков.
                                        if (
                                            node_text
                                            and node_text[-1].isalnum()
                                            and chunk_text[0].isalnum()
                                        ):
                                            node_text += " "
                                        node_text += chunk_text
                                elif isinstance(chunk, str):
                                    chunk_text = chunk
                                    if chunk_text:
                                        if (
                                            node_text
                                            and node_text[-1].isalnum()
                                            and chunk_text[0].isalnum()
                                        ):
                                            node_text += " "
                                        node_text += chunk_text
                        elif "text" in node:
                            node_text = node.get("text", "")

                        if node_text.strip():
                            clean_content += node_text.strip() + "\n\n"

            # Разбиваем на параграфы
            paragraphs = [p.strip() for p in clean_content.split("\n\n") if p.strip()]
        else:
            paragraphs = []

        # Создаем параграфы в FB2
        for para in paragraphs:
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
    pretty_xml = pretty.toprettyxml(indent="  ", encoding="utf-8")
    
    # Убираем лишние пустые строки между тегами <p>
    if isinstance(pretty_xml, bytes):
        # Убираем две или более пустых строки между </p> и следующим <p>
        pretty_xml = re.sub(rb"</p>\s*\n\s*\n+(\s*)<p>", rb"</p>\n\1<p>", pretty_xml)
        # Убираем две или более пустых строки между любым закрывающим тегом и <p>
        pretty_xml = re.sub(rb">\s*\n\s*\n+(\s*)<p>", rb">\n\1<p>", pretty_xml)
        # Убираем множественные пустые строки подряд (3 и более)
        while b"\n\n\n" in pretty_xml:
            pretty_xml = pretty_xml.replace(b"\n\n\n", b"\n\n")
    else:
        # Убираем две или более пустых строки между </p> и следующим <p>
        pretty_xml = re.sub(r"</p>\s*\n\s*\n+(\s*)<p>", r"</p>\n\1<p>", pretty_xml)
        # Убираем две или более пустых строки между любым закрывающим тегом и <p>
        pretty_xml = re.sub(r">\s*\n\s*\n+(\s*)<p>", r">\n\1<p>", pretty_xml)
        # Убираем множественные пустые строки подряд (3 и более)
        while "\n\n\n" in pretty_xml:
            pretty_xml = pretty_xml.replace("\n\n\n", "\n\n")
    
    return pretty_xml


def deep_copy_element(source_element, target_parent):
    """Рекурсивно копирует элемент и все его дочерние элементы"""
    new_element = ET.SubElement(target_parent, source_element.tag)

    # Копируем текст
    if source_element.text:
        new_element.text = source_element.text

    # Копируем атрибуты
    if source_element.attrib:
        new_element.attrib.update(source_element.attrib)

    # Копируем хвостовой текст
    if source_element.tail:
        new_element.tail = source_element.tail

    # Рекурсивно копируем дочерние элементы
    for child in source_element:
        deep_copy_element(child, new_element)

    return new_element


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
        book_name = book_info.get("display_name", book_info.get("name", "Книга"))
        safe_name = "".join(c for c in book_name if c.isalnum() or c in " -_").rstrip()
        current_time = datetime.now()
        time_str = current_time.strftime("%Y-%m-%d_%H-%M-%S")
        results_dir = "results"
        os.makedirs(results_dir, exist_ok=True)
        base_output = os.path.join(results_dir, f"{safe_name}_{time_str}.fb2")
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

        # Создаем корневой элемент
        root = ET.Element("FictionBook")
        root.set("xmlns:l", "http://www.w3.org/1999/xlink")

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

                # Находим секцию с контентом
                chapter_body = chapter_root.find(".//body")
                if chapter_body is not None:
                    chapter_section = chapter_body.find("section")
                    if chapter_section is not None:
                        # Копируем section в новый body
                        new_section = ET.SubElement(body, "section")

                        # Копируем все элементы из секции главы
                        for element in chapter_section:
                            deep_copy_element(element, new_section)

            except Exception as e:
                print(f"    ❌ Ошибка при обработке {filename}: {e}")
                continue

        # Форматируем и сохраняем объединенный файл
        print("💾 Сохраняем объединенную книгу...")

        rough_string = ET.tostring(root, encoding="utf-8")
        reparsed = minidom.parseString(rough_string)
        pretty_xml = reparsed.toprettyxml(indent="  ", encoding="utf-8")

        # Убираем лишние пустые строки между тегами <p>
        if isinstance(pretty_xml, bytes):
            pretty_xml = re.sub(
                rb"</p>\s*\n\s*\n+(\s*)<p>", rb"</p>\n\1<p>", pretty_xml
            )
            pretty_xml = re.sub(
                rb">\s*\n\s*\n+(\s*)<p>", rb">\n\1<p>", pretty_xml
            )
            while b"\n\n\n" in pretty_xml:
                pretty_xml = pretty_xml.replace(b"\n\n\n", b"\n\n")
        else:
            pretty_xml = re.sub(
                r"</p>\s*\n\s*\n+(\s*)<p>", r"</p>\n\1<p>", pretty_xml
            )
            pretty_xml = re.sub(
                r">\s*\n\s*\n+(\s*)<p>", r">\n\1<p>", pretty_xml
            )
            while "\n\n\n" in pretty_xml:
                pretty_xml = pretty_xml.replace("\n\n\n", "\n\n")

        with open(part_output, "wb") as f:
            f.write(pretty_xml)

        print(f"✅ Объединенная книга сохранена: {part_output}")
        print(f"📊 Всего глав объединено в части: {len(chunk)}")
        created_files.append(part_output)

    # Для обратной совместимости возвращаем первый файл
    return created_files[0] if created_files else None
