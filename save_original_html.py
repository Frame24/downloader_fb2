#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Скрипт для сохранения исходного HTML из главы для отладки
"""

import json
import os
from ranobe2fb2.client import fetch_chapter


def save_original_html():
    """Сохраняет исходный HTML из главы для отладки"""

    # Параметры для получения главы
    slug = "133676--guangyin-zhi-wai"
    branch_id = 20720  # Это нужно уточнить
    volume = 1
    chapter_num = 30  # Глава "Кровавые сумерки 2"

    print(f"📥 Получаем исходный HTML главы {chapter_num}...")

    try:
        # Получаем данные главы
        data = fetch_chapter(slug, branch_id, volume, chapter_num)

        if not data:
            print("❌ Не удалось получить данные главы")
            return

        # Сохраняем полные данные главы в JSON
        json_filename = f"debug_chapter_{chapter_num}_full_data.json"
        with open(json_filename, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        print(f"💾 Полные данные главы сохранены в: {json_filename}")

        # Сохраняем только HTML контент
        if "content" in data:
            html_filename = f"debug_chapter_{chapter_num}_content.html"
            with open(html_filename, "w", encoding="utf-8") as f:
                f.write(data["content"])

            print(f"💾 HTML контент главы сохранен в: {html_filename}")

            # Показываем статистику
            content = data["content"]
            paragraph_count = content.count("<p data-paragraph-index")
            print(f"📊 В HTML найдено параграфов: {paragraph_count}")

            # Показываем первые несколько параграфов
            import re

            paragraphs = re.findall(
                r'<p[^>]*data-paragraph-index="([^"]*)"[^>]*>(.*?)</p>',
                content,
                re.DOTALL,
            )

            print(f"\n📝 Первые 5 параграфов:")
            for i, (index, text) in enumerate(paragraphs[:5], 1):
                clean_text = re.sub(r"<[^>]+>", "", text).strip()
                print(
                    f"   {index}: {clean_text[:100]}{'...' if len(clean_text) > 100 else ''}"
                )

        else:
            print("⚠️ В данных главы нет поля 'content'")

    except Exception as e:
        print(f"❌ Ошибка при получении главы: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    save_original_html()
