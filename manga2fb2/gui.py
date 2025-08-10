import threading
import tkinter as tk
from tkinter import ttk, messagebox
from .client import extract_info, fetch_chapters_list, fetch_chapter
from .fb2 import build_fb2


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Manga2FB2")
        self.resizable(False, False)
        self._build()

    def _build(self):
        frm = ttk.Frame(self, padding=10)
        frm.grid()
        # URL
        ttk.Label(frm, text="URL:").grid(row=0, column=0, sticky="w")
        self.url = tk.StringVar()
        ttk.Entry(frm, textvariable=self.url, width=50).grid(
            row=0, column=1, columnspan=3
        )
        # start/end
        ttk.Label(frm, text="Start:").grid(row=1, column=0, sticky="w")
        self.start = tk.StringVar()
        ttk.Entry(frm, textvariable=self.start, width=5).grid(row=1, column=1)
        ttk.Label(frm, text="End:").grid(row=1, column=2, sticky="w")
        self.end = tk.StringVar()
        ttk.Entry(frm, textvariable=self.end, width=5).grid(row=1, column=3)
        # кнопка
        btn = ttk.Button(frm, text="Download", command=self._on_download)
        btn.grid(row=2, column=0, columnspan=4, pady=10)
        # статус
        self.status = ttk.Label(frm, text="Готов.", foreground="blue")
        self.status.grid(row=3, column=0, columnspan=4, sticky="w")

    def _log(self, msg):
        self.status.config(text=msg)
        self.update_idletasks()

    def _on_download(self):
        threading.Thread(target=self._download, daemon=True).start()

    def _download(self):
        try:
            url = self.url.get().strip()
            start = int(self.start.get()) if self.start.get().isdigit() else None
            end = int(self.end.get()) if self.end.get().isdigit() else None

            slug, mode, bid, chap = extract_info(url)
            if mode == "list":
                lst = fetch_chapters_list(slug)
                nums = [n for n, _ in lst]
                brm = {n: b for n, b in lst}
                start = start or nums[0]
                end = end or nums[-1]
                to_dl = [n for n in nums if start <= n <= end]
            else:
                to_dl = [chap]
                brm = {chap: bid}

            for n in to_dl:
                self._log(f"Гл. {n}…")
                data = fetch_chapter(slug, brm[n], volume=1, number=n)
                slug_ch = str(data.get("slug") or data.get("id") or n)
                fname = f"{slug}_vol{data.get('volume')}_ch{slug_ch}.fb2"
                fb2 = build_fb2(data)
                with open(fname, "wb") as f:
                    f.write(fb2)
                self._log(f"Сохранено: {fname}")

            messagebox.showinfo("Manga2FB2", "Готово!")
            self._log("Готов.")
        except Exception as e:
            messagebox.showerror("Error", str(e))
            self._log("Ошибка.")


if __name__ == "__main__":
    App().mainloop()
