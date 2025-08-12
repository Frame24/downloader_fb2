#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Скрипт для конвертации исходных данных в FB2 главы
"""

import os
import json
import re
from ranobe2fb2.fb2 import build_fb2


def convert_to_fb2():
    """Конвертирует исходные данные в FB2 главы"""

    print("🔄 Конвертируем исходные данные в FB2 главы...")

    # Пути к папкам
    data_dir = "results_chapters/133676--guangyin-zhi-wai"
    chapters_dir = "results_chapters/133676--guangyin-zhi-wai"

    # Создаем временную папку для FB2
    temp_fb2_dir = "temp_fb2_chapters"
    if not os.path.exists(temp_fb2_dir):
        os.makedirs(temp_fb2_dir)

    if not os.path.exists(data_dir):
        print(f"❌ Папка с исходными данными не найдена: {data_dir}")
        return

    # Создаем папку для FB2 глав
    if not os.path.exists(chapters_dir):
        os.makedirs(chapters_dir)

    # Получаем список JSON файлов
    json_files = [f for f in os.listdir(data_dir) if f.endswith(".json")]

    if not json_files:
        print("❌ JSON файлы не найдены!")
        return

    print(f"📊 Найдено JSON файлов: {len(json_files)}")

    successful = 0
    failed = 0

    for json_file in json_files:
        try:
            # Извлекаем номер главы и том из имени файла
            match = re.match(r"(\d+)_Том(\d+)_(.+)\.json", json_file)
            if not match:
                print(f"   ⚠️  Пропускаем файл с неправильным именем: {json_file}")
                continue

            chapter_num = int(match.group(1))
            volume = int(match.group(2))
            chapter_name = match.group(3)

            print(
                f"📄 [{successful + failed + 1}/{len(json_files)}] Конвертируем главу {chapter_num} (Том {volume})..."
            )

            # Читаем JSON данные
            json_path = os.path.join(data_dir, json_file)
            with open(json_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            # Создаем FB2
            fb2_content = build_fb2(data, chapter_number=chapter_num, volume=volume)

            if not fb2_content:
                print(f"   ❌ Не удалось создать FB2 для главы {chapter_num}")
                failed += 1
                continue

            # Сохраняем FB2 во временную папку
            fb2_filename = f"{chapter_num:03d}_Том{volume}_{chapter_name}.fb2"
            fb2_path = os.path.join(temp_fb2_dir, fb2_filename)

            # Проверяем, что fb2_content - это строка или байты
            if isinstance(fb2_content, bytes):
                with open(fb2_path, "wb") as f:
                    f.write(fb2_content)
            else:
                with open(fb2_path, "w", encoding="utf-8") as f:
                    f.write(fb2_content)

            print(f"   ✅ Сохранено: {fb2_filename}")
            successful += 1

        except Exception as e:
            print(f"   ❌ Ошибка при конвертации {json_file}: {e}")
            failed += 1
            continue

    print(f"\n📊 Итоговая статистика:")
    print(f"   ✅ Успешно конвертировано: {successful} глав")
    print(f"   ❌ Ошибок: {failed} глав")

    if successful > 0:
        print(f"\n🎉 FB2 главы успешно созданы!")
        print(f"📁 Файлы сохранены в: {temp_fb2_dir}")
        print(f"💡 Теперь можно переместить их в {chapters_dir}")

    return successful, failed


if __name__ == "__main__":
    convert_to_fb2()
