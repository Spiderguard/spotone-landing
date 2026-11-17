# spotonerealty.com

Sitio de Dario Jhangimal (corredor de bienes raíces, licencia PN-1240). HTML estático en GitHub Pages: rama `main` del repositorio `Spiderguard/spotone-landing`, dominio en `CNAME`.

**La documentación completa (decisiones, pruebas, generadores y consejos) está fuera del repo:**
`~/Documents/SpotOne/Revision web 2026-10-29/00-LEER-PRIMERO.md`

## Publicar
1. Solo con orden de Dario.
2. Trabaja en `~/Developer/spotone-landing`. La copia `_RESPALDO-web-icloud-*` de Documents ya no se usa.
3. Antes de publicar: `git fetch` + `git merge origin/main`. Hay más de una sesión trabajando el sitio.
4. Publica con `./deploy.sh "qué cambia"`. El script solo publica desde `main`, trae origin/main, regenera y verifica el sitemap, y no sube `.claude/` ni respaldos.
5. Verifica en vivo con `?nc=1` al final de la URL. GitHub Pages tarda 1 o 2 minutos.

## Archivos que se generan (no se editan a mano)
| Salida | Generador |
|---|---|
| `sitemap.xml` | `python3 build-sitemap.py` (`--check` para verificar) |
| `peatonal68/descargas/` (ficha PDF + ZIP para corredores) | `python3 ficha-peatonal.py`. Correr el mismo día que se alquile un local, después de marcarlo en `js/peatonal-availability.js` |
| `/zonas/` y `/en/areas/` | `Revision web 2026-10-29/r9-marca-seo/zonas-gen.py <salida> zonas-datos.json`. Generar en una carpeta temporal y comparar con el sitio antes de copiar |
| notas de `/criterio/` | `Revision web 2026-10-29/pruebas/generador/` |

## Reglas que no se discuten
Mandan `~/Documents/SpotOne/Brand Manual/HECHOS-DARIO-Y-POSICIONAMIENTO.md` y `VOZ_Y_TONO.md`:
- solo hechos verificables;
- la comisión nunca se publica;
- nada que prometa dinero, tiempos de respuesta ni visitas;
- primera persona y tuteo, sin emojis;
- nunca IA en caras;
- casos de clientes solo con permiso.

Firma en español: «Corredor de bienes raíces · PN-1240». En inglés: «Real Estate Broker · License PN-1240».
