@echo off
REM TD2 Rapor Paneli - tek dosyalik Windows programi (dist\TD2RaporPaneli.exe)
cd /d "%~dp0\.."
python -m pip install --quiet pyinstaller
python -m PyInstaller --noconfirm --onefile --windowed --name TD2RaporPaneli --icon "%CD%\icon\td2.ico" --add-data "%CD%\icon\td2.ico;icon" --paths "%CD%\panel" --hidden-import github_api --distpath dist\panel --workpath build\panel --specpath build\panel panel\panel.py
if errorlevel 1 exit /b 1
echo.
echo Hazir: dist\panel\TD2RaporPaneli.exe
