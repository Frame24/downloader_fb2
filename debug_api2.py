import requests
import json

# Получаем сырые данные от API
resp = requests.get('https://api.cdnlibs.org/api/manga/40906--worm/chapters', timeout=30)
data = resp.json()
arr = data.get("data", [])

print(f"Total items in API response: {len(arr)}")

# Соберем все уникальные комбинации number + volume
chapters_map = {}
for ch in arr:
    number_str = ch.get("number", "")
    volume = ch.get("volume", "1")
    chapter_id = ch.get("id")

    key = f"{volume}_{number_str}"
    if key not in chapters_map:
        chapters_map[key] = chapter_id

print(f"Unique volume_number combinations: {len(chapters_map)}")

# Покажем первые 50
print("\nFirst 50 unique combinations:")
for i, (key, cid) in enumerate(list(chapters_map.items())[:50]):
    volume, number = key.split("_", 1)
    print(f"{i+1}. Volume {volume}, Chapter {number}, ID {cid}")

print(f"\nTotal unique chapters: {len(chapters_map)}")

# Теперь проверим, сколько глав в каждом томе
volumes_count = {}
for key in chapters_map.keys():
    volume = key.split("_")[0]
    volumes_count[volume] = volumes_count.get(volume, 0) + 1

print("\nChapters per volume:")
for vol in sorted(volumes_count.keys(), key=int):
    print(f"Volume {vol}: {volumes_count[vol]} chapters")


