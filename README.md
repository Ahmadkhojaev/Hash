# Yengil vaznli kriptografik xesh funksiyalarning tahlili

Diplom ishi doirasida yaratilgan dastur — yengil vaznli (lightweight)
kriptografik xesh funksiyalarni amalga oshiradi, ularni xavfsizlik,
unumdorlik va resurs sarfi bo'yicha tahlil qiladi va taqqoslaydi.

Grafik interfeysli (Tkinter) Windows ilovasi.

## Imkoniyatlari

- **Xeshlash** — matn yoki faylni tanlangan funksiya bilan xeshlash
- **Avalanche (ko'chki) effekti tahlili** — diffuziya sifatini o'lchash
- **Unumdorlik tahlili** — qayta ishlash tezligini taqqoslash (log shkala)
- **Resurs tahlili** — holat hajmi, apparat maydoni (GE), xotira sarfi
- **PDF hisobot** — barcha tahlillarni jadval va grafiklar bilan jamlash

## Amalga oshirilgan xesh funksiyalar

### Yengil vaznli (lightweight)
| Funksiya | Chiqish | Holat | Tekshiruv |
|----------|---------|-------|-----------|
| Ascon-Hash256 | 256 bit | 320 bit | NIST test vektori |
| PHOTON-Beetle-Hash | 256 bit | 256 bit | NIST KAT vektorlari |
| SPONGENT-128 | 128 bit | 136 bit | Rasmiy test vektori |

### Taqqoslash uchun (standart)
SHA-256, SHA-3-256, BLAKE2s (`hashlib` orqali).

> Yengil funksiyalar (Ascon, PHOTON, SPONGENT) ta'lim maqsadida toza Python'da
> yozilgan va rasmiy test vektorlariga tekshirilgan. Ularning sekinligi
> apparat-yo'naltirilgan dizayn natijasidir; ustunligi resurs sarfida.

## Loyiha tuzilmasi

```
.
├── app.py                  # GUI ilova (asosiy)
├── main.py                 # CLI versiya (ixtiyoriy)
├── hashes/                 # xesh funksiyalar implementatsiyasi
│   ├── ascon_hash.py
│   ├── photon.py
│   ├── spongent.py
│   └── reference.py        # SHA, BLAKE2 (taqqoslash uchun)
├── analysis/               # tahlil modullari
│   ├── avalanche.py
│   ├── performance.py
│   ├── resources.py
│   └── report.py           # PDF hisobot
├── make_icon.py            # logo.png -> icon.ico
├── app.spec                # PyInstaller konfiguratsiyasi
├── installer.iss           # Inno Setup o'rnatuvchi skripti
├── build_exe.bat           # .exe yaratish
└── build_installer.bat     # o'rnatuvchi yaratish
```

## Ishga tushirish (manba koddan)

Python 3.10+ kerak.

```bash
pip install -r requirements.txt
python app.py
```

## Mustaqil ilova yaratish (.exe)

```bash
build_exe.bat
```
Natija: `dist\XeshTahlil\XeshTahlil.exe`

## O'rnatuvchi yaratish (installer)

[Inno Setup](https://jrsoftware.org/isdl.php) o'rnatilgan bo'lishi kerak.

```bash
build_installer.bat
```
Natija: `Output\XeshTahlil_Setup.exe`

## Test vektorlari bilan tekshirish

Har bir yengil funksiyani alohida tekshirish mumkin:

```bash
python hashes/ascon_hash.py    # Ascon NIST test vektori
python hashes/photon.py        # PHOTON-Beetle NIST KAT vektorlari
python hashes/spongent.py      # SPONGENT rasmiy test vektori
```

## Litsenziya va manbalar

Dastur ta'lim/ilmiy maqsadda yaratilgan. Algoritmlar quyidagi rasmiy
spetsifikatsiyalar va public-domain reference implementatsiyalarga asoslangan:

- Ascon: https://ascon.iaik.tugraz.at
- PHOTON-Beetle: NIST Lightweight Cryptography finalisti
- SPONGENT: ISO/IEC 29192-5
