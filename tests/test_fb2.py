from ranobe2fb2.fb2 import build_fb2


def test_simple_fb2(tmp_path):
    data = {
        "id": 1,
        "number": "1",
        "volume": "1",
        "name": "Тест",
        "created_at": "2025-06-12T00:00:00.000Z",
        "content": {"content": [{"type": "paragraph", "content": [{"text": "Hello"}]}]},
        "attachments": [],
    }
    xml = build_fb2(data).decode("utf-8")
    assert "<FictionBook" in xml
    assert "<p>Hello</p>" in xml
    assert "Тест" in xml
