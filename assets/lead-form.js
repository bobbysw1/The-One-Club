/* The One Club — shared lead-form submitter.
 *
 * Markup contract (per form):
 *   <form data-lead-form="valuation" novalidate>
 *     <div class="field"><label for="x">…</label><input id="x" name="firstName" required/>
 *       <span class="field-error">Please enter your first name</span>
 *     </div>
 *     …
 *     <input class="hp-field" name="hp_field" tabindex="-1" autocomplete="off"/>
 *     <button class="fsub" type="submit">Submit</button>
 *     <p class="form-status" role="status"></p>
 *   </form>
 *
 * Optional attributes on <form>:
 *   data-success         Custom success message (default: "Request received — we'll be in touch within 24 hours")
 *   data-gtag-event      Custom GA event name (default: form_submit)
 *   data-gtag-label      GA event label
 *
 * The script POSTs to (window.ONE_CLUB_API || '/api') + '/lead' with
 *   { source, fields, page }.
 */
(function () {
  var API_BASE = (window.ONE_CLUB_API || '/api').replace(/\/+$/, '');

  function setError(field, on) {
    if (!field) return;
    if (on) field.classList.add('invalid');
    else    field.classList.remove('invalid');
  }

  function validateField(input) {
    var field = input.closest('.field');
    if (!field) return true;
    var v = (input.value || '').trim();
    var bad = false;
    if (input.required && !v) bad = true;
    else if (input.type === 'email' && v && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(v)) bad = true;
    else if (input.type === 'tel' && v && !/^[0-9+ ()\-]{6,}$/.test(v)) bad = true;
    setError(field, bad);
    return !bad;
  }

  function setStatus(form, msg, kind) {
    var status = form.querySelector('.form-status');
    if (!status) return;
    status.textContent = msg || '';
    status.classList.remove('is-error', 'is-ok');
    if (kind) status.classList.add('is-' + kind);
  }

  function gatherFields(form) {
    var out = {};
    var els = form.querySelectorAll('input[name], select[name], textarea[name]');
    els.forEach(function (el) {
      if (el.type === 'checkbox') { out[el.name] = el.checked ? 'yes' : ''; return; }
      if (el.tagName === 'SELECT' && el.multiple) {
        out[el.name] = Array.from(el.selectedOptions).map(function (o) { return o.value; }).join(', ');
        return;
      }
      out[el.name] = (el.value || '').trim();
    });
    return out;
  }

  function submit(form, e) {
    e.preventDefault();
    var inputs = form.querySelectorAll('input[name], select[name], textarea[name]');
    var ok = true;
    inputs.forEach(function (i) { if (!validateField(i)) ok = false; });
    if (!ok) {
      setStatus(form, 'Please correct the highlighted fields.', 'error');
      var first = form.querySelector('.field.invalid input, .field.invalid select');
      if (first) first.focus();
      return;
    }

    var btn = form.querySelector('button[type="submit"]') || form.querySelector('.fsub');
    var origText = btn ? btn.textContent : '';
    if (btn) { btn.disabled = true; btn.textContent = 'Sending…'; }
    setStatus(form, '', null);

    var source = form.getAttribute('data-lead-form');
    var payload = {
      source: source,
      fields: gatherFields(form),
      page: location.pathname + location.hash
    };

    fetch(API_BASE + '/lead', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
      credentials: 'omit'
    }).then(function (res) {
      return res.json().catch(function () { return {}; }).then(function (data) {
        return { ok: res.ok, status: res.status, data: data };
      });
    }).then(function (r) {
      if (!r.ok) {
        if (btn) { btn.disabled = false; btn.textContent = origText; }
        var msg = (r.data && r.data.error) ? r.data.error : 'Something went wrong. Please try again or call +61 404 774 272.';
        setStatus(form, msg, 'error');
        return;
      }
      // Success: show success state on the button + GA event.
      if (btn) {
        var success = form.getAttribute('data-success') || "Request received — we'll be in touch within 24 hours";
        btn.textContent = success;
        btn.style.background = 'transparent';
        btn.style.color = '#4ade80';
        btn.style.border = '1px solid rgba(74,222,128,.25)';
        btn.style.boxShadow = 'none';
        btn.style.transform = 'none';
      }
      setStatus(form, '', 'ok');
      if (typeof window.gtag === 'function') {
        window.gtag('event', form.getAttribute('data-gtag-event') || 'form_submit', {
          event_category: 'Lead',
          event_label: form.getAttribute('data-gtag-label') || source
        });
      }
      // Disable the form so it can't be resubmitted.
      inputs.forEach(function (i) { i.disabled = true; });
    }).catch(function () {
      if (btn) { btn.disabled = false; btn.textContent = origText; }
      setStatus(form, 'Network error. Please try again or call +61 404 774 272.', 'error');
    });
  }

  function bind(form) {
    if (form.__leadBound) return;
    form.__leadBound = true;
    form.addEventListener('submit', function (e) { submit(form, e); });
    form.querySelectorAll('input, select, textarea').forEach(function (el) {
      el.addEventListener('input', function () { setError(el.closest('.field'), false); setStatus(form, '', null); });
      el.addEventListener('blur', function () { validateField(el); });
    });
  }

  function init() {
    document.querySelectorAll('form[data-lead-form]').forEach(bind);
  }

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init);
  else init();
})();
