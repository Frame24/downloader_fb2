from ranobe2fb2.client import extract_info, fetch_chapters_list, fetch_chapter
from ranobe2fb2.fb2 import build_fb2
import json

try:
    url = "https://ranobelib.me/ru/book/183707--dao-of-the-bizarre-immortal?section=chapters"
    print(f"Extracting info from URL: {url}")
    slug, mode, bid, chap = extract_info(url)
    print(f"Slug: {slug}, mode: {mode}")
    all_ch = fetch_chapters_list(slug)
    print(f"Total chapters found: {len(all_ch)}")
    nums = [n for n, _ in all_ch]
    branch_m = {n: b for n, b in all_ch}
    to_dl = nums[:1]  # Только первая глава для отладки

    for n in to_dl:
        b = branch_m[n]
        print(f"Downloading chapter {n} (branch {b})…")
        data = fetch_chapter(slug, b, volume=1, number=n)

        # Отладочная информация
        print(f"Chapter data keys: {list(data.keys())}")
        print(f"Content type: {type(data.get('content'))}")
        if isinstance(data.get("content"), str):
            print(f"Content preview: {data.get('content')[:200]}...")
        elif isinstance(data.get("content"), dict):
            print(
                f"Content structure: {json.dumps(data.get('content'), indent=2, ensure_ascii=False)[:500]}..."
            )

        slug_ch = str(data.get("slug") or data.get("id") or n)
        fname = f"{slug}_vol{data.get('volume')}_ch{slug_ch}.fb2"
        fb2 = build_fb2(data)
        with open(fname, "wb") as f:
            f.write(fb2)
        print(f"  → Saved: {fname}")
except Exception as e:
    import traceback

    print("ERROR:", e)
    traceback.print_exc()
