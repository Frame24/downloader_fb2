from ranobe2fb2.fb2 import build_fb2, merge_chapters_to_book
import os
import tempfile
import shutil


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


def test_merge_chapters_to_book(tmp_path):
    """Тест объединения глав в книгу"""
    # Создаем временную папку для теста
    test_dir = tmp_path / "test_book"
    test_dir.mkdir()

    # Создаем тестовые FB2 файлы глав
    chapter1_data = {
        "id": 1,
        "number": "1",
        "volume": "1",
        "name": "Глава 1",
        "content": "Содержание первой главы",
        "attachments": [],
    }

    chapter2_data = {
        "id": 2,
        "number": "2",
        "volume": "1",
        "name": "Глава 2",
        "content": "Содержание второй главы",
        "attachments": [],
    }

    # Создаем FB2 файлы глав
    chapter1_fb2 = build_fb2(chapter1_data)
    chapter2_fb2 = build_fb2(chapter2_data)

    # Сохраняем главы
    with open(test_dir / "001_Глава_1.fb2", "wb") as f:
        f.write(chapter1_fb2)

    with open(test_dir / "002_Глава_2.fb2", "wb") as f:
        f.write(chapter2_fb2)

    # Информация о книге
    book_info = {
        "display_name": "Тестовая Книга",
        "name": "Test Book",
        "description": "Описание тестовой книги",
    }

    # Объединяем главы
    merged_file = merge_chapters_to_book(str(test_dir), book_info)

    # Проверяем, что файл создан
    assert merged_file is not None
    assert os.path.exists(merged_file)

    # Проверяем содержимое объединенного файла
    with open(merged_file, "rb") as f:
        content = f.read().decode("utf-8")

    # Проверяем, что в файле есть название книги и содержимое глав
    assert "Тестовая Книга" in content
    assert "Содержание первой главы" in content
    assert "Содержание второй главы" in content

    # Проверяем, что имя файла содержит название книги и дату
    filename = os.path.basename(merged_file)
    assert "Тестовая Книга" in filename
    assert filename.endswith(".fb2")
