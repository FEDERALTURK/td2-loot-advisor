@echo off
rem TD2 Loot Advisor sunucusunu gunceller (npx wrangler deploy). Cikti: deploy_log.txt
cd /d "%~dp0"
set CI=1
echo %date% %time% > deploy_log.txt
call npx --yes wrangler deploy >> deploy_log.txt 2>&1
echo EXIT %ERRORLEVEL% >> deploy_log.txt
