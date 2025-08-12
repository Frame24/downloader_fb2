#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Скрипт для проверки, какие главы действительно существуют на сервере
"""

import requests
import time


def check_server_chapters():
    """Проверяет, какие главы существуют на сервере"""

    print("🔍 Проверяем существование глав на сервере...")

    base_url = "https://api.cdnlibs.org/api/manga"
    slug = "133676--guangyin-zhi-wai"
    branch_id = 20720

    # Проверяем проблемные главы
    test_chapters = [
        (172, 3),  # Глава 172, Том 3
        (173, 3),  # Глава 173, Том 3
        (0, 1),  # Глава 0, Том 1
        (440, 5),  # Глава 440, Том 5
        (441, 5),  # Глава 441, Том 5
    ]

    existing_chapters = []
    non_existing_chapters = []

    for chapter_num, volume in test_chapters:
        print(f"\n📄 Проверяем главу {chapter_num} (Том {volume})...")

        try:
            url = f"{base_url}/{slug}/chapter"
            params = {"branch_id": branch_id, "volume": volume, "number": chapter_num}

            response = requests.get(url, params=params, timeout=30)

            if response.status_code == 200:
                data = response.json()
                if data.get("data"):
                    print(f"   ✅ Глава существует")
                    existing_chapters.append((chapter_num, volume))
                else:
                    print(f"   ❌ Глава не найдена (пустые данные)")
                    non_existing_chapters.append((chapter_num, volume))
            elif response.status_code == 404:
                print(f"   ❌ Глава не найдена (404)")
                non_existing_chapters.append((chapter_num, volume))
            elif response.status_code == 500:
                print(f"   ❌ Ошибка сервера (500)")
                non_existing_chapters.append((chapter_num, volume))
            else:
                print(f"   ❌ Неожиданный статус: {response.status_code}")
                non_existing_chapters.append((chapter_num, volume))

        except Exception as e:
            print(f"   ❌ Ошибка при проверке: {e}")
            non_existing_chapters.append((chapter_num, volume))

        # Небольшая задержка между запросами
        time.sleep(1)

    print(f"\n📊 Результаты проверки:")
    print(f"   ✅ Существующие главы: {existing_chapters}")
    print(f"   ❌ Несуществующие главы: {non_existing_chapters}")

    if existing_chapters:
        print(f"\n🔧 Рекомендации:")
        print(
            f"   📥 Скачайте только существующие главы: {len(existing_chapters)} глав"
        )

    return existing_chapters, non_existing_chapters


if __name__ == "__main__":
    check_server_chapters()
