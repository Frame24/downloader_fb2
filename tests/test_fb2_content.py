#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from src.fb2 import (
    _append_text_chunk,
    _blocks_from_prosemirror,
    _chapter_heading,
    _inline_paragraphs,
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
    assert "Том 1, Глава 96.1" in text


def test_folder_name_is_rus_title_and_id():
    from src.client import folder_name_for_book, safe_filename

    assert folder_name_for_book("Рай Реинкарнации", "42087") == "Рай Реинкарнации_42087"
    assert safe_filename("Рай Реинкарнации") == "Рай Реинкарнации"
