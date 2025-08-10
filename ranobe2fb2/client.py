import re
import requests
import time

API_BASE = "https://api.cdnlibs.org/api/manga"
TIMEOUT = 30  # таймаут в секундах для API запросов
RETRY_DELAY = 2  # задержка между повторными попытками


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


def fetch_book_info(slug: str, max_retries: int = 3):
    """
    Возвращает информацию о книге (название, описание и т.д.).
    """
    for attempt in range(max_retries):
        try:
            resp = requests.get(f"{API_BASE}/{slug}", timeout=TIMEOUT)
            resp.raise_for_status()
            return resp.json().get("data", {})
        except requests.exceptions.Timeout:
            print(
                f"  → Таймаут при получении информации о книге (попытка {attempt + 1}/{max_retries})"
            )
            if attempt < max_retries - 1:
                time.sleep(RETRY_DELAY)
        except requests.exceptions.RequestException as e:
            print(
                f"  → Ошибка сети при получении информации о книге: {e} (попытка {attempt + 1}/{max_retries})"
            )
            if attempt < max_retries - 1:
                time.sleep(RETRY_DELAY)
        except Exception as e:
            print(
                f"  → Неожиданная ошибка при получении информации о книге: {e} (попытка {attempt + 1}/{max_retries})"
            )
            if attempt < max_retries - 1:
                time.sleep(RETRY_DELAY)

    print("  → Не удалось получить информацию о книге после всех попыток")
    return {}


def fetch_chapters_list(slug: str, max_retries: int = 3):
    """
    Возвращает список (номер, branch_id, volume) для всех глав.
    """
    for attempt in range(max_retries):
        try:
            resp = requests.get(f"{API_BASE}/{slug}/chapters", timeout=TIMEOUT)
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
                # Получаем номер тома
                volume = ch.get("volume", 1)
                result.append((num, branch_id, volume))
            return sorted(result, key=lambda x: x[0])
        except requests.exceptions.Timeout:
            print(
                f"  → Таймаут при получении списка глав (попытка {attempt + 1}/{max_retries})"
            )
            if attempt < max_retries - 1:
                time.sleep(RETRY_DELAY)
        except requests.exceptions.RequestException as e:
            print(
                f"  → Ошибка сети при получении списка глав: {e} (попытка {attempt + 1}/{max_retries})"
            )
            if attempt < max_retries - 1:
                time.sleep(RETRY_DELAY)
        except Exception as e:
            print(
                f"  → Неожиданная ошибка при получении списка глав: {e} (попытка {attempt + 1}/{max_retries})"
            )
            if attempt < max_retries - 1:
                time.sleep(RETRY_DELAY)

    print("  → Не удалось получить список глав после всех попыток")
    return []


def fetch_chapter(
    slug: str, branch_id: int, volume: int, number: int, max_retries: int = 3
):
    """
    Возвращает dict с JSON-полем 'data' для одной главы.
    """
    for attempt in range(max_retries):
        try:
            resp = requests.get(
                f"{API_BASE}/{slug}/chapter",
                params={"branch_id": branch_id, "volume": volume, "number": number},
                timeout=TIMEOUT,
            )
            resp.raise_for_status()
            return resp.json().get("data", {})
        except requests.exceptions.Timeout:
            print(
                f"    → Таймаут при получении главы {number} (попытка {attempt + 1}/{max_retries})"
            )
            if attempt < max_retries - 1:
                time.sleep(RETRY_DELAY)
        except requests.exceptions.RequestException as e:
            print(
                f"    → Ошибка сети при получении главы {number}: {e} (попытка {attempt + 1}/{max_retries})"
            )
            if attempt < max_retries - 1:
                time.sleep(RETRY_DELAY)
        except Exception as e:
            print(
                f"    → Неожиданная ошибка при получении главы {number}: {e} (попытка {attempt + 1}/{max_retries})"
            )
            if attempt < max_retries - 1:
                time.sleep(RETRY_DELAY)

    print(f"    → Не удалось получить главу {number} после всех попыток")
    return {}
