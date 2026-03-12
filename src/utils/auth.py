from pathlib import Path
from typing import Optional


AUTH_TOKEN_FILE = Path(__file__).parent.parent / "output" / "ranobelib_auth_token.txt"


def load_auth_token() -> Optional[str]:
    try:
        if not AUTH_TOKEN_FILE.is_file():
            return None
        token = AUTH_TOKEN_FILE.read_text(encoding="utf-8").strip()
        if not token:
            return None
        return token
    except OSError:
        return None


def save_auth_token(token: str) -> None:
    try:
        AUTH_TOKEN_FILE.parent.mkdir(parents=True, exist_ok=True)
        AUTH_TOKEN_FILE.write_text(token.strip(), encoding="utf-8")
    except OSError:
        return

