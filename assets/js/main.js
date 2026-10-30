/* Site-wide behaviour: navigation, copy link, print, report-error context. */
(function () {
  'use strict';

  function ready(fn) {
    if (document.readyState !== 'loading') fn();
    else document.addEventListener('DOMContentLoaded', fn);
  }

  ready(function () {
    // --- mobile navigation ---
    var toggle = document.querySelector('.nav-toggle');
    var links = document.getElementById('nav-links');
    if (toggle && links) {
      var sync = function () {
        if (window.innerWidth > 820) { links.hidden = false; toggle.setAttribute('aria-expanded', 'false'); }
        else if (toggle.getAttribute('aria-expanded') !== 'true') { links.hidden = true; }
      };
      toggle.addEventListener('click', function () {
        var open = toggle.getAttribute('aria-expanded') === 'true';
        toggle.setAttribute('aria-expanded', String(!open));
        links.hidden = open;
      });
      window.addEventListener('resize', sync);
      sync();
    }

    // --- current year ---
    var y = document.getElementById('year');
    if (y) y.textContent = String(new Date().getFullYear());

    // --- copy link ---
    var copy = document.querySelector('[data-copy-link]');
    if (copy) {
      copy.addEventListener('click', function () {
        var url = window.location.href.split('#')[0];
        var done = function () {
          var old = copy.textContent;
          copy.textContent = 'Link copied';
          window.setTimeout(function () { copy.textContent = old; }, 2000);
        };
        if (navigator.clipboard && navigator.clipboard.writeText) {
          navigator.clipboard.writeText(url).then(done, done);
        } else {
          var ta = document.createElement('textarea');
          ta.value = url; document.body.appendChild(ta); ta.select();
          try { document.execCommand('copy'); } catch (e) {}
          document.body.removeChild(ta); done();
        }
      });
    }

    // --- print ---
    var pr = document.querySelector('[data-print]');
    if (pr) pr.addEventListener('click', function () { window.print(); });

    // --- report-error form: carry term and revision context from the URL ---
    var params = new URLSearchParams(window.location.search);
    ['term', 'entry_id', 'revision'].forEach(function (k) {
      var field = document.querySelector('[data-context="' + k + '"]');
      if (field && params.get(k)) field.value = params.get(k);
    });
  });
})();
