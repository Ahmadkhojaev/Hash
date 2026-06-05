; ============================================================
;  Inno Setup skripti
;  "Yengil vaznli xesh funksiyalar tahlili" ilovasi uchun
;  o'rnatuvchi (installer) yaratadi.
;
;  Kompilyatsiya:
;    "C:\Users\<user>\AppData\Local\Programs\Inno Setup 6\ISCC.exe" installer.iss
;  yoki build_installer.bat faylini ishga tushiring.
;
;  Natija: Output\XeshTahlil_Setup.exe
; ============================================================

#define AppName "Yengil Xesh Funksiyalar Tahlili"
#define AppVersion "1.0"
#define AppPublisher "Diplom ishi"
#define AppExeName "XeshTahlil.exe"

[Setup]
; Ilovaning noyob identifikatori (GUID)
AppId={{8F3A2B71-4C9D-4E2A-9B1F-7D6C5E4A3B21}
AppName={#AppName}
AppVersion={#AppVersion}
AppPublisher={#AppPublisher}
DefaultDirName={autopf}\XeshTahlil
DefaultGroupName={#AppName}
; O'rnatishni oddiy foydalanuvchi (admin huquqisiz) ham bajara olishi uchun
PrivilegesRequiredOverridesAllowed=dialog
OutputDir=Output
OutputBaseFilename=XeshTahlil_Setup
SetupIconFile=icon.ico
Compression=lzma2/max
SolidCompression=yes
WizardStyle=modern
; O'rnatishdan keyin ilovani ishga tushirish uchun
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible

[Languages]
Name: "default"; MessagesFile: "compiler:Default.isl"

[Tasks]
; Ish stoliga yorliq qo'shish (foydalanuvchi tanlovi)
Name: "desktopicon"; Description: "Ish stoliga yorliq qo'shish"; GroupDescription: "Qo'shimcha yorliqlar:"; Flags: unchecked

[Files]
; Butun onedir papkasini o'rnatish papkasiga ko'chiramiz
Source: "dist\XeshTahlil\*"; DestDir: "{app}"; Flags: recursesubdirs createallsubdirs ignoreversion

[Icons]
; Start menyu yorlig'i
Name: "{group}\{#AppName}"; Filename: "{app}\{#AppExeName}"
; Start menyudan o'chirish yorlig'i
Name: "{group}\{#AppName} ni o'chirish"; Filename: "{uninstallexe}"
; Ish stoli yorlig'i (agar tanlangan bo'lsa)
Name: "{autodesktop}\{#AppName}"; Filename: "{app}\{#AppExeName}"; Tasks: desktopicon

[Run]
; O'rnatish tugagach ilovani ishga tushirish imkoni
Filename: "{app}\{#AppExeName}"; Description: "Ilovani hozir ishga tushirish"; Flags: nowait postinstall skipifsilent
