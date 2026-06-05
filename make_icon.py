"""
Logo rasmini (PNG/JPG) Windows ikonka fayliga (.ico) aylantiradi.

Foydalanish:
    python make_icon.py logo.png

Natija: icon.ico (bir nechta o'lchamli, shaffof fonni saqlaydi).
Agar argument berilmasa, joriy papkadan logo.png yoki logo.jpg qidiriladi.
"""

import os
import sys

from PIL import Image

# Windows ikonkasi uchun standart o'lchamlar
ICON_SIZES = [(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]

DEFAULT_CANDIDATES = ["logo.png", "logo.jpg", "logo.jpeg", "tatu.png", "tatu.jpg"]


def find_source(argv) -> str | None:
    """Manba rasm faylini argument yoki standart nomlardan topadi."""
    if len(argv) > 1 and os.path.isfile(argv[1]):
        return argv[1]
    for name in DEFAULT_CANDIDATES:
        if os.path.isfile(name):
            return name
    return None


def make_icon(src_path: str, out_path: str = "icon.ico") -> None:
    """Rasmni kvadrat shaklga keltirib, ko'p o'lchamli .ico ga saqlaydi."""
    img = Image.open(src_path).convert("RGBA")

    # Rasmni kvadratga aylantiramiz (markazga joylab, atrofini shaffof qilamiz),
    # shunda ikonka cho'zilib ketmaydi.
    w, h = img.size
    side = max(w, h)
    square = Image.new("RGBA", (side, side), (0, 0, 0, 0))
    square.paste(img, ((side - w) // 2, (side - h) // 2), img)

    square.save(out_path, format="ICO", sizes=ICON_SIZES)
    print(f"Ikonka yaratildi: {out_path}")
    print(f"Manba: {src_path}  ({w}x{h})")


if __name__ == "__main__":
    source = find_source(sys.argv)
    if not source:
        print("XATO: Logo rasm topilmadi.")
        print("Logoni 'logo.png' nomi bilan shu papkaga saqlang yoki")
        print("yo'lni argument qilib bering: python make_icon.py rasm.png")
        sys.exit(1)
    make_icon(source)
