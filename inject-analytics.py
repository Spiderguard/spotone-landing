#!/usr/bin/env python3
"""
Inyecta el tag de analítica de SpotOne en el <head> de cada página real.

- Idempotente: si la página ya tiene el tag, no hace nada.
- Salta los redirects (http-equiv="refresh") — no tiene sentido medir un stub
  que rebota al instante.
- Una sola fuente de verdad: el código vive en /js/spotone-analytics.js; aquí
  solo se garantiza que cada página lo cargue.

Se corre solo en cada ./deploy.sh, igual que build-sitemap.py. Así toda página
nueva queda instrumentada sin tener que acordarse de pegar nada.
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parent
TAG = '<script defer src="/js/spotone-analytics.js"></script>'
MARKER = "/js/spotone-analytics.js"


def is_redirect(html: str) -> bool:
    low = html.lower()
    return 'http-equiv="refresh"' in low or "location.replace(" in low


def main() -> None:
    injected, skipped_redirect, already, no_head = 0, 0, 0, 0

    for path in sorted(ROOT.rglob("*.html")):
        if ".git" in path.parts:
            continue
        html = path.read_text(encoding="utf-8")

        if is_redirect(html):
            skipped_redirect += 1
            continue
        if MARKER in html:
            already += 1
            continue
        if "</head>" not in html:
            no_head += 1
            continue

        # Inserta el tag justo antes de </head>, respetando la indentación.
        updated = html.replace("</head>", f"{TAG}\n</head>", 1)
        path.write_text(updated, encoding="utf-8")
        injected += 1
        print(f"  + {path.relative_to(ROOT)}")

    print(
        f"\nAnalítica: {injected} inyectadas · {already} ya tenían · "
        f"{skipped_redirect} redirects saltados · {no_head} sin <head>"
    )


if __name__ == "__main__":
    main()
