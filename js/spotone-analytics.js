/* ============================================================================
   SpotOne Realty · Analítica + seguimiento de conversiones
   ----------------------------------------------------------------------------
   Fuente única de verdad. Toda página del sitio carga ESTE archivo con una sola
   línea en el <head>:  <script defer src="/js/spotone-analytics.js"></script>

   PARA ACTIVAR:
     1. Crea una propiedad GA4 en https://analytics.google.com
     2. Copia el "Measurement ID" (formato G-XXXXXXXXXX)
     3. Pégalo abajo en MEASUREMENT_ID y publica con ./deploy.sh

   Mientras el ID sea el placeholder, el script queda INERTE: no envía nada,
   no rompe nada, el sitio se comporta igual que hoy. El cambio para ir en vivo
   es UNA línea.
   ========================================================================== */
(function () {
  "use strict";

  // ── Pega aquí tu ID de GA4 ──────────────────────────────────────────────
  var MEASUREMENT_ID = "G-J68CEBVH69";
  // ── Mapas de calor (Microsoft Clarity). Inerte hasta pegar el ID real ───
  // 1. clarity.microsoft.com → nuevo proyecto → copia el ID (10 caracteres)
  // 2. Pégalo abajo. Recomendado: enmascarado «Strict» e integración con GA4.
  var CLARITY_ID = "";
  // ────────────────────────────────────────────────────────────────────────

  // Solo se mide en el dominio publicado. La vista previa local y las pruebas
  // automáticas no deben sumar visitas ni clics de WhatsApp a GA4.
  var PRODUCTION = /(^|\.)spotonerealty\.com$/i.test(location.hostname);

  var CONFIGURED = PRODUCTION &&
    /^G-[A-Z0-9]{6,}$/.test(MEASUREMENT_ID) && MEASUREMENT_ID !== "G-XXXXXXXXXX";

  // dataLayer + gtag disponibles siempre (no rompe aunque GA no esté activo).
  window.dataLayer = window.dataLayer || [];
  function gtag() { window.dataLayer.push(arguments); }
  window.gtag = window.gtag || gtag;

  // ── 1. Carga de GA4 (solo si hay ID real) ───────────────────────────────
  if (CONFIGURED) {
    var s = document.createElement("script");
    s.async = true;
    s.src = "https://www.googletagmanager.com/gtag/js?id=" + MEASUREMENT_ID;
    document.head.appendChild(s);

    gtag("js", new Date());
    gtag("config", MEASUREMENT_ID, {
      // dimensión útil para separar tráfico ES vs EN sin tocar más código:
      language: (document.documentElement.lang || "es")
    });
  }

  if (PRODUCTION && /^[a-z0-9]{8,12}$/i.test(CLARITY_ID)) {
    (function (c, l, a, r, i) {
      c[a] = c[a] || function () { (c[a].q = c[a].q || []).push(arguments); };
      var t = l.createElement(r); t.async = 1; t.src = "https://www.clarity.ms/tag/" + i;
      l.head.appendChild(t);
    })(window, document, "clarity", "script", CLARITY_ID);
  }

  // ── 2. Conversiones: los clics que de verdad pagan ──────────────────────
  // WhatsApp, llamada y correo son la única acción de contacto del sitio.
  // GA4 NO las captura por defecto: hay que mandarlas como eventos. Estos tres
  // se marcan luego como "Key events" (conversiones) en la interfaz de GA4.
  function track(name, params) {
    if (CONFIGURED) { gtag("event", name, params); }
    // Rastro local: permite verificar que el listener dispara aunque GA aún no
    // esté configurado. Abre la consola del navegador y haz clic en WhatsApp.
    if (window.console && console.debug) { console.debug("[spotone]", name, params); }
  }

  document.addEventListener("click", function (e) {
    var a = e.target && e.target.closest ? e.target.closest("a[href]") : null;
    if (!a) { return; }

    var href = a.getAttribute("href") || "";
    var label = (a.textContent || "").trim().slice(0, 80);
    var base = {
      link_url: href,
      link_text: label,
      page_path: location.pathname,
      page_language: (document.documentElement.lang || "es"),
      // v1.2: qué invitación convierte (héroe, cierre, menú, pie, ficha)
      cta_position: a.closest(".phero,.hero") ? "hero" : a.closest(".close,.pclose") ? "cierre" :
        a.closest("footer,.sf") ? "pie" : a.closest("#mobileMenu,.mm") ? "menu" :
        a.closest(".site-header") ? "barra" : a.closest(".lb") ? "galeria" : a.closest(".u,.card") ? "ficha" : "otro"
    };
    // v1.3 (21-nov): local de origen de la consulta, leído de la etiqueta del texto prellenado (web-p68-l4 → "4")
    var loc = href.match(/web-p68-l(\d+)/);
    if (loc) base.local_id = "l" + loc[1];   // mismo formato que view_local (data-gal="l4")

    if (/wa\.me|api\.whatsapp\.com|\/\/whatsapp\.com/i.test(href)) {
      base.method = "whatsapp";
      track("contact_whatsapp", base);
    } else if (/^tel:/i.test(href)) {
      base.method = "phone";
      track("contact_call", base);
    } else if (/^mailto:/i.test(href)) {
      base.method = "email";
      track("contact_email", base);
    }
  }, true);

  // ── 3. Interés: qué miran antes de escribir (v1.2) ──────────────────────
  document.addEventListener("click", function (e) {
    var t = e.target;
    if (!t || !t.closest) { return; }
    var lang = document.documentElement.lang || "es";
    var pin = t.closest(".fac .pin");
    if (pin) { track("select_local", { local_id: (pin.getAttribute("href") || "").replace("#", ""), page_language: lang }); return; }
    var gal = t.closest("[data-gal]");
    if (gal) { track("view_local", { local_id: gal.getAttribute("data-gal"), page_language: lang }); return; }
    var lng = t.closest(".lang a,.mm-lang a");
    if (lng) { track("lang_switch", { to: lng.getAttribute("lang") || "", page_language: lang }); }
  }, true);

  document.addEventListener("toggle", function (e) {
    var d = e.target;
    if (!d || d.tagName !== "DETAILS" || !d.open) { return; }
    var sum = d.querySelector("summary");
    var name = d.classList.contains("calc") ? "open_breakdown" : "faq_open";
    track(name, { question: sum ? sum.textContent.trim().slice(0, 100) : "", page_path: location.pathname });
  }, true);

  if ("IntersectionObserver" in window) {
    var seen = {};
    var io = new IntersectionObserver(function (es) {
      es.forEach(function (en) {
        var id = en.target.id || en.target.getAttribute("data-sec");
        if (en.isIntersecting && id && !seen[id]) { seen[id] = 1; track("reach_section", { section: id, page_path: location.pathname }); }
      });
    }, { threshold: 0.4 });
    ["disponibilidad", "ubicacion", "contacto"].forEach(function (id) {
      var el = document.getElementById(id); if (el) { io.observe(el); }
    });
    // 20-nov-2026: medir hasta dónde se lee cada página (decisión de Dario: medir
    // la home antes de recortarla). Cada <section> de <main> manda un reach_section
    // una vez, con su orden y un nombre legible (id, o etiqueta/título de la sección).
    var secs = document.querySelectorAll("main > section, main > header, body > section");
    for (var i = 0; i < secs.length; i++) {
      var s = secs[i];
      if (!s.id) {
        var h = s.querySelector(".idx, h2, h1");
        var name = h ? h.textContent.trim().toLowerCase().replace(/\s+/g, "-").replace(/[^a-z0-9áéíóúñü-]/g, "").slice(0, 40) : "";
        s.setAttribute("data-sec", (i + 1) + "-" + (name || "seccion"));
      }
      io.observe(s);
    }
  }
})();
