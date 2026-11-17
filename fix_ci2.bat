@echo off
cd /d "C:\Users\PC\Desktop\Thedivision2program"

echo [1/4] Conflict dosyalari kabul ediliyor (theirs)...
git checkout --theirs tests/test_tasks_live.py
git checkout --theirs .github/workflows/translate-check.yml

echo [2/4] Node surumu 22.5 olarak sabitleniyor...
powershell -Command "(Get-Content .github/workflows/translate-check.yml) -replace 'node-version: \"22\"', 'node-version: \"22.5\"' | Set-Content .github/workflows/translate-check.yml"

echo [3/4] test_tasks_live.py stderr=DEVNULL guncelleniyor...
powershell -Command "(Get-Content tests/test_tasks_live.py) -replace 'stderr=subprocess.DEVNULL', 'stderr=subprocess.PIPE, text=True' | Set-Content tests/test_tasks_live.py"

echo [4/4] Git add, commit ve push yapiliyor...
git add .github/workflows/translate-check.yml tests/test_tasks_live.py
git commit -m "fix: pin Node.js to 22.5+ and capture dev_server stderr in CI"
git push

echo.
echo TAMAMLANDI!
pause
