#!/usr/bin/env python3
"""
Chequeo del índice de propiedades (/propiedades/ y /properties/) y de llms.txt.
N20-36 · 20-nov-2026. Falla (exit 1) si:
  - una tarjeta lleva más de 21 días sin reconfirmar (data-verificado);
  - la fecha de una tarjeta no coincide con el dateModified del RealEstateListing de su ficha;
  - aparece algo de la lista negra: inventario privado o prohibido, bancos, colegas o comisión,
    un teléfono que no sea el de Dario o un correo que no sea info@.
La página se arma a mano desde las fichas; este chequeo no lee ninguna base.

Uso: python3 check-propiedades.py
"""
from __future__ import annotations

import datetime
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
PAGES = ["propiedades/index.html", "properties/index.html"]
SCAN = PAGES + ["llms.txt"]
MAX_DIAS = 21

NEGRA = [
    r"tzanetatos", r"\bmetric\b", r"paitilla", r"shahani", r"mois[eé]s",
    r"\bSH-\d", r"\bGS-\d",
    r"banesco", r"banistmo", r"unibank", r"banco general", r"\bbnp\b", r"lafise",
    r"caja de ahorros", r"global bank", r"reposeíd", r"repossess",
    r"colega", r"colleague", r"comisi[oó]n", r"commission", r"co-?broke",
]
TEL_OK = {"66758127"}
MAIL_OK = {"info@spotonerealty.com"}


def leer(p):
    with open(os.path.join(ROOT, p), encoding="utf-8") as f:
        return f.read()


def fecha_ficha(href):
    p = href.strip("/") + "/index.html"
    s = leer(p)
    for b in re.findall(r'<script type="application/ld\+json">(.*?)</script>', s, re.S):
        d = json.loads(b)
        nodos = d.get("@graph", [d]) if isinstance(d, dict) else d
        for n in nodos:
            if isinstance(n, dict) and n.get("@type") == "RealEstateListing":
                return n.get("dateModified")
    return None


def main():
    hoy = datetime.date.today()
    errores = []
    for p in PAGES:
        s = leer(p)
        tarjetas = re.findall(r'<a class="card" href="([^"]+)" data-verificado="([^"]+)">', s)
        if not tarjetas:
            errores.append(f"{p}: no hay tarjetas con data-verificado")
        for href, f in tarjetas:
            d = datetime.date.fromisoformat(f)
            dias = (hoy - d).days
            if dias > MAX_DIAS:
                errores.append(f"{p}: {href} lleva {dias} días sin reconfirmar (máx. {MAX_DIAS}). Reconfirmar con Dario o quitar la tarjeta.")
            fm = fecha_ficha(href)
            if fm != f:
                errores.append(f"{p}: {href} data-verificado={f}, pero la ficha dice dateModified={fm}")
    for p in SCAN:
        s = leer(p)
        texto = re.sub(r"%[0-9A-F]{2}", lambda m: bytes.fromhex(m.group(0)[1:]).decode("latin-1"), s)
        for pat in NEGRA:
            for m in re.finditer(pat, s, re.I):
                errores.append(f"{p}: lista negra «{m.group(0)}»")
        for m in re.finditer(r"(?<![\d,.])(?:\+?507[\s-]?)?([2-9]\d{3})[\s-]?(\d{4})(?![\d,])", texto):
            n = m.group(1) + m.group(2)
            if n not in TEL_OK and not re.match(r"20[0-9]{2}$", m.group(1)):
                errores.append(f"{p}: teléfono no permitido {m.group(0).strip()}")
        for m in re.finditer(r"[\w.+-]+@[\w-]+\.[\w.]+", s):
            if m.group(0).lower() not in MAIL_OK:
                errores.append(f"{p}: correo no permitido {m.group(0)}")
    if errores:
        print("✗ check-propiedades:")
        for e in errores:
            print("  -", e)
        sys.exit(1)
    n = sum(len(re.findall(r'<a class="card"[^>]*data-verificado', leer(p))) for p in PAGES)
    print(f"✓ check-propiedades: {n} tarjetas al día, lista negra limpia.")


if __name__ == "__main__":
    main()
