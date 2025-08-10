import re
import requests

API_BASE = "https://api.cdnlibs.org/api/manga"


def extract_info(url: str):
    """
    Разбирает URL пользователя.
    Возвращает (slug, mode, branch_id, chap_number).
    """
    # Список глав
    m = re.search(r"/book/([^/?]+)", url)
    if m:
        return m.group(1), "list", None, None

    # Одна глава
    m2 = re.search(r"/read/v1/c(\d+)", url)
    bid = re.search(r"bid=(\d+)", url)
    slug_m = re.search(r"/ru/([^/]+)/read", url)
    if m2 and bid and slug_m:
        return slug_m.group(1), "single", int(bid.group(1)), int(m2.group(1))

    raise ValueError(f"URL не распознан: {url}")


def fetch_chapters_list(slug: str):
    """
    Возвращает список (номер, branch_id) для всех глав.
    """
    resp = requests.get(f"{API_BASE}/{slug}/chapters")
    resp.raise_for_status()
    arr = resp.json().get("data", [])
    result = []
    for ch in arr:
        try:
            num = int(ch.get("number", ""))
        except ValueError:
            continue
        branches = ch.get("branches") or []
        if not branches:
            continue
        # Используем id из branches вместо branch_id
        branch_id = branches[0].get("id")
        if branch_id is None:
            continue
        result.append((num, branch_id))
    return sorted(result, key=lambda x: x[0])


def fetch_chapter(slug: str, branch_id: int, volume: int, number: int):
    """
    Возвращает dict с JSON-полем 'data' для одной главы.
    """
    resp = requests.get(
        f"{API_BASE}/{slug}/chapter",
        params={"branch_id": branch_id, "volume": volume, "number": number},
    )
    resp.raise_for_status()
    return resp.json().get("data", {})
