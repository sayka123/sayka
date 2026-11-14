@echo off
cd /d "%~dp0"
where py >nul 2>nul
if errorlevel 1 goto python
py -3 -m bimmertool.gui
if errorlevel 1 goto failed
exit /b 0
:python
where python >nul 2>nul
if errorlevel 1 goto missing
python -m bimmertool.gui
if errorlevel 1 goto failed
exit /b 0
:missing
echo Python bulunamadi. python.org adresinden Python 3.10 veya uzerini kurun.
pause
exit /b 1
:failed
echo Program acilamadi. Yukaridaki hatanin ekran goruntusunu paylasin.
pause
exit /b 1
