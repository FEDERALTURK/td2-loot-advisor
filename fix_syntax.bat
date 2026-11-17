@echo off
cd /d "C:\Users\PC\Desktop\Thedivision2program"

echo [1/3] test_tasks_live.py icindeki duplicate text=True duzeltiliyor...
powershell -Command "(Get-Content 'tests\test_tasks_live.py' -Raw) -replace 'stderr=subprocess\.PIPE, text=True, text=True', 'stderr=subprocess.PIPE, text=True' | Set-Content 'tests\test_tasks_live.py' -NoNewline"

echo [2/3] Degisiklik commit ediliyor...
git add tests/test_tasks_live.py
git commit -m "fix: remove duplicate text=True in Popen call (SyntaxError)

tests/test_tasks_live.py satir 145'teki subprocess.Popen cagrisinda
fix_ci3.bat tarafindan hatali eklenen duplicate text=True kaldirildi.

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_019puJcpmi1mPj3qdczCYr6K"

echo [3/3] main branch'e push ediliyor...
git push origin main

echo.
echo TAMAMLANDI! CI yeniden calisacak ve v9.1.5.39 release olusturulacak.
echo GitHub Actions: https://github.com/FEDERALTURK/td2-loot-advisor/actions
pause
