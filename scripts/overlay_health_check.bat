@echo off
setlocal
cd /d "%~dp0.."
set "TD2_REPORT=%TEMP%\td2-overlay-health-%RANDOM%-%RANDOM%.json"
echo Yerel sentetik pencere testi basliyor. Oyun acik olmak zorunda degil.
echo Test sirasinda pencereyi kapatmayin veya ustunu ortmeyin.
py -3.13 -B app.py --translation-probe models/en-tr "%TD2_REPORT%"
set "TD2_RESULT=%ERRORLEVEL%"
echo Test cikis kodu: %TD2_RESULT%
echo Rapor: %TD2_REPORT%
if exist "%TD2_REPORT%" type "%TD2_REPORT%"
pause
exit /b %TD2_RESULT%
