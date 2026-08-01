/* The One Club | Unified AI chat handler.
 *
 * Replaces per-page Gemini clients with a single Mistral proxy.
 * - Local KB for instant FAQ responses
 * - /api/chat (Vercel → Mistral AI + web search)
 * - Off-topic detection to avoid unnecessary API calls
 * - Region-aware response customization
 *
 * Usage: include <script src="/assets/chat.js"></script> in any page,
 * then call sendChat() from the chat form's onsubmit or click handler.
 * Expects: <input id="chat-input" placeholder="Ask...">
 *          <div id="chat-messages"></div>
 *          <div id="chat-quick" class="quick-buttons">…</div> (optional)
 */

(function() {
  window.CHAT_API     = '/api/chat';
  window.CHAT_HISTORY = [];

  var DEFLECT_MSG  = "That sits outside what I can help with. For any Gold Coast property question I'm here, otherwise the Free Valuation form at the bottom of the page is the fastest way to reach Bobby directly.";
  var DEFLECT_MSG_CAIRNS = "That sits outside what I can help with. For any Cairns or Port Douglas property question I'm here, otherwise the Free Valuation form at the bottom of the page is the fastest way to reach Bobby directly.";

  var OFF_TOPIC_RE = /\b(weather|joke|funny|riddle|recipe|cook|sport|football|cricket|nba|nfl|election|trump|biden|crypto|bitcoin|stock market|capital of|tell me about yourself|are you (a|an) ai|what.*your name)\b/i;

  function _deflectMsg() {
    return /cairns/i.test(location.pathname) ? DEFLECT_MSG_CAIRNS : DEFLECT_MSG;
  }

  function _looksOnTopic(msg){
    if (!msg || msg.length < 4) return false;
    if (OFF_TOPIC_RE.test(msg)) return false;
    return msg.split(/\s+/).filter(function(w){ return w.length > 2 && /[a-zA-Z]/.test(w); }).length >= 1;
  }

  var LOCAL_FALLBACK_PREFIX = "That's a good one";
  function _localOrNull(msg){
    if (typeof getBotReply !== 'function') return null;
    var reply = getBotReply(msg);
    if (!reply || reply.indexOf(LOCAL_FALLBACK_PREFIX) === 0) return null;
    return reply;
  }

  // ── CONVERSION TRACKING ───────────────────────────────────────
  // Fires gtag events for the interactions that actually indicate a
  // lead, rather than tracking every click. Silently no-ops if gtag
  // isn't loaded (e.g. ad blockers) so it never breaks the chat itself.
  var PRICING_RE = /\b(1%|commission|fee|cost|price|save|saving|matterport|\$)\b/i;
  var BOOKING_RE = /\b(inspect|inspection|book|appraisal|valuation|call|speak|contact|agent)\b/i;

  function _trackEvent(name, params){
    try {
      if (typeof gtag === 'function') gtag('event', name, params || {});
    } catch (e) {}
  }

  function _classifyIntent(msg){
    if (BOOKING_RE.test(msg)) return 'booking';
    if (PRICING_RE.test(msg)) return 'pricing';
    return 'general';
  }

  var _chatOpenTracked = false;
  function _trackChatOpen(){
    if (_chatOpenTracked) return;
    _chatOpenTracked = true;
    _trackEvent('chat_opened', { event_category: 'Chatbot', page_path: location.pathname });
  }

  window.askAI = function(userMsg){
    var sessionCount = parseInt(sessionStorage.getItem('toc_chat_count') || '0', 10) + 1;
    sessionStorage.setItem('toc_chat_count', sessionCount.toString());

    if (sessionCount > 15) {
      return Promise.resolve({
        reply: "You've asked some great questions! To get personalized advice or tailored property info, leave your details below and Bobby will reach out to you directly.",
        quickReplies: ['Get a free valuation', 'Call Bobby'],
        suggestLeadForm: true,
        leadType: 'inquiry'
      });
    }

    var isMobile = window.innerWidth < 768;
    return fetch(window.CHAT_API, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        message: userMsg.slice(0, 350),
        history: window.CHAT_HISTORY.slice(-6),
        region: /cairns/i.test(location.pathname) ? 'cairns' : 'gc',
        isMobile: isMobile,
        page: location.pathname
      })
    })
    .then(function(r){ if(!r.ok) throw new Error(r.status); return r.json(); })
    .then(function(d){
      return {
        reply: (d.reply || _deflectMsg()).trim(),
        quickReplies: d.quickReplies || [],
        suggestLeadForm: d.suggestLeadForm || false,
        leadType: d.leadType || null,
        escalated: d.escalated || false,
        phoneCta: d.phoneCta || null,
        requiresAgent: d.requiresAgent || false
      };
    })
    .catch(function(){
      return {
        reply: _deflectMsg(),
        quickReplies: [],
        suggestLeadForm: false
      };
    });
  };

  function _typingDots(){
    var t = document.createElement('div');
    t.id = 'typing-indicator';
    t.style.cssText = 'display:flex;gap:10px;align-items:flex-start';
    t.innerHTML = '<div style="width:28px;height:28px;border-radius:8px;background:var(--gold);display:grid;place-items:center;font-size:9px;font-weight:700;color:#000;flex-shrink:0">1%</div>'
      + '<div style="background:rgba(var(--fg-rgb),.06);border-radius:4px 14px 14px 14px;padding:12px 16px;display:flex;gap:5px;align-items:center">'
      + '<span style="width:7px;height:7px;border-radius:50%;background:var(--muted);display:inline-block;animation:dot-bounce .9s ease-in-out infinite"></span>'
      + '<span style="width:7px;height:7px;border-radius:50%;background:var(--muted);display:inline-block;animation:dot-bounce .9s ease-in-out .18s infinite"></span>'
      + '<span style="width:7px;height:7px;border-radius:50%;background:var(--muted);display:inline-block;animation:dot-bounce .9s ease-in-out .36s infinite"></span>'
      + '</div>';
    return t;
  }

  function _addMessage(text, role){
    if (typeof addMessage !== 'function') return;
    addMessage(text, role === 'user' ? 'user' : 'bot');
  }

  window.sendChat = function(){
    var input = document.getElementById('chat-input');
    var msg = input.value.trim(); if (!msg) return;
    input.value = '';
    _addMessage(msg, 'user');
    window.CHAT_HISTORY.push({ role: 'user', content: msg });
    _trackEvent('chat_message_sent', { event_category: 'Chatbot', event_label: _classifyIntent(msg), page_path: location.pathname });
    var q = document.getElementById('chat-quick'); if (q) q.style.display = 'none';
    var t = _typingDots();
    var container = document.getElementById('chat-messages');
    if (!container) return;
    container.appendChild(t);
    container.scrollTop = 99999;

    // 1. Local KB, instant.
    var local = _localOrNull(msg);
    if (local){
      window.CHAT_HISTORY.push({ role: 'assistant', content: local });
      setTimeout(function(){ var ti = document.getElementById('typing-indicator'); if(ti) ti.remove(); _addMessage(local, 'bot'); }, 600 + Math.random() * 400);
      return;
    }
    // 2. Off-topic, deflect without API call.
    if (!_looksOnTopic(msg)){
      var deflect = _deflectMsg();
      window.CHAT_HISTORY.push({ role: 'assistant', content: deflect });
      setTimeout(function(){ var ti = document.getElementById('typing-indicator'); if(ti) ti.remove(); _addMessage(deflect, 'bot'); }, 500);
      return;
    }
    // 3. Mistral AI via backend.
    window.askAI(msg).then(function(resp){
      if (!resp || !resp.reply) {
        var ti = document.getElementById('typing-indicator'); if(ti) ti.remove();
        _addMessage('Something went wrong. Please try again.', 'bot');
        return;
      }
      window.CHAT_HISTORY.push({ role: 'assistant', content: resp.reply });
      var ti = document.getElementById('typing-indicator'); if(ti) ti.remove();
      _addMessage(resp.reply, 'bot');

      // Show quick replies if available
      if (resp.quickReplies && resp.quickReplies.length > 0) {
        setTimeout(function(){ _showQuickReplies(resp.quickReplies); }, 800);
      }

      // Show lead form prompt if buyer/seller intent detected
      if (resp.suggestLeadForm && resp.leadType) {
        setTimeout(function(){
          var prompt = resp.leadType === 'seller'
            ? 'Ready for a free valuation? Leave your details and I\'ll send you a realistic price range.'
            : 'Want to know when matching properties come on the market? Register your buyer profile.';
          _addMessage(prompt, 'bot');
          _showLeadForm(resp.leadType);
          _trackEvent('chat_lead_form_shown', { event_category: 'Chatbot', event_label: resp.leadType, page_path: location.pathname });
        }, 1200);
      }

      // Show phone CTA for mobile
      if (resp.phoneCta) {
        setTimeout(function(){
          var phoneMsg = document.createElement('div');
          phoneMsg.style.cssText = 'background:rgba(var(--gold-rgb),.1);border-radius:8px;padding:12px;margin:12px 0;text-align:center;font-size:13px';
          phoneMsg.innerHTML = '<strong>' + resp.phoneCta + '</strong>';
          document.getElementById('chat-messages').appendChild(phoneMsg);
        }, 1600);
        _trackEvent('chat_phone_cta_shown', { event_category: 'Chatbot', page_path: location.pathname });
      }

      // High-intent signal: the backend decided a human agent is needed
      if (resp.requiresAgent || resp.escalated) {
        _trackEvent('chat_escalated_to_agent', { event_category: 'Chatbot', page_path: location.pathname });
      }
    });
  };

  window.sendQuick = function(text){
    var input = document.getElementById('chat-input');
    if (input) { input.value = text; window.sendChat(); }
  };

  // ── SUBTLE DISCOVERY TACTICS ──────────────────────────────────
  // Elegant, non-intrusive ways to surface the chatbot

  // Scroll trigger: gentle hint after scrolling
  function _initScrollHint(){
    var hintShown = false;
    var scrollPos = 0;
    window.addEventListener('scroll', function(){
      var newPos = window.scrollY;
      if (newPos > scrollPos + 500 && !hintShown && newPos > 800){
        hintShown = true;
        var hint = document.createElement('div');
        hint.style.cssText = 'position:fixed;bottom:80px;right:20px;background:rgba(var(--gold-rgb),.95);color:#000;padding:12px 16px;border-radius:6px;font-size:12px;z-index:9997;opacity:0;transform:translateY(20px);transition:all.3s;cursor:pointer;max-width:180px';
        hint.innerHTML = '💬 <strong>Quick question?</strong> Ask our AI agent';
        hint.onclick = function(){
          document.getElementById('chat-widget')?.click?.();
          this.remove();
        };
        document.body.appendChild(hint);
        setTimeout(function(){ hint.style.opacity = '1'; hint.style.transform = 'translateY(0)'; }, 10);
        setTimeout(function(){ hint.style.opacity = '0'; hint.style.transform = 'translateY(20px)'; }, 4000);
        setTimeout(function(){ hint.remove(); }, 4300);
      }
      scrollPos = newPos;
    });
  }

  // Blog/article inline: suggest chat after reading
  function _initBlogInline(){
    // Disabled as requested
  }

  // Contextual in listings: suggest chat for property-specific Qs
  window.askAboutProperty = function(addrText) {
    var bubble = document.getElementById('chat-bubble');
    var panel = document.getElementById('chat-panel');
    if (bubble && panel && !panel.classList.contains('active')) {
      bubble.click();
    }
    var prompt = addrText ? 'Tell me about ' + addrText + ', school catchments, flight paths, and commute times' : 'Tell me about this address, school catchments and flight paths';
    var input = document.getElementById('chat-input');
    if (input) {
      input.value = prompt;
      window.sendChat();
    }
  };

  function _initListingHint(){
    var listings = document.querySelectorAll('.listing-card, [data-listing], .property-detail, .listing-info');
    if (!listings || listings.length === 0) return;

    listings.forEach(function(card){
      if (card.querySelector('.ai-listing-prompt')) return;
      var addrEl = card.querySelector('.listing-address, .listing-suburb, h3, h2');
      var addrText = addrEl ? addrEl.textContent.trim() : '';

      var hint = document.createElement('div');
      hint.className = 'ai-listing-prompt';
      hint.style.cssText = 'background:rgba(var(--gold-rgb),.06);border:1px solid rgba(var(--gold-rgb),.2);border-radius:10px;padding:10px 14px;margin:12px 14px;font-size:12px;display:flex;align-items:center;justify-content:space-between;gap:8px';
      hint.innerHTML = '<span>💡 <strong>Ask AI about this home:</strong> school zones, flight paths &amp; commutes</span> '
        + '<button style="background:var(--gold);color:#000;border:none;border-radius:6px;padding:5px 10px;font-weight:600;cursor:pointer;font-size:11px;white-space:nowrap" onclick="event.stopPropagation(); window.askAboutProperty(\'' + addrText.replace(/'/g, "\\'") + '\')">Ask AI →</button>';
      card.appendChild(hint);
    });
  }

  // Boot discovery features after page loads
  function _initDiscovery(){
    try {
      _initScrollHint();
      if (document.querySelector('article, [role="article"]')) _initBlogInline();
      _initListingHint();
      var bubble = document.getElementById('chat-bubble');
      if (bubble) bubble.addEventListener('click', _trackChatOpen);
      var mobileAsk = document.querySelector('.mobile-cta-bar .btn-gold');
      if (mobileAsk) mobileAsk.addEventListener('click', _trackChatOpen);
    } catch(e) {}
  }

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', _initDiscovery);
  else _initDiscovery();

  function _showQuickReplies(replies){
    if (!replies || replies.length === 0) return;
    var container = document.getElementById('chat-messages');
    if (!container) return;
    var quickDiv = document.createElement('div');
    quickDiv.style.cssText = 'display:flex;gap:8px;flex-wrap:wrap;margin:8px 0;padding:0 12px';
    replies.slice(0, 3).forEach(function(text){
      var btn = document.createElement('button');
      btn.style.cssText = 'background:rgba(var(--fg-rgb),.08);border:1px solid rgba(var(--fg-rgb),.2);border-radius:6px;padding:6px 12px;font-size:12px;cursor:pointer;transition:all.2s';
      btn.textContent = text;
      btn.onmouseover = function(){ this.style.background = 'rgba(var(--fg-rgb),.12)'; };
      btn.onmouseout = function(){ this.style.background = 'rgba(var(--fg-rgb),.08)'; };
      btn.onclick = function(){ _trackEvent('chat_quick_reply_click', { event_category: 'Chatbot', event_label: text }); window.sendQuick(text); };
      quickDiv.appendChild(btn);
    });
    container.appendChild(quickDiv);
    container.scrollTop = container.scrollHeight;
  }

  function _showLeadForm(type){
    var container = document.getElementById('chat-messages');
    if (!container) return;
    var form = document.createElement('form');
    form.style.cssText = 'background:rgba(var(--gold-rgb),.05);border:1px solid rgba(var(--gold-rgb),.2);border-radius:8px;padding:12px;margin:8px 0 0;font-size:13px';
    form.innerHTML = '<input type="text" placeholder="First name" style="width:100%;padding:6px;margin-bottom:6px;border:1px solid rgba(var(--fg-rgb),.2);border-radius:4px;font-size:12px" required>'
      + '<input type="email" placeholder="Email" style="width:100%;padding:6px;margin-bottom:6px;border:1px solid rgba(var(--fg-rgb),.2);border-radius:4px;font-size:12px" required>'
      + '<input type="text" placeholder="Property address" style="width:100%;padding:6px;margin-bottom:8px;border:1px solid rgba(var(--fg-rgb),.2);border-radius:4px;font-size:12px" required>'
      + '<button type="submit" style="width:100%;background:var(--gold);color:#000;border:none;border-radius:4px;padding:8px;font-weight:600;cursor:pointer;font-size:12px">Register</button>';
    form.onsubmit = function(e){
      e.preventDefault();
      var inputs = form.querySelectorAll('input');
      var data = { firstName: inputs[0].value, email: inputs[1].value, address: inputs[2].value, source: type === 'seller' ? 'valuation' : 'buyer' };
      fetch('/api/lead', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ source: data.source, fields: data, page: location.pathname })
      }).then(function(){
        form.innerHTML = '<div style="text-align:center;color:var(--gold);font-weight:600">Thanks! We\'ll be in touch within 24 hours.</div>';
        _trackEvent('chat_lead_form_submit', { event_category: 'Lead', event_label: data.source, page_path: location.pathname });
      });
    };
    container.appendChild(form);
    container.scrollTop = container.scrollHeight;
  }
})();
