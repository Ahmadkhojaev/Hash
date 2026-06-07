"""
Yengil vaznli kriptografik xesh funksiyalarni tahlil qilish dasturi (GUI).

Diplom ishi: "Yengil vaznli kriptografik xesh funksiyalarning tahlili"
Muallif: 070-21 | Axmadxo'jayev Abbosxon

Grafik interfeysli Windows ilovasi (Tkinter asosida). Beshta asosiy bo'lim:
    1. Xeshlash      - matn yoki faylni tanlangan funksiya bilan xeshlash
    2. Avalanche     - ko'chki effekti tahlili va grafigi
    3. Unumdorlik    - funksiyalar tezligini taqqoslash grafigi
    4. Resurslar     - holat hajmi, apparat maydoni va xotira sarfi tahlili
    5. PDF hisobot   - barcha tahlillarni jamlovchi hisobot yaratish

Ishga tushirish:
    python app.py
"""

import os
import sys
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

import matplotlib
matplotlib.use("TkAgg")
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from hashes import HASH_REGISTRY
from analysis import avalanche_test, performance_test, generate_pdf_report, collect_resources


def resource_path(relative: str) -> str:
    """
    Resurs faylining to'liq yo'lini qaytaradi.

    PyInstaller bilan paketlanganda fayllar vaqtinchalik _MEIPASS papkasiga
    joylanadi; oddiy ishga tushirilganda esa joriy papkadan olinadi.
    """
    base = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, relative)


# Rang sxemasi
BG = "#1e1e2e"
PANEL = "#2a2a3c"
ACCENT = "#89b4fa"
TEXT = "#cdd6f4"
GREEN = "#a6e3a1"
RED = "#f38ba8"

# Xeshlash uchun kiritiladigan matnning maksimal uzunligi (belgi).
# SPONGENT toza Python'da sekin (~370 belgi/soniya), shu sababli matn
# kiritish bo'limida oqilona chegara qo'yiladi. Fayl xeshlashda alohida
# (kattaroq) chegara ishlatiladi.
MAX_INPUT_CHARS = 1000
MAX_FILE_BYTES = 100 * 1024  # 100 KB

# Dastur muallifi (diplom ishi)
AUTHOR = "070-21 | Axmadxo'jayev Abbosxon"


class HashAnalyzerApp(tk.Tk):
    """Asosiy ilova oynasi."""

    def __init__(self):
        super().__init__()
        self.title("Yengil vaznli xesh funksiyalar tahlili")
        self.geometry("900x680")
        self.configure(bg=BG)
        self.minsize(800, 600)

        self._set_icon()
        self._setup_style()
        self._build_ui()

    def _set_icon(self):
        """Oyna ikonkasini (TATU logosi) o'rnatadi, agar mavjud bo'lsa."""
        ico = resource_path("icon.ico")
        if os.path.isfile(ico):
            try:
                self.iconbitmap(ico)
            except tk.TclError:
                pass  # ikonka yuklanmasa, jim o'tkazib yuboramiz

    # ------------------------------------------------------------------ #
    # Stil sozlamalari
    # ------------------------------------------------------------------ #
    def _setup_style(self):
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure("TNotebook", background=BG, borderwidth=0)
        style.configure(
            "TNotebook.Tab",
            background=PANEL,
            foreground=TEXT,
            padding=(18, 10),
            font=("Segoe UI", 10, "bold"),
        )
        style.map(
            "TNotebook.Tab",
            background=[("selected", ACCENT)],
            foreground=[("selected", BG)],
        )
        style.configure("TFrame", background=BG)
        style.configure("TLabel", background=BG, foreground=TEXT, font=("Segoe UI", 10))
        style.configure(
            "Header.TLabel",
            background=BG,
            foreground=ACCENT,
            font=("Segoe UI", 14, "bold"),
        )
        style.configure(
            "Accent.TButton",
            background=ACCENT,
            foreground=BG,
            font=("Segoe UI", 10, "bold"),
            borderwidth=0,
            padding=(14, 8),
        )
        style.map("Accent.TButton", background=[("active", "#74a0e0")])
        style.configure(
            "TCombobox",
            fieldbackground=PANEL,
            background=PANEL,
            foreground=TEXT,
            arrowcolor=TEXT,
        )

    def _build_ui(self):
        # Doimiy pastki satr (muallif) - oynaning eng pastida turadi
        footer = ttk.Label(
            self,
            text=AUTHOR,
            background=PANEL,
            foreground=TEXT,
            font=("Segoe UI", 9),
            anchor="e",
            padding=(12, 4),
        )
        footer.pack(side="bottom", fill="x")

        notebook = ttk.Notebook(self)
        notebook.pack(fill="both", expand=True, padx=12, pady=12)

        self.hash_tab = HashTab(notebook)
        self.avalanche_tab = AvalancheTab(notebook)
        self.performance_tab = PerformanceTab(notebook)
        self.resource_tab = ResourceTab(notebook)
        self.report_tab = ReportTab(notebook)

        notebook.add(self.hash_tab, text="  Xeshlash  ")
        notebook.add(self.avalanche_tab, text="  Avalanche effekti  ")
        notebook.add(self.performance_tab, text="  Unumdorlik  ")
        notebook.add(self.resource_tab, text="  Resurslar  ")
        notebook.add(self.report_tab, text="  PDF hisobot  ")


# ====================================================================== #
# 1-BO'LIM: Xeshlash
# ====================================================================== #
class HashTab(ttk.Frame):
    """Matn yoki faylni xeshlash bo'limi."""

    def __init__(self, parent):
        super().__init__(parent)
        self._build()

    def _build(self):
        ttk.Label(self, text="Xesh qiymatini hisoblash", style="Header.TLabel").pack(
            anchor="w", padx=20, pady=(20, 12)
        )

        # Funksiya tanlash
        row = ttk.Frame(self)
        row.pack(fill="x", padx=20, pady=(0, 10))
        ttk.Label(row, text="Xesh funksiya:").pack(side="left")
        self.func_var = tk.StringVar(value="Ascon-Hash256")
        combo = ttk.Combobox(
            row,
            textvariable=self.func_var,
            values=list(HASH_REGISTRY.keys()),
            state="readonly",
            width=20,
        )
        combo.pack(side="left", padx=10)

        # Matn kiritish maydoni
        label_row = ttk.Frame(self)
        label_row.pack(fill="x", padx=20)
        ttk.Label(label_row, text="Kiritiladigan matn:").pack(side="left")
        self.counter = ttk.Label(
            label_row, text=f"0 / {MAX_INPUT_CHARS}", foreground=ACCENT
        )
        self.counter.pack(side="right")

        self.text_input = tk.Text(
            self,
            height=6,
            bg=PANEL,
            fg=TEXT,
            insertbackground=TEXT,
            relief="flat",
            font=("Consolas", 11),
            padx=10,
            pady=10,
        )
        self.text_input.pack(fill="x", padx=20, pady=(4, 10))
        self.text_input.insert("1.0", "Salom, dunyo!")
        # Har bir o'zgarishda belgilar sonini yangilab boramiz
        self.text_input.bind("<KeyRelease>", self._update_counter)
        self._update_counter()

        # Tugmalar
        btn_row = ttk.Frame(self)
        btn_row.pack(fill="x", padx=20, pady=4)
        self.hash_btn = ttk.Button(
            btn_row, text="Xeshlash", style="Accent.TButton", command=self._hash_text
        )
        self.hash_btn.pack(side="left")
        self.file_btn = ttk.Button(
            btn_row, text="Fayl tanlash...", style="Accent.TButton", command=self._hash_file
        )
        self.file_btn.pack(side="left", padx=10)

        # Natija
        ttk.Label(self, text="Natija (hex):").pack(anchor="w", padx=20, pady=(14, 4))
        self.result = tk.Text(
            self,
            height=4,
            bg=PANEL,
            fg=GREEN,
            relief="flat",
            font=("Consolas", 12, "bold"),
            padx=10,
            pady=10,
            wrap="word",
        )
        self.result.pack(fill="x", padx=20)
        self.result.configure(state="disabled")

        self.info = ttk.Label(self, text="", foreground=ACCENT)
        self.info.pack(anchor="w", padx=20, pady=8)

    def _update_counter(self, event=None):
        """Belgilar sonini yangilab, chegaradan oshganda rangini o'zgartiradi."""
        n = len(self.text_input.get("1.0", "end-1c"))
        self.counter.config(text=f"{n} / {MAX_INPUT_CHARS}")
        # Chegaradan oshsa qizil, yaqinlashsa sariq, aks holda oddiy
        if n > MAX_INPUT_CHARS:
            self.counter.config(foreground=RED)
        else:
            self.counter.config(foreground=ACCENT)

    def _show_result(self, digest: bytes):
        self.result.configure(state="normal")
        self.result.delete("1.0", "end")
        self.result.insert("1.0", digest.hex())
        self.result.configure(state="disabled")
        self.info.config(text=f"Uzunligi: {len(digest)} bayt ({len(digest) * 8} bit)")

    def _set_busy(self, busy: bool):
        """Hisoblash vaqtida tugmalarni bloklab, holatni ko'rsatadi."""
        state = "disabled" if busy else "normal"
        self.hash_btn.config(state=state)
        self.file_btn.config(state=state)
        if busy:
            self.info.config(text="Hisoblanmoqda, kuting...")

    def _run_hash(self, func, data: bytes, source_info: str):
        """Xeshlashni fon oqimida bajaradi (GUI qotmasligi uchun)."""
        self._set_busy(True)

        def worker():
            digest = func(data)
            self.after(0, lambda: self._on_hash_done(digest, source_info))

        threading.Thread(target=worker, daemon=True).start()

    def _on_hash_done(self, digest: bytes, source_info: str):
        self._set_busy(False)
        self._show_result(digest)
        if source_info:
            self.info.config(text=source_info)

    def _hash_text(self):
        text = self.text_input.get("1.0", "end-1c")
        if len(text) > MAX_INPUT_CHARS:
            messagebox.showwarning(
                "Matn juda uzun",
                f"Kiritilgan matn {len(text)} belgidan iborat.\n"
                f"Maksimal ruxsat etilgan: {MAX_INPUT_CHARS} belgi.\n\n"
                "Sabab: SPONGENT kabi yengil funksiyalar toza Python'da sekin "
                "ishlaydi. Kattaroq ma'lumotni xeshlash uchun 'Fayl tanlash' "
                "tugmasidan foydalaning.",
            )
            return
        func, _ = HASH_REGISTRY[self.func_var.get()]
        data = text.encode("utf-8")
        self._run_hash(func, data, source_info="")

    def _hash_file(self):
        path = filedialog.askopenfilename(title="Faylni tanlang")
        if not path:
            return
        try:
            with open(path, "rb") as f:
                data = f.read()
        except OSError as exc:
            messagebox.showerror("Xato", f"Faylni o'qib bo'lmadi:\n{exc}")
            return

        # Sekin funksiyalar uchun fayl hajmini ham cheklaymiz
        if len(data) > MAX_FILE_BYTES:
            proceed = messagebox.askyesno(
                "Fayl katta",
                f"Fayl hajmi {len(data) // 1024} KB.\n"
                f"Tavsiya etilgan chegara: {MAX_FILE_BYTES // 1024} KB.\n\n"
                "Yengil funksiyalar (ayniqsa SPONGENT) katta fayllarni juda sekin "
                "qayta ishlaydi va bu bir necha daqiqa davom etishi mumkin.\n\n"
                "Davom etilsinmi?",
            )
            if not proceed:
                return

        func, _ = HASH_REGISTRY[self.func_var.get()]
        info = f"Fayl: {path}  ({len(data)} bayt)"
        self._run_hash(func, data, source_info=info)


# ====================================================================== #
# 2-BO'LIM: Avalanche effekti
# ====================================================================== #
class AvalancheTab(ttk.Frame):
    """Avalanche (ko'chki) effekti tahlili bo'limi."""

    def __init__(self, parent):
        super().__init__(parent)
        self._build()

    def _build(self):
        ttk.Label(self, text="Avalanche (ko'chki) effekti tahlili", style="Header.TLabel").pack(
            anchor="w", padx=20, pady=(20, 4)
        )
        ttk.Label(
            self,
            text="Ideal qiymat: 0.5 — kirishning 1 biti o'zgarsa, chiqishning yarmi o'zgarishi kerak.",
        ).pack(anchor="w", padx=20, pady=(0, 12))

        ctrl = ttk.Frame(self)
        ctrl.pack(fill="x", padx=20)
        ttk.Label(ctrl, text="Namunalar soni:").pack(side="left")
        self.samples = tk.IntVar(value=30)
        ttk.Spinbox(ctrl, from_=5, to=200, textvariable=self.samples, width=6).pack(
            side="left", padx=8
        )
        self.run_btn = ttk.Button(
            ctrl, text="Tahlilni boshlash", style="Accent.TButton", command=self._run
        )
        self.run_btn.pack(side="left", padx=12)
        self.status = ttk.Label(ctrl, text="", foreground=ACCENT)
        self.status.pack(side="left", padx=8)

        # Grafik maydoni
        self.fig = Figure(figsize=(7, 3.6), facecolor=BG)
        self.ax = self.fig.add_subplot(111)
        self._style_axes()
        self.canvas = FigureCanvasTkAgg(self.fig, master=self)
        self.canvas.get_tk_widget().pack(fill="both", expand=True, padx=20, pady=14)

    def _style_axes(self):
        self.ax.set_facecolor(PANEL)
        self.ax.tick_params(colors=TEXT)
        for spine in self.ax.spines.values():
            spine.set_color(TEXT)

    def _run(self):
        self.run_btn.config(state="disabled")
        self.status.config(text="Hisoblanmoqda...")
        threading.Thread(target=self._worker, daemon=True).start()

    def _worker(self):
        results = {}
        n = self.samples.get()
        for name, (func, _) in HASH_REGISTRY.items():
            results[name] = avalanche_test(func, num_samples=n, message_size=16)
        self.after(0, lambda: self._plot(results))

    def _plot(self, results: dict):
        self.ax.clear()
        self._style_axes()

        names = list(results.keys())
        ratios = [results[n]["avalanche_ratio"] for n in names]
        colors = [GREEN if HASH_REGISTRY[n][1] == "yengil" else ACCENT for n in names]

        bars = self.ax.bar(names, ratios, color=colors)
        self.ax.axhline(0.5, color="#f38ba8", linestyle="--", linewidth=1.5, label="Ideal (0.5)")
        self.ax.set_ylim(0.4, 0.6)
        self.ax.set_ylabel("Avalanche nisbati", color=TEXT)
        self.ax.set_title("Avalanche effekti taqqoslashi", color=TEXT, fontweight="bold")
        self.ax.legend(facecolor=PANEL, labelcolor=TEXT)

        for bar, ratio in zip(bars, ratios):
            self.ax.text(
                bar.get_x() + bar.get_width() / 2,
                bar.get_height() + 0.003,
                f"{ratio:.4f}",
                ha="center",
                color=TEXT,
                fontsize=9,
            )

        self.fig.tight_layout()
        self.canvas.draw()
        self.status.config(text="Tayyor")
        self.run_btn.config(state="normal")


# ====================================================================== #
# 3-BO'LIM: Unumdorlik
# ====================================================================== #
class PerformanceTab(ttk.Frame):
    """Xesh funksiyalar tezligini taqqoslash bo'limi."""

    def __init__(self, parent):
        super().__init__(parent)
        self._build()

    def _build(self):
        ttk.Label(self, text="Unumdorlik (tezlik) tahlili", style="Header.TLabel").pack(
            anchor="w", padx=20, pady=(20, 4)
        )
        ttk.Label(
            self,
            text="Har bir funksiya belgilangan vaqt ichida qancha ma'lumotni qayta ishlay olishi (MB/s) o'lchanadi.",
        ).pack(anchor="w", padx=20, pady=(0, 12))

        ctrl = ttk.Frame(self)
        ctrl.pack(fill="x", padx=20)
        ttk.Label(ctrl, text="Har biri uchun vaqt (soniya):").pack(side="left")
        self.budget = tk.DoubleVar(value=1.0)
        ttk.Spinbox(ctrl, from_=0.5, to=5.0, increment=0.5, textvariable=self.budget, width=6).pack(
            side="left", padx=8
        )
        self.run_btn = ttk.Button(
            ctrl, text="O'lchashni boshlash", style="Accent.TButton", command=self._run
        )
        self.run_btn.pack(side="left", padx=12)
        self.status = ttk.Label(ctrl, text="", foreground=ACCENT)
        self.status.pack(side="left", padx=8)

        self.fig = Figure(figsize=(7, 3.6), facecolor=BG)
        self.ax = self.fig.add_subplot(111)
        self._style_axes()
        self.canvas = FigureCanvasTkAgg(self.fig, master=self)
        self.canvas.get_tk_widget().pack(fill="both", expand=True, padx=20, pady=14)

    def _style_axes(self):
        self.ax.set_facecolor(PANEL)
        self.ax.tick_params(colors=TEXT)
        for spine in self.ax.spines.values():
            spine.set_color(TEXT)

    def _run(self):
        self.run_btn.config(state="disabled")
        self.status.config(text="O'lchanmoqda...")
        threading.Thread(target=self._worker, daemon=True).start()

    def _worker(self):
        budget = self.budget.get()
        results = {}
        for name, (func, _) in HASH_REGISTRY.items():
            results[name] = performance_test(func, time_budget=budget, block_size=256)
        self.after(0, lambda: self._plot(results))

    def _plot(self, results: dict):
        self.ax.clear()
        self._style_axes()

        names = list(results.keys())
        speeds = [results[n]["throughput_mbps"] for n in names]
        colors = [GREEN if HASH_REGISTRY[n][1] == "yengil" else ACCENT for n in names]

        bars = self.ax.bar(names, speeds, color=colors)
        self.ax.set_ylabel("Tezlik (MB/s, log shkala)", color=TEXT)
        self.ax.set_yscale("log")
        self.ax.set_title("Unumdorlik taqqoslashi", color=TEXT, fontweight="bold")

        for bar, speed in zip(bars, speeds):
            self.ax.text(
                bar.get_x() + bar.get_width() / 2,
                bar.get_height(),
                f"{speed:.3g}",
                ha="center",
                va="bottom",
                color=TEXT,
                fontsize=9,
            )

        self.fig.tight_layout()
        self.canvas.draw()
        self.status.config(text="Tayyor")
        self.run_btn.config(state="normal")


# ====================================================================== #
# 4-BO'LIM: Resurslar (xotira va apparat)
# ====================================================================== #
class ResourceTab(ttk.Frame):
    """Funksiyalarning resurs sarfini (holat hajmi, xotira) taqqoslash bo'limi."""

    def __init__(self, parent):
        super().__init__(parent)
        self._build()

    def _build(self):
        ttk.Label(self, text="Resurs (xotira va apparat) tahlili", style="Header.TLabel").pack(
            anchor="w", padx=20, pady=(20, 4)
        )
        ttk.Label(
            self,
            text="Yengil funksiyalarning asl ustunligi - kichik holat hajmi va resurs sarfi.\n"
            "Holat hajmi (state size) apparatdagi joy (gate count) bilan bevosita bog'liq.",
            justify="left",
        ).pack(anchor="w", padx=20, pady=(0, 10))

        ctrl = ttk.Frame(self)
        ctrl.pack(fill="x", padx=20)
        self.run_btn = ttk.Button(
            ctrl, text="Tahlilni boshlash", style="Accent.TButton", command=self._run
        )
        self.run_btn.pack(side="left")
        self.status = ttk.Label(ctrl, text="", foreground=ACCENT)
        self.status.pack(side="left", padx=10)

        # Yuqorida diagramma, pastda jadval
        self.fig = Figure(figsize=(7, 2.8), facecolor=BG)
        self.ax = self.fig.add_subplot(111)
        self._style_axes()
        self.canvas = FigureCanvasTkAgg(self.fig, master=self)
        self.canvas.get_tk_widget().pack(fill="x", padx=20, pady=10)

        # Ma'lumotlar jadvali (matn)
        self.table = tk.Text(
            self, height=10, bg=PANEL, fg=TEXT, relief="flat",
            font=("Consolas", 9), padx=10, pady=10, wrap="none",
        )
        self.table.pack(fill="both", expand=True, padx=20, pady=(0, 16))
        self.table.configure(state="disabled")

    def _style_axes(self):
        self.ax.set_facecolor(PANEL)
        self.ax.tick_params(colors=TEXT)
        for spine in self.ax.spines.values():
            spine.set_color(TEXT)

    def _run(self):
        self.run_btn.config(state="disabled")
        self.status.config(text="Hisoblanmoqda...")
        threading.Thread(target=self._worker, daemon=True).start()

    def _worker(self):
        results = collect_resources(HASH_REGISTRY)
        self.after(0, lambda: self._show(results))

    def _show(self, results: dict):
        # --- Diagramma: holat hajmi (state size) ---
        self.ax.clear()
        self._style_axes()
        names = list(results.keys())
        states = [results[n].get("state_bits", 0) for n in names]
        colors = [GREEN if results[n]["type"] == "yengil" else ACCENT for n in names]

        bars = self.ax.bar(names, states, color=colors)
        self.ax.set_ylabel("Holat hajmi (bit)", color=TEXT)
        self.ax.set_title("Ichki holat hajmi (kichik = apparatga qulay)",
                          color=TEXT, fontweight="bold")
        self.ax.tick_params(axis="x", rotation=15)
        for bar, s in zip(bars, states):
            self.ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height(),
                         str(s), ha="center", va="bottom", color=TEXT, fontsize=8)
        self.fig.tight_layout()
        self.canvas.draw()

        # --- Jadval ---
        lines = []
        header = f"{'Funksiya':<15}{'Holat':>7}{'Rate':>6}{'Sig.':>6}{'Raund':>7}{'Xesh':>6}{'GE~':>7}  Konstruksiya"
        lines.append(header)
        lines.append("-" * len(header))
        for n in names:
            m = results[n]
            cap = m.get("capacity")
            cap_s = str(cap) if cap is not None else "-"
            ge = m.get("ge_estimate")
            ge_s = str(ge) if ge is not None else "-"
            lines.append(
                f"{n:<15}{m.get('state_bits',0):>7}{m.get('rate_bits',0):>6}"
                f"{cap_s:>6}{m.get('rounds',0):>7}{m.get('digest_bits',0):>6}"
                f"{ge_s:>7}  {m.get('construction','')}"
            )
        lines.append("")
        lines.append("Izoh: GE~ - taxminiy apparat maydoni (gate equivalents, adabiyotdan).")
        lines.append("Holat va Rate - bit. Yengil funksiyalar (yashil) kichik holatga ega.")

        self.table.configure(state="normal")
        self.table.delete("1.0", "end")
        self.table.insert("1.0", "\n".join(lines))
        self.table.configure(state="disabled")

        self.status.config(text="Tayyor")
        self.run_btn.config(state="normal")


# ====================================================================== #
# 5-BO'LIM: PDF hisobot
# ====================================================================== #
class ReportTab(ttk.Frame):
    """Barcha tahlillarni jamlab, PDF hisobot yaratish bo'limi."""

    def __init__(self, parent):
        super().__init__(parent)
        self._build()

    def _build(self):
        ttk.Label(self, text="To'liq PDF hisobot yaratish", style="Header.TLabel").pack(
            anchor="w", padx=20, pady=(20, 4)
        )
        ttk.Label(
            self,
            text="Barcha funksiyalar bo'yicha avalanche, unumdorlik va resurs tahlillari\n"
            "jadval va diagrammalar bilan ko'p sahifali PDF hisobotga jamlanadi.",
            justify="left",
        ).pack(anchor="w", padx=20, pady=(0, 16))

        # Sozlamalar
        cfg = ttk.Frame(self)
        cfg.pack(fill="x", padx=20)

        ttk.Label(cfg, text="Avalanche namunalari:").grid(row=0, column=0, sticky="w", pady=6)
        self.samples = tk.IntVar(value=30)
        ttk.Spinbox(cfg, from_=5, to=200, textvariable=self.samples, width=8).grid(
            row=0, column=1, sticky="w", padx=10
        )

        ttk.Label(
            cfg,
            text="(Unumdorlik vaqt budjeti asosida avtomatik o'lchanadi)",
            foreground="#888899",
        ).grid(row=1, column=0, columnspan=2, sticky="w", pady=(2, 0))

        # Tugma
        self.run_btn = ttk.Button(
            self, text="PDF hisobotni yaratish...", style="Accent.TButton", command=self._run
        )
        self.run_btn.pack(anchor="w", padx=20, pady=20)

        # Holat va natija
        self.status = ttk.Label(self, text="", foreground=ACCENT, font=("Segoe UI", 10, "bold"))
        self.status.pack(anchor="w", padx=20)

        self.summary = tk.Text(
            self,
            height=12,
            bg=PANEL,
            fg=TEXT,
            relief="flat",
            font=("Consolas", 10),
            padx=12,
            pady=12,
            wrap="word",
        )
        self.summary.pack(fill="both", expand=True, padx=20, pady=(14, 20))
        self.summary.configure(state="disabled")

    def _run(self):
        path = filedialog.asksaveasfilename(
            title="PDF hisobotni saqlash",
            defaultextension=".pdf",
            initialfile="xesh_tahlil_hisoboti.pdf",
            filetypes=[("PDF fayllar", "*.pdf")],
        )
        if not path:
            return

        self.run_btn.config(state="disabled")
        self.status.config(text="Hisobot yaratilmoqda, kuting...")
        threading.Thread(target=self._worker, args=(path,), daemon=True).start()

    def _worker(self, path: str):
        try:
            results = generate_pdf_report(
                path,
                num_samples=self.samples.get(),
            )
        except Exception as exc:  # noqa: BLE001 - foydalanuvchiga xatoni ko'rsatamiz
            self.after(0, lambda: self._on_error(exc))
            return
        self.after(0, lambda: self._on_done(path, results))

    def _on_error(self, exc: Exception):
        self.status.config(text="Xatolik yuz berdi", foreground="#f38ba8")
        messagebox.showerror("Xato", f"Hisobotni yaratib bo'lmadi:\n{exc}")
        self.run_btn.config(state="normal")

    def _on_done(self, path: str, results: dict):
        self.status.config(text=f"Tayyor: {path}", foreground=GREEN)
        self.run_btn.config(state="normal")

        # Qisqacha xulosani matn maydonida ko'rsatamiz
        lines = ["=== TAHLIL XULOSASI ===", ""]
        lines.append(f"{'Funksiya':<16}{'Turi':<10}{'Avalanche':<12}{'Tezlik (MB/s)':<14}")
        lines.append("-" * 52)
        for name, data in results.items():
            kind = HASH_REGISTRY[name][1]
            av = data["avalanche"]["avalanche_ratio"]
            sp = data["performance"]["throughput_mbps"]
            lines.append(f"{name:<16}{kind:<10}{av:<12.4f}{sp:<14.2f}")
        lines.append("")
        lines.append(f"Hisobot fayli: {path}")

        self.summary.configure(state="normal")
        self.summary.delete("1.0", "end")
        self.summary.insert("1.0", "\n".join(lines))
        self.summary.configure(state="disabled")

        # Foydalanuvchidan faylni ochishni so'raymiz
        if messagebox.askyesno("Tayyor", "Hisobot yaratildi. Hozir ochilsinmi?"):
            try:
                os.startfile(path)  # Windows'da PDF'ni standart dastur bilan ochadi
            except OSError:
                pass


if __name__ == "__main__":
    app = HashAnalyzerApp()
    app.mainloop()