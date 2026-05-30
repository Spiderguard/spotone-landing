# SpotOne Realty — Landing

Sitio editorial boutique para SpotOne Realty, publicado vía GitHub Pages.

## Edición y deploy

```bash
cd ~/Projects/spotone-landing
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

Las imágenes oficiales de Dario son únicamente las versiones con saco ink navy, camisa crema y manos dentro de los bolsillos.

- Vertical oficial para web: `images/dario-brand-vertical.jpg` (`1023 × 1537`)
- Horizontal oficial y fuentes PNG: `/Users/dario/Downloads/SpotOne Realty/Brand Manual/assets/images/`

No usar las versiones anteriores con camisa celeste ni retratos sentados. El repo web solo debe incluir assets que la página usa en producción; los archivos maestros viven en el manual de marca.
