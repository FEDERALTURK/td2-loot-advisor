@echo off
cd /d "C:\Users\PC\Desktop\Thedivision2program"

echo [1/4] Main branch'e geciliyor...
git checkout main

echo [2/4] Branch merge ediliyor...
git merge codex/division-hud-v9.1.5.39 --no-ff -m "release: merge v9.1.5.39 — Division HUD update"

echo [3/4] Tag olusturuluyor...
git tag v9.1.5.39

echo [4/4] Main ve tag push ediliyor...
git push origin main
git push origin v9.1.5.39

echo.
echo TAMAMLANDI! GitHub Actions build-installer.yml otomatik baslar.
echo Release: https://github.com/FEDERALTURK/td2-loot-advisor/releases
pause
