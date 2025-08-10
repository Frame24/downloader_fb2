import pytest
from ranobe2fb2.client import extract_info, fetch_chapters_list, fetch_chapter
import requests


def test_extract_list():
    url = "https://ranobelib.me/ru/book/183707--dao-of-the-bizarre-immortal?section=chapters"
    slug, mode, bid, chap = extract_info(url)
    assert slug.startswith("183707")
    assert mode == "list"
    assert bid is None and chap is None


def test_extract_single():
    url = "https://ranobelib.me/ru/183707--dao/read/v1/c193?bid=20720"
    slug, mode, bid, chap = extract_info(url)
    assert slug == "183707--dao"
    assert mode == "single"
    assert bid == 20720 and chap == 193


def test_fetch_chapters_list(monkeypatch):
    # подменяем ответ
    sample = [
        {"number": "1", "branches": [{"id": 10}]},
        {"number": "2", "branches": [{"id": 20}]},
    ]

    def mock_get(url, timeout=None):
        return type(
            "R",
            (object,),
            {"raise_for_status": lambda s: None, "json": lambda s: {"data": sample}},
        )()

    monkeypatch.setattr(requests, "get", mock_get)
    lst = fetch_chapters_list("any-slug")
    assert lst == [(1, 10, 1), (2, 20, 1)]


def test_fetch_chapter(monkeypatch):
    sample = {"id": 123, "number": "5", "content": {}}

    def mock_get(url, params=None, timeout=None):
        return type(
            "R",
            (object,),
            {"raise_for_status": lambda s: None, "json": lambda s: {"data": sample}},
        )()

    monkeypatch.setattr(requests, "get", mock_get)
    data = fetch_chapter("slug", 10, 1, 5)
    assert data["id"] == 123
