import click
from .client import extract_info, fetch_chapters_list, fetch_chapter
from .fb2 import build_fb2


@click.command()
@click.option("--url", required=True, help="URL книги или главы")
@click.option("--start", type=int, help="Номер первой главы")
@click.option("--end", type=int, help="Номер последней главы")
def main(url, start, end):
    """
    CLI-точка входа.
    """
    slug, mode, bid, chap = extract_info(url)

    if mode == "list":
        all_ch = fetch_chapters_list(slug)
        nums = [n for n, _ in all_ch]
        branch_m = {n: b for n, b in all_ch}
        start = start or nums[0]
        end = end or nums[-1]
        to_dl = [n for n in nums if start <= n <= end]
    else:
        to_dl = [chap]
        branch_m = {chap: bid}

    for n in to_dl:
        b = branch_m[n]
        click.echo(f"Downloading chapter {n} (branch {b})…")
        data = fetch_chapter(slug, b, volume=1, number=n)
        slug_ch = str(data.get("slug") or data.get("id") or n)
        fname = f"{slug}_vol{data.get('volume')}_ch{slug_ch}.fb2"
        fb2 = build_fb2(data)
        with open(fname, "wb") as f:
            f.write(fb2)
        click.secho(f"  → Saved: {fname}", fg="green")


if __name__ == "__main__":
    main()
