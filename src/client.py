import re
import time
import requests
from typing import Optional, Dict

# Настройка кодировки для Windows консоли
from .utils.encoding import setup_console_encoding
setup_console_encoding()

API_BASE = "https://api.cdnlibs.org/api/manga"
TIMEOUT = 30  # таймаут в секундах для API запросов
RETRY_DELAY = 2  # задержка между повторными попытками
ERROR_TIMEOUT = 10  # таймаут после ошибок в секундах


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


def fetch_book_info(slug: str, max_retries: int = 3, cookies: Optional[Dict[str, str]] = None):
    """
    Возвращает информацию о книге (название, описание и т.д.).
    Получает информацию из списка глав, так как прямой endpoint не работает.
    
    Args:
        slug: Slug книги
        max_retries: Максимальное количество попыток
        cookies: Словарь с cookies для авторизации (опционально)
    """
    for attempt in range(max_retries):
        try:
            # Получаем информацию из списка глав
            resp = requests.get(
                f"{API_BASE}/{slug}/chapters",
                timeout=TIMEOUT,
                cookies=cookies
            )
            resp.raise_for_status()
            chapters_data = resp.json().get("data", [])

            if not chapters_data:
                return {"display_name": f"Книга_{slug}", "name": slug}

            # Извлекаем информацию из первой главы
            first_chapter = chapters_data[0]

            # Создаем базовую информацию о книге
            book_info = {
                "display_name": f"Книга_{slug}",
                "name": slug,
                "slug": slug,
                "chapters_count": len(chapters_data),
                "first_chapter": first_chapter,
            }

            return book_info
        except requests.exceptions.Timeout:
            print(
                f"  Таймаут при получении информации о книге (попытка {attempt + 1}/{max_retries})"
            )
            if attempt < max_retries - 1:
                delay = RETRY_DELAY * (2**attempt)
                print(f"    Ждем {delay} секунд...")
                time.sleep(delay)
        except requests.exceptions.RequestException as e:
            print(
                f"  Ошибка сети при получении информации о книге: {e} "
                f"(попытка {attempt + 1}/{max_retries})"
            )
            if attempt < max_retries - 1:
                if "429" in str(e):
                    delay = ERROR_TIMEOUT * (2**attempt)
                    print(f"    Rate limit - ждем {delay} секунд...")
                    time.sleep(delay)
                else:
                    delay = RETRY_DELAY * (2**attempt)
                    print(f"    Ждем {delay} секунд...")
                    time.sleep(delay)
        except (ValueError, KeyError) as e:
            print(
                f"  Неожиданная ошибка при получении информации о книге: {e} "
                f"(попытка {attempt + 1}/{max_retries})"
            )
            if attempt < max_retries - 1:
                delay = RETRY_DELAY * (2**attempt)
                print(f"    Ждем {delay} секунд...")
                time.sleep(delay)

    print("  Не удалось получить информацию о книге после всех попыток")
    return {}


def fetch_chapters_list(slug: str, max_retries: int = 3, cookies: Optional[Dict[str, str]] = None):
    """
    Возвращает список (номер, branch_id, volume) для всех глав.
    
    Args:
        slug: Slug книги
        max_retries: Максимальное количество попыток
        cookies: Словарь с cookies для авторизации (опционально)
    """
    for attempt in range(max_retries):
        try:
            resp = requests.get(
                f"{API_BASE}/{slug}/chapters",
                timeout=TIMEOUT,
                cookies=cookies
            )
            resp.raise_for_status()
            arr = resp.json().get("data", [])
            result = []
            seen_chapters = set()  # Для отслеживания уже обработанных глав

            for ch in arr:
                try:
                    # Парсим номер главы, сохраняя полный номер для API
                    number_str = ch.get("number", "")
                    if "." in number_str:
                        # Для подглав типа "1.1" берем основную часть для группировки
                        full_number = number_str  # Сохраняем полный номер
                    else:
                        full_number = number_str
                except (ValueError, IndexError):
                    continue

                # Получаем номер тома
                volume = int(ch.get("volume", 1))

                # Пропускаем дубликаты глав по комбинации том + полный номер
                chapter_key = f"{volume}_{full_number}"
                if chapter_key in seen_chapters:
                    continue
                seen_chapters.add(chapter_key)

                branches = ch.get("branches") or []
                if not branches:
                    continue
                # Используем id самой главы, а не ветки
                chapter_id = ch.get("id")
                if chapter_id is None:
                    continue

                result.append((full_number, chapter_id, volume))
            return sorted(result, key=lambda x: (x[2], x[0]))  # Сортировка по тому, затем по номеру
        except requests.exceptions.Timeout:
            print(
                f"  Таймаут при получении списка глав (попытка {attempt + 1}/{max_retries})"
            )
            if attempt < max_retries - 1:
                delay = RETRY_DELAY * (2**attempt)
                print(f"    Ждем {delay} секунд...")
                time.sleep(delay)
        except requests.exceptions.RequestException as e:
            print(
                f"  Ошибка сети при получении списка глав: {e} "
                f"(попытка {attempt + 1}/{max_retries})"
            )
            if attempt < max_retries - 1:
                if "429" in str(e):
                    delay = ERROR_TIMEOUT * (2**attempt)
                    print(f"    Rate limit - ждем {delay} секунд...")
                    time.sleep(delay)
                else:
                    delay = RETRY_DELAY * (2**attempt)
                    print(f"    Ждем {delay} секунд...")
                    time.sleep(delay)
        except (ValueError, KeyError) as e:
            print(
                f"  Неожиданная ошибка при получении списка глав: {e} "
                f"(попытка {attempt + 1}/{max_retries})"
            )
            if attempt < max_retries - 1:
                delay = RETRY_DELAY * (2**attempt)
                print(f"    Ждем {delay} секунд...")
                time.sleep(delay)

    print("  Не удалось получить список глав после всех попыток")
    return []


def fetch_chapter(
    slug: str, volume: int, number: str, max_retries: int = 3,
    cookies: Optional[Dict[str, str]] = None, branch_id: Optional[int] = None
):
    """
    Возвращает dict с JSON-полем 'data' для одной главы.
    
    Args:
        slug: Slug книги
        volume: Номер тома
        number: Номер главы
        max_retries: Максимальное количество попыток
        cookies: Словарь с cookies для авторизации (опционально)
        branch_id: ID ветки главы (опционально, не требуется для некоторых книг)
    """
    for attempt in range(max_retries):
        try:
            params = {"volume": volume, "number": number}
            if branch_id is not None:
                params["branch_id"] = branch_id
            
            resp = requests.get(
                f"{API_BASE}/{slug}/chapter",
                params=params,
                timeout=TIMEOUT,
                cookies=cookies
            )
            resp.raise_for_status()
            return resp.json().get("data", {})
        except requests.exceptions.Timeout:
            print(
                f"    Таймаут при получении главы {number} (попытка {attempt + 1}/{max_retries})"
            )
            if attempt < max_retries - 1:
                # Увеличиваем задержку при таймаутах
                delay = RETRY_DELAY * (2**attempt)
                print(f"      Ждем {delay} секунд...")
                time.sleep(delay)
        except requests.exceptions.RequestException as e:
            print(
                f"    Ошибка сети при получении главы {number}: {e} "
                f"(попытка {attempt + 1}/{max_retries})"
            )
            if attempt < max_retries - 1:
                # При ошибках 429 (Too Many Requests) увеличиваем задержку
                if "429" in str(e):
                    delay = ERROR_TIMEOUT * (2**attempt)
                    print(f"      Rate limit - ждем {delay} секунд...")
                    time.sleep(delay)
                else:
                    delay = RETRY_DELAY * (2**attempt)
                    print(f"      Ждем {delay} секунд...")
                    time.sleep(delay)
        except (ValueError, KeyError) as e:
            print(
                f"    Неожиданная ошибка при получении главы {number}: {e} "
                f"(попытка {attempt + 1}/{max_retries})"
            )
            if attempt < max_retries - 1:
                delay = RETRY_DELAY * (2**attempt)
                print(f"      Ждем {delay} секунд...")
                time.sleep(delay)

    print(f"    Не удалось получить главу {number} после всех попыток")
    return {}
