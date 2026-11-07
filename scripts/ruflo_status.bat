@echo off
cd /d "%~dp0.."
echo Ruflo Node kontrolu:
npx --yes ruflo@latest doctor --json -c node
echo.
echo MCP sunucusu stdio modunda baslatilabilir:
echo npx --yes ruflo@latest mcp start
pause
