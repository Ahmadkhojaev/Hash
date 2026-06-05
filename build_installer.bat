@echo off
REM ============================================================
REM  O'rnatuvchi (installer) yaratish skripti.
REM
REM  1. Logo'dan ikonka yaratadi (agar logo.png mavjud bo'lsa)
REM  2. .exe ni build qiladi
REM  3. Inno Setup orqali o'rnatuvchini yaratadi
REM
REM  Natija: Output\XeshTahlil_Setup.exe
REM ============================================================

REM --- 1-qadam: Ikonka yaratish ---
if not exist icon.ico (
    echo Ikonka yaratilmoqda...
    python make_icon.py
)

REM --- 2-qadam: .exe build qilish ---
echo .exe build qilinmoqda...
python -m PyInstaller app.spec --noconfirm --clean

REM --- 3-qadam: Inno Setup kompilyatorini topish ---
set "ISCC=%LOCALAPPDATA%\Programs\Inno Setup 6\ISCC.exe"
if not exist "%ISCC%" set "ISCC=%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe"
if not exist "%ISCC%" set "ISCC=%ProgramFiles%\Inno Setup 6\ISCC.exe"

if not exist "%ISCC%" (
    echo XATO: Inno Setup topilmadi.
    echo Iltimos o'rnating: winget install JRSoftware.InnoSetup
    pause
    exit /b 1
)

REM --- 4-qadam: O'rnatuvchini yaratish ---
echo O'rnatuvchi yaratilmoqda...
"%ISCC%" installer.iss

echo.
if exist Output\XeshTahlil_Setup.exe (
    echo TAYYOR! O'rnatuvchi: Output\XeshTahlil_Setup.exe
) else (
    echo XATO: O'rnatuvchi yaratilmadi.
)
pause
