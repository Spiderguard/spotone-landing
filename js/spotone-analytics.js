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
  // ────────────────────────────────────────────────────────────────────────

  var CONFIGURED =
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
      anonymize_ip: true,
      // dimensión útil para separar tráfico ES vs EN sin tocar más código:
      language: (document.documentElement.lang || "es")
    });
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
      page_language: (document.documentElement.lang || "es")
    };

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
})();
