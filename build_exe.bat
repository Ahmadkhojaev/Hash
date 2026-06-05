@echo off
REM ============================================================
REM  "Yengil vaznli xesh funksiyalar tahlili" ilovasini
REM  mustaqil .exe faylga aylantirish skripti.
REM
REM  Ishlatish: ushbu faylni ikki marta bosing yoki terminalda
REM             build_exe.bat deb yozing.
REM  Natija:    dist\XeshTahlil.exe
REM ============================================================

echo PyInstaller o'rnatilganini tekshirish...
python -m PyInstaller --version >nul 2>&1
if errorlevel 1 (
    echo PyInstaller topilmadi. O'rnatilmoqda...
    python -m pip install pyinstaller
)

echo.
echo .exe fayl yaratilmoqda... (bir necha daqiqa olishi mumkin)
python -m PyInstaller app.spec --noconfirm --clean

echo.
if exist dist\XeshTahlil\XeshTahlil.exe (
    echo TAYYOR! Fayl: dist\XeshTahlil\XeshTahlil.exe
    echo Butun "dist\XeshTahlil" papkasini birga ko'chiring.
) else (
    echo XATO: .exe fayl yaratilmadi. Yuqoridagi xabarlarni tekshiring.
)
pause
