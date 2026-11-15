#!/bin/sh
# Mac / Linux başlatıcı: çift tıklayın veya terminalde ./baslat.command
cd "$(dirname "$0")" || exit 1
if ! command -v node >/dev/null 2>&1; then
  echo "Node.js bulunamadı. https://nodejs.org adresinden LTS sürümünü kurun."
  exit 1
fi
(sleep 1; open http://localhost:8080 2>/dev/null || xdg-open http://localhost:8080) &
node server.js
