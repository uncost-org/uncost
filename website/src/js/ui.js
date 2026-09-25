/* Uncost — UI behaviour only. All markup lives in partials/ as real HTML.
   Progressive enhancement: every link works with JS disabled. No third-party requests. */
(function () {
  function ready(fn){ if(document.readyState==='loading') document.addEventListener('DOMContentLoaded',fn); else fn(); }
  ready(function () {
    var items = [].slice.call(document.querySelectorAll('.hd-item'));
    var megas = [].slice.call(document.querySelectorAll('.hd-mega'));
    var hdEl  = document.querySelector('.hd');
    var drawerEl = document.querySelector('.drawer');
    var searchEl = document.querySelector('.search-ov');

    /* The overlay is a JS-only control: it is display:none until `open` is set
       below, so with this file absent it can never appear. partials/search.njk
       therefore ships it as an ordinary in-flow block (.search-ov--nojs) with
       no dialog semantics, and the header control ships as a real link to
       /search/. Everything that makes it a dialog is added here, where a
       dialog can actually open — a reader without script is never offered
       dialog semantics, and never a close button that cannot close anything. */
    if (searchEl) {
      searchEl.classList.remove('search-ov--nojs');
      searchEl.setAttribute('role', 'dialog');
      searchEl.setAttribute('aria-modal', 'true');
      searchEl.setAttribute('aria-label', 'Search');
    }

    function closeAll(){
      items.forEach(function(it){ it.classList.remove('open'); it.querySelector('a').setAttribute('aria-expanded','false'); });
      megas.forEach(function(m){ m.classList.remove('open'); });
    }
    function openItem(i){
      closeAll();
      items[i].classList.add('open');
      items[i].querySelector('a').setAttribute('aria-expanded','true');
      if (megas[i]) megas[i].classList.add('open');
    }
    items.forEach(function(it,i){
      var link = it.querySelector('a');
      if (window.matchMedia('(hover:hover)').matches) it.addEventListener('mouseenter', function(){ openItem(i); });
      link.addEventListener('focus', function(){ openItem(i); });
      link.addEventListener('click', function(e){ if(!it.classList.contains('open')){ e.preventDefault(); openItem(i); } });
    });
    if (hdEl) hdEl.addEventListener('mouseleave', closeAll);
    document.addEventListener('click', function(e){
      if (!e.target.closest('.hd-item') && !e.target.closest('.hd-mega')) closeAll();
    });

    function toggleDrawer(on){ if(!drawerEl) return; drawerEl.classList.toggle('open', on); document.body.style.overflow = on ? 'hidden' : ''; }
    function toggleSearch(on){ if(!searchEl) return; searchEl.classList.toggle('open', on); document.body.style.overflow = on ? 'hidden' : ''; if(on){ var f = searchEl.querySelector('input, a, button'); if(f) f.focus(); } }  /* null-guarded on integration: with searchEnabled false the overlay renders
     no input at all, and the export's unguarded .focus() would throw. */
    var bOpen = document.querySelector('[data-drawer-open]'), bClose = document.querySelector('[data-drawer-close]');
    var sOpen = document.querySelector('[data-search]'),      sClose = document.querySelector('[data-search-close]');
    if (bOpen)  bOpen.addEventListener('click', function(){ toggleDrawer(true); });
    if (bClose) bClose.addEventListener('click', function(){ toggleDrawer(false); });
    /* [data-search] is an <a href="/search/">, so it works with this file
       absent. Where it is present the overlay is the faster answer, so the
       navigation is cancelled and the overlay opened instead — the link's
       destination stays the honest fallback, and Enter on the link behaves
       exactly like the click. */
    if (sOpen)  { sOpen.setAttribute('aria-haspopup', 'dialog');
                  sOpen.addEventListener('click', function(e){ e.preventDefault(); toggleSearch(true); }); }
    if (sClose) sClose.addEventListener('click', function(){ toggleSearch(false); });
    document.addEventListener('keydown', function(e){ if(e.key==='Escape'){ closeAll(); toggleDrawer(false); toggleSearch(false); } });

    /* Mobile drawer accordion (one section open at a time) */
    if (drawerEl) drawerEl.querySelectorAll('[data-acc]').forEach(function(btn){
      btn.addEventListener('click', function(){
        var acc = btn.parentElement, was = acc.classList.contains('open');
        drawerEl.querySelectorAll('.drawer-acc').forEach(function(a){
          a.classList.remove('open');
          a.querySelector('.pm').textContent = '+';
          a.querySelector('[data-acc]').setAttribute('aria-expanded','false');
        });
        if (!was){ acc.classList.add('open'); acc.querySelector('.pm').textContent = '\u2212'; btn.setAttribute('aria-expanded','true'); }
      });
    });

    /* FAQ / policy disclosure groups use native <details> — no JS needed. */

    /* Forms: inert until data/site.json flags.formsOpen is true and a backend is wired.
       Hooks: [data-form="pledge"] [data-form="updates"] [data-form="contact"] */
    document.querySelectorAll('[data-form]').forEach(function(f){
      f.addEventListener('submit', function(e){ e.preventDefault(); });
    });
  });
})();
