// Shared availability for both languages.
window.PEATONAL_AVAILABILITY = {"11": {"id": 11, "floor": 1, "area": 70, "rent": null, "total": null, "status": "leased", "gal": "l11"}, "13": {"id": 13, "floor": 1, "area": 120, "rent": null, "total": null, "status": "leased", "gal": "l13"}, "15": {"id": 15, "floor": 1, "area": 120, "rent": 2400, "total": 2904.0, "status": "available", "gal": "l15"}, "16": {"id": 16, "floor": 1, "area": 200, "rent": null, "total": null, "status": "occupied", "gal": "l16"}, "21": {"id": 21, "floor": 2, "area": 77, "rent": 1386, "total": 1704.0, "status": "available", "gal": "l21"}, "22": {"id": 22, "floor": 2, "area": 100, "rent": 1800, "total": 2208.5, "status": "available", "gal": "l22"}, "23": {"id": 23, "floor": 2, "area": 100, "rent": 1800, "total": 2208.5, "status": "available", "gal": "l23"}};
// Fecha de la ULTIMA verificacion real del inventario con la administracion.
// Se cambia a mano solo cuando se vuelve a verificar; no la toca ningun build.
window.PEATONAL_VERIFIED = "2026-09-15";
window.PEATONAL_COMBINATIONS = [[21,22],[22,23],[21,22,23]].filter(c => c.every(id => window.PEATONAL_AVAILABILITY[id].status === "available"));
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
