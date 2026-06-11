#!/usr/bin/env python3
"""
Genera sitemap.xml automaticamente leyendo lo que cada pagina ya declara.

Fuente de verdad = el <head> de cada pagina:
  - <link rel="canonical">           -> la URL (loc)
  - <link rel="alternate" hreflang>  -> los pares ES/EN (hreflang)
  - lastmod                          -> hoy si el archivo tiene cambios sin commitear,
                                        si no, la fecha del ultimo commit de ese archivo.

No requiere ninguna lista manual. Para agregar paginas al sitemap, basta con
que tengan <link rel="canonical"> en su <head> y esten en INCLUDE_GLOBS.

Uso:
  python3 build-sitemap.py            # escribe sitemap.xml
  python3 build-sitemap.py --check    # no escribe; falla si esta desactualizado
"""
from __future__ import annotations

import datetime
import glob
import os
import re
import subprocess
import sys

BASE = "https://www.spotonerealty.com"
ROOT = os.path.dirname(os.path.abspath(__file__))

# Que paginas entran al sitemap (rutas relativas al repo).
INCLUDE_GLOBS = [
    "index.html",
    "index-en.html",
    "criterio/index.html",
    "criterio/en/index.html",
    "criterio/*/index.html",
]

# Prioridad por URL exacta; el resto (articulos) usa DEFAULT_PRIORITY.
PRIORITY = {
    f"{BASE}/": "1.0",
    f"{BASE}/index-en.html": "0.9",
    f"{BASE}/criterio/": "0.9",
    f"{BASE}/criterio/en/": "0.8",
}
DEFAULT_PRIORITY = "0.8"

CANONICAL_RE = re.compile(
    r'<link[^>]+rel="canonical"[^>]+href="([^"]+)"', re.IGNORECASE
)
ALT_RE = re.compile(
    r'<link[^>]+rel="alternate"[^>]+hreflang="([^"]+)"[^>]+href="([^"]+)"',
    re.IGNORECASE,
)


def git_lastmod(relpath: str) -> str:
    """Hoy si el archivo cambio en el working tree; si no, fecha del ultimo commit."""
    today = datetime.date.today().isoformat()
    try:
        dirty = subprocess.run(
            ["git", "status", "--porcelain", "--", relpath],
            cwd=ROOT, capture_output=True, text=True, check=True,
        ).stdout.strip()
        if dirty:
            return today
        committed = subprocess.run(
            ["git", "log", "-1", "--format=%cs", "--", relpath],
            cwd=ROOT, capture_output=True, text=True, check=True,
        ).stdout.strip()
        return committed or today
    except (subprocess.CalledProcessError, FileNotFoundError):
        return today


def collect_files() -> list[str]:
    seen, files = set(), []
    for pat in INCLUDE_GLOBS:
        for f in sorted(glob.glob(os.path.join(ROOT, pat))):
            if f not in seen:
                seen.add(f)
                files.append(f)
    return files


def parse_page(path: str) -> dict | None:
    with open(path, encoding="utf-8") as fh:
        html = fh.read()
    m = CANONICAL_RE.search(html)
    if not m:
        return None  # sin canonical -> no entra (evita basura en el sitemap)
    loc = m.group(1).strip()
    alternates = [(lang, href.strip()) for lang, href in ALT_RE.findall(html)]
    rel = os.path.relpath(path, ROOT)
    return {
        "loc": loc,
        "alternates": alternates,
        "lastmod": git_lastmod(rel),
        "priority": PRIORITY.get(loc, DEFAULT_PRIORITY),
    }


def sort_key(u: dict):
    order = {
        f"{BASE}/": 0,
        f"{BASE}/index-en.html": 1,
        f"{BASE}/criterio/": 2,
        f"{BASE}/criterio/en/": 3,
    }
    return (order.get(u["loc"], 99), u["loc"])


def build_xml(urls: list[dict]) -> str:
    out = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"',
        '        xmlns:xhtml="http://www.w3.org/1999/xhtml">',
    ]
    for u in urls:
        out.append("  <url>")
        out.append(f"    <loc>{u['loc']}</loc>")
        for lang, href in u["alternates"]:
            out.append(
                f'    <xhtml:link rel="alternate" hreflang="{lang}" href="{href}"/>'
            )
        out.append(f"    <lastmod>{u['lastmod']}</lastmod>")
        out.append(f"    <priority>{u['priority']}</priority>")
        out.append("  </url>")
    out.append("</urlset>")
    return "\n".join(out) + "\n"


def main() -> int:
    check = "--check" in sys.argv
    urls = [p for p in (parse_page(f) for f in collect_files()) if p]
    urls.sort(key=sort_key)
    xml = build_xml(urls)
    target = os.path.join(ROOT, "sitemap.xml")

    if check:
        current = ""
        if os.path.exists(target):
            with open(target, encoding="utf-8") as fh:
                current = fh.read()
        if current != xml:
            print("✗ sitemap.xml desactualizado. Corre: python3 build-sitemap.py")
            return 1
        print(f"✓ sitemap.xml al dia ({len(urls)} URLs).")
        return 0

    with open(target, "w", encoding="utf-8") as fh:
        fh.write(xml)
    print(f"✓ sitemap.xml generado: {len(urls)} URLs.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
