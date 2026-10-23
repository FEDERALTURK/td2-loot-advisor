@echo off
REM Claude Code kurulumu ve girisi / Claude Code install and sign-in
REM Resmi Anthropic kurulum komutunu calistirir (yonetici yetkisi gerekmez).
REM Runs the official Anthropic installer (no admin rights needed).
REM Not: Claude Code icin Pro, Max, Team veya Enterprise aboneligi gerekir.
REM Note: Claude Code needs a Pro, Max, Team or Enterprise plan.

set "CLAUDE_EXE=%USERPROFILE%\.local\bin\claude.exe"

if exist "%CLAUDE_EXE%" (
  echo Claude Code zaten kurulu / already installed.
) else (
  echo Claude Code kuruluyor, bu bir dakika surebilir... / Installing Claude Code...
  powershell -NoProfile -ExecutionPolicy Bypass -Command "irm https://claude.ai/install.ps1 | iex"
)

if not exist "%CLAUDE_EXE%" (
  echo.
  echo [HATA] Kurulum tamamlanamadi. / Installation failed.
  pause
  exit /b 1
)

"%CLAUDE_EXE%" --version
echo.
"%CLAUDE_EXE%" auth status --text >NUL 2>&1
if errorlevel 1 (
  echo Simdi giris yapilacak: acilan tarayicida Claude hesabinla onayla.
  echo Now signing in: approve with your Claude account in the browser.
  "%CLAUDE_EXE%" auth login
)
echo.
"%CLAUDE_EXE%" auth status --text
echo.
echo Bitti. Uygulamada Asistan sekmesinden "Claude (abonelik, Claude Code)" sec.
echo Done. In the app choose "Claude (subscription, Claude Code)" on the Assistant tab.
pause
