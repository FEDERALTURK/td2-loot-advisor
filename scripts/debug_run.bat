@echo off
REM Teshis betigi / diagnostic script - silinebilir
cd /d "%~dp0.."
echo === where python === > debug_log.txt
where python >> debug_log.txt 2>&1
where py >> debug_log.txt 2>&1
echo === version === >> debug_log.txt
python --version >> debug_log.txt 2>&1
py -0p >> debug_log.txt 2>&1
echo === pip list === >> debug_log.txt
python -m pip list >> debug_log.txt 2>&1
echo === imports === >> debug_log.txt
python -c "import mss, pytesseract, PIL, pynput, tkinter; print(\"imports ok\")" >> debug_log.txt 2>&1
echo === app.py === >> debug_log.txt
python app.py >> debug_log.txt 2>&1
echo === exit code %errorlevel% === >> debug_log.txt
