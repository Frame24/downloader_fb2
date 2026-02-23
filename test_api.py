import requests
import json

# Проверяем структуру ответа API
resp = requests.get('https://api.cdnlibs.org/api/manga/40906--worm/chapters', timeout=30)
data = resp.json()

print('Keys in response:', list(data.keys()))
if 'data' in data:
    print(f'Items in data: {len(data["data"])}')
    if data['data']:
        print('First item:')
        print(json.dumps(data['data'][0], indent=2, ensure_ascii=False)[:500])

print()
print('Checking pagination:')
total_chapters = 0
for page in range(1, 10):
    resp = requests.get(f'https://api.cdnlibs.org/api/manga/40906--worm/chapters?page={page}', timeout=30)
    data = resp.json()
    count = len(data.get('data', []))
    total_chapters += count
    print(f'Page {page}: {count} chapters (total so far: {total_chapters})')
    if count == 0 or count < 50:  # Предполагаем, что страница содержит максимум 50 глав
        break


