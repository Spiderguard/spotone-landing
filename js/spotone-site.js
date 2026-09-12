/* Native navigation. Contact anchors continue to bubble to spotone-analytics.js. */
(() => {
  const menu = document.getElementById('mobileMenu');
  const opener = document.getElementById('menuOpen');
  const closer = document.getElementById('menuClose');
  const background = [...document.body.children].filter(el => ![menu].includes(el) && !['SCRIPT','STYLE'].includes(el.tagName));
  function closeMenu(restore = true) {
    menu.hidden = true; menu.inert = true;
    background.forEach(el => el.inert = false);
    document.body.classList.remove('menu-open');
    opener.setAttribute('aria-expanded', 'false');
    if (restore) opener.focus();
  }
  opener.addEventListener('click', () => {
    menu.hidden = false; menu.inert = false;
    background.forEach(el => el.inert = true);
    document.body.classList.add('menu-open');
    opener.setAttribute('aria-expanded', 'true'); closer.focus();
  });
  closer.addEventListener('click', () => closeMenu());
  const gallery = document.getElementById('lb');
  if (gallery) {
    let galleryOpener;
    document.addEventListener('click', e => { const shot=e.target.closest('.shot[data-gal]'); if(shot) galleryOpener=shot; }, true);
    const syncGallery = () => {
      const open = gallery.classList.contains('on');
      gallery.inert = !open;
      gallery.setAttribute('aria-hidden', String(!open));
      [...document.body.children].filter(el => el !== gallery && !['SCRIPT','STYLE'].includes(el.tagName)).forEach(el => { el.inert = open || (el === menu && menu.hidden); });
      if (!open && galleryOpener) galleryOpener.focus({preventScroll:true});
    };
    new MutationObserver(syncGallery).observe(gallery, {attributes:true,attributeFilter:['class']});
    syncGallery();
  }
  menu.querySelectorAll('a').forEach(a => a.addEventListener('click', () => closeMenu(false)));
  document.addEventListener('keydown', e => {
    const gallery = document.getElementById('lb');
    const modal = !menu.hidden ? menu : gallery?.classList.contains('on') ? gallery : null;
    if (!modal) return;
    if (e.key === 'Escape' && modal === menu) closeMenu();
    if (e.key !== 'Tab') return;
    const items = [...modal.querySelectorAll('a[href],button,[tabindex="0"]')].filter(el => !el.disabled && el.getClientRects().length);
    if (!items.length) return;
    if (e.shiftKey && document.activeElement === items[0]) { e.preventDefault(); items.at(-1).focus(); }
    else if (!e.shiftKey && document.activeElement === items.at(-1)) { e.preventDefault(); items[0].focus(); }
  });
  matchMedia('(min-width:1001px)').addEventListener('change', e => { if(e.matches && !menu.hidden) closeMenu(); });
  const links = [...document.querySelectorAll('.site-nav .lnk[href^="#"],.site-nav .cta,#mobileMenu nav a[href^="#"]')];
  const sections = links.map(a => document.getElementById(a.hash.slice(1))).filter(Boolean);
  function markSection() {
    let active;
    for (const section of sections) if (section.getBoundingClientRect().top <= 150) active = section.id;
    if (scrollY + innerHeight >= document.documentElement.scrollHeight - 5) active='contacto';
    links.forEach(a => { if(a.hash === '#'+active) a.setAttribute('aria-current','location'); else a.removeAttribute('aria-current'); });
  }
  addEventListener('scroll',markSection,{passive:true}); markSection();
  // Arrow navigation for existing view/floor tabs, without replacing their click handlers.
  document.querySelectorAll('[role="tablist"]').forEach(group => {
    const tabs=[...group.querySelectorAll('[role="tab"]')];
    const sync=()=>tabs.forEach(t=>t.tabIndex=t.getAttribute('aria-selected')==='true'?0:-1);
    sync(); group.addEventListener('click',sync);
    group.addEventListener('keydown', e => {
      if(group.classList.contains('facade-tabs'))return;
      const i=tabs.indexOf(document.activeElement); if(i<0) return;
      let next;
      if(e.key==='ArrowRight') next=(i+1)%tabs.length;
      if(e.key==='ArrowLeft') next=(i+tabs.length-1)%tabs.length;
      if(e.key==='Home') next=0;
      if(e.key==='End') next=tabs.length-1;
      if(next===undefined) return;
      e.preventDefault(); tabs[next].click(); tabs[next].focus(); sync();
    });
  });
})();
