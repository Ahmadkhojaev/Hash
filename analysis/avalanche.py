"""
Avalanche (ko'chki) effekti tahlili.

Yaxshi kriptografik xesh funksiyada kirishning bitta biti o'zgarsa,
chiqishning taxminan yarmi (~50%) o'zgarishi kerak. Bu xususiyat
"strict avalanche criterion" (SAC) deb ataladi va diffuziya sifatini
o'lchaydi.

Ushbu modul tasodifiy xabarlarni generatsiya qilib, har bir kirish bitini
navbatma-navbat o'zgartiradi va chiqishdagi o'zgargan bitlar sonini
(Hamming masofasini) hisoblaydi.
"""

import os
import time
from typing import Callable


def _hamming_distance(a: bytes, b: bytes) -> int:
    """Ikki bayt ketma-ketligi orasidagi Hamming masofasi (farq qiluvchi bitlar soni)."""
    return sum(bin(x ^ y).count("1") for x, y in zip(a, b))


def _flip_bit(data: bytes, bit_index: int) -> bytes:
    """Berilgan indeksdagi bitni teskari qiladi (0 -> 1, 1 -> 0)."""
    byte_index = bit_index // 8
    bit_in_byte = bit_index % 8
    mutable = bytearray(data)
    mutable[byte_index] ^= (1 << (7 - bit_in_byte))
    return bytes(mutable)


def avalanche_test(
    hash_func: Callable[[bytes], bytes],
    num_samples: int = 1000,
    message_size: int = 16,
    max_time: float = 8.0,
) -> dict:
    """
    Xesh funksiya uchun avalanche effektini o'lchaydi.

    Parametrlar:
        hash_func    - bytes qabul qilib bytes qaytaradigan xesh funksiya.
        num_samples  - sinaladigan tasodifiy xabarlar soni (maqsad).
        message_size - har bir xabarning hajmi (baytlarda).
        max_time     - eng ko'p sarflanadigan vaqt (soniya). Sekin funksiyalar
                       (PHOTON, SPONGENT) dasturni muzlatmasligi uchun, vaqt
                       tugasa, tahlil shu paytgacha yig'ilgan namunalar bilan
                       yakunlanadi.

    Qaytaradi:
        Statistik natijalardan iborat lug'at:
            - hash_bits          : chiqish uzunligi (bit)
            - samples_done       : haqiqatda bajarilgan namunalar soni
            - avg_changed_bits   : o'rtacha o'zgargan bitlar soni
            - avalanche_ratio    : o'rtacha o'zgarish nisbati (ideal = 0.5)
            - min_ratio, max_ratio : nisbatning eng kichik/katta qiymati
    """
    total_ratio = 0.0
    min_ratio = 1.0
    max_ratio = 0.0
    comparisons = 0
    samples_done = 0

    # Chiqish bitlari sonini aniqlash uchun bitta namuna xesh hisoblaymiz
    hash_bits = len(hash_func(b"\x00")) * 8
    deadline = time.perf_counter() + max_time

    for _ in range(num_samples):
        message = os.urandom(message_size)
        base_digest = hash_func(message)
        total_input_bits = message_size * 8
        stop = False

        for bit_index in range(total_input_bits):
            mutated = _flip_bit(message, bit_index)
            mutated_digest = hash_func(mutated)

            changed = _hamming_distance(base_digest, mutated_digest)
            ratio = changed / hash_bits

            total_ratio += ratio
            min_ratio = min(min_ratio, ratio)
            max_ratio = max(max_ratio, ratio)
            comparisons += 1

            # Vaqt budjeti tugagan bo'lsa, namuna o'rtasida ham to'xtaymiz
            # (sekin funksiyalarda bitta namuna ham juda uzoq davom etishi mumkin)
            if time.perf_counter() >= deadline:
                stop = True
                break

        samples_done += 1
        if stop:
            break

    avg_ratio = total_ratio / comparisons if comparisons else 0.0

    return {
        "hash_bits": hash_bits,
        "samples_done": samples_done,
        "comparisons": comparisons,
        "avg_changed_bits": avg_ratio * hash_bits,
        "avalanche_ratio": avg_ratio,
        "min_ratio": min_ratio,
        "max_ratio": max_ratio,
    }
