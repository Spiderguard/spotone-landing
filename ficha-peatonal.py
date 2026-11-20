#!/usr/bin/env python3
"""Ficha para corredores de Plaza La Peatonal 68: un PDF con fotos y condiciones,
y un ZIP con ese PDF más las fotografías en buena resolución.

Uso:  python3 ficha-peatonal.py           (genera peatonal68/descargas/)
      python3 ficha-peatonal.py --check   (falla si la ficha no coincide con la disponibilidad)

Fuente de disponibilidad: js/peatonal-availability.js (la misma que usa la web).
Los textos repiten lo publicado en peatonal68/index.html; si cambias un dato en la
página, cámbialo aquí y vuelve a generar. Cuando se alquile un local, márcalo en
peatonal-availability.js y corre este script: el local sale de la ficha y del ZIP.
Nunca se publica la comisión.
"""
import datetime, html, json, os, re, shutil, subprocess, sys, tempfile, zipfile

ROOT = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(ROOT, "peatonal68", "descargas")
PDF_NAME = "ficha-plaza-la-peatonal-68.pdf"
ZIP_NAME = "fotos-y-ficha-plaza-la-peatonal-68.zip"
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
MESES = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto",
         "septiembre", "octubre", "noviembre", "diciembre"]

UNITS = {
    "4": {
        "titulo": "Local 4", "nivel": "Planta baja", "area": "102 m²",
        "area_det": "102 m² (82 interiores + 20 de terraza)",
        "alquiler": 3060, "otros": [("Mantenimiento (aseo incluido)", 255)], "total": 3315,
        "puntos": [
            "82 m² interiores y 20 m² de terraza de uso exclusivo.",
            "Gas, extracción y aire acondicionado instalados.",
            "Equipado para restaurante; admite bar, venta de alcohol y karaoke.",
            "Ya desocupado: entrega inmediata con lo instalado (gas, extracción y aire acondicionado). El mobiliario y los equipos de las fotos son del inquilino anterior, que los vende aparte.",
        ],
        "fotos": [
            ("local-04-salon-hacia-la-terraza.jpg", "El salón hacia la vitrina y la terraza"),
            ("local-04-terraza.jpg", "Terraza de uso exclusivo"),
            ("local-04-noche.jpg", "La terraza, de noche"),
            ("local-04-salon-hacia-la-barra.jpg", "El salón hacia la barra y el acceso a la cocina"),
            ("local-04-barra.jpg", "La barra"),
            ("local-04-cocina.jpg", "Cocina con campana de extracción y línea de gas"),
            ("local-04-cocina-preparacion.jpg", "Cocina: zona de preparación y fregadero"),
            ("local-04-bano.jpg", "Baño"),
        ],
    },
    "22": {
        "titulo": "Local 22", "nivel": "Segundo piso", "area": "100 m²", "area_det": "100 m²",
        "alquiler": 1800, "otros": [("Mantenimiento", 250), ("Aseo", 15)], "total": 2065,
        "puntos": [
            "Planta abierta con un baño.",
            "Se puede unir con el 23, que es contiguo, para 200 m².",
            "La separación respecto al Local 21 y la condición de entrega quedan por escrito antes de firmar.",
            "Gas y aire: se revisan en el local según el giro.",
        ],
        "fotos": [
            ("local-22-espacio.jpg", "Espacio completo desde la entrada, con el ventanal al fondo"),
            ("local-22-ventanal.jpg", "La luz del ventanal"),
            ("local-22a.jpg", "Planta abierta con piso de madera y banda de mármol"),
        ],
    },
    "23": {
        "titulo": "Local 23", "nivel": "Segundo piso", "area": "100 m²", "area_det": "100 m²",
        "alquiler": 1800, "otros": [("Mantenimiento", 250), ("Aseo", 15)], "total": 2065,
        "puntos": [
            "Vitrina al pasillo y un baño interno.",
            "Se puede unir con el 22, que es contiguo, para 200 m².",
            "Distribución y condición de entrega se confirman antes de contratar.",
            "Gas y aire: se revisan en el local según el giro.",
        ],
        "fotos": [
            ("local-23-espacio.jpg", "El espacio principal, con la ventana al fondo"),
            ("local-23-pasillo.jpg", "El pasillo interior"),
            ("local-23-cuarto.jpg", "El área principal desde la entrada"),
            ("local-23-vitrina.jpg", "Vitrina desde el pasillo del segundo piso"),
        ],
    },
}
PLAZA_FOTOS = [
    ("../../images/plaza-noche-32.jpg", "La plaza de noche, con los restaurantes de planta baja en operación"),
    ("plaza-operando.jpg", "La plaza de día desde Calle 68 Este"),
    ("planta-baja-restaurantes-y-acceso.jpg", "Planta baja: restaurantes, estacionamiento y entrada peatonal"),
    ("estacionamientos.jpg", "Estacionamiento techado en el sótano, con escalera y elevador"),
]
FACHADA = "fachada-master-2026-09-21.jpg"


def disponibles():
    src = open(os.path.join(ROOT, "js", "peatonal-availability.js"), encoding="utf-8").read()
    data = json.loads(re.search(r"PEATONAL_AVAILABILITY\s*=\s*(\{.*?\});", src, re.S).group(1))
    libres = [k for k, v in data.items() if v["status"] == "available"]
    faltan = [k for k in libres if k not in UNITS]
    if faltan:
        sys.exit(f"ERROR: disponibles sin ficha en este script: {faltan}. Agrega su texto y fotos.")
    for k in libres:
        u, d = UNITS[k], data[k]
        if d["rent"] != u["alquiler"] or float(d["total"]) != float(u["total"]):
            sys.exit(f"ERROR: Local {k}: alquiler/total distinto a peatonal-availability.js")
    return [k for k in ("4", "22", "23") if k in libres] + [k for k in libres if k not in ("4", "22", "23")]


def slug(s):
    import unicodedata
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode().lower()
    s = re.sub(r"[^a-z0-9]+", "-", s).strip("-")
    return "-".join(s.split("-")[:6])


def money(n):
    return f"${n:,.0f}"


TMP_IMG = None


def img(name):
    p = os.path.normpath(os.path.join(ROOT, "peatonal68", "img", name))
    assert os.path.exists(p), p
    if TMP_IMG:
        dst = os.path.join(TMP_IMG, os.path.basename(p))
        if not os.path.exists(dst):
            subprocess.run(["sips", "-Z", "1400", "-s", "formatOptions", "78", p, "--out", dst],
                           check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return "file://" + dst
    return "file://" + p


def construir_html(libres, fecha):
    e = html.escape
    filas = "".join(
        f"<tr><td>{e(UNITS[k]['titulo'])}</td><td>{e(UNITS[k]['nivel'])}</td><td>{e(UNITS[k]['area_det'])}</td>"
        f"<td class='n'>{money(UNITS[k]['alquiler'])}</td><td class='n'>{money(UNITS[k]['total'])}</td></tr>"
        for k in libres)
    union = ("<li>El 22 y el 23 son contiguos y se pueden unir para 200 m². Si se toman los dos, son dos estacionamientos. "
             "La obra y la entrega de la unión se acuerdan por escrito con la administración antes de firmar.</li>"
             if "22" in libres and "23" in libres else "")
    contacto = ("<div class='contacto'><p class='quien'>Dario Jhangimal</p>"
                "<p>Corredor de bienes raíces · Licencia PN-1240 · SpotOne Realty</p>"
                "<p>WhatsApp <a href='https://wa.me/50766758127'>+507 6675-8127</a> · info@spotonerealty.com</p>"
                "<p><a href='https://www.spotonerealty.com/peatonal68/'>www.spotonerealty.com/peatonal68/</a></p></div>")
    pie = (f"<p class='pie'>Cánones sin ITBMS. Información referencial; manda el contrato con la administración. "
           f"Ficha del {fecha}: confirma la disponibilidad antes de presentarla.</p>")

    paginas = [f"""
<section class="pag portada">
  <p class="kicker">Locales comerciales en alquiler · San Francisco, Ciudad de Panamá</p>
  <h1>Plaza La Peatonal 68</h1>
  <img class="fachada" src="{img(FACHADA)}" alt="">
  <p class="leyenda">La plaza desde Calle 68 Este: el Local 4 está en planta baja; el 22 y el 23, en el segundo piso.</p>
  <table><thead><tr><th>Local</th><th>Nivel</th><th>Área</th><th class="n">Alquiler mensual</th><th class="n">Total mensual antes de ITBMS</th></tr></thead>
  <tbody>{filas}</tbody></table>
  <ul class="claves">
    {union}
    <li>Un estacionamiento por contrato. La plaza tiene 60, gratuitos para visitantes: 14 en planta baja y 46 bajo techo en el sótano.</li>
    <li>Para firmar: primer mes y un mes de depósito de garantía.</li>
    <li>Represento la plaza con exclusividad. Si tienes un cliente para alguno de estos locales, escríbeme y coordinamos la visita.</li>
  </ul>
  {contacto}
  {pie}
</section>"""]

    for k in libres:
        u = UNITS[k]
        otros = "".join(f"<div><dt>{e(n)}</dt><dd>{money(v)}</dd></div>" for n, v in u["otros"])
        fotos = "".join(f"<figure><img src='{img(f)}' alt=''><figcaption>{e(c)}</figcaption></figure>" for f, c in u["fotos"])
        resto = len(u["fotos"]) - 1
        grid = "c4" if resto > 4 else ("c3" if resto == 3 else "c2")
        paginas.append(f"""
<section class="pag local">
  <p class="kicker">Plaza La Peatonal 68 · {e(u['nivel'])}</p>
  <div class="cab"><h2>{e(u['titulo'])}</h2><p class="area">{e(u['area'])}</p></div>
  <div class="dos">
    <ul class="claves">{''.join(f'<li>{e(p)}</li>' for p in u['puntos'])}</ul>
    <dl class="ledger"><div><dt>Alquiler mensual</dt><dd>{money(u['alquiler'])}</dd></div>{otros}
      <div class="tot"><dt>Total mensual antes de ITBMS</dt><dd>{money(u['total'])}</dd></div></dl>
  </div>
  <div class="fotos {grid}">{fotos}</div>
  {pie}
</section>""")

    pf = "".join(f"<figure><img src='{img(f)}' alt=''><figcaption>{e(c)}</figcaption></figure>" for f, c in PLAZA_FOTOS)
    paginas.append(f"""
<section class="pag plaza">
  <p class="kicker">La plaza</p>
  <h2>Ocho restaurantes en planta baja.</h2>
  <div class="fotos g2">{pf}</div>
  <div class="dos">
    <ul class="claves">
      <li>En los niveles superiores funcionan negocios que reciben clientes por citas, clases y servicios.</li>
      <li>60 estacionamientos, gratuitos para visitantes: 14 en planta baja y 46 bajo techo en el sótano, dos para personas con discapacidad. Un estacionamiento por contrato; las condiciones de uso las fija la administración.</li>
      <li>Elevador y escaleras.</li>
      <li>Calle 68 Este, San Francisco. <a href='https://www.google.com/maps?q=8.9943381,-79.5112507'>Ver en el mapa</a>.</li>
    </ul>
    <ul class="claves">
      <li><b>Se confirma en cada local:</b> agua, desagüe y extracción; frente y fondo (envío el plano); horario y acceso de carga y descarga, por escrito antes de firmar.</li>
      <li><b>No incluido:</b> electricidad, internet, permisos, adecuaciones, seguros y consumos propios del negocio.</li>
    </ul>
  </div>
  {contacto}
  {pie}
</section>""")

    fonts = "file://" + os.path.join(ROOT, "fonts")
    return f"""<!doctype html><html lang="es"><head><meta charset="utf-8"><title>Plaza La Peatonal 68 · Ficha para corredores</title>
<style>
@font-face{{font-family:'Newsreader';src:url('{fonts}/newsreader.woff2') format('woff2');font-weight:200 800}}
@font-face{{font-family:'Hanken Grotesk';src:url('{fonts}/hanken.woff2') format('woff2');font-weight:100 900}}
@page{{size:letter;margin:14mm 14mm 12mm}}
*{{box-sizing:border-box}}
body{{margin:0;font-family:'Hanken Grotesk',Arial,sans-serif;font-weight:300;color:#1A1A18;font-size:9.5pt;line-height:14pt;
  -webkit-print-color-adjust:exact;print-color-adjust:exact}}
.pag{{break-after:page;position:relative}}
.pag:last-child{{break-after:auto}}
.kicker{{text-transform:uppercase;letter-spacing:.12em;font-size:7.5pt;font-weight:500;color:#5A5F69;margin:0 0 3mm}}
h1,h2{{font-family:'Newsreader',Georgia,serif;font-weight:300;color:#050E1E;margin:0}}
h1{{font-size:34pt;line-height:38pt;margin-bottom:5mm}}
h2{{font-size:24pt;line-height:28pt}}
.cab{{display:flex;justify-content:space-between;align-items:baseline;border-bottom:1px solid rgba(26,26,24,.18);padding-bottom:3mm;margin-bottom:4mm}}
.area{{font-family:'Newsreader',Georgia,serif;font-size:24pt;line-height:28pt;color:#050E1E;margin:0}}
.fachada{{width:100%;height:auto;display:block}}
.leyenda,figcaption{{font-size:7.5pt;line-height:10pt;color:#5A5F69;margin:1.5mm 0 0}}
table{{width:100%;border-collapse:collapse;margin:6mm 0 4mm}}
th{{text-align:left;font-weight:500;font-size:7.5pt;text-transform:uppercase;letter-spacing:.08em;color:#5A5F69;border-bottom:1px solid #1A1A18;padding:0 2mm 2mm 0}}
td{{padding:2.5mm 2mm 2.5mm 0;border-bottom:1px solid rgba(26,26,24,.15)}}
td:first-child{{font-weight:500}}
.n{{text-align:right;font-variant-numeric:tabular-nums}}
.claves{{margin:0;padding:0 0 0 4mm}}
.claves li{{margin:0 0 1.6mm}}
.claves b{{font-weight:500}}
.dos{{display:grid;grid-template-columns:1.3fr 1fr;gap:8mm;margin-bottom:5mm}}
.plaza .dos{{grid-template-columns:1fr 1fr;margin-top:4mm}}
.ledger{{margin:0}}
.ledger div{{display:flex;justify-content:space-between;padding:1.6mm 0;border-bottom:1px solid rgba(26,26,24,.15)}}
.ledger dt{{color:#5A5F69}} .ledger dd{{margin:0;font-variant-numeric:tabular-nums}}
.ledger .tot dt,.ledger .tot dd{{color:#050E1E;font-weight:500}}
.fotos{{display:grid;gap:3mm}}
.fotos.g2{{grid-template-columns:1fr 1fr}}
.fotos.g4{{grid-template-columns:1fr 1fr 1fr}}
.fotos figure{{margin:0;break-inside:avoid}}
.fotos img{{width:100%;aspect-ratio:3/2;object-fit:cover;display:block}}
.fotos.c2{{grid-template-columns:repeat(2,1fr)}}
.fotos.c3{{grid-template-columns:repeat(3,1fr)}}
.fotos.c4{{grid-template-columns:repeat(4,1fr)}}
.local .fotos figure:first-child{{grid-column:1/-1}}
.local .fotos figure:first-child img{{aspect-ratio:16/7}}
.plaza .fotos{{margin-top:5mm}}
.plaza .fotos img{{aspect-ratio:16/9}}
.contacto{{background:#050E1E;color:#F4F1EA;padding:5mm 6mm;margin-top:5mm}}
.contacto p{{margin:0;font-size:8.5pt;line-height:12.5pt;color:rgba(244,241,234,.8)}}
.plaza .claves a{{color:#050E1E}}
.pag .contacto a{{color:inherit;text-decoration:none}}
.contacto .quien{{font-family:'Newsreader',Georgia,serif;font-size:15pt;line-height:19pt;color:#F4F1EA;margin-bottom:1mm}}
.pie{{font-size:7pt;line-height:9.5pt;color:#5A5F69;margin:4mm 0 0}}
</style></head><body>{''.join(paginas)}</body></html>"""


def main():
    check = "--check" in sys.argv
    libres = disponibles()
    hoy = datetime.date.today()
    fecha = f"{hoy.day} de {MESES[hoy.month - 1]} de {hoy.year}"
    if check:
        print("OK: la ficha cubre los locales disponibles:", ", ".join(libres))
        return
    os.makedirs(OUT, exist_ok=True)
    global TMP_IMG
    tmp = tempfile.mkdtemp(prefix="ficha-peatonal-")
    TMP_IMG = os.path.join(tmp, "img"); os.makedirs(TMP_IMG)
    try:
        src = os.path.join(tmp, "ficha.html")
        open(src, "w", encoding="utf-8").write(construir_html(libres, fecha))
        pdf = os.path.join(OUT, PDF_NAME)
        subprocess.run([CHROME, "--headless=new", "--disable-gpu", "--no-pdf-header-footer",
                        "--allow-file-access-from-files", f"--user-data-dir={tmp}/perfil",
                        "--virtual-time-budget=8000", f"--print-to-pdf={pdf}", "file://" + src],
                       check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=120)
        zp = os.path.join(OUT, ZIP_NAME)
        with zipfile.ZipFile(zp, "w", zipfile.ZIP_STORED) as z:
            z.write(pdf, PDF_NAME)
            for k in libres:
                for i, (f, cap) in enumerate(UNITS[k]["fotos"], 1):
                    base = slug(cap)
                    z.write(os.path.join(ROOT, "peatonal68", "img", f),
                            f"Local {k}/{i:02d}_{base}_PH-Plaza-La-Peatonal-68-Local-{k}.jpg")
            for i, (f, cap) in enumerate([(FACHADA, "Fachada desde Calle 68 Este")] + PLAZA_FOTOS, 1):
                p = os.path.normpath(os.path.join(ROOT, "peatonal68", "img", f))
                z.write(p, f"Plaza/{i:02d}_{slug(cap)}_PH-Plaza-La-Peatonal-68.jpg")
        print("PDF:", os.path.relpath(pdf, ROOT), os.path.getsize(pdf) // 1024, "KB")
        print("ZIP:", os.path.relpath(zp, ROOT), os.path.getsize(zp) // 1024, "KB")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    main()
