"""
Yengil vaznli kriptografik xesh funksiyalarni tahlil qilish dasturi.

Diplom ishi: "Yengil vaznli kriptografik xesh funksiyalarning tahlili"

Hozircha amalga oshirilgan:
    - Ascon-Hash256 (NIST lightweight crypto standarti)
    - Avalanche (ko'chki) effekti tahlili

Foydalanish:
    python main.py hash "matn"      - matnni xeshlash
    python main.py avalanche        - avalanche effektini tahlil qilish
    python main.py selftest         - test vektorini tekshirish
"""

import sys
import time

from hashes import ascon_hash, ascon_hash_hex
from analysis import avalanche_test


def cmd_hash(text: str) -> None:
    """Berilgan matnni xeshlab, natijani chiqaradi."""
    digest = ascon_hash_hex(text.encode("utf-8"))
    print(f"Kirish : {text!r}")
    print(f"Ascon-Hash256: {digest}")


def cmd_avalanche() -> None:
    """Avalanche effektini tahlil qilib, natijalarni chiqaradi."""
    print("Avalanche effekti tahlili (Ascon-Hash256)...")
    print("Bu biroz vaqt olishi mumkin...\n")

    start = time.time()
    result = avalanche_test(ascon_hash, num_samples=50, message_size=16)
    elapsed = time.time() - start

    print(f"Chiqish uzunligi      : {result['hash_bits']} bit")
    print(f"Taqqoslashlar soni    : {result['comparisons']}")
    print(f"O'rtacha o'zgargan bit : {result['avg_changed_bits']:.2f}")
    print(f"Avalanche nisbati     : {result['avalanche_ratio']:.4f} (ideal = 0.5000)")
    print(f"Min nisbat            : {result['min_ratio']:.4f}")
    print(f"Max nisbat            : {result['max_ratio']:.4f}")
    print(f"\nVaqt                  : {elapsed:.2f} soniya")


def cmd_selftest() -> None:
    """Ma'lum test vektori bilan to'g'rilikni tekshiradi."""
    expected = "7346bc14f036e87ae03d0997913088f5f68411434b3cf8b54fa796a80d251f91"
    result = ascon_hash_hex(b"")
    ok = result == expected
    print(f"Bo'sh xabar xeshi: {result}")
    print(f"Kutilgan qiymat : {expected}")
    print(f"Natija          : {'MUVAFFAQIYATLI' if ok else 'XATO'}")


def main() -> None:
    if len(sys.argv) < 2:
        print(__doc__)
        return

    command = sys.argv[1].lower()

    if command == "hash":
        text = sys.argv[2] if len(sys.argv) > 2 else ""
        cmd_hash(text)
    elif command == "avalanche":
        cmd_avalanche()
    elif command == "selftest":
        cmd_selftest()
    else:
        print(f"Noma'lum buyruq: {command}")
        print(__doc__)


if __name__ == "__main__":
    main()
