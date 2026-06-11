# SpotOne Realty — Landing

Sitio editorial para SpotOne Realty, publicado vía GitHub Pages.

## Edición y deploy

```bash
cd ~/Documents/SpotOne/web
# edita index.html
./deploy.sh "mensaje del cambio"
```

## Estructura

```
spotone-landing/
├── index.html
├── index-en.html
├── CNAME
├── favicon-32.png
├── favicon-180.png
├── robots.txt
├── sitemap.xml
├── en/
├── contacto/
├── contact/
├── que-hago/
├── what-i-do/
├── images/
│   ├── logo.svg
│   ├── hero-main-desktop.jpg
│   ├── hero-main-mobile.jpg
│   └── dario-brand-vertical.jpg
├── deploy.sh
├── .nojekyll
└── README.md
```

## Dominio

GitHub Pages publica el sitio desde `main` y usa `www.spotonerealty.com` como dominio canonico.

DNS esperado:

- `www` CNAME -> `spiderguard.github.io`
- `spotonerealty.com` con A records de GitHub Pages

El sitio no depende de Netlify. Las carpetas `en/`, `contacto/`, `contact/`, `que-hago/` y `what-i-do/` reemplazan los redirects de Netlify con rutas estaticas utiles.

## Brand notes

- Tipografía: Instrument Sans
- Paleta: blanco editorial + tinta carbón + azul SpotOne
- Voz: analítica, sobria, sin empujar

## Imagen de marca

Imagen oficial de Dario (sesión real 2026): saco navy lavado, camisa blanca de cuello abierto, gafas Moscot oliva translúcidas, barba corta. Retrato auténtico, sin sobreedición de la cara.

- Vertical oficial para web: `images/dario-brand-vertical.jpg` (`1086 × 1448`)
- Maestros renombrados (vertical + cuadrada frontal + cuadrada alt): `/Users/dario/Documents/SpotOne/redes/fotos-perfil-2026/`
- Horizontal oficial y fuentes PNG: `/Users/dario/Documents/SpotOne/Brand Manual/assets/images/`

No usar las versiones anteriores: ni la de camisa celeste/retratos sentados, ni la sesión de estudio HD 2025 (fondo gris seamless, gafas negras, sobreeditada). El repo web solo debe incluir assets que la página usa en producción; los archivos maestros viven en el manual de marca.
