#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from src.fb2 import (
    _append_text_chunk,
    _blocks_from_prosemirror,
    _chapter_heading,
    _html_to_blocks,
    _image_ref,
    _inline_paragraphs,
    _is_image_block,
    build_fb2,
)


def test_append_space_after_period_before_letter():
    assert _append_text_chunk("Текст текст.", "Текст дальше") == "Текст текст. Текст дальше"


def test_append_space_between_words():
    assert _append_text_chunk("жирный", "курсив") == "жирный курсив"


def test_append_keeps_punctuation_glued_to_word():
    assert _append_text_chunk("слово", ".") == "слово."
    assert _append_text_chunk("слово", ",") == "слово,"


def test_hard_breaks_become_separate_paragraphs():
    chunks = [
        {"type": "text", "text": "Первый абзац."},
        {"type": "hardBreak"},
        {"type": "hardBreak"},
        {"type": "text", "text": "Второй абзац."},
        {"type": "hardBreak"},
        {"type": "text", "text": "Третий."},
    ]
    assert _inline_paragraphs(chunks) == ["Первый абзац.", "Второй абзац.", "Третий."]


def test_snake_case_hard_break():
    chunks = [
        {"type": "text", "text": "A"},
        {"type": "hard_break"},
        {"type": "text", "text": "B"},
    ]
    assert _inline_paragraphs(chunks) == ["A", "B"]


def test_prosemirror_doc_with_single_paragraph_and_breaks():
    content = {
        "type": "doc",
        "content": [
            {
                "type": "paragraph",
                "content": [
                    {"type": "hardBreak"},
                    {"type": "text", "text": "Хотя бонусы были хороши."},
                    {"type": "hardBreak"},
                    {"type": "hardBreak"},
                    {"type": "text", "text": "Увидев бонусы, сердце забилось."},
                ],
            }
        ],
    }
    blocks = _blocks_from_prosemirror(content)
    assert blocks == [
        "Хотя бонусы были хороши.",
        "Увидев бонусы, сердце забилось.",
    ]


def test_marked_chunks_do_not_glue_sentences():
    content = {
        "type": "doc",
        "content": [
            {
                "type": "paragraph",
                "content": [
                    {"type": "text", "text": "Обычный текст."},
                    {
                        "type": "text",
                        "text": "Жирное продолжение.",
                        "marks": [{"type": "bold"}],
                    },
                ],
            }
        ],
    }
    assert _blocks_from_prosemirror(content) == [
        "Обычный текст. Жирное продолжение."
    ]


def test_fb2_emits_separate_p_tags():
    data = {
        "name": "Глава",
        "volume": 1,
        "number": 1,
        "content": {
            "type": "doc",
            "content": [
                {
                    "type": "paragraph",
                    "content": [
                        {"type": "text", "text": "Раз."},
                        {"type": "hardBreak"},
                        {"type": "hardBreak"},
                        {"type": "text", "text": "Два."},
                    ],
                }
            ],
        },
        "attachments": [],
    }
    fb2 = build_fb2(data, chapter_number="1", volume=1)
    text = fb2.decode("utf-8") if isinstance(fb2, bytes) else fb2
    assert text.count("<p>Раз.</p>") == 1
    assert text.count("<p>Два.</p>") == 1


def test_subchapter_heading_keeps_dotted_number():
    assert _chapter_heading(1, 96) == "Том 1, Глава 96"
    assert _chapter_heading(1, "96.1") == "Том 1, Глава 96.1"
    assert _chapter_heading(1, "96.2") == "Том 1, Глава 96.2"
    assert _chapter_heading("1", "51.6") == "Том 1, Глава 51.6"


def test_fb2_title_includes_subchapter():
    data = {"name": "x", "volume": 1, "number": "96.1", "content": "", "attachments": []}
    fb2 = build_fb2(data, chapter_number="96.1", volume=1)
    text = fb2.decode("utf-8") if isinstance(fb2, bytes) else fb2
    assert "<title>" in text
    assert "<p>Том 1, Глава 96.1</p>" in text
    assert "xmlns:ns0" not in text
    assert 'xmlns="http://www.gribuser.ru/xml/fictionbook/2.0"' in text
    assert 'xmlns:l="http://www.w3.org/1999/xlink"' in text


def test_folder_name_is_rus_title_and_id():
    from src.client import cover_url_from_payload, folder_name_for_book, safe_filename

    assert folder_name_for_book("Рай Реинкарнации", "42087") == "Рай Реинкарнации_42087"
    assert safe_filename("Рай Реинкарнации") == "Рай Реинкарнации"
    assert cover_url_from_payload(
        {
            "cover": {
                "filename": "56761e0c-1134-4b63-80c6-658a747c980f",
                "thumbnail": "https://cover.cdnlibs.org/thumb.jpg",
                "default": "https://cover.cdnlibs.org/full.jpg",
                "md": "https://cover.cdnlibs.org/full.jpg",
            }
        }
    ) == "https://cover.cdnlibs.org/full.jpg"
    assert cover_url_from_payload({"cover": {"thumbnail": "https://x/t.jpg"}}) == ""


def test_refresh_cover_replaces_stale_url(tmp_path, monkeypatch):
    from src import client as client_mod
    from src.client import load_book_meta, save_book_meta, refresh_cover_in_meta

    save_book_meta(
        str(tmp_path),
        {
            "display_name": "Рай Реинкарнации",
            "id": "42087",
            "slug": "42087--reincarnation-paradise",
            "cover_url": "https://cover.cdnlibs.org/old.jpg",
        },
    )
    monkeypatch.setattr(
        client_mod,
        "fetch_book_info",
        lambda slug, cookies=None, auth_token=None: {
            "display_name": "Рай Реинкарнации",
            "id": "42087",
            "cover_url": "https://cover.cdnlibs.org/new.jpg",
            "description": "",
        },
    )
    url = refresh_cover_in_meta(
        str(tmp_path),
        slug="42087--reincarnation-paradise",
        announce=False,
    )
    assert url == "https://cover.cdnlibs.org/new.jpg"
    assert load_book_meta(str(tmp_path))["cover_url"] == url


def test_html_keeps_images_in_order():
    html = (
        "<p>До картинки.</p>"
        '<img src="https://example.com/a.jpg" />'
        "<p>Между.</p>"
        '<img data-src="/uploads/b.png" />'
        "<p>После.</p>"
    )
    blocks = _html_to_blocks(html)
    assert blocks[0] == "До картинки."
    assert _is_image_block(blocks[1])
    assert _image_ref(blocks[1]) == "https://example.com/a.jpg"
    assert blocks[2] == "Между."
    assert _image_ref(blocks[3]) == "/uploads/b.png"
    assert blocks[4] == "После."


def test_prosemirror_inline_image():
    content = {
        "type": "doc",
        "content": [
            {
                "type": "paragraph",
                "content": [
                    {"type": "text", "text": "До."},
                    {
                        "type": "image",
                        "attrs": {"src": "https://example.com/x.jpg"},
                    },
                    {"type": "text", "text": "После."},
                ],
            }
        ],
    }
    blocks = _blocks_from_prosemirror(content)
    assert blocks[0] == "До."
    assert _image_ref(blocks[1]) == "https://example.com/x.jpg"
    assert blocks[2] == "После."


def test_binary_id_has_no_dots():
    from src.fb2 import _binary_id

    bid = _binary_id(2, 1, 1, "https://ranobelib.me/uploads/cover/wqkj1jqnsta_xU7c.jpg")
    assert "." not in bid
    assert bid.startswith("img_v1_c2_1_")


def test_fb2_image_is_block_level_not_inside_empty_p(monkeypatch):
    from src import fb2 as fb2_mod

    monkeypatch.setattr(
        fb2_mod,
        "_download_image",
        lambda url: (b"\xff\xd8" + b"x" * 60, "image/jpeg"),
    )
    data = {
        "name": "Глава",
        "volume": 1,
        "number": 2,
        "content": '<p>До.</p><img src="https://example.com/pic.jpg" /><p>После.</p>',
        "attachments": [],
    }
    text = build_fb2(data, chapter_number=2, volume=1).decode("utf-8")
    assert "xmlns:ns0" not in text
    assert "<p>Изображение</p>" in text
    assert not re.search(r"<p>\s*<image", text)
    assert re.search(r"<p>Изображение</p>\s*<image l:href=\"#img_", text)
    assert "<binary " in text
    assert 'id="img_v1_c2_1_' in text


def test_merge_unwraps_old_image_in_empty_p(tmp_path):
    from src.fb2 import merge_chapters_to_book

    chapter = """<?xml version="1.0" encoding="utf-8"?>
<FictionBook xmlns:ns0="http://www.w3.org/1999/xlink" xmlns:l="http://www.w3.org/1999/xlink">
  <description><title-info><book-title>x</book-title></title-info></description>
  <body>
    <section>
      <title>Том 1, Глава 2</title>
      <p>До.</p>
      <p>Изображение</p>
      <p><image l:href="#img_v1_c2_1_pic_jpg"/></p>
      <p>После.</p>
    </section>
  </body>
  <binary id="img_v1_c2_1_pic_jpg" content-type="image/jpeg">QQ==</binary>
</FictionBook>
"""
    (tmp_path / "2_Том1_Глава_2.fb2").write_text(chapter, encoding="utf-8")
    out = tmp_path / "book.fb2"
    merge_chapters_to_book(str(tmp_path), {"display_name": "Тест"}, str(out))
    text = out.read_text(encoding="utf-8")
    assert "xmlns:ns0" not in text
    assert not re.search(r"<p>\s*<image", text)
    assert '<image l:href="#img_v1_c2_1_pic_jpg"' in text
    assert "<title>" in text and "<p>Том 1, Глава 2</p>" in text
    assert 'id="img_v1_c2_1_pic_jpg"' in text


def test_merge_adds_coverpage(tmp_path, monkeypatch):
    from src import fb2 as fb2_mod
    from src.fb2 import merge_chapters_to_book

    jpeg = b"\xff\xd8" + b"y" * 60
    monkeypatch.setattr(
        fb2_mod, "_download_image", lambda url: (jpeg, "image/jpeg")
    )
    chapter = """<?xml version="1.0" encoding="utf-8"?>
<FictionBook>
  <description><title-info><book-title>x</book-title></title-info></description>
  <body><section><title><p>Том 1, Глава 1</p></title><p>Текст.</p></section></body>
</FictionBook>
"""
    (tmp_path / "1_Том1_Глава_1.fb2").write_text(chapter, encoding="utf-8")
    out = tmp_path / "book.fb2"
    merge_chapters_to_book(
        str(tmp_path),
        {
            "display_name": "Рай Реинкарнации",
            "cover_url": "https://cover.cdnlibs.org/full.jpg",
        },
        str(out),
    )
    text = out.read_text(encoding="utf-8")
    assert "<coverpage>" in text
    assert '<image l:href="#cover"' in text
    assert 'id="cover"' in text
    assert 'content-type="image/jpeg"' in text
    cover_file = tmp_path / "cover.jpg"
    assert cover_file.exists()
    assert cover_file.read_bytes() == jpeg
