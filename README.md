# SpotOne Realty

Sitio estático ES/EN: Home, Peatonal 68 y Criterio.

## Desarrollo
Servir la raíz mediante un servidor HTTP local. Home: index.html e index-en.html. Peatonal: templates/peatonal-es.html y templates/peatonal-en.html. Los estilos compartidos están en css/ y los controles en js/.

## Generación
python3 generate-peatonal.py genera ambas páginas de Peatonal desde data/peatonal68.json y actualiza el resumen de Home. El JSON contiene únicamente datos destinados a la experiencia pública. No editar las salidas generadas a mano.

## QA y actualización segura
La validación completa se ejecuta con ./deploy.sh --check. Configurar SPOTONE_RELEASE_TOOL con el validador de publicación del entorno de trabajo y su lista aprobada. El script se detiene si falta esa configuración. No realiza commit ni push. El staging exige una opción explícita y una lista de hashes aprobada.

build-sitemap.py debe ejecutarse desde la raíz Git con historial; --check comprueba el resultado. El control de publicación incluye generación determinista, inventario, navegación, enlaces y revisión de archivos permitidos.

## Documentación vigente
CHANGELOG_AI.md registra cambios de implementación. El expediente de revisión R03_07 se mantiene separado del sitio. Este documento no sustituye el manual canónico de SpotOne. Ante cualquier conflicto, prevalece la fuente canónica vigente.
