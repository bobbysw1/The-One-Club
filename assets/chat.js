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

  window.askAI = function(userMsg){
    return fetch(window.CHAT_API, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        message: userMsg.slice(0, 500),
        history: window.CHAT_HISTORY.slice(-8),
        region: /cairns/i.test(location.pathname) ? 'cairns' : 'gc'
      })
    })
    .then(function(r){ if(!r.ok) throw new Error(r.status); return r.json(); })
    .then(function(d){ return (d.reply || _deflectMsg()).trim(); })
    .catch(function(){ return _deflectMsg(); });
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
    window.askAI(msg).then(function(reply){
      window.CHAT_HISTORY.push({ role: 'assistant', content: reply });
      var ti = document.getElementById('typing-indicator'); if(ti) ti.remove();
      _addMessage(reply, 'bot');
    });
  };

  window.sendQuick = function(text){
    var input = document.getElementById('chat-input');
    if (input) { input.value = text; window.sendChat(); }
  };
})();
