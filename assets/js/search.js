/* Dictionary search, filtering and autocomplete.
   The page is fully usable without this file: every entry is rendered as a link in the
   no-script list and each term has its own crawlable URL. */
(function () {
  'use strict';

  var PAGE_SIZE = 20;
  var state = { q: '', subject: '', letter: '', page: 1, reviewed: false };
  var index = null;

  function norm(s) {
    return (s || '').toLowerCase()
      .replace(/[\u2018\u2019\u201c\u201d]/g, "'")
      .replace(/[-\u2010-\u2015_/]+/g, ' ')
      .replace(/[^a-z0-9*:+' ]+/g, ' ')
      .replace(/\s+/g, ' ')
      .trim();
  }

  function levenshtein(a, b) {
    if (a === b) return 0;
    if (!a.length || !b.length) return Math.max(a.length, b.length);
    var prev = [], cur = [], i, j;
    for (j = 0; j <= b.length; j++) prev[j] = j;
    for (i = 1; i <= a.length; i++) {
      cur[0] = i;
      for (j = 1; j <= b.length; j++) {
        cur[j] = Math.min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (a[i - 1] === b[j - 1] ? 0 : 1));
      }
      prev = cur.slice();
    }
    return prev[b.length];
  }

  /* Ranking, highest first:
     100 exact preferred term | 90 exact acronym | 85 exact synonym
     70 term prefix | 60 acronym/synonym prefix | 50 word-start inside term
     40 substring in term | 30 substring in synonym | 20 substring in definition */
  function score(rec, q) {
    var t = rec.nterm, a = rec.nacronym, defn = rec.ndef, syn = rec.nsyn || [];
    var i, s = 0;
    if (t === q) return 100;
    if (a && a === q) return 90;
    for (i = 0; i < syn.length; i++) if (syn[i] === q) return 85;
    if (t.indexOf(q) === 0) s = Math.max(s, 70);
    if (a && a.indexOf(q) === 0) s = Math.max(s, 60);
    for (i = 0; i < syn.length; i++) if (syn[i].indexOf(q) === 0) s = Math.max(s, 60);
    if (s === 0 && (' ' + t).indexOf(' ' + q) > -1) s = 50;
    if (s === 0 && t.indexOf(q) > -1) s = 40;
    if (s === 0) { for (i = 0; i < syn.length; i++) if (syn[i].indexOf(q) > -1) { s = 30; break; } }
    if (s === 0 && defn.indexOf(q) > -1) s = 20;
    return s;
  }

  function matches(rec) {
    if (state.reviewed && rec.state !== 'published') return false;
    if (state.subject && rec.subjects.indexOf(state.subject) === -1) return false;
    if (state.letter) {
      if (state.letter === '#') { if (/^[a-z]/.test(rec.letter)) return false; }
      else if (rec.letter !== state.letter.toLowerCase()) return false;
    }
    if (state.q) { if (score(rec, norm(state.q)) <= 0) return false; }
    return true;
  }

  function results() {
    var out = index.filter(matches);
    if (state.q) {
      var q = norm(state.q);
      out.sort(function (x, y) {
        var d = score(y, q) - score(x, q);
        return d !== 0 ? d : x.term.localeCompare(y.term);
      });
    } else {
      out.sort(function (x, y) { return x.term.localeCompare(y.term); });
    }
    return out;
  }

  function didYouMean(q) {
    var nq = norm(q), best = null, bestD = 99;
    if (nq.length < 4) return null;
    index.forEach(function (r) {
      var d = levenshtein(nq, r.nterm);
      if (d < bestD) { bestD = d; best = r; }
    });
    return (best && bestD > 0 && bestD <= 2) ? best : null;
  }

  function esc(s) {
    return String(s).replace(/[&<>"']/g, function (c) {
      return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c];
    });
  }

  function chip(text, cls) { return '<span class="chip ' + (cls || '') + '">' + esc(text) + '</span>'; }

  function renderList(rows, root) {
    var start = (state.page - 1) * PAGE_SIZE;
    var slice = rows.slice(start, start + PAGE_SIZE);
    var html = '<ul class="entry-list">';
    slice.forEach(function (r) {
      html += '<li><h3><a href="' + root + 'terms/' + r.slug + '/">' + esc(r.term) + '</a>' +
        (r.acronym ? ' <span class="acronym">(' + esc(r.acronym) + ')</span>' : '') + '</h3>' +
        '<p>' + esc(r.definition) + '</p><div class="entry-meta">' +
        r.subjects.map(function (s) { return chip(s.replace(/-/g, ' ')); }).join('') +
        chip(r.state === 'published' ? 'Published' : 'Draft — not yet reviewed',
             r.state === 'published' ? 'chip-published' : 'chip-draft') +
        '</div></li>';
    });
    html += '</ul>';
    return html;
  }

  function renderPagination(total) {
    var pages = Math.ceil(total / PAGE_SIZE);
    if (pages <= 1) return '';
    var html = '<nav aria-label="Result pages"><ul class="pagination">';
    var add = function (p, label, cur) {
      html += '<li><a href="' + queryString({ page: p }) + '" data-page="' + p + '"' +
        (cur ? ' aria-current="page"' : '') + '>' + label + '</a></li>';
    };
    if (state.page > 1) add(state.page - 1, 'Previous');
    var from = Math.max(1, state.page - 2), to = Math.min(pages, state.page + 2);
    if (from > 1) add(1, '1');
    if (from > 2) html += '<li><span>…</span></li>';
    for (var p = from; p <= to; p++) add(p, String(p), p === state.page);
    if (to < pages - 1) html += '<li><span>…</span></li>';
    if (to < pages) add(pages, String(pages));
    if (state.page < pages) add(state.page + 1, 'Next');
    html += '</ul></nav>';
    return html;
  }

  function queryString(over) {
    var s = Object.assign({}, state, over || {});
    var p = new URLSearchParams();
    if (s.q) p.set('q', s.q);
    if (s.subject) p.set('subject', s.subject);
    if (s.letter) p.set('letter', s.letter);
    if (s.reviewed) p.set('reviewed', '1');
    if (s.page && s.page > 1) p.set('page', String(s.page));
    var qs = p.toString();
    return qs ? '?' + qs : location.pathname;
  }

  function readState() {
    var p = new URLSearchParams(location.search);
    state.q = p.get('q') || '';
    state.subject = p.get('subject') || '';
    state.letter = p.get('letter') || '';
    state.reviewed = p.get('reviewed') === '1';
    state.page = Math.max(1, parseInt(p.get('page') || '1', 10) || 1);
  }

  function pushState(replace) {
    var url = queryString();
    if (replace) history.replaceState(state, '', url);
    else history.pushState(state, '', url);
  }

  function render(root, announce) {
    var rows = results();
    var listEl = document.getElementById('results');
    var countEl = document.getElementById('result-count');
    var activeEl = document.getElementById('active-filters');
    var pages = Math.ceil(rows.length / PAGE_SIZE);
    if (state.page > pages && pages > 0) state.page = pages;

    countEl.textContent = rows.length === 1 ? '1 entry' : rows.length + ' entries';

    var bits = [];
    if (state.q) bits.push('search “' + esc(state.q) + '”');
    if (state.subject) bits.push('subject ' + esc(state.subject.replace(/-/g, ' ')));
    if (state.letter) bits.push('letter ' + esc(state.letter.toUpperCase()));
    if (state.reviewed) bits.push('scientifically reviewed entries only');
    activeEl.innerHTML = bits.length
      ? 'Active filters: ' + bits.map(function (b) { return chip(b); }).join(' ') +
        ' <button type="button" class="btn btn-secondary btn-small" id="reset-filters">Reset all</button>'
      : '';
    var reset = document.getElementById('reset-filters');
    if (reset) reset.addEventListener('click', function () {
      state = { q: '', subject: '', letter: '', page: 1, reviewed: false };
      syncControls(); pushState(false); render(root, true);
    });

    if (rows.length === 0) {
      var dym = state.q ? didYouMean(state.q) : null;
      listEl.innerHTML = '<div class="callout callout-warn"><h2>No entries matched</h2>' +
        (dym ? '<p>Did you mean <a href="' + root + 'terms/' + dym.slug + '/">' + esc(dym.term) +
               '</a>? Your search was not changed automatically.</p>' : '') +
        '<p>You can remove a filter, try a synonym or an acronym, browse by subject, or ' +
        '<a href="' + root + 'contribute/#suggest">suggest this term</a> for a future release. ' +
        'The dictionary does not generate definitions automatically.</p></div>';
    } else {
      listEl.innerHTML = renderList(rows, root) + renderPagination(rows.length);
      Array.prototype.forEach.call(listEl.querySelectorAll('[data-page]'), function (a) {
        a.addEventListener('click', function (ev) {
          ev.preventDefault();
          state.page = parseInt(a.getAttribute('data-page'), 10);
          pushState(false); render(root, true);
          document.getElementById('results-heading').focus();
        });
      });
    }
    if (announce) {
      var live = document.getElementById('result-status');
      live.textContent = rows.length + ' entr' + (rows.length === 1 ? 'y' : 'ies') + ' found';
    }
    var azLinks = document.querySelectorAll('.az a[data-letter]');
    Array.prototype.forEach.call(azLinks, function (a) {
      if (a.getAttribute('data-letter') === state.letter) a.setAttribute('aria-current', 'true');
      else a.removeAttribute('aria-current');
    });
  }

  function syncControls() {
    var q = document.getElementById('q'); if (q) q.value = state.q;
    var s = document.getElementById('subject'); if (s) s.value = state.subject;
    var r = document.getElementById('reviewed-only'); if (r) r.checked = state.reviewed;
  }

  function initDictionary(root) {
    readState();
    syncControls();
    render(root, false);

    var form = document.getElementById('filter-form');
    var q = document.getElementById('q');
    var timer = null;
    if (q) q.addEventListener('input', function () {
      window.clearTimeout(timer);
      timer = window.setTimeout(function () {
        state.q = q.value; state.page = 1; pushState(true); render(root, true);
      }, 180);
    });
    if (form) form.addEventListener('submit', function (ev) {
      ev.preventDefault();
      state.q = q ? q.value : '';
      state.page = 1; pushState(false); render(root, true);
    });
    var s = document.getElementById('subject');
    if (s) s.addEventListener('change', function () {
      state.subject = s.value; state.page = 1; pushState(false); render(root, true);
    });
    var rv = document.getElementById('reviewed-only');
    if (rv) rv.addEventListener('change', function () {
      state.reviewed = rv.checked; state.page = 1; pushState(false); render(root, true);
    });
    Array.prototype.forEach.call(document.querySelectorAll('.az a[data-letter]'), function (a) {
      a.addEventListener('click', function (ev) {
        ev.preventDefault();
        var L = a.getAttribute('data-letter');
        state.letter = (state.letter === L) ? '' : L;
        state.page = 1; pushState(false); render(root, true);
      });
    });
    window.addEventListener('popstate', function () {
      readState(); syncControls(); render(root, true);
    });
  }

  function initAutocomplete(root) {
    var input = document.querySelector('[data-autocomplete]');
    if (!input) return;
    var list = document.getElementById(input.getAttribute('aria-owns'));
    if (!list) return;
    input.addEventListener('input', function () {
      var q = norm(input.value);
      list.innerHTML = '';
      if (q.length < 2 || !index) return;
      var hits = index.map(function (r) { return { r: r, s: score(r, q) }; })
        .filter(function (o) { return o.s > 0; })
        .sort(function (a, b) { return b.s - a.s || a.r.term.localeCompare(b.r.term); })
        .slice(0, 8);
      hits.forEach(function (o) {
        var li = document.createElement('li');
        li.innerHTML = '<a href="' + root + 'terms/' + o.r.slug + '/">' + esc(o.r.term) +
          (o.r.acronym ? ' <span class="s-sub">(' + esc(o.r.acronym) + ')</span>' : '') + '</a>';
        list.appendChild(li);
      });
    });
    document.addEventListener('click', function (ev) {
      if (!list.contains(ev.target) && ev.target !== input) list.innerHTML = '';
    });
  }

  document.addEventListener('DOMContentLoaded', function () {
    var root = document.body.getAttribute('data-root') || '';
    fetch(root + 'search-index.json')
      .then(function (r) { return r.json(); })
      .then(function (data) {
        index = data.map(function (r) {
          r.nterm = norm(r.term);
          r.nacronym = norm(r.acronym || '');
          r.nsyn = (r.synonyms || []).map(norm);
          r.ndef = norm(r.definition);
          r.letter = (r.term[0] || '').toLowerCase();
          return r;
        });
        if (document.getElementById('results')) initDictionary(root);
        initAutocomplete(root);
      })
      .catch(function () {
        var el = document.getElementById('search-fallback');
        if (el) el.hidden = false;
      });
  });
})();
