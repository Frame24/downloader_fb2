import re
from dataclasses import dataclass
from difflib import SequenceMatcher
from pathlib import Path


@dataclass(frozen=True)
class ChapterStats:
    chapter: int
    chars: int
    lines: int


TITLE_RE = r"<title>\s*(?:Том\s*\d+\s*,\s*)?Глава\s*{ch}\s*</title>"
STRONG_CH_RE = r"<p>\s*<strong>\s*{ch}\s*</strong>\s*</p>"


def _title_pat(ch: int) -> re.Pattern[str]:
    return re.compile(TITLE_RE.format(ch=ch))


def _strong_ch_pat(ch: int) -> re.Pattern[str]:
    return re.compile(STRONG_CH_RE.format(ch=ch))


def _find_any_chapter_start(text: str, ch: int) -> re.Match[str] | None:
    # Prefer <title> if present, fall back to <p><strong>N</strong></p>
    return _title_pat(ch).search(text) or _strong_ch_pat(ch).search(text)


def _find_any_next_chapter_start(text: str, ch: int, pos: int) -> re.Match[str] | None:
    return _title_pat(ch).search(text, pos) or _strong_ch_pat(ch).search(text, pos)


def extract_chapter_sections(text: str, start: int, end: int) -> dict[int, str | None]:
    chunk_start = _find_any_chapter_start(text, start)
    if not chunk_start:
        raise ValueError(f"Start title not found: {start}")

    chunk_end_title = _find_any_chapter_start(text, end)
    if not chunk_end_title:
        raise ValueError(f"End title not found: {end}")

    next_title = _find_any_next_chapter_start(text, end + 1, chunk_end_title.end())
    chunk_end = next_title.start() if next_title else len(text)
    chunk = text[chunk_start.start() : chunk_end]

    sections: dict[int, str | None] = {}
    for ch in range(start, end + 1):
        mt = _find_any_chapter_start(chunk, ch)
        if not mt:
            sections[ch] = None
            continue
        mn = _find_any_next_chapter_start(chunk, ch + 1, mt.end())
        sec_end = mn.start() if mn else len(chunk)
        sections[ch] = chunk[mt.start() : sec_end]
    return sections


def normalize_section(section: str | None) -> str | None:
    if section is None:
        return None
    ps = re.findall(r"<p>(.*?)</p>", section, flags=re.S)
    out: list[str] = []
    for p in ps:
        p = re.sub(r"<.*?>", "", p)
        p = re.sub(r"\s+", " ", p).strip()
        if p:
            out.append(p)
    return "\n".join(out)


def stats_for_sections(sections: dict[int, str | None]) -> tuple[list[ChapterStats], list[int]]:
    stats: list[ChapterStats] = []
    missing: list[int] = []
    for ch, sec in sections.items():
        n = normalize_section(sec)
        if n is None:
            missing.append(ch)
            continue
        lines = n.count("\n") + (1 if n else 0)
        stats.append(ChapterStats(chapter=ch, chars=len(n), lines=lines))
    return stats, missing


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    small = root / "output" / "Книга_177465--changjiacmul-sogro" / "2216-2241.fb2"
    big = (
        root
        / "output"
        / "Книга_177465--changjiacmul-sogro"
        / "Книга_177465--changjiacmul-sogro_2026-05-08_20-48-48_Часть6.fb2"
    )

    start, end = 2216, 2241

    big_text = big.read_text(encoding="utf-8", errors="replace")
    small_text = small.read_text(encoding="utf-8", errors="replace")

    big_secs = extract_chapter_sections(big_text, start, end)
    small_secs = extract_chapter_sections(small_text, start, end)

    big_stats, big_missing = stats_for_sections(big_secs)
    small_stats, small_missing = stats_for_sections(small_secs)

    def total(sts: list[ChapterStats]) -> tuple[int, int]:
        return sum(s.chars for s in sts), sum(s.lines for s in sts)

    b_chars, b_lines = total(big_stats)
    s_chars, s_lines = total(small_stats)

    print("FILES:")
    print("  big  :", big)
    print("  small:", small)
    print()
    print("TOTAL (normalized <p> text):")
    print(f"  big  : {b_chars} chars; {b_lines} paragraph-lines")
    print(f"  small: {s_chars} chars; {s_lines} paragraph-lines")
    print()

    if big_missing or small_missing:
        print("MISSING CHAPTER TITLES:")
        if big_missing:
            print("  big missing  :", big_missing)
        if small_missing:
            print("  small missing:", small_missing)
        print()

    big_map = {s.chapter: s for s in big_stats}
    small_map = {s.chapter: s for s in small_stats}

    any_len_diff = False
    print("PER-CHAPTER LENGTH DIFF (small - big) [normalized]:")
    for ch in range(start, end + 1):
        bc = big_map.get(ch, ChapterStats(ch, 0, 0)).chars
        sc = small_map.get(ch, ChapterStats(ch, 0, 0)).chars
        if sc != bc:
            any_len_diff = True
            print(f"  {ch}: {sc - bc:+} chars (small {sc}, big {bc})")
    if not any_len_diff:
        print("  none (lengths match for every chapter)")

    # Find first content difference (not just length)
    for ch in range(start, end + 1):
        btxt = normalize_section(big_secs.get(ch)) or ""
        stxt = normalize_section(small_secs.get(ch)) or ""
        if btxt != stxt:
            sm = SequenceMatcher(None, btxt, stxt)
            print()
            print(f"FIRST CONTENT DIFFERENCE: chapter {ch}")
            print("  similarity:", round(sm.ratio(), 6))
            bl = btxt.splitlines()
            sl = stxt.splitlines()
            i = 0
            while i < min(len(bl), len(sl)) and bl[i] == sl[i]:
                i += 1
            lo = max(0, i - 2)
            hi_b = min(len(bl), i + 3)
            hi_s = min(len(sl), i + 3)
            print("  first differing paragraph index:", i)
            print("  big context:")
            for j in range(lo, hi_b):
                print(f"    [{j}] {bl[j]}")
            print("  small context:")
            for j in range(lo, hi_s):
                print(f"    [{j}] {sl[j]}")
            break
    else:
        print()
        print("CONTENT: identical for all chapters (normalized <p> text).")


if __name__ == "__main__":
    main()

