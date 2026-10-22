/* Uncost — UI behaviour only. All markup lives in partials/ as real HTML.
   Progressive enhancement: every link works with JS disabled. This file makes no
   third-party request: its only fetch is the contact form's same-origin /api/contact. */
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
      link.addEventListener('focus', function(){ if (!escaping) openItem(i); });
      link.addEventListener('click', function(e){ if(!it.classList.contains('open')){ e.preventDefault(); openItem(i); } });
    });
    if (hdEl) hdEl.addEventListener('mouseleave', closeAll);
    document.addEventListener('click', function(e){
      if (!e.target.closest('.hd-item') && !e.target.closest('.hd-mega')) closeAll();
    });
    /* Keyboard (compliance pass 2026-10-20; WCAG 2.4.11 and 1.4.13). A panel
       that focus opened stayed open after Tab left the header, lying over the
       control that then had focus (the /sectors/ breadcrumb, for one). Now it
       closes when focus moves to anything outside the header (a null
       relatedTarget, such as a click on panel text, leaves it alone), and
       Escape closes an open panel and puts focus back on its menu item. */
    var escaping = false;
    if (hdEl) hdEl.addEventListener('focusout', function(e){
      if (e.relatedTarget && !hdEl.contains(e.relatedTarget)) closeAll();
    });
    document.addEventListener('keydown', function(e){
      if (e.key !== 'Escape') return;
      var open = null;
      items.forEach(function(it){ if (it.classList.contains('open')) open = it; });
      if (!open) return;
      var a = document.activeElement, back = a && (a.closest('.hd-mega') || open.contains(a));
      closeAll();
      if (back) { escaping = true; open.querySelector('a').focus(); escaping = false; }
    });

    /* Mobile menu focus (pre-launch 2026-10; CANVAS-SYNC 176). The drawer is an
       aria-modal dialog, so while it is open keyboard focus lives inside it:
       opening moves focus to its first control (the close button); Tab and
       Shift+Tab wrap within it; Escape or the close button closes it; and
       closing returns focus to the menu button. Without this, focus stayed on
       the page behind the open menu (about 63 Tabs to reach it). */
    function drawerFocusables(){
      return [].slice.call(drawerEl.querySelectorAll('a[href], button:not([disabled]), input:not([disabled]), select, textarea, [tabindex]:not([tabindex="-1"])'))
        .filter(function(el){ return el.getClientRects().length > 0; });
    }
    function toggleDrawer(on){
      if(!drawerEl) return;
      var was = drawerEl.classList.contains('open');
      drawerEl.classList.toggle('open', on); document.body.style.overflow = on ? 'hidden' : '';
      if (on && !was) { var f = drawerFocusables()[0]; if (f) f.focus(); }
      else if (!on && was && bOpen) bOpen.focus();
    }
    document.addEventListener('keydown', function(e){
      if (e.key !== 'Tab' || !drawerEl || !drawerEl.classList.contains('open')) return;
      var f = drawerFocusables(); if (!f.length) return;
      var first = f[0], last = f[f.length - 1], a = document.activeElement;
      if (!drawerEl.contains(a)) { e.preventDefault(); (e.shiftKey ? last : first).focus(); }
      else if (e.shiftKey && a === first) { e.preventDefault(); last.focus(); }
      else if (!e.shiftKey && a === last) { e.preventDefault(); first.focus(); }
    });
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

    /* Forms: inert unless the build rendered them live. Hooks: [data-form="pledge"]
       [data-form="updates"] [data-form="contact"]. A form is live only when its
       switch rendered it with data-live and an action: features.contactFormOpen
       for the contact form (partials/forms/contact.njk), features.formsOpen for
       the pledge and updates sign-ups (partials/forms/pledge.njk, updates.njk;
       CHG-009). Every other form's submit stays cancelled. A live form is sent
       with fetch to its same-origin action and the outcome is written into its
       live region; with JS off the browser posts it and the handler answers
       with a plain page. */
    function contactResult(note, ok){
      note.textContent = '';
      if (ok) { note.textContent = 'Thank you — your message has been sent. We’ll reply by email.'; return; }
      var a = document.createElement('a');
      a.href = 'mailto:contact@uncost.org'; a.textContent = 'contact@uncost.org';
      note.appendChild(document.createTextNode('Your message could not be sent. Please email '));
      note.appendChild(a);
      note.appendChild(document.createTextNode(' instead.'));
    }
    function wireContact(f){
      var note = f.querySelector('.cnote'), btn = f.querySelector('button[type="submit"]');
      f.addEventListener('submit', function(e){
        e.preventDefault();
        if (btn) btn.disabled = true;
        if (note) note.textContent = 'Sending…';
        fetch(f.getAttribute('action'), { method: 'POST', body: new FormData(f), headers: { 'Accept': 'application/json' } })
          .then(function(r){ return r.ok ? r.json() : { ok: false }; })
          .catch(function(){ return { ok: false }; })
          .then(function(res){
            var ok = !!(res && res.ok);
            if (note) contactResult(note, ok);
            if (ok) f.reset();
            if (btn) btn.disabled = false;
          });
      });
    }
    /* Sign-ups: the answer is the same for a new, repeated or opted-out
       address, so "check your inbox" is all a success can say. */
    var SIGNUP_SENT = {
      pledge: 'Check your inbox: we’ve sent you a link to confirm your signature. It works for 24 hours, and your signature counts once you open it and press Confirm.',
      updates: 'Check your inbox: we’ve sent you a link to confirm. It works for 7 days, and we won’t email you anything else until you open it and press Confirm.'
    };
    function signupNote(f){
      return f.querySelector('.err') || (f.parentNode && f.parentNode.querySelector('[data-updates-note]'));
    }
    function wireSignup(f){
      var kind = f.getAttribute('data-form'), note = signupNote(f), btn = f.querySelector('button[type="submit"]');
      f.addEventListener('submit', function(e){
        e.preventDefault();
        if (btn) btn.disabled = true;
        if (note) note.textContent = 'Sending…';
        fetch(f.getAttribute('action'), { method: 'POST', body: new FormData(f), headers: { 'Accept': 'application/json' } })
          .then(function(r){ return r.status; })
          .catch(function(){ return 0; })
          .then(function(status){
            var msg = status === 202 ? SIGNUP_SENT[kind]
              : status === 400 ? 'That wasn’t accepted. Check your email address and the required boxes, then try again.'
              : status === 404 ? 'Sign-ups are closed just now. Please try again later.'
              : status === 429 ? 'Too many tries from here. Please wait a few minutes, then try again.'
              : 'That didn’t go through. Please try again in a few minutes.';
            if (note) note.textContent = msg;
            if (status === 202) f.reset();
            if (btn) btn.disabled = false;
          });
      });
    }
    document.querySelectorAll('[data-form]').forEach(function(f){
      if (f.matches('form[data-form="contact"][data-live][action]')) { wireContact(f); return; }
      if (f.matches('form[data-form="pledge"][data-live][action], form[data-form="updates"][data-live][action]')) { wireSignup(f); return; }
      f.addEventListener('submit', function(e){ e.preventDefault(); });
    });
  });
})();
