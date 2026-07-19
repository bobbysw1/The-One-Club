/* Region-aware copy for shared pages.
   Visiting any /cairns/ page remembers the visitor as a Cairns customer;
   visiting the Gold Coast homepage remembers Gold Coast. Shared pages
   (About, Guides, Calculators, etc.) then read as the visitor's region:
   visible "Gold Coast" copy becomes "Cairns" and valuation/suburb links
   route to the Cairns page. Region-specific pages are never rewritten,
   and nothing inside <script> tags (JSON-LD/SEO) is touched. */
(function () {
  var KEY = 'toc.region';
  var path = location.pathname;
  var region = null;
  try {
    if (path.indexOf('/cairns/') === 0 || path === '/cairns') {
      localStorage.setItem(KEY, 'cairns');
      return;
    }
    if (path === '/' || path === '/index.html') {
      localStorage.setItem(KEY, 'gc');
      return;
    }
    region = localStorage.getItem(KEY);
  } catch (e) { return; }
  if (region !== 'cairns') return;

  // Shared pages only; Gold Coast suburb pages keep their own copy.
  var ALLOW = ['/about/', '/how-it-works/', '/blog/', '/agents/', '/calculators/',
               '/after-sale/', '/for-sale/', '/auctions/', '/rentals/', '/privacy/',
               '/terms/', '/complaints/', '/mortgage/'];
  var ok = false;
  for (var i = 0; i < ALLOW.length; i++) {
    if (path.indexOf(ALLOW[i]) === 0) { ok = true; break; }
  }
  if (!ok) return;

  function swapText(s) {
    return s
      .replace(/the Gold Coast and Cairns & Port Douglas/g, '\x01') // protect from the generic rules below
      .replace(/on the Gold Coast/g, 'in Cairns')
      .replace(/the Gold Coast/g, 'Cairns')
      .replace(/Gold Coast/g, 'Cairns')
      .replace(/\x01/g, 'Cairns & Port Douglas and the Gold Coast');
  }

  // Some lines pair a region name with region-specific facts (prices, stats)
  // that a word-level swap can't correct safely, e.g. "$900,000" tied to
  // "Gold Coast". Those are authored explicitly via data-cairns-text
  // (textContent) or data-cairns-html (innerHTML, for lines with emphasis
  // markup) and applied whole, never touched by the generic word swap below.
  function applyOverrides(root) {
    if (!root || !root.querySelectorAll) return;
    root.querySelectorAll('[data-cairns-text]').forEach(function (el) {
      el.textContent = el.getAttribute('data-cairns-text');
    });
    root.querySelectorAll('[data-cairns-html]').forEach(function (el) {
      el.innerHTML = el.getAttribute('data-cairns-html');
    });
    // Region-specific photography, e.g. the before/after comparison shots
    // on shared pages like /how-it-works/, swap to real Cairns/FNQ images
    // rather than showing Gold Coast properties to a Cairns visitor.
    root.querySelectorAll('[data-cairns-src]').forEach(function (el) {
      el.setAttribute('src', el.getAttribute('data-cairns-src'));
      if (el.hasAttribute('data-cairns-srcset')) el.setAttribute('srcset', el.getAttribute('data-cairns-srcset'));
      if (el.hasAttribute('data-cairns-alt')) el.setAttribute('alt', el.getAttribute('data-cairns-alt'));
    });
  }

  function walk(root) {
    if (!root) return;
    var w = document.createTreeWalker(root, NodeFilter.SHOW_TEXT, {
      acceptNode: function (n) {
        var p = n.parentNode && n.parentNode.nodeName;
        if (p === 'SCRIPT' || p === 'STYLE' || p === 'NOSCRIPT' || p === 'TEXTAREA') return NodeFilter.FILTER_REJECT;
        if (n.parentNode && n.parentNode.closest && n.parentNode.closest('[data-cairns-text],[data-cairns-html]')) return NodeFilter.FILTER_REJECT;
        return n.nodeValue.indexOf('Gold Coast') !== -1 ? NodeFilter.FILTER_ACCEPT : NodeFilter.FILTER_SKIP;
      }
    });
    var nodes = [];
    while (w.nextNode()) nodes.push(w.currentNode);
    for (var i = 0; i < nodes.length; i++) nodes[i].nodeValue = swapText(nodes[i].nodeValue);
  }

  function rewriteLinks(root) {
    if (!root || !root.querySelectorAll) return;
    ['valuation', 'suburbs', 'savings'].forEach(function (a) {
      root.querySelectorAll('a[href="/#' + a + '"]').forEach(function (el) {
        el.setAttribute('href', '/cairns/#' + a);
        el.removeAttribute('onclick');
      });
    });
  }

  function apply() {
    document.title = swapText(document.title);
    applyOverrides(document);
    walk(document.body);
    rewriteLinks(document);
    // Content injected later (chat replies, listings) stays consistent too.
    if (typeof MutationObserver !== 'undefined') {
      var mo = new MutationObserver(function (muts) {
        for (var i = 0; i < muts.length; i++) {
          var added = muts[i].addedNodes || [];
          for (var j = 0; j < added.length; j++) {
            var n = added[j];
            if (n.nodeType === 3 && n.nodeValue.indexOf('Gold Coast') !== -1) n.nodeValue = swapText(n.nodeValue);
            else if (n.nodeType === 1) { applyOverrides(n); walk(n); rewriteLinks(n); }
          }
        }
      });
      mo.observe(document.body, { childList: true, subtree: true });
    }
  }

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', apply);
  else apply();
})();
