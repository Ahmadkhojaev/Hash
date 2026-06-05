"""
Unumdorlik (performance) tahlili.

Yengil vaznli xesh funksiyalar uchun tezlik muhim mezon hisoblanadi.
Ushbu modul xesh funksiyaning qayta ishlash tezligini (throughput, MB/s) va
bitta amal uchun o'rtacha vaqtni o'lchaydi.

MUHIM: Funksiyalarning tezligi juda turlicha (toza Python'dagi yengil
funksiyalar C'dagi standart funksiyalardan yuzlab marta sekinroq). Shu sababli
o'lchov VAQT BUDJETI asosida ishlaydi: har bir funksiya belgilangan vaqt
ichida nechta baytni qayta ishlashga ulgursa, shunga qarab tezlik hisoblanadi.
Bu sekin funksiyalar dasturni "muzlatib" qo'yishining oldini oladi.
"""

import os
import time
from typing import Callable


def performance_test(
    hash_func: Callable[[bytes], bytes],
    time_budget: float = 1.0,
    block_size: int = 256,
    max_operations: int = 1_000_000,
) -> dict:
    """
    Xesh funksiyaning unumdorligini vaqt budjeti asosida o'lchaydi.

    Parametrlar:
        hash_func      - sinaladigan xesh funksiya.
        time_budget    - o'lchash uchun ajratilgan vaqt (soniya).
        block_size     - har bir xeshlashda ishlatiladigan blok hajmi (bayt).
        max_operations - amallarning yuqori chegarasi (xavfsizlik uchun).

    Qaytaradi:
        - throughput_mbps : tezlik (MB/s)
        - avg_block_ms    : bitta amal uchun o'rtacha vaqt (millisekund)
        - operations      : bajarilgan xeshlash amallari soni
        - elapsed_sec     : sarflangan haqiqiy vaqt (soniya)
    """
    data = os.urandom(block_size)

    operations = 0
    start = time.perf_counter()
    deadline = start + time_budget

    # Vaqt budjeti tugaguncha (yoki amallar chegarasiga yetguncha) xeshlaymiz
    while operations < max_operations:
        hash_func(data)
        operations += 1
        if time.perf_counter() >= deadline:
            break

    elapsed = time.perf_counter() - start

    processed_bytes = operations * block_size
    throughput_mbps = (processed_bytes / (1024 * 1024)) / elapsed if elapsed > 0 else 0.0
    avg_block_ms = (elapsed / operations) * 1000 if operations else 0.0

    return {
        "throughput_mbps": throughput_mbps,
        "avg_block_ms": avg_block_ms,
        "operations": operations,
        "elapsed_sec": elapsed,
    }
