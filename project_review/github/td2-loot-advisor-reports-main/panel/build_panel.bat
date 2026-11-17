@echo off
REM TD2 Rapor Paneli - tek dosyalik Windows programi (dist\TD2RaporPaneli.exe)
cd /d "%~dp0\.."
python -m pip install --quiet pyinstaller pystray pillow
set "ICON=%CD%\icon\td2.ico"
if not exist "%ICON%" set "ICON=%~dp0..\..\..\..\icon\td2.ico"
if not exist "%ICON%" (
  echo HATA: td2.ico bulunamadi.
  exit /b 2
)
python -m PyInstaller --noconfirm --onefile --windowed --name TD2RaporPaneli --icon "%ICON%" --add-data "%ICON%;icon" --paths "%CD%\panel" --hidden-import github_api --hidden-import license_tab --hidden-import tasks_tab --hidden-import dashboard_tab --hidden-import lock --hidden-import selfupdate --hidden-import tray --hidden-import pystray._win32 --distpath dist\panel --workpath build\panel --specpath build\panel panel\panel.py
if errorlevel 1 exit /b 1
echo.
echo Hazir: dist\panel\TD2RaporPaneli.exe

