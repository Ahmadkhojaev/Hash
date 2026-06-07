"""
Yengil vaznli kriptografik xesh funksiyalarni tahlil qilish dasturi (CLI).

Diplom ishi: "Yengil vaznli kriptografik xesh funksiyalarning tahlili"

Bu buyruq qatori (CLI) interfeysi. Grafik interfeys uchun: python app.py

Foydalanish:
    python main.py list                  - mavjud funksiyalar ro'yxati
    python main.py hash <funksiya> "matn" - matnni tanlangan funksiya bilan xeshlash
    python main.py avalanche [funksiya]  - avalanche effektini tahlil qilish
    python main.py selftest              - barcha funksiyalarni test vektorlari bilan tekshirish

Misol:
    python main.py hash Ascon-Hash256 "Salom"
    python main.py hash SPONGENT-128 "Salom"
"""

import sys
import time

from hashes import HASH_REGISTRY
from hashes.ascon_hash import ascon_hash_hex
from hashes.photon import photon_beetle_hash_hex
from hashes.spongent import spongent_hash_hex, SPONGENT_88
from analysis import avalanche_test


def cmd_list() -> None:
    """Mavjud xesh funksiyalar ro'yxatini chiqaradi."""
    print("Mavjud xesh funksiyalar:")
    for name, (_, kind) in HASH_REGISTRY.items():
        print(f"  {name:<16} ({kind})")


def cmd_hash(func_name: str, text: str) -> None:
    """Berilgan matnni tanlangan funksiya bilan xeshlab, natijani chiqaradi."""
    if func_name not in HASH_REGISTRY:
        print(f"Noma'lum funksiya: {func_name}")
        print("Mavjud funksiyalarni ko'rish uchun: python main.py list")
        return
    func, _ = HASH_REGISTRY[func_name]
    digest = func(text.encode("utf-8"))
    print(f"Funksiya : {func_name}")
    print(f"Kirish   : {text!r}")
    print(f"Xesh     : {digest.hex()}")
    print(f"Uzunligi : {len(digest)} bayt ({len(digest) * 8} bit)")


def cmd_avalanche(func_name: str) -> None:
    """Tanlangan funksiya uchun avalanche effektini tahlil qiladi."""
    if func_name not in HASH_REGISTRY:
        print(f"Noma'lum funksiya: {func_name}")
        return
    func, _ = HASH_REGISTRY[func_name]
    print(f"Avalanche effekti tahlili ({func_name})...")
    print("Bu biroz vaqt olishi mumkin...\n")

    start = time.time()
    result = avalanche_test(func, num_samples=30, message_size=16)
    elapsed = time.time() - start

    print(f"Chiqish uzunligi      : {result['hash_bits']} bit")
    print(f"Bajarilgan namunalar  : {result['samples_done']}")
    print(f"Taqqoslashlar soni    : {result['comparisons']}")
    print(f"O'rtacha o'zgargan bit : {result['avg_changed_bits']:.2f}")
    print(f"Avalanche nisbati     : {result['avalanche_ratio']:.4f} (ideal = 0.5000)")
    print(f"Min nisbat            : {result['min_ratio']:.4f}")
    print(f"Max nisbat            : {result['max_ratio']:.4f}")
    print(f"\nVaqt                  : {elapsed:.2f} soniya")


def cmd_selftest() -> None:
    """Yengil funksiyalarni rasmiy test vektorlari bilan tekshiradi."""
    tests = [
        ("Ascon-Hash256 (bo'sh xabar)",
         ascon_hash_hex(b""),
         "7346bc14f036e87ae03d0997913088f5f68411434b3cf8b54fa796a80d251f91"),
        ("PHOTON-Beetle (bo'sh xabar)",
         photon_beetle_hash_hex(b"").lower(),
         "44a99882fea033566856a27e7f0c94dc84fac7e411b08b890a4a574e3db75d4a"),
        ("SPONGENT-88 (test xabari)",
         spongent_hash_hex(b"Sponge + Present = Spongent", SPONGENT_88).lower(),
         "69971bf96def95bfc46822"),
    ]
    print("Rasmiy test vektorlari bilan tekshirish:\n")
    all_ok = True
    for label, got, expected in tests:
        ok = got == expected
        all_ok = all_ok and ok
        print(f"  {label}: {'MUVAFFAQIYATLI' if ok else 'XATO'}")
        if not ok:
            print(f"    olingan : {got}")
            print(f"    kutilgan: {expected}")
    natija = "BARCHA TEST MUVAFFAQIYATLI" if all_ok else "XATOLIK BOR"
    print(f"\nUmumiy natija: {natija}")


def main() -> None:
    if len(sys.argv) < 2:
        print(__doc__)
        return

    command = sys.argv[1].lower()

    if command == "list":
        cmd_list()
    elif command == "hash":
        if len(sys.argv) < 4:
            print("Foydalanish: python main.py hash <funksiya> \"matn\"")
            return
        cmd_hash(sys.argv[2], sys.argv[3])
    elif command == "avalanche":
        func_name = sys.argv[2] if len(sys.argv) > 2 else "Ascon-Hash256"
        cmd_avalanche(func_name)
    elif command == "selftest":
        cmd_selftest()
    else:
        print(f"Noma'lum buyruq: {command}")
        print(__doc__)


if __name__ == "__main__":
    main()
