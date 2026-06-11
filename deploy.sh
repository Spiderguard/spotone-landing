#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"

MSG="${1:-update}"

# Regenera el sitemap automaticamente leyendo lo que cada pagina declara.
# Asi nunca hay que editar sitemap.xml a mano.
echo "→ Generando sitemap.xml…"
python3 build-sitemap.py

if [[ -z "$(git status --porcelain)" ]]; then
  echo "✓ Sin cambios para publicar."
  exit 0
fi

git add -A
git commit -m "$MSG"
git push origin main

echo ""
echo "✓ Cambios publicados."
URL=$(gh repo view --json url -q .url 2>/dev/null || echo "")
if [[ -n "$URL" ]]; then
  USER=$(echo "$URL" | awk -F/ '{print $(NF-1)}')
  REPO=$(echo "$URL" | awk -F/ '{print $NF}')
  echo "  Live: https://${USER}.github.io/${REPO}/"
fi
