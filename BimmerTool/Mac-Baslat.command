#!/bin/sh
cd -- "$(dirname -- "$0")" || exit 1
if ! command -v python3 >/dev/null 2>&1; then
    printf '\nPython 3 bulunamadi. python.org adresinden Python 3.10 veya uzerini kurun.\n'
    printf 'Kapatmak icin Enter tusuna basin.'
    read -r answer
    exit 1
fi
if ! python3 -c 'import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1)' 2>/dev/null; then
    printf '\nPython 3.10 veya uzeri gerekiyor. python.org adresinden guncelleyin.\n'
    read -r answer
    exit 1
fi
if ! python3 -c 'import tkinter' 2>/dev/null; then
    printf '\nBu Python kurulumunda Tkinter eksik. python.org macOS kurulumunu kullanin.\n'
    read -r answer
    exit 1
fi
python3 -m bimmertool.gui
result=$?
if [ "$result" -ne 0 ]; then
    printf '\nProgram acilamadi. Yukaridaki hatanin ekran goruntusunu paylasin.\n'
    printf 'Kapatmak icin Enter tusuna basin.'
    read -r answer
fi
exit "$result"
