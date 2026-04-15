import re
import time
import requests
from typing import Optional, Dict, Any, List
from urllib.parse import urlparse, parse_qs

# Настройка кодировки для Windows консоли
from .utils.encoding import setup_console_encoding
setup_console_encoding()

API_BASE = "https://api.cdnlibs.org/api/manga"
TIMEOUT = 30  # таймаут в секундах для API запросов
RETRY_DELAY = 2  # задержка между повторными попытками
ERROR_TIMEOUT = 10  # таймаут после ошибок в секундах

DEFAULT_API_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    ),
    "Referer": "https://ranobelib.me/",
    "Origin": "https://ranobelib.me",
    "Accept": "application/json",
}


def _jwt_from_cookies(cookies: Optional[Dict[str, str]]) -> Optional[str]:
    if not cookies:
        return None
    for name in (
        "access_token",
        "auth_token",
        "token",
        "api_token",
        "sanctum_token",
    ):
        v = cookies.get(name)
        if v and len(v.split(".")) >= 3:
            return v
    return None


def _effective_auth_token(
    auth_token: Optional[str], cookies: Optional[Dict[str, str]]
) -> Optional[str]:
    if auth_token:
        return auth_token
    return _jwt_from_cookies(cookies)


def _api_headers(
    auth_token: Optional[str] = None,
    cookies: Optional[Dict[str, str]] = None,
) -> Dict[str, str]:
    h = dict(DEFAULT_API_HEADERS)
    token = _effective_auth_token(auth_token, cookies)
    if token:
        h["Authorization"] = f"Bearer {token}"
    return h


def _parse_ui_param(url: str) -> Optional[int]:
    parsed = urlparse(url)
    vals = parse_qs(parsed.query).get("ui") or []
    if not vals:
        return None
    try:
        return int(vals[0])
    except ValueError:
        return None


def _pick_branch(
    branches: List[Dict[str, Any]], branch_ui: Optional[int]
) -> Optional[Dict[str, Any]]:
    if not branches:
        return None
    if branch_ui is None:
        return branches[0]
    for b in branches:
        if not isinstance(b, dict):
            continue
        if b.get("id") == branch_ui or b.get("branch_id") == branch_ui:
            return b
        user = b.get("user")
        if isinstance(user, dict) and user.get("id") == branch_ui:
            return b
        for t in b.get("teams") or []:
            if isinstance(t, dict) and t.get("id") == branch_ui:
                return b
    return branches[0]


def extract_info(url: str):
    """
    Разбирает URL пользователя.
    Возвращает (slug, mode, branch_ui_or_bid, chap_number).
    Для /book/... третий элемент — int из query ui= (ветка/команда) или None.
    Для /read/... третий элемент — bid из URL.
    """
    path = urlparse(url).path or url
    branch_ui = _parse_ui_param(url)

    m = re.search(r"/book/([^/?]+)", path)
    if m:
        return m.group(1), "list", branch_ui, None

    m2 = re.search(r"/read/v1/c(\d+)", path)
    bid = re.search(r"bid=(\d+)", url)
    slug_m = re.search(r"/ru/([^/]+)/read", path)
    if m2 and bid and slug_m:
        return slug_m.group(1), "single", int(bid.group(1)), int(m2.group(1))

    raise ValueError(f"URL не распознан: {url}")


def fetch_book_info(
    slug: str,
    max_retries: int = 3,
    cookies: Optional[Dict[str, str]] = None,
    auth_token: Optional[str] = None,
):
    """
    Возвращает информацию о книге (название, описание и т.д.).
    Получает информацию из списка глав, так как прямой endpoint не работает.
    """
    for attempt in range(max_retries):
        try:
            resp = requests.get(
                f"{API_BASE}/{slug}/chapters",
                timeout=TIMEOUT,
                cookies=cookies,
                headers=_api_headers(auth_token, cookies),
            )
            resp.raise_for_status()
            raw = resp.json().get("data", [])
            chapters_data = raw if isinstance(raw, list) else []

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
    print(
        "  Подсказка: 18+ и часть каталога требуют сессии — cookies из браузера, "
        "JWT в cookie (подхватывается автоматически) или --auth-token."
    )
    return {}


def fetch_chapters_list(
    slug: str,
    max_retries: int = 3,
    cookies: Optional[Dict[str, str]] = None,
    auth_token: Optional[str] = None,
    branch_ui: Optional[int] = None,
):
    """
    Возвращает список (номер, branch_id для API, volume) для всех глав.
    branch_ui — значение из ?ui= в URL книги (совпадение с id ветки, branch_id или id команды).
    """
    for attempt in range(max_retries):
        try:
            resp = requests.get(
                f"{API_BASE}/{slug}/chapters",
                timeout=TIMEOUT,
                cookies=cookies,
                headers=_api_headers(auth_token, cookies),
            )
            if resp.status_code in (401, 403) and auth_token:
                print("🔐 Bearer-токен не работает или устарел (API вернул 401/403). Обновите токен.")
                return []
            resp.raise_for_status()
            raw = resp.json().get("data", [])
            arr = raw if isinstance(raw, list) else []
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
                if branches:
                    picked = _pick_branch(branches, branch_ui)
                    api_branch_id = (picked or branches[0]).get("id")
                else:
                    api_branch_id = ch.get("id")
                if api_branch_id is None:
                    continue

                result.append((full_number, api_branch_id, volume))
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
    print(
        "  Подсказка: войдите на ranobelib.me, подтвердите 18+ в профиле, "
        "закройте браузер и снова --cookies …; либо --auth-token из DevTools "
        "(запрос к api.cdnlibs.org → Authorization: Bearer …); "
        "либо --cookies-file с экспортом cookies для ranobelib.me."
    )
    return []


def fetch_chapter(
    slug: str,
    volume: int,
    number: str,
    max_retries: int = 3,
    cookies: Optional[Dict[str, str]] = None,
    branch_id: Optional[int] = None,
    auth_token: Optional[str] = None,
):
    """
    Возвращает dict с JSON-полем 'data' для одной главы.
    """
    for attempt in range(max_retries):
        try:
            params = {"volume": volume, "number": number}
            if branch_id is not None:
                params["branch_id"] = branch_id

            headers = _api_headers(auth_token, cookies)
            resp = requests.get(
                f"{API_BASE}/{slug}/chapter",
                params=params,
                timeout=TIMEOUT,
                cookies=cookies,
                headers=headers,
            )
            if resp.status_code in (401, 403) and auth_token:
                print("🔐 Bearer-токен не работает или устарел (API вернул 401/403). Обновите токен.")
                return {}
            resp.raise_for_status()
            data = resp.json().get("data", {})
            if (
                branch_id is not None
                and isinstance(data, dict)
                and not data.get("content")
            ):
                resp2 = requests.get(
                    f"{API_BASE}/{slug}/chapter",
                    params={"volume": volume, "number": number},
                    timeout=TIMEOUT,
                    cookies=cookies,
                    headers=headers,
                )
                resp2.raise_for_status()
                alt = resp2.json().get("data", {})
                if isinstance(alt, dict) and alt.get("content"):
                    return alt
            return data if isinstance(data, dict) else {}
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
