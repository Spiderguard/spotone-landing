#!/usr/bin/env python3
"""
IndexNow para spotonerealty.com: avisa a Bing (y a los buscadores de IndexNow)
SOLO las URLs públicas nuevas, modificadas o retiradas entre dos commits.

deploy.sh lo llama después del push:
    python3 indexnow.py --desde <origin/main antes> --hasta HEAD

Qué hace, en orden:
  1. Calcula las URLs: compara el sitemap.xml de los dos commits (nuevas / retiradas)
     y las páginas cuyo archivo cambió y siguen en el sitemap (modificadas).
     CSS, JS, imágenes sueltas y páginas sin canonical no se notifican.
  2. Verifica producción: el sitemap en vivo y cada página nueva o modificada deben
     ser idénticos byte a byte al commit; las retiradas no deben seguir en el sitemap
     en vivo. Además, el archivo de clave debe responder. Si no cuadra en 6 min, no envía.
  3. Quita lo ya enviado con éxito (misma URL + mismo contenido) según el registro.
  4. Envía un solo POST a https://api.indexnow.org/indexnow.
     200/202 = aceptado. 400/403/422 = error de datos: no se reintenta.
     429 = demasiadas solicitudes: no se reintenta ahora. 5xx o red: hasta 3 intentos.
  5. Registra todo en ~/.spotone/logs/indexnow.jsonl (una línea por corrida).

Uso:
  python3 indexnow.py --desde A --hasta B            # verifica y envía
  python3 indexnow.py --desde A --hasta B --simular  # verifica, no envía
  python3 indexnow.py --desde A --hasta B --simular --sin-verificar   # solo lista
IndexNow facilita el descubrimiento; no garantiza la indexación.
"""
from __future__ import annotations

import argparse
import datetime
import hashlib
import json
import os
import re
import subprocess
import sys
import time
import urllib.error
import urllib.request

HOST = "www.spotonerealty.com"
BASE = f"https://{HOST}"
KEY = "d6e6a6ac3a5e1453499923e089bb6c32"
KEY_LOCATION = f"{BASE}/{KEY}.txt"
API = os.environ.get("INDEXNOW_API", "https://api.indexnow.org/indexnow")  # override solo para pruebas
ROOT = os.path.dirname(os.path.abspath(__file__))
LOG = os.environ.get("INDEXNOW_LOG", os.path.expanduser("~/.spotone/logs/indexnow.jsonl"))
UA = "spotone-indexnow/1.0"
CANON = re.compile(r'<link[^>]+rel="canonical"[^>]+href="([^"]+)"', re.I)
LOC = re.compile(r"<loc>([^<]+)</loc>")


def git(*args: str, binary: bool = False):
    out = subprocess.run(["git", *args], cwd=ROOT, capture_output=True, check=True).stdout
    return out if binary else out.decode()


def show(rev: str, path: str) -> bytes | None:
    try:
        return git("show", f"{rev}:{path}", binary=True)
    except subprocess.CalledProcessError:
        return None


def sitemap_urls(rev: str) -> set[str]:
    data = show(rev, "sitemap.xml") or b""
    return set(LOC.findall(data.decode("utf-8", "replace")))


def canonical(data: bytes | None) -> str | None:
    if not data:
        return None
    m = CANON.search(data.decode("utf-8", "replace"))
    return m.group(1).strip() if m else None


def calcular(desde: str, hasta: str):
    viejo, nuevo = sitemap_urls(desde), sitemap_urls(hasta)
    nuevas = nuevo - viejo
    retiradas = viejo - nuevo
    archivos: dict[str, str] = {}  # url -> archivo en el commit nuevo
    cambiados = git("diff", "--name-only", "--no-renames", desde, hasta).split()
    modificadas = set()
    for f in cambiados:
        if not f.endswith(".html"):
            continue
        url = canonical(show(hasta, f))
        if url and url in nuevo:
            archivos[url] = f
            if url not in nuevas:
                modificadas.add(url)
        else:
            url_vieja = canonical(show(desde, f))
            if url_vieja and url_vieja in viejo and url_vieja not in nuevo:
                retiradas.add(url_vieja)
    # Una página nueva puede no tener su archivo en el diff si solo cambió el sitemap.
    for url in nuevas - archivos.keys():
        f = archivo_de(url, hasta)
        if f:
            archivos[url] = f
    return sorted(nuevas), sorted(modificadas), sorted(retiradas), archivos


def archivo_de(url: str, rev: str) -> str | None:
    path = url[len(BASE):].lstrip("/") if url.startswith(BASE) else None
    if path is None:
        return None
    if not path.endswith(".html"):
        path = f"{path.rstrip('/')}/index.html" if path else "index.html"
    return path if show(rev, path) is not None else None


def fetch(url: str) -> tuple[int, bytes]:
    sep = "&" if "?" in url else "?"
    req = urllib.request.Request(f"{url}{sep}nc={int(time.time()*1000)}",
                                 headers={"User-Agent": UA, "Cache-Control": "no-cache"})
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            return r.status, r.read()
    except urllib.error.HTTPError as e:
        return e.code, b""
    except Exception:
        return 0, b""


def sha(b: bytes | None) -> str:
    return hashlib.sha256(b or b"").hexdigest()


def verificar(hasta: str, nuevas, modificadas, retiradas, archivos, espera: int = 360) -> list[str]:
    """Devuelve la lista de fallas (vacía = producción al día)."""
    esperado_sitemap = show(hasta, "sitemap.xml")
    fin = time.time() + espera
    while True:
        fallas = []
        st, key = fetch(KEY_LOCATION)
        if st != 200 or key.decode("utf-8", "replace").strip() != KEY:
            fallas.append(f"clave {KEY_LOCATION} → {st}")
        st, sm = fetch(f"{BASE}/sitemap.xml")
        if sha(sm) != sha(esperado_sitemap):
            fallas.append(f"sitemap en vivo ≠ commit (HTTP {st})")
        vivas = set(LOC.findall(sm.decode("utf-8", "replace")))
        for url in retiradas:
            if url in vivas:
                fallas.append(f"retirada sigue en el sitemap en vivo: {url}")
        for url in [*nuevas, *modificadas]:
            f = archivos.get(url)
            st, body = fetch(url)
            if st != 200 or (f and sha(body) != sha(show(hasta, f))):
                fallas.append(f"{url} → HTTP {st}, contenido {'ok' if f and sha(body)==sha(show(hasta, f)) else 'distinto'}")
        if not fallas or time.time() >= fin:
            return fallas
        time.sleep(20)


def ya_enviadas() -> set[str]:
    hechas = set()
    if not os.path.exists(LOG):
        return hechas
    with open(LOG, encoding="utf-8") as fh:
        for line in fh:
            try:
                r = json.loads(line)
            except ValueError:
                continue
            if r.get("resultado") == "aceptado":
                hechas.update(r.get("huellas", []))
    return hechas


def huella(url: str, hasta: str, archivos, retirada: bool) -> str:
    if retirada:
        return f"{url}|retirada"
    return f"{url}|{sha(show(hasta, archivos[url])) if url in archivos else hasta}"


def enviar(urls: list[str]) -> tuple[str, int, str]:
    body = json.dumps({"host": HOST, "key": KEY, "keyLocation": KEY_LOCATION,
                       "urlList": urls}).encode()
    for intento in range(3):
        req = urllib.request.Request(API, data=body, method="POST", headers={
            "Content-Type": "application/json; charset=utf-8", "User-Agent": UA})
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                return "aceptado", r.status, r.read(500).decode("utf-8", "replace")
        except urllib.error.HTTPError as e:
            txt = e.read(500).decode("utf-8", "replace")
            if e.code in (400, 403, 422):
                return "error_datos", e.code, txt
            if e.code == 429:
                return "limite", e.code, txt
            ultimo = ("error_servidor", e.code, txt)
        except Exception as e:  # red
            ultimo = ("error_red", 0, str(e)[:300])
        time.sleep((5, 15, 0)[intento])
    return ultimo


def registrar(r: dict) -> None:
    os.makedirs(os.path.dirname(LOG), exist_ok=True)
    with open(LOG, "a", encoding="utf-8") as fh:
        fh.write(json.dumps(r, ensure_ascii=False) + "\n")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--desde", required=True)
    ap.add_argument("--hasta", default="HEAD")
    ap.add_argument("--simular", action="store_true", help="no envía ni registra éxito")
    ap.add_argument("--sin-verificar", action="store_true", help="solo con --simular")
    ap.add_argument("--espera", type=int, default=360)
    a = ap.parse_args()
    if a.sin_verificar and not a.simular:
        print("✗ --sin-verificar solo se permite con --simular"); return 2
    desde = git("rev-parse", a.desde).strip()
    hasta = git("rev-parse", a.hasta).strip()
    nuevas, modificadas, retiradas, archivos = calcular(desde, hasta)
    print(f"IndexNow {desde[:8]}..{hasta[:8]}: {len(nuevas)} nuevas · "
          f"{len(modificadas)} modificadas · {len(retiradas)} retiradas")
    for etiqueta, lista in (("+", nuevas), ("~", modificadas), ("-", retiradas)):
        for u in lista:
            print(f"  {etiqueta} {u}")
    reg = {"fecha": datetime.datetime.now().isoformat(timespec="seconds"),
           "desde": desde, "hasta": hasta, "simulado": a.simular,
           "nuevas": nuevas, "modificadas": modificadas, "retiradas": retiradas}
    if not (nuevas or modificadas or retiradas):
        print("✓ Nada que notificar."); return 0

    if not a.sin_verificar:
        fallas = verificar(hasta, nuevas, modificadas, retiradas, archivos, a.espera)
        if fallas:
            print("✗ Producción no coincide con el commit; no se envía nada:")
            for f in fallas[:15]:
                print("   ·", f)
            reg.update(resultado="sin_verificar", fallas=fallas)
            if not a.simular:
                registrar(reg)
            return 1
        print("✓ Producción verificada (sitemap, páginas y clave).")

    hechas = ya_enviadas()
    pend = [(u, huella(u, hasta, archivos, u in retiradas)) for u in [*nuevas, *modificadas, *retiradas]]
    pend = [(u, h) for u, h in pend if h not in hechas]
    if not pend:
        print("✓ Todo ya estaba notificado; no se repite."); return 0
    if a.simular:
        print(f"(simulación) se enviarían {len(pend)} URL a {API}"); return 0

    resultado, codigo, texto = enviar([u for u, _ in pend])
    reg.update(resultado=resultado, http=codigo, respuesta=texto,
               enviadas=[u for u, _ in pend], huellas=[h for _, h in pend])
    registrar(reg)
    simbolo = "✓" if resultado == "aceptado" else "✗"
    print(f"{simbolo} IndexNow: {resultado} (HTTP {codigo}). Registro: {LOG}")
    return 0 if resultado == "aceptado" else 1


if __name__ == "__main__":
    sys.exit(main())
