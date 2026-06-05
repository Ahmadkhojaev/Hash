"""
Tahlil natijalarini PDF hisobot sifatida shakllantirish.

Ushbu modul barcha xesh funksiyalar uchun avalanche va unumdorlik
tahlillarini o'tkazib, natijalarni ko'p sahifali PDF hisobotga jamlaydi:
    1-sahifa: Sarlavha va umumiy ma'lumot
    2-sahifa: Avalanche effekti (jadval + diagramma)
    3-sahifa: Unumdorlik (jadval + diagramma)

Faqat matplotlib ishlatiladi (qo'shimcha kutubxona shart emas).
"""

from datetime import datetime

import matplotlib
matplotlib.use("Agg")  # GUI'siz, faylga chizish rejimi
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages

from hashes import HASH_REGISTRY
from .avalanche import avalanche_test
from .performance import performance_test


# Hisobotda ishlatiladigan ranglar
LIGHT_COLOR = "#2e8b57"   # yengil funksiyalar uchun (yashil)
STD_COLOR = "#4169e1"     # standart funksiyalar uchun (ko'k)
IDEAL_COLOR = "#d62728"   # ideal chiziq (qizil)


def _color_for(name: str) -> str:
    """Funksiya turiga qarab rang qaytaradi."""
    return LIGHT_COLOR if HASH_REGISTRY[name][1] == "yengil" else STD_COLOR


def collect_results(num_samples: int, data_kb: int) -> dict:
    """
    Barcha xesh funksiyalar bo'yicha tahlil natijalarini yig'adi.

    Eslatma: 'data_kb' endi to'g'ridan-to'g'ri ishlatilmaydi; unumdorlik vaqt
    budjeti asosida o'lchanadi (sekin funksiyalar dasturni muzlatmasligi uchun).

    Qaytaradi:
        {nom: {"avalanche": {...}, "performance": {...}}, ...}
    """
    results = {}
    for name, (func, _) in HASH_REGISTRY.items():
        results[name] = {
            "avalanche": avalanche_test(func, num_samples=num_samples, message_size=16),
            "performance": performance_test(func, time_budget=1.0, block_size=256),
        }
    return results


def _draw_title_page(pdf: PdfPages, num_samples: int, data_kb: int) -> None:
    """Sarlavha sahifasini chizadi."""
    fig = plt.figure(figsize=(8.27, 11.69))  # A4
    fig.patch.set_facecolor("white")
    ax = fig.add_axes([0, 0, 1, 1])
    ax.axis("off")

    ax.text(0.5, 0.82, "Yengil vaznli kriptografik xesh\nfunksiyalarning tahlili",
            ha="center", va="center", fontsize=20, fontweight="bold")
    ax.text(0.5, 0.70, "Tahlil hisoboti", ha="center", fontsize=15, color="#555555")

    ax.plot([0.15, 0.85], [0.66, 0.66], color="#cccccc", linewidth=1)

    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    info_lines = [
        f"Hisobot sanasi: {now}",
        f"Tahlil qilingan funksiyalar soni: {len(HASH_REGISTRY)}",
        f"Avalanche namunalari: {num_samples}",
        f"Unumdorlik uchun ma'lumot hajmi: {data_kb} KB",
        "",
        "Tahlil qilingan funksiyalar:",
    ]
    for i, (name, (_, kind)) in enumerate(HASH_REGISTRY.items()):
        info_lines.append(f"    • {name}  ({kind})")

    ax.text(0.15, 0.55, "\n".join(info_lines), ha="left", va="top", fontsize=12,
            linespacing=1.8)

    ax.text(0.5, 0.06, "Hisobot avtomatik tarzda shakllantirilgan",
            ha="center", fontsize=9, color="#999999", style="italic")
    pdf.savefig(fig)
    plt.close(fig)


def _draw_avalanche_page(pdf: PdfPages, results: dict) -> None:
    """Avalanche effekti sahifasi: jadval + ustun diagramma."""
    fig = plt.figure(figsize=(8.27, 11.69))
    fig.suptitle("1. Avalanche (ko'chki) effekti tahlili", fontsize=16, fontweight="bold", y=0.97)

    names = list(results.keys())
    ratios = [results[n]["avalanche"]["avalanche_ratio"] for n in names]
    colors = [_color_for(n) for n in names]

    # Diagramma
    ax1 = fig.add_axes([0.12, 0.55, 0.78, 0.33])
    bars = ax1.bar(names, ratios, color=colors)
    ax1.axhline(0.5, color=IDEAL_COLOR, linestyle="--", linewidth=1.4, label="Ideal (0.5)")
    ax1.set_ylim(0.4, 0.6)
    ax1.set_ylabel("Avalanche nisbati")
    ax1.set_title("Funksiyalar bo'yicha avalanche nisbati")
    ax1.legend()
    ax1.tick_params(axis="x", rotation=15)
    for bar, r in zip(bars, ratios):
        ax1.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.004,
                 f"{r:.4f}", ha="center", fontsize=9)

    # Jadval
    ax2 = fig.add_axes([0.08, 0.10, 0.84, 0.34])
    ax2.axis("off")
    table_data = [["Funksiya", "Turi", "Nisbat", "O'rt. o'zg. bit", "Min", "Max"]]
    for n in names:
        a = results[n]["avalanche"]
        table_data.append([
            n,
            HASH_REGISTRY[n][1],
            f"{a['avalanche_ratio']:.4f}",
            f"{a['avg_changed_bits']:.1f}",
            f"{a['min_ratio']:.3f}",
            f"{a['max_ratio']:.3f}",
        ])
    table = ax2.table(cellText=table_data, loc="center", cellLoc="center")
    table.auto_set_font_size(False)
    table.set_fontsize(9)
    table.scale(1, 1.6)
    for j in range(len(table_data[0])):
        table[0, j].set_facecolor("#34495e")
        table[0, j].set_text_props(color="white", fontweight="bold")

    note = ("Izoh: Avalanche nisbati 0.5 ga qanchalik yaqin bo'lsa, funksiyaning "
            "diffuziya xususiyati shunchalik yaxshi. Kirishning 1 biti o'zgarganda "
            "chiqishning ~50% o'zgarishi kriptografik mustahkamlik belgisidir.")
    fig.text(0.08, 0.05, note, fontsize=9, color="#555555", wrap=True)

    pdf.savefig(fig)
    plt.close(fig)


def _draw_performance_page(pdf: PdfPages, results: dict) -> None:
    """Unumdorlik sahifasi: jadval + ustun diagramma."""
    fig = plt.figure(figsize=(8.27, 11.69))
    fig.suptitle("2. Unumdorlik (tezlik) tahlili", fontsize=16, fontweight="bold", y=0.97)

    names = list(results.keys())
    speeds = [results[n]["performance"]["throughput_mbps"] for n in names]
    colors = [_color_for(n) for n in names]

    ax1 = fig.add_axes([0.12, 0.55, 0.78, 0.33])
    bars = ax1.bar(names, speeds, color=colors)
    ax1.set_ylabel("Tezlik (MB/s, log shkala)")
    ax1.set_yscale("log")
    ax1.set_title("Funksiyalar bo'yicha qayta ishlash tezligi")
    ax1.tick_params(axis="x", rotation=15)
    for bar, s in zip(bars, speeds):
        ax1.text(bar.get_x() + bar.get_width() / 2, bar.get_height(),
                 f"{s:.3g}", ha="center", va="bottom", fontsize=8)

    ax2 = fig.add_axes([0.08, 0.10, 0.84, 0.34])
    ax2.axis("off")
    table_data = [["Funksiya", "Turi", "Tezlik (MB/s)", "Blok vaqti (ms)", "Amallar"]]
    for n in names:
        p = results[n]["performance"]
        table_data.append([
            n,
            HASH_REGISTRY[n][1],
            f"{p['throughput_mbps']:.2f}",
            f"{p['avg_block_ms']:.4f}",
            str(p["operations"]),
        ])
    table = ax2.table(cellText=table_data, loc="center", cellLoc="center")
    table.auto_set_font_size(False)
    table.set_fontsize(9)
    table.scale(1, 1.6)
    for j in range(len(table_data[0])):
        table[0, j].set_facecolor("#34495e")
        table[0, j].set_text_props(color="white", fontweight="bold")

    note = ("Izoh: Tezlik vaqt budjeti asosida o'lchangan (log shkalada). Toza Python'dagi "
            "yengil funksiyalar (Ascon, PHOTON, SPONGENT) o'rganish maqsadida yozilgani uchun "
            "C tilidagi standart funksiyalardan (SHA, BLAKE2) ancha sekin. Haqiqiy qurilmalarda "
            "yengil funksiyalar xotira va energiya bo'yicha ustun keladi.")
    fig.text(0.08, 0.05, note, fontsize=9, color="#555555", wrap=True)

    pdf.savefig(fig)
    plt.close(fig)


def generate_pdf_report(path: str, num_samples: int = 30, data_kb: int = 200) -> dict:
    """
    To'liq PDF hisobotni shakllantirib, berilgan yo'lga saqlaydi.

    Parametrlar:
        path        - saqlanadigan PDF fayl yo'li.
        num_samples - avalanche tahlili uchun namunalar soni.
        data_kb     - unumdorlik tahlili uchun ma'lumot hajmi (KB).

    Qaytaradi:
        Yig'ilgan natijalar lug'ati (collect_results natijasi).
    """
    results = collect_results(num_samples, data_kb)
    with PdfPages(path) as pdf:
        _draw_title_page(pdf, num_samples, data_kb)
        _draw_avalanche_page(pdf, results)
        _draw_performance_page(pdf, results)
        meta = pdf.infodict()
        meta["Title"] = "Yengil vaznli xesh funksiyalar tahlili"
        meta["Subject"] = "Diplom ishi hisoboti"
    return results
