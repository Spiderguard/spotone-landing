#!/usr/bin/env bash
# Publica spotonerealty.com (GitHub Pages, rama main).
# Solo se corre por orden de Dario. Uso: ./deploy.sh "mensaje del cambio"
#
# 17-nov-2026: corrige el «error de rama» y evita choques entre sesiones:
#  - solo publica desde main (antes empujaba main aunque estuvieras en otra rama);
#  - trae origin/main antes de publicar (fast-forward, o se detiene si hay choque);
#  - verifica el sitemap y nunca sube .claude/, respaldos .bak ni archivos sueltos de Mac.
#
# 23-nov-2026 (TARA, auditoría UX):
#  - si había cambios sin commit Y la copia estaba atrasada, se detiene: esos cambios se hicieron sobre archivos viejos;
#  - corre check-propiedades (tarjetas, lista negra y zonas al día con el catálogo);
#  - si los commits ya están hechos, ahora sí empuja (antes decía «sin cambios» y salía).
#  - corre presencia_visual.js: foto del héroe y WhatsApp en las fichas, menú móvil y desborde a 390 px.
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
ATRAS=$(git rev-list HEAD..origin/main --count)
if [[ "$ATRAS" -gt 0 ]] && [[ -n "$(git status --porcelain)" ]]; then
  echo "✗ Esta copia está $ATRAS commit(s) atrás de origin/main y tiene cambios sin commit."
  echo "  Esos cambios se hicieron sobre archivos viejos. Guárdalos en una rama, actualiza (git pull --ff-only) y rehazlos encima."
  exit 1
fi
if ! git merge --ff-only -q origin/main 2>/dev/null; then
  echo "✗ origin/main tiene cambios que chocan con los tuyos. Haz «git merge origin/main», resuelve y vuelve a correr."
  exit 1
fi

echo "→ Generando sitemap.xml…"
python3 build-sitemap.py >/dev/null
python3 build-sitemap.py --check

if [[ -f "$HOME/.spotone/bin/check-propiedades.py" ]]; then
  python3 "$HOME/.spotone/bin/check-propiedades.py" .
fi
# 23-nov (aprendizaje Peatonal): comprobación visual en perfil iPhone sobre los archivos locales.
if [[ -f "$HOME/.spotone/bin/presencia_visual.js" ]]; then
  node "$HOME/.spotone/bin/presencia_visual.js" .
fi

git add -A   # .claude/, *.bak* y .DS_Store ya están en .gitignore
if ! git diff --cached --quiet; then
  git commit -q -m "$MSG"
fi
if [[ "$(git rev-list origin/main..HEAD --count)" -eq 0 ]]; then
  echo "✓ Sin cambios para publicar."
  exit 0
fi
git push -q origin main
echo "✓ Publicado: $(git rev-parse --short HEAD) · https://www.spotonerealty.com/"
echo "  GitHub Pages tarda 1–2 minutos. Verifica en vivo con ?nc=1 al final de la URL."
