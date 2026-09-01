from pathlib import Path
from typing import Optional
import re


AUTH_TOKEN_FILE = Path(__file__).parent.parent / "output" / "ranobelib_auth_token.txt"

# JS для консоли браузера на странице тайтла ranobelib.me (F12 → Console).
# Ищет JWT в localStorage / sessionStorage / cookie и копирует в буфер обмена.
BROWSER_TOKEN_JS = r"""(() => {
  const jwtRe = /eyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+/;
  const keys = [
    "access_token", "auth_token", "token", "api_token",
    "sanctum_token", "authToken", "accessToken", "Authorization"
  ];

  const fromStore = (store) => {
    if (!store) return null;
    for (const k of keys) {
      try {
        const v = store.getItem(k);
        if (!v) continue;
        const m = String(v).match(jwtRe);
        if (m) return m[0];
      } catch (_) {}
    }
    try {
      for (let i = 0; i < store.length; i++) {
        const v = store.getItem(store.key(i)) || "";
        const m = String(v).match(jwtRe);
        if (m) return m[0];
      }
    } catch (_) {}
    return null;
  };

  let token =
    fromStore(window.localStorage) ||
    fromStore(window.sessionStorage);

  if (!token) {
    try {
      const m = document.cookie.match(jwtRe);
      if (m) token = m[0];
    } catch (_) {}
  }

  if (!token) {
    console.warn(
      "Токен не найден. Откройте Network → запрос к api.cdnlibs.org → " +
      "заголовок Authorization: Bearer … и скопируйте JWT вручную."
    );
    return null;
  }

  const copy = (t) => {
    if (typeof window.copy === "function") {
      window.copy(t);
      return true;
    }
    if (navigator.clipboard && navigator.clipboard.writeText) {
      navigator.clipboard.writeText(t);
      return true;
    }
    return false;
  };

  const ok = copy(token);
  console.log(ok ? "Токен скопирован в буфер обмена:" : "Токен (скопируйте вручную):");
  console.log(token);
  return token;
})();"""


def _normalize_token(token: str) -> str:
    t = (token or "").strip()
    if not t:
        return ""

    # If user pasted multiple lines or a full "Authorization: Bearer …" header,
    # extract the first JWT-like substring.
    if "bearer" in t.lower() or "\n" in t or "\r" in t or "\t" in t or " " in t:
        matches = re.findall(r"eyJ[0-9A-Za-z_-]+\.[0-9A-Za-z_-]+\.[0-9A-Za-z_-]+", t)
        if matches:
            return matches[0].strip()

    if t.lower().startswith("bearer "):
        t = t[7:].strip()
    return t


def load_auth_token() -> Optional[str]:
    try:
        if not AUTH_TOKEN_FILE.is_file():
            return None
        token = _normalize_token(AUTH_TOKEN_FILE.read_text(encoding="utf-8"))
        if not token:
            return None
        return token
    except OSError:
        return None


def save_auth_token(token: str) -> None:
    try:
        AUTH_TOKEN_FILE.parent.mkdir(parents=True, exist_ok=True)
        AUTH_TOKEN_FILE.write_text(_normalize_token(token), encoding="utf-8")
    except OSError:
        return


def clear_auth_token() -> None:
    try:
        if AUTH_TOKEN_FILE.is_file():
            AUTH_TOKEN_FILE.unlink()
    except OSError:
        return


def token_status_label() -> str:
    token = load_auth_token()
    if not token:
        return "не задан"
    preview = token[:12] + "…" if len(token) > 12 else token
    return f"задан ({preview})"

