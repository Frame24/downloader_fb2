import pytest
import requests
from ranobe2fb2.client import extract_info, fetch_chapters_list, fetch_chapter


def test_book_parsing(monkeypatch):
    # Mock response for the book chapters list
    book_url = "https://ranobelib.me/ru/book/183707--dao-of-the-bizarre-immortal?section=chapters&ui=6052250"
    expected_slug = "183707--dao-of-the-bizarre-immortal"
    expected_response = {
        "data": [
            {
                "id": 123456,
                "model": "chapter",
                "volume": "1",
                "number": "1",
                "branches": [{"id": 20720}],
            },
            {
                "id": 123457,
                "model": "chapter",
                "volume": "1",
                "number": "2",
                "branches": [{"id": 20720}],
            },
        ]
    }

    def mock_get(url, timeout=None):
        if url == f"https://api.cdnlibs.org/api/manga/{expected_slug}/chapters":
            return type(
                "MockResponse",
                (object,),
                {
                    "json": lambda self: expected_response,
                    "raise_for_status": lambda self: None,
                },
            )()
        raise ValueError("Unexpected URL: " + url)

    monkeypatch.setattr(requests, "get", mock_get)

    slug, mode, bid, chap = extract_info(book_url)
    assert slug == expected_slug
    assert mode == "list"
    chapters = fetch_chapters_list(slug)
    assert chapters == [(1, 20720, "1"), (2, 20720, "1")]


def test_chapter_parsing(monkeypatch):
    # Mock response for a specific chapter
    chapter_url = "https://ranobelib.me/ru/183707--dao-of-the-bizarre-immortal/read/v1/c193?bid=20720&ui=6052250"
    expected_slug = "183707--dao-of-the-bizarre-immortal"
    expected_response = {
        "data": {
            "id": 654321,
            "model": "chapter",
            "volume": "1",
            "number": "193",
            "name": "Название главы",
            "branch_id": 20720,
            "manga_id": 183707,
            "created_at": "2023-06-22T20:38:44.000000Z",
            "content": {
                "type": "doc",
                "content": [
                    {
                        "type": "paragraph",
                        "content": [
                            {"type": "text", "text": "Текст первого абзаца главы…"}
                        ],
                    }
                ],
            },
            "attachments": [
                {"id": 999, "url": "https://…/image.jpg", "mime_type": "image/jpeg"}
            ],
        }
    }

    def mock_get(url, params=None, timeout=None):
        if url == f"https://api.cdnlibs.org/api/manga/{expected_slug}/chapter":
            return type(
                "MockResponse",
                (object,),
                {
                    "json": lambda self: expected_response,
                    "raise_for_status": lambda self: None,
                },
            )()
        raise ValueError("Unexpected URL: " + url)

    monkeypatch.setattr(requests, "get", mock_get)

    slug, mode, bid, chap = extract_info(chapter_url)
    assert slug == expected_slug
    assert mode == "single"
    chapter_data = fetch_chapter(slug, 20720, 1, 193)
    assert chapter_data["id"] == 654321
    assert chapter_data["name"] == "Название главы"
    assert (
        chapter_data["content"]["content"][0]["content"][0]["text"]
        == "Текст первого абзаца главы…"
    )
