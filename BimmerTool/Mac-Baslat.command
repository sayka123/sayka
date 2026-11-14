#!/bin/sh
cd -- "$(dirname -- "$0")" || exit 1
if ! command -v python3 >/dev/null 2>&1; then
    printf '\nPython 3 bulunamadi. python.org adresinden Python 3.10 veya uzerini kurun.\n'
    printf 'Kapatmak icin Enter tusuna basin.'
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
