#!/usr/bin/env bash
# Publica spotonerealty.com (GitHub Pages, rama main).
# Solo se corre por orden de Dario. Uso: ./deploy.sh "mensaje del cambio"
#
# 17-nov-2026: corrige el «error de rama» y evita choques entre sesiones:
#  - solo publica desde main (antes empujaba main aunque estuvieras en otra rama);
#  - trae origin/main antes de publicar (fast-forward, o se detiene si hay choque);
#  - verifica el sitemap y nunca sube .claude/, respaldos .bak ni archivos sueltos de Mac.
set -euo pipefail
cd "$(dirname "$0")"

MSG="${1:-}"
if [[ -z "$MSG" ]]; then
  echo "✗ Falta el mensaje: ./deploy.sh \"qué cambia\""; exit 1
fi

BR=$(git rev-parse --abbrev-ref HEAD)
if [[ "$BR" != "main" ]]; then
  echo "✗ Estás en la rama «$BR». Publica desde main:"
  echo "    git checkout main && git merge --ff-only $BR"
  exit 1
fi

echo "→ Trayendo origin/main…"
git fetch -q origin
if ! git merge --ff-only -q origin/main 2>/dev/null; then
  echo "✗ origin/main tiene cambios que chocan con los tuyos. Haz «git merge origin/main», resuelve y vuelve a correr."
  exit 1
fi

echo "→ Generando sitemap.xml…"
python3 build-sitemap.py >/dev/null
python3 build-sitemap.py --check

git add -A -- . ':(exclude).claude' ':(exclude)*.bak*' ':(exclude).DS_Store'
if git diff --cached --quiet; then
  echo "✓ Sin cambios para publicar."
  exit 0
fi

git commit -q -m "$MSG"
git push -q origin main
echo "✓ Publicado: $(git rev-parse --short HEAD) · https://www.spotonerealty.com/"
echo "  GitHub Pages tarda 1–2 minutos. Verifica en vivo con ?nc=1 al final de la URL."
