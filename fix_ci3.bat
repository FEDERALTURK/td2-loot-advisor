@echo off
cd /d "C:\Users\PC\Desktop\Thedivision2program"

echo [1/5] Merge durumu kontrol ediliyor...
git status

echo.
echo [2/5] Tum conflict dosyalari 'theirs' (remote) ile cozuluyor...
git checkout --theirs .
git add .

echo [3/5] Node surumu 22.5 olarak sabitleniyor...
powershell -Command "(Get-Content .github/workflows/translate-check.yml) -replace 'node-version: \"22\"', 'node-version: \"22.5\"' | Set-Content .github/workflows/translate-check.yml"

echo [4/5] test_tasks_live.py stderr=DEVNULL guncelleniyor...
powershell -Command "(Get-Content tests/test_tasks_live.py) -replace 'stderr=subprocess.DEVNULL', 'stderr=subprocess.PIPE, text=True' | Set-Content tests/test_tasks_live.py"

echo [5/5] Git add, commit ve push yapiliyor...
git add .github/workflows/translate-check.yml tests/test_tasks_live.py
git commit -m "fix: pin Node.js to 22.5+ and capture dev_server stderr in CI"
git push

echo.
echo TAMAMLANDI!
pause
