@echo off
title Gary IPTV
cd /d "%~dp0"
where node >nul 2>nul
if errorlevel 1 (
  echo Node.js bulunamadi. https://nodejs.org adresinden LTS surumunu kurup tekrar deneyin.
  start https://nodejs.org
  pause
  exit /b 1
)
start "" http://localhost:8080
node server.js
pause
