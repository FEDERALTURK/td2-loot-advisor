@echo off
REM TD2 Loot Advisor v5 - .exe olusturucu / .exe builder (Windows)
REM NOT: Ses ozellikleri (faster-whisper) .exe'yi cok buyutur (yuzlerce MB).
REM Sorun yasarsan run.bat ile calistirmak en guvenli yoldur.
REM NOTE: the voice features make the .exe very large. If it fails, use run.bat.
REM Proje kok klasorune gec / switch to project root
cd /d "%~dp0.."

REM Python secimi: once 3.13, sonra 3.12, yoksa varsayilan python.
set "PY=python"
py -3.13 -c "import sys" >nul 2>&1 && set "PY=py -3.13" && goto :have_py
py -3.12 -c "import sys" >nul 2>&1 && set "PY=py -3.12" && goto :have_py
:have_py
echo Kullanilan Python / Python in use: %PY%

%PY% -m pip install -r requirements.txt
%PY% -m pip install pyinstaller
REM Ses paketleri opsiyonel; kurulamazsa .exe sessiz surumle derlenir.
REM Voice packages are optional; if they fail, the .exe is built without voice.
%PY% -m pip install -r requirements-voice.txt

%PY% -m PyInstaller --onefile --noconsole --name TD2LootAdvisor ^
  --add-data "builds.json;." ^
  --add-data "lang;lang" ^
  --add-data "meta;meta" ^
  --hidden-import pyttsx3.drivers --hidden-import pyttsx3.drivers.sapi5 ^
  --collect-all faster_whisper --collect-all ctranslate2 ^
  app.py

copy /Y builds.json dist\builds.json
if not exist dist\lang mkdir dist\lang
copy /Y lang\*.json dist\lang\

echo.
echo Bitti / Done: dist\TD2LootAdvisor.exe
echo   dist\builds.json  - ayarlar + build kurallari / settings + build rules
echo   dist\lang\        - dil dosyalari / language files
echo Not: Tesseract OCR ayrica kurulu olmali / must be installed separately.
pause
