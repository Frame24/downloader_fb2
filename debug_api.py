import requests
import json

# Получаем сырые данные от API
resp = requests.get('https://api.cdnlibs.org/api/manga/40906--worm/chapters', timeout=30)
data = resp.json()
arr = data.get("data", [])

print(f"Total items in API response: {len(arr)}")

# Посмотрим на первые 50 элементов
print("\nFirst 50 items:")
for i, ch in enumerate(arr[:50]):
    number_str = ch.get("number", "")
    chapter_id = ch.get("id")
    branches = ch.get("branches", [])
    print(f"Item {i}: number='{number_str}', id={chapter_id}, branches_count={len(branches)}")

# Имитируем логику из fetch_chapters_list
result = []
seen_chapters = set()

for i, ch in enumerate(arr):
    try:
        number_str = ch.get("number", "")
        if "." in number_str:
            main_num = int(number_str.split(".")[0])
            full_number = number_str
        else:
            main_num = int(number_str)
            full_number = number_str
    except (ValueError, IndexError):
        continue

    if full_number in seen_chapters:
        continue
    seen_chapters.add(full_number)

    branches = ch.get("branches") or []
    if not branches:
        continue

    chapter_id = ch.get("id")
    if chapter_id is None:
        continue

    volume = ch.get("volume", 1)
    result.append((full_number, chapter_id, volume))

print(f"\nFinal result count: {len(result)}")
print("All unique chapter numbers:")
for num, cid, vol in sorted(result, key=lambda x: x[0]):
    print(f"  {num}")
