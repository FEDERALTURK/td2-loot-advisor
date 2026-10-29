@echo off
REM TD2 Loot Advisor v5 - .exe olusturucu / .exe builder (Windows)
REM NOT: Ses ozellikleri (faster-whisper) .exe'yi cok buyutur (yuzlerce MB).
REM Sorun yasarsan run.bat ile calistirmak en guvenli yoldur.
REM NOTE: the voice features make the .exe very large. If it fails, use run.bat.
REM Proje kok klasorune gec / switch to project root
cd /d "%~dp0.."

REM Python secimi: beta CI TD2_PYTHON ile 3.14'u sabitler; yerelde 3.13 tercih edilir.
set "PY=python"
if defined TD2_PYTHON py -%TD2_PYTHON% -c "import sys" >nul 2>&1 && set "PY=py -%TD2_PYTHON%" && goto :have_py
py -3.13 -c "import sys" >nul 2>&1 && set "PY=py -3.13" && goto :have_py
py -3.12 -c "import sys" >nul 2>&1 && set "PY=py -3.12" && goto :have_py
:have_py
echo Kullanilan Python / Python in use: %PY%

%PY% -m pip install -r requirements.txt
%PY% -m pip install pyinstaller
REM Ses paketleri opsiyonel; kurulamazsa .exe sessiz surumle derlenir.
REM Voice packages are optional; if they fail, the .exe is built without voice.
%PY% -m pip install -r requirements-voice.txt
REM Yeni OCR motoru (onerilen) / new OCR engine (recommended)
%PY% -m pip install onnxruntime-directml rapidocr qrcode
%PY% -c "import ocr_backend; ocr_backend.Engine('rapidocr').text(__import__('PIL.Image').Image.new('RGB',(64,32)))"

REM Kisisel builds.json pakete GIRMEZ: temiz varsayilan ayarlar kullanilir
if not exist build\pkg mkdir build\pkg
copy /Y scripts\default_builds.json build\pkg\builds.json >nul

%PY% -m PyInstaller --onefile --noconsole --name TD2LootAdvisor --icon icon\td2.ico ^
  --add-data "build\pkg\builds.json;." ^
  --add-data "lang;lang" ^
  --add-data "meta;meta" ^
  --collect-all edge_tts --collect-all aiohttp --copy-metadata edge-tts ^
  --add-data "icon;icon" ^
  --add-data "art/agents;art/agents" --add-data "art/branding;art/branding" --add-data "art/backgrounds;art/backgrounds" ^
  --hidden-import PIL._tkinter_finder ^
  --hidden-import pyttsx3.drivers --hidden-import pyttsx3.drivers.sapi5 ^
  --hidden-import ocr_backend --hidden-import features --hidden-import stash --hidden-import vendor --hidden-import companion --hidden-import share --hidden-import dropstats --hidden-import fx --hidden-import bgvideo --hidden-import view3d --hidden-import display --hidden-import updater --hidden-import syncer --hidden-import gameinfo --hidden-import updates --hidden-import reports --hidden-import account --hidden-import service --hidden-import screenstate --hidden-import localapi --hidden-import presence --hidden-import notify --hidden-import knowledge --hidden-import voicepack --hidden-import livetranslate --hidden-import pystray._win32 ^
  --collect-all rapidocr --collect-all onnxruntime --collect-all faster_whisper --collect-all ctranslate2 --collect-all av --collect-all tokenizers --collect-all huggingface_hub ^
  app.py

if not exist dist\lang mkdir dist\lang
copy /Y lang\*.json dist\lang\
if not exist dist\meta mkdir dist\meta
copy /Y meta\*.json dist\meta\

echo.
echo Bitti / Done: dist\TD2LootAdvisor.exe
echo   dist\lang\        - dil dosyalari / language files
echo   dist\meta\        - oyun kutuphanesi ve gunluk listeler / game library and feeds
echo Arka plan videolari ilk acilista otomatik uretilir / background videos are generated on first start.
echo Not: RapidOCR pakete dahil; Tesseract yalniz yedek olarak gerekir / RapidOCR is bundled; Tesseract is only a fallback.
pause
