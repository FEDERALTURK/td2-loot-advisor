@echo off
setlocal EnableExtensions EnableDelayedExpansion
REM ==========================================================================
REM  TD2 Loot Advisor - kurulum dosyasi olusturucu / installer builder
REM  Cift tikla: once programi derler (PyInstaller), sonra kurulum dosyasi
REM  uretir (Inno Setup):  installer\TD2LootAdvisor_Setup_<surum>.exe
REM  Inno Setup yoksa kurmayi dener; olmazsa tasinabilir ZIP uretir.
REM  Kisisel dosyalarin (builds.json, stash.json, private\, lisans) pakete GIRMEZ.
REM ==========================================================================
cd /d "%~dp0.."
title TD2 Loot Advisor - kurulum dosyasi olusturuluyor

REM ---- 1) Python secimi (3.13 > 3.12 > 3.11 > varsayilan)
set "PY="
for %%V in (3.13 3.12 3.11) do (
  if not defined PY (
    py -%%V -c "import sys" >nul 2>&1 && set "PY=py -%%V"
  )
)
if not defined PY set "PY=python"
%PY% -c "import sys; assert (3,10) <= sys.version_info[:2] <= (3,14), sys.version" >nul 2>&1
if errorlevel 1 (
  echo [HATA] Uygun Python bulunamadi. Python 3.13 kurun: https://www.python.org/downloads/
  echo [ERROR] No suitable Python found. Install Python 3.13.
  goto :fail
)
for /f "delims=" %%v in ('%PY% -c "import sys;print(sys.version.split()[0])"') do set "PYVER=%%v"
echo [1/7] Python: %PY% (%PYVER%)

REM ---- 2) Paketler
echo [2/7] Paketler kuruluyor / installing packages...
%PY% -m pip install --upgrade pip >nul 2>&1
%PY% -m pip install -r requirements.txt pyinstaller
if errorlevel 1 (
  echo [HATA] Temel paketler kurulamadi. Yukaridaki hatayi okuyun.
  goto :fail
)
REM Istege bagli: yeni OCR motoru, QR, ses (kurulamazsa paket onlarsiz derlenir)
for %%P in (onnxruntime rapidocr qrcode pyttsx3 sounddevice numpy) do (
  %PY% -m pip install %%P >nul 2>&1 || echo     [UYARI] %%P kurulamadi, onsuz devam / skipped
)

REM ---- 3) OCR modellerini indir (pakete girsin, ilk acilista beklenmesin)
echo [3/7] OCR modelleri hazirlaniyor / preparing OCR models...
set "COLLECT="
%PY% -c "import rapidocr, onnxruntime" >nul 2>&1 && (
  %PY% -c "import ocr_backend; from PIL import Image; ocr_backend.Engine('rapidocr').text(Image.new('RGB',(64,32)))" >nul 2>&1
  set "COLLECT=--collect-all rapidocr --collect-all onnxruntime"
)
if not defined COLLECT echo     [UYARI] RapidOCR yok: paket Tesseract ile calisir (kullanicida Tesseract kurulu olmali).

REM ---- 4) Temiz varsayilan ayarlar + simge + surum
echo [4/7] Paket hazirlaniyor / preparing package...
if exist build\pkg rmdir /s /q build\pkg
mkdir build\pkg >nul 2>&1
copy /Y scripts\default_builds.json build\pkg\builds.json >nul
if exist icon\td2.ico (copy /Y icon\td2.ico build\td2.ico >nul) else (%PY% scripts\make_icon.py build\td2.ico >nul)
for /f "delims=" %%v in ('%PY% scripts\version.py') do set "VER=%%v"
if not defined VER set "VER=5.0"
echo     Surum / version: %VER%

REM ---- 5) Derleme (PyInstaller, klasor modu: hizli acilis)
echo [5/7] Program derleniyor (birkac dakika) / building...
if exist dist\TD2LootAdvisor rmdir /s /q dist\TD2LootAdvisor
%PY% -m PyInstaller --noconfirm --clean --onedir --noconsole --name TD2LootAdvisor ^
  --icon build\td2.ico ^
  --add-data "build\pkg\builds.json;." ^
  --add-data "lang;lang" ^
  --add-data "meta;meta" ^
  --add-data "icon;icon" ^
  --hidden-import PIL._tkinter_finder --hidden-import PIL.ImageTk ^
  --hidden-import pynput.keyboard._win32 --hidden-import pynput.mouse._win32 ^
  --hidden-import pyttsx3.drivers --hidden-import pyttsx3.drivers.sapi5 ^
  --hidden-import ocr_backend --hidden-import features --hidden-import stash --hidden-import vendor ^
  --hidden-import companion --hidden-import share --hidden-import dropstats ^
  --hidden-import fx --hidden-import bgvideo --hidden-import view3d --hidden-import display ^
  --exclude-module faster_whisper --exclude-module ctranslate2 --exclude-module torch --exclude-module av ^
  %COLLECT% ^
  app.py
if errorlevel 1 goto :fail
if not exist "dist\TD2LootAdvisor\TD2LootAdvisor.exe" (
  echo [HATA] Derleme cikti uretmedi / build produced no exe.
  goto :fail
)

REM ---- 6) Inno Setup bul (yoksa kurmayi dene)
echo [6/7] Kurulum araci araniyor / looking for Inno Setup...
call :find_iscc
if not defined ISCC (
  echo     Inno Setup yok, kuruluyor / installing Inno Setup ^(winget^)...
  if defined CI (choco install innosetup -y --no-progress >nul 2>&1) else (winget install --id JRSoftware.InnoSetup -e --silent --accept-package-agreements --accept-source-agreements >nul 2>&1)
  call :find_iscc
)

REM ---- 7) Kurulum dosyasi (ya da tasinabilir ZIP)
if not exist installer mkdir installer
if defined ISCC (
  echo [7/7] Kurulum dosyasi olusturuluyor / building installer...
  "!ISCC!" /Q /DAppVersion=%VER% scripts\installer.iss
  if errorlevel 1 goto :fail
  set "OUT=installer\TD2LootAdvisor_Setup_%VER%.exe"
) else (
  echo [7/7] Inno Setup kurulamadi: tasinabilir ZIP uretiliyor / making portable ZIP...
  powershell -NoProfile -Command "Compress-Archive -Path 'dist\TD2LootAdvisor\*' -DestinationPath 'installer\TD2LootAdvisor_%VER%_portable.zip' -Force"
  if errorlevel 1 goto :fail
  set "OUT=installer\TD2LootAdvisor_%VER%_portable.zip"
)

echo.
echo ==========================================================================
echo  BITTI / DONE:  !OUT!
echo  Bu dosyayi baskalarina verebilirsin. Kurulum yonetici izni istemez.
echo  Kisisel ayarlarin, lisansin ve private klasorun pakette YOK.
echo ==========================================================================
if not defined CI (
  explorer /select,"%CD%\!OUT!"
  pause
)
exit /b 0

:find_iscc
set "ISCC="
for %%I in ("%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe" "%ProgramFiles%\Inno Setup 6\ISCC.exe" "%LOCALAPPDATA%\Programs\Inno Setup 6\ISCC.exe") do (
  if not defined ISCC if exist "%%~I" set "ISCC=%%~I"
)
if not defined ISCC (
  for /f "delims=" %%I in ('where ISCC 2^>nul') do if not defined ISCC set "ISCC=%%I"
)
exit /b 0

:fail
echo.
echo [HATA] Islem tamamlanamadi. Yukaridaki mesajlara bakin. / Build failed, see messages above.
if not defined CI pause
exit /b 1
