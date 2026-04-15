from pathlib import Path
from typing import Optional
import re


AUTH_TOKEN_FILE = Path(__file__).parent.parent / "output" / "ranobelib_auth_token.txt"

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

