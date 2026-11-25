#!/usr/bin/env python3
"""
IndexNow para spotonerealty.com: avisa a Bing (y a los buscadores de IndexNow)
SOLO las URLs públicas nuevas, modificadas o retiradas.

deploy.sh lo llama después del push:
    python3 indexnow.py --desde <origin/main antes del push> --hasta HEAD

Qué hace, en orden:
  1. Rango: desde el CURSOR guardado (último commit ya procesado) o --desde, el más
     antiguo de los dos. Así, si alguien publicó con «git push» sin deploy.sh, la
     siguiente corrida cubre también esos commits.
  2. URLs: compara el sitemap.xml de los dos commits (nuevas / retiradas) y las páginas
     cuyo archivo cambió y siguen en el sitemap (modificadas). CSS, JS, imágenes y
     páginas sin canonical no se notifican. Se suman las PENDIENTES de corridas anteriores.
  3. Persiste: antes de verificar o enviar, guarda pendientes + cursor en
     ~/.spotone/state/indexnow.json. Si la API falla, vence la espera o se corta el
     proceso, las URLs siguen pendientes para la próxima corrida.
  4. Verifica producción: sitemap en vivo y cada página viva idénticos byte a byte al
     commit; cada retirada responde 404/410 y no sigue en el sitemap en vivo; la clave
     responde. Si no cuadra en 6 min, no envía (quedan pendientes).
  5. Quita lo ya aceptado antes (misma URL + mismo contenido) y envía un solo POST a
     https://api.indexnow.org/indexnow.
       200 = enviado · 202 = recibido, clave en validación. Ninguno significa indexado.
       429 = respeta Retry-After (o 1 h): no envía antes de esa hora.
       400/403/422 = error de datos: sin reintento inmediato, quedan pendientes.
       5xx o red = hasta 3 intentos en la misma corrida.
  6. Registra cada corrida en ~/.spotone/logs/indexnow.jsonl.

Uso:
  python3 indexnow.py --desde A --hasta B            # verifica y envía
  python3 indexnow.py                                 # solo pendientes / desde el cursor
  python3 indexnow.py --desde A --hasta B --simular  # verifica, no envía ni guarda estado
  python3 indexnow.py --desde A --hasta B --simular --sin-verificar   # solo lista
  python3 indexnow.py --estado                        # muestra cursor y pendientes
IndexNow facilita el descubrimiento; no garantiza la indexación.
"""
from __future__ import annotations

import argparse
import datetime
import email.utils
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
# Las variables de entorno existen solo para pruebas locales.
API = os.environ.get("INDEXNOW_API", "https://api.indexnow.org/indexnow")
LOG = os.environ.get("INDEXNOW_LOG", os.path.expanduser("~/.spotone/logs/indexnow.jsonl"))
STATE = os.environ.get("INDEXNOW_STATE", os.path.expanduser("~/.spotone/state/indexnow.json"))
ROOT = os.path.dirname(os.path.abspath(__file__))
UA = "spotone-indexnow/1.1"
CANON = re.compile(r'<link[^>]+rel="canonical"[^>]+href="([^"]+)"', re.I)
LOC = re.compile(r"<loc>([^<]+)</loc>")
ACEPTADOS = ("enviado", "recibido_clave_en_validacion")


# ── git ──────────────────────────────────────────────────────────────────────
def git(*args: str, binary: bool = False):
    out = subprocess.run(["git", *args], cwd=ROOT, capture_output=True, check=True).stdout
    return out if binary else out.decode()


def show(rev: str, path: str) -> bytes | None:
    try:
        return git("show", f"{rev}:{path}", binary=True)
    except subprocess.CalledProcessError:
        return None


def es_ancestro(a: str, b: str) -> bool:
    return subprocess.run(["git", "merge-base", "--is-ancestor", a, b], cwd=ROOT,
                          capture_output=True).returncode == 0


def sitemap_urls(rev: str) -> set[str]:
    return set(LOC.findall((show(rev, "sitemap.xml") or b"").decode("utf-8", "replace")))


def canonical(data: bytes | None) -> str | None:
    m = CANON.search(data.decode("utf-8", "replace")) if data else None
    return m.group(1).strip() if m else None


def archivo_de(url: str, rev: str) -> str | None:
    if not url.startswith(BASE):
        return None
    path = url[len(BASE):].lstrip("/")
    if not path.endswith(".html"):
        path = f"{path.rstrip('/')}/index.html" if path else "index.html"
    return path if show(rev, path) is not None else None


def calcular(desde: str, hasta: str):
    if desde == hasta:
        return [], [], []
    viejo, nuevo = sitemap_urls(desde), sitemap_urls(hasta)
    nuevas, retiradas, modificadas = nuevo - viejo, viejo - nuevo, set()
    for f in git("diff", "--name-only", "--no-renames", desde, hasta).split():
        if not f.endswith(".html"):
            continue
        url = canonical(show(hasta, f))
        if url and url in nuevo:
            if url not in nuevas:
                modificadas.add(url)
        else:
            vieja = canonical(show(desde, f))
            if vieja and vieja in viejo and vieja not in nuevo:
                retiradas.add(vieja)
    return sorted(nuevas), sorted(modificadas), sorted(retiradas)


# ── estado y registro ────────────────────────────────────────────────────────
def cargar_estado() -> dict:
    try:
        with open(STATE, encoding="utf-8") as fh:
            e = json.load(fh)
    except (OSError, ValueError):
        e = {}
    e.setdefault("cursor", None)
    e.setdefault("pendientes", {})
    e.setdefault("no_antes_de", None)
    return e


def guardar_estado(e: dict) -> None:
    os.makedirs(os.path.dirname(STATE), exist_ok=True)
    tmp = STATE + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(e, fh, ensure_ascii=False, indent=1)
    os.replace(tmp, STATE)  # escritura atómica: un corte no deja el archivo a medias


def registrar(r: dict) -> None:
    os.makedirs(os.path.dirname(LOG), exist_ok=True)
    with open(LOG, "a", encoding="utf-8") as fh:
        fh.write(json.dumps(r, ensure_ascii=False) + "\n")


def huellas_aceptadas() -> set[str]:
    hechas = set()
    try:
        with open(LOG, encoding="utf-8") as fh:
            for line in fh:
                try:
                    r = json.loads(line)
                except ValueError:
                    continue
                if r.get("resultado") in ACEPTADOS:
                    hechas.update(r.get("huellas", []))
    except OSError:
        pass
    return hechas


def ahora() -> datetime.datetime:
    return datetime.datetime.now(datetime.timezone.utc)


# ── red ──────────────────────────────────────────────────────────────────────
def sha(b: bytes | None) -> str:
    return hashlib.sha256(b or b"").hexdigest()


def fetch(url: str) -> tuple[int, bytes]:
    sep = "&" if "?" in url else "?"
    req = urllib.request.Request(f"{url}{sep}nc={int(time.time() * 1000)}",
                                 headers={"User-Agent": UA, "Cache-Control": "no-cache"})
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            return r.status, r.read()
    except urllib.error.HTTPError as e:
        return e.code, e.read() or b""
    except Exception:
        return 0, b""


def verificar(hasta: str, vivas: list[str], retiradas: list[str], espera: int) -> list[str]:
    """Lista de fallas; vacía = producción coincide con el commit."""
    esperado = show(hasta, "sitemap.xml")
    fin = time.time() + espera
    while True:
        fallas = []
        st, key = fetch(KEY_LOCATION)
        if st != 200 or key.decode("utf-8", "replace").strip() != KEY:
            fallas.append(f"clave {KEY_LOCATION} → HTTP {st}")
        st, sm = fetch(f"{BASE}/sitemap.xml")
        if sha(sm) != sha(esperado):
            fallas.append(f"sitemap en vivo ≠ commit (HTTP {st})")
        en_vivo = set(LOC.findall(sm.decode("utf-8", "replace")))
        for url in vivas:
            f = archivo_de(url, hasta)
            st, body = fetch(url)
            if st != 200 or not f or sha(body) != sha(show(hasta, f)):
                fallas.append(f"{url} → HTTP {st}, contenido distinto al commit")
        for url in retiradas:
            st, _ = fetch(url)
            if st not in (404, 410):
                fallas.append(f"retirada {url} → HTTP {st} (se espera 404/410)")
            if url in en_vivo:
                fallas.append(f"retirada sigue en el sitemap en vivo: {url}")
        if not fallas or time.time() >= fin:
            return fallas
        time.sleep(20)


def retry_after(valor: str | None) -> datetime.datetime:
    if valor:
        valor = valor.strip()
        if valor.isdigit():
            return ahora() + datetime.timedelta(seconds=int(valor))
        try:
            d = email.utils.parsedate_to_datetime(valor)
            return d if d.tzinfo else d.replace(tzinfo=datetime.timezone.utc)
        except (TypeError, ValueError):
            pass
    return ahora() + datetime.timedelta(hours=1)


def enviar(urls: list[str]) -> dict:
    body = json.dumps({"host": HOST, "key": KEY, "keyLocation": KEY_LOCATION,
                       "urlList": urls}).encode()
    ultimo: dict = {}
    for intento in range(3):
        req = urllib.request.Request(API, data=body, method="POST", headers={
            "Content-Type": "application/json; charset=utf-8", "User-Agent": UA})
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                txt = r.read(500).decode("utf-8", "replace")
                res = "recibido_clave_en_validacion" if r.status == 202 else "enviado"
                return {"resultado": res, "http": r.status, "respuesta": txt}
        except urllib.error.HTTPError as e:
            txt = e.read(500).decode("utf-8", "replace")
            if e.code in (400, 403, 422):
                return {"resultado": "error_datos", "http": e.code, "respuesta": txt}
            if e.code == 429:
                return {"resultado": "limite", "http": 429, "respuesta": txt,
                        "no_antes_de": retry_after(e.headers.get("Retry-After")).isoformat()}
            ultimo = {"resultado": "error_servidor", "http": e.code, "respuesta": txt}
        except Exception as e:
            ultimo = {"resultado": "error_red", "http": 0, "respuesta": str(e)[:300]}
        if intento < 2:
            time.sleep((5, 15)[intento])
    return ultimo


# ── principal ────────────────────────────────────────────────────────────────
def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--desde")
    ap.add_argument("--hasta", default="HEAD")
    ap.add_argument("--simular", action="store_true", help="no envía ni guarda estado")
    ap.add_argument("--sin-verificar", action="store_true", help="solo con --simular")
    ap.add_argument("--espera", type=int, default=360)
    ap.add_argument("--estado", action="store_true")
    a = ap.parse_args()
    est = cargar_estado()
    if a.estado:
        print(json.dumps(est, ensure_ascii=False, indent=1)); return 0
    if a.sin_verificar and not a.simular:
        print("✗ --sin-verificar solo se permite con --simular"); return 2

    hasta = git("rev-parse", a.hasta).strip()
    candidatos = [git("rev-parse", c).strip() for c in (a.desde, est["cursor"]) if c]
    candidatos = [c for c in candidatos if es_ancestro(c, hasta)]
    desde = min(candidatos, key=lambda c: int(git("rev-list", "--count", c)), default=hasta)
    if a.desde and est["cursor"] and desde != git("rev-parse", a.desde).strip():
        print(f"  (cubre también {desde[:8]}..{a.desde[:8]}: publicado fuera de deploy.sh o pendiente)")

    nuevas, modificadas, retiradas = calcular(desde, hasta)
    previas = set(est["pendientes"])
    mapa = sitemap_urls(hasta)
    todas = sorted(set(nuevas) | set(modificadas) | set(retiradas) | previas)
    vivas = [u for u in todas if u in mapa]
    muertas = [u for u in todas if u not in mapa]

    print(f"IndexNow {desde[:8]}..{hasta[:8]}: {len(nuevas)} nuevas · {len(modificadas)} "
          f"modificadas · {len(retiradas)} retiradas · {len(previas)} pendientes previas")
    for u in todas:
        tag = "+" if u in nuevas else "~" if u in modificadas else "-" if u in muertas else "·"
        print(f"  {tag} {u}{'  (pendiente)' if u in previas else ''}")

    reg = {"fecha": ahora().isoformat(timespec="seconds"), "desde": desde, "hasta": hasta,
           "simulado": a.simular, "nuevas": nuevas, "modificadas": modificadas,
           "retiradas": retiradas, "pendientes_previas": sorted(previas)}

    # Persistir ANTES de verificar o enviar: un corte no pierde nada.
    if not a.simular:
        hoy = ahora().isoformat(timespec="seconds")
        for u in todas:
            est["pendientes"].setdefault(u, {"desde": hoy, "intentos": 0, "ultimo": None})
        est["cursor"] = hasta
        guardar_estado(est)

    if not todas:
        print("✓ Nada que notificar."); return 0

    if est["no_antes_de"] and datetime.datetime.fromisoformat(est["no_antes_de"]) > ahora():
        print(f"⏸ Retry-After vigente hasta {est['no_antes_de']}: quedan {len(todas)} pendientes.")
        return 0

    if not a.sin_verificar:
        fallas = verificar(hasta, vivas, muertas, a.espera)
        if fallas:
            print("✗ Producción no coincide con el commit; no se envía (quedan pendientes):")
            for f in fallas[:15]:
                print("   ·", f)
            if not a.simular:
                for u in todas:
                    est["pendientes"][u]["ultimo"] = "sin_verificar"
                guardar_estado(est)
                registrar({**reg, "resultado": "sin_verificar", "fallas": fallas})
            return 1
        print("✓ Producción verificada (sitemap, páginas vivas byte a byte, retiradas 404/410, clave).")

    hechas = huellas_aceptadas()
    def huella(u: str) -> str:
        f = archivo_de(u, hasta) if u in mapa else None
        return f"{u}|retirada" if u not in mapa else f"{u}|{sha(show(hasta, f)) if f else hasta}"
    pend = [(u, huella(u)) for u in todas]
    repetidas = [u for u, h in pend if h in hechas]
    pend = [(u, h) for u, h in pend if h not in hechas]
    if not a.simular:
        for u in repetidas:
            est["pendientes"].pop(u, None)
        guardar_estado(est)
    if not pend:
        print("✓ Todo ya estaba notificado con este contenido; no se repite."); return 0
    if a.simular:
        print(f"(simulación) se enviarían {len(pend)} URL a {API}"); return 0

    r = enviar([u for u, _ in pend])
    reg.update(r, enviadas=[u for u, _ in pend], huellas=[h for _, h in pend])
    registrar(reg)
    if r["resultado"] in ACEPTADOS:
        for u, _ in pend:
            est["pendientes"].pop(u, None)
        est["no_antes_de"] = None
    else:
        for u, _ in pend:
            p = est["pendientes"][u]
            p["intentos"] += 1
            p["ultimo"] = f"{r['resultado']} {r['http']}"
        if r["resultado"] == "limite":
            est["no_antes_de"] = r["no_antes_de"]
    guardar_estado(est)

    msg = {"enviado": "✓ IndexNow 200: URLs enviadas (envío ≠ indexación).",
           "recibido_clave_en_validacion": "✓ IndexNow 202: recibidas; la clave está en validación (recepción ≠ indexación).",
           "limite": f"⏸ IndexNow 429: se respetará Retry-After hasta {r.get('no_antes_de')}; quedan pendientes.",
           }.get(r["resultado"], f"✗ IndexNow {r['resultado']} (HTTP {r['http']}): quedan pendientes.")
    print(msg, f"Registro: {LOG}")
    return 0 if r["resultado"] in ACEPTADOS or r["resultado"] == "limite" else 1


if __name__ == "__main__":
    sys.exit(main())
