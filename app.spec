# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec fayli - "Yengil vaznli xesh funksiyalar tahlili" ilovasi.

ONEDIR rejimi: .exe va kutubxonalar 'dist\\XeshTahlil\\' papkasida joylashadi.
Bu rejim ONEFILE'dan ancha TEZ ishga tushadi, chunki har safar fayllarni
vaqtinchalik papkaga ochish (extract) jarayoni yo'q.

Build qilish:
    python -m PyInstaller app.spec --noconfirm --clean
Ishga tushirish:
    dist\\XeshTahlil\\XeshTahlil.exe
"""

block_cipher = None


a = Analysis(
    ['app.py'],
    pathex=[],
    binaries=[],
    datas=[('icon.ico', '.')],
    hiddenimports=[
        'hashes',
        'hashes.ascon_hash',
        'hashes.reference',
        'hashes.photon',
        'hashes.spongent',
        'analysis',
        'analysis.avalanche',
        'analysis.performance',
        'analysis.resources',
        'analysis.report',
        'matplotlib.backends.backend_tkagg',
        'matplotlib.backends.backend_pdf',
    ],
    hookspath=[],
    hooksconfig={
        # matplotlib uchun faqat kerakli backendlarni jamlash
        "matplotlib": {"backends": ["TkAgg", "PDF"]},
    },
    runtime_hooks=[],
    # Faqat ANIQ ishlatilmaydigan katta paketlarni chiqarib tashlaymiz.
    # MUHIM: stdlib modullari (unittest), test freymvorklari (pytest) va
    # matplotlib ichki bog'liqliklarini (pyparsing PIL kabi) chiqarib
    # tashlamaymiz - ular import zanjirida kerak bo'lib qoladi.
    excludes=[
        # Boshqa GUI freymvorklar (kerak emas, biz Tkinter ishlatamiz)
        'PyQt5', 'PyQt6', 'PySide2', 'PySide6', 'wx',
        # Yirik ilmiy kutubxonalar (matplotlib yadrosi ularni talab qilmaydi)
        'pandas', 'scipy',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

# ONEDIR rejimi: EXE faqat skriptlarni o'z ichiga oladi,
# kutubxonalar esa COLLECT orqali alohida papkaga joylanadi.
exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,        # kutubxonalar EXE ichiga emas, papkaga
    name='XeshTahlil',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,                # GUI ilova - konsol oynasi ko'rinmaydi
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='icon.ico',            # TATU logosi (make_icon.py yaratadi)
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='XeshTahlil',
)
