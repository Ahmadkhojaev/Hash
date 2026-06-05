"""
Resurs (xotira va apparat) tahlili.

Yengil vaznli xesh funksiyalarning asosiy ustunligi tezlikda EMAS, balki
kichik resurs sarfida namoyon bo'ladi. Ushbu modul quyidagi mezonlarni
taqqoslaydi:

    - Ichki holat hajmi (state size, bit) - apparatdagi joy (gate count) bilan
      bevosita bog'liq; yengil funksiyalar uchun eng muhim mezon.
    - Rate (bit)        - bitta permutatsiyada qayta ishlanadigan bitlar.
    - Capacity (bit)    - xavfsizlik zaxirasi.
    - Raundlar soni     - permutatsiyaning murakkabligi.
    - Xesh uzunligi (bit).
    - Ish vaqtidagi xotira sarfi (toza Python implementatsiyalari uchun,
      tracemalloc orqali o'lchanadi).
    - Taxminiy apparat maydoni (GE - gate equivalents, adabiyotdan).

Holat hajmi va boshqa strukturaviy parametrlar funksiyalarning rasmiy
spetsifikatsiyalaridan olingan.
"""

import tracemalloc
from typing import Callable


# Har bir funksiyaning strukturaviy parametrlari (spetsifikatsiyadan).
# state_bits  - ichki holat hajmi (bit)
# rate_bits   - bitta permutatsiyada yutiladigan bitlar
# capacity    - xavfsizlik sig'imi (bit); sponge bo'lmaganlar uchun None
# rounds      - permutatsiya/siqish funksiyasi raundlari
# digest_bits - xesh chiqishi (bit)
# ge_estimate - taxminiy apparat maydoni (gate equivalents, adabiyotdan); None
#               bo'lsa - bu funksiya apparat uchun mo'ljallanmagan
# construction - konstruksiya turi
HASH_METADATA = {
    "Ascon-Hash256": {
        "state_bits": 320,
        "rate_bits": 64,
        "capacity": 256,
        "rounds": 12,
        "digest_bits": 256,
        "ge_estimate": 3750,
        "construction": "Sponge (Ascon-p)",
    },
    "PHOTON-Beetle": {
        "state_bits": 256,
        "rate_bits": 32,
        "capacity": 224,
        "rounds": 12,
        "digest_bits": 256,
        "ge_estimate": 1120,
        "construction": "Sponge (PHOTON-256)",
    },
    "SPONGENT-128": {
        "state_bits": 136,
        "rate_bits": 8,
        "capacity": 128,
        "rounds": 70,
        "digest_bits": 128,
        "ge_estimate": 1060,
        "construction": "Sponge (PRESENT-tipidagi)",
    },
    "SHA-256": {
        "state_bits": 256,
        "rate_bits": 512,
        "capacity": None,
        "rounds": 64,
        "digest_bits": 256,
        "ge_estimate": 11000,
        "construction": "Merkle-Damgård",
    },
    "SHA-3-256": {
        "state_bits": 1600,
        "rate_bits": 1088,
        "capacity": 512,
        "rounds": 24,
        "digest_bits": 256,
        "ge_estimate": 10500,
        "construction": "Sponge (Keccak-f)",
    },
    "BLAKE2s": {
        "state_bits": 256,
        "rate_bits": 512,
        "capacity": None,
        "rounds": 10,
        "digest_bits": 256,
        "ge_estimate": 13000,
        "construction": "HAIFA (ChaCha asosida)",
    },
}


def measure_memory(hash_func: Callable[[bytes], bytes], data_size: int = 64) -> int:
    """
    Bitta xeshlash amali davomidagi eng yuqori (peak) xotira sarfini o'lchaydi.

    tracemalloc orqali Python darajasidagi ajratmalarni kuzatadi. Bu toza
    Python implementatsiyalari (Ascon, PHOTON, SPONGENT) uchun ma'noli; C
    darajasidagi funksiyalar (hashlib: SHA, BLAKE2) uchun ajratma deyarli
    ko'rinmaydi, chunki ular xotirani C tomonda ajratadi.

    Qaytaradi:
        eng yuqori ajratilgan xotira (bayt).
    """
    data = b"\xa5" * data_size

    tracemalloc.start()
    tracemalloc.reset_peak()
    hash_func(data)
    _, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    return peak


def collect_resources(registry: dict) -> dict:
    """
    Barcha funksiyalar uchun resurs ma'lumotlarini yig'adi.

    Parametr:
        registry - {nom: (funksiya, turi)} ko'rinishidagi xesh registri.
    Qaytaradi:
        {nom: {metadata + "memory_bytes" + "type"}} lug'ati.
    """
    results = {}
    for name, (func, kind) in registry.items():
        meta = dict(HASH_METADATA.get(name, {}))
        meta["type"] = kind
        try:
            meta["memory_bytes"] = measure_memory(func)
        except Exception:  # noqa: BLE001
            meta["memory_bytes"] = None
        results[name] = meta
    return results
