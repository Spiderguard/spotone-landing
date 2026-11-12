// Shared availability for both languages.
// total = canon + mantenimiento (US$2.50/m²) + aseo (US$15); sin ITBMS, igual que lo publicado.
// 29-oct-2026: disponibles el 4 (planta baja, 102 m2, canon 3060 + mantenimiento
// 255 con aseo incluido = 3315), el 22 y el 23. 11, 13, 15 y 21 alquilados;
// 16 administracion.
window.PEATONAL_AVAILABILITY = {"4": {"id": 4, "floor": 0, "area": 102, "rent": 3060, "total": 3315.0, "status": "available", "gal": "l4"}, "11": {"id": 11, "floor": 1, "area": 70, "rent": null, "total": null, "status": "leased", "gal": "l11"}, "13": {"id": 13, "floor": 1, "area": 120, "rent": null, "total": null, "status": "leased", "gal": "l13"}, "15": {"id": 15, "floor": 1, "area": 120, "rent": null, "total": null, "status": "leased", "gal": "l15"}, "16": {"id": 16, "floor": 1, "area": 200, "rent": null, "total": null, "status": "occupied", "gal": "l16"}, "21": {"id": 21, "floor": 2, "area": 77, "rent": null, "total": null, "status": "leased", "gal": "l21"}, "22": {"id": 22, "floor": 2, "area": 100, "rent": 1800, "total": 2065.0, "status": "available", "gal": "l22"}, "23": {"id": 23, "floor": 2, "area": 100, "rent": 1800, "total": 2065.0, "status": "available", "gal": "l23"}};
// Fecha en que Dario comunico la actualizacion de disponibilidad. NO es una
// inspeccion ni una verificacion integral del inventario.
// Se cambia a mano solo cuando se vuelve a verificar; no la toca ningun build.
window.PEATONAL_VERIFIED = "2026-10-29";
// 12-nov-2026, dato de Dario: el 22 y el 23 SI se pueden unir para formar un
// local de 200 m2, y asi se dice en el heroe, en las dos fichas y en la FAQ.
// La lista sigue vacia porque no hay un canon combinado que publicar; cuando lo
// haya, entra aqui y la ficha combinada sale de esta misma fuente.
window.PEATONAL_COMBINATIONS = [];
// Keep rendered availability and structured offers aligned with the shared source.
document.addEventListener('DOMContentLoaded', function () {
  const units = window.PEATONAL_AVAILABILITY;
  const en = document.documentElement.lang.startsWith('en');
  Object.values(units).forEach(function (unit) {
    const card = document.getElementById('local-' + unit.id);
    if (!card || unit.status === 'available') return;
    const label = unit.status === 'occupied' ? (en ? 'MANAGEMENT OFFICE · OCCUPIED' : 'OFICINA DE ADMINISTRACIÓN · OCUPADO') : (en ? 'RENTED' : 'ALQUILADO');
    card.dataset.alq = '1';
    const badge = card.querySelector('.alqb');
    if (badge) badge.textContent = label;
    const price = card.querySelector('.price');
    if (price) { price.replaceChildren(); const note = document.createElement('p'); note.className = 'p-alq'; note.textContent = label; price.appendChild(note); }
    card.querySelectorAll('.uacts').forEach(function (actions) { actions.remove(); });
  });
  document.querySelectorAll('script[type="application/ld+json"]').forEach(function (script) {
    const data = JSON.parse(script.textContent);
    (data['@graph'] || []).forEach(function (node) {
      if (node.makesOffer) node.makesOffer = node.makesOffer.filter(function (offer) { const id = offer.url.split('local-').pop(); return units[id] && units[id].status === 'available'; });
    });
    script.textContent = JSON.stringify(data);
  });
});
