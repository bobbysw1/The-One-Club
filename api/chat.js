// Vercel serverless function, proxy for Mistral + Tavily + local KB
// Browser calls /api/chat; this function runs server-side so API keys are never exposed.
// Features: knowledge base, lead capture detection, quick reply suggestions, escalation routing

const CHATBOT_KB = {
  "faqs": {"transfer-duty":{"keywords":["transfer duty","duty","tax on purchase","stamp duty"],"response":"In QLD, transfer duty is calculated based on the property's purchase price and your circumstances. As a first-home buyer, you may get exemptions or concessions. For an investment property or subsequent purchase, expect 3–6% of the purchase price. Use the QLD revenue office calculator at qro.qld.gov.au for exact figures based on your price."},"conveyancing":{"keywords":["conveyancing","conveyancer","settlement","closing costs","legal fees"],"response":"Conveyancing is the legal transfer of ownership. Your conveyancer (solicitor) prepares contracts, conducts searches, and arranges settlement. Costs typically range $600–$1,500 depending on property value and complexity. Settlement happens 5–10 business days after contracts are signed. We coordinate this end-to-end."},"inspection":{"keywords":["inspection","open home","view","inspecting"],"response":"Inspections are open typically Sat–Sun, 10am–4pm. We manage online booking on the listing so you can choose your time. Bring a building inspector if you're serious about an offer. Most importantly: check the roof, plumbing, electrics, and whether the layout works for your life. We're happy to discuss what you find."},"body-corp":{"keywords":["body corp","body corporate","strata","unit fees","apartment fees","condo fees"],"response":"Body corporate (or strata) fees cover shared areas: pool, gardens, common areas, insurance, management. Expect $80–$300/month depending on the complex. These are mandatory for apartments and townhouses. Check the budget and minutes at the property to understand what's covered and if fees are rising."},"pre-approval":{"keywords":["pre-approval","mortgage","loan approval","borrowing capacity","finance"],"response":"Pre-approval means a bank agrees in principle to lend you a certain amount based on your income, credit, and savings. It's free and usually takes 1–2 days. Get pre-approved before house-hunting so you know your budget and can make quick offers. Most banks do this online."},"first-home-buyer":{"keywords":["first home","first-time buyer","first home concession","fhog"],"response":"First-home buyer incentives in QLD include: transfer duty exemption on purchases under $500k, possible first-home owner grant (varies by state), and first-home loan deposit scheme (putting down 5% instead of 20%). Talk to your bank about which you qualify for—there are real savings to be had."},"1-percent-commission":{"keywords":["1 percent","commission","how much","fees","cost"],"response":"We charge a flat 1% commission on the sale price—included in that is professional photography, 3D walkthrough, floor plans, digital marketing, signboard, and settlement coordination. The only extra is the REA/Domain portal listing, which you choose. No hidden fees."}}
};

const CHAT_SYSTEM_GC = `You are the AI assistant for The One Club, a Gold Coast real estate agency charging 1% commission. The lead agent is Bobby, 10+ years experience across London and the Gold Coast. Everything is included in the 1%: professional AI-enhanced photography, floor plans, interactive 3D walkthrough (captured in-house using PlayCanvas SuperSplat technology), digital marketing on Meta and Google, signboard, and settlement coordination. The only extra is the portal listing on REA and Domain (seller chooses Standard, Feature or Premiere level).

Answer questions about: Gold Coast real estate; buying or selling property; the 1% commission model and what is included; photography, 3D walkthroughs, floor plans; Gold Coast suburbs including Burleigh Heads, Palm Beach, Surfers Paradise, Broadbeach, Hope Island, Robina, Mermaid Beach, Coolangatta, Mudgeeraba, Currumbin, Kirra, Southport, Coomera, Varsity Lakes, Bilinga, Tugun, Miami; QLD school catchment zones; body corporate fees; settlement process; mortgages at a high level.

For school catchment questions: give your best answer for the suburb or address, then always end with, Confirm the exact zone at edmap.eq.edu.au as boundaries do change.

For anything unrelated to property: reply with exactly, That sits outside what I can help with. For any Gold Coast property question I'm here, otherwise the Free Valuation form at the bottom of the page is the fastest way to reach Bobby directly.

Keep all answers under 150 words. Plain English. Never invent specific listing addresses, prices, or sale results.`;

const CHAT_SYSTEM_CAIRNS = `You are the AI assistant for The One Club, a Cairns & Port Douglas real estate agency charging 1% commission. The lead agent is Bobby, 10+ years experience across London, the Gold Coast and now Far North Queensland. Everything is included in the 1%: professional AI-enhanced photography, floor plans, interactive 3D walkthrough (captured in-house using PlayCanvas SuperSplat technology), digital marketing on Meta and Google, signboard, and settlement coordination. The only extra is the portal listing on REA and Domain (seller chooses Standard, Feature or Premiere level).

Answer questions about: Cairns and Port Douglas real estate; buying or selling property; the 1% commission model and what is included; photography, 3D walkthroughs, floor plans; Cairns and Port Douglas suburbs including Palm Cove, Trinity Beach, Kewarra Beach, Clifton Beach, Yorkeys Knob, Smithfield, Redlynch, Edge Hill, Whitfield, Cairns City, Cairns North, Parramatta Park, Manunda, Manoora, Mooroobool, Earlville, Woree, Bayview Heights, Mount Sheridan, Bentley Park, Edmonton, Gordonvale, Kuranda, the Atherton Tablelands, and Port Douglas; QLD school catchment zones; body corporate fees; settlement process; mortgages at a high level; the wet and dry season selling calendar in Far North Queensland.

For school catchment questions: give your best answer for the suburb or address, then always end with, Confirm the exact zone at edmap.eq.edu.au as boundaries do change.

For anything unrelated to property: reply with exactly, That sits outside what I can help with. For any Cairns or Port Douglas property question I'm here, otherwise the Free Valuation form at the bottom of the page is the fastest way to reach Bobby directly.

Keep all answers under 150 words. Plain English. Never invent specific listing addresses, prices, or sale results.`;

function getQuickReplies(message, region) {
  const msg = message.toLowerCase();
  const isCairns = region === 'cairns';

  // Suggest next steps based on conversation
  if (msg.includes('sell') || msg.includes('listing') || msg.includes('market') || msg.includes('value')) {
    return ['Get a free valuation', 'How does 1% work?', 'See current listings'];
  }
  if (msg.includes('buy') || msg.includes('purchase') || msg.includes('suburbs') || msg.includes('school')) {
    return ['Browse listings', 'Compare suburbs', 'Schedule inspection'];
  }
  if (msg.includes('suburb') || msg.includes('palm') || msg.includes('burleigh') || msg.includes('surfers')) {
    return ['Compare other suburbs', 'School zones?', 'Browse listings in this area'];
  }
  if (msg.includes('commission') || msg.includes('cost') || msg.includes('fee')) {
    return ["What's included?", 'See listings', 'Get a valuation'];
  }
  // Default suggestions
  return ['Get a free valuation', 'Browse listings', 'Ask another question'];
}

function detectLeadCapture(message, region) {
  const msg = message.toLowerCase();

  // Trigger lead form if they express buying/selling intent
  const buyingIntent = /want to buy|looking to purchase|interested in|find.*home|price.*range/i.test(msg);
  const sellingIntent = /want to sell|sell.*house|listing|value.*home|how much.*worth/i.test(msg);
  const agentRequest = /talk to.*agent|speak.*bobby|contact.*agent|call.*agent/i.test(msg);

  if (buyingIntent || sellingIntent || agentRequest) {
    return {
      shouldCapture: true,
      type: sellingIntent ? 'seller' : buyingIntent ? 'buyer' : 'inquiry'
    };
  }
  return { shouldCapture: false };
}

function detectEscalation(message) {
  const msg = message.toLowerCase();

  // Detect frustration or complexity requiring agent escalation
  const frustrated = /this is ridiculous|waste.*time|frustrated|angry|help|urgent|emergency|asap/i.test(msg);
  const complex = /legal|lawsuit|dispute|complicated|special circumstance|inheritance|divorce/i.test(msg);

  if (frustrated || complex) {
    return true;
  }
  return false;
}

function escapeHTML(s) {
  return String(s == null ? '' : s).replace(/[&<>"']/g, c => (
    { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]
  ));
}

// Emails the full chat transcript to Bobby when the bot escalates, so a
// human sees the exact conversation instead of the visitor having to
// re-explain themselves over the phone. Never blocks or throws — a failed
// send just means no email, the chat reply still goes out either way.
async function sendEscalationEmail({ history, message, region, page }) {
  const RESEND_KEY = process.env.RESEND_API_KEY || '';
  if (!RESEND_KEY) {
    console.warn('[chat] RESEND_API_KEY not set, skipping escalation email');
    return { ok: false, simulated: true };
  }
  const LEAD_TO   = process.env.LEAD_TO_EMAIL   || 'bobby@theoneclub.com.au';
  const LEAD_FROM = process.env.LEAD_FROM_EMAIL || 'leads@theoneclub.com.au';
  const isCairns  = region === 'cairns';

  const rows = [...history.slice(-8), { role: 'user', content: message }]
    .map(m => {
      const who = m.role === 'user' ? 'Visitor' : 'AI';
      return `<tr><td style="padding:6px 12px 6px 0;color:#666;font-size:12px;white-space:nowrap;vertical-align:top">${who}</td><td style="padding:6px 0;font-size:14px">${escapeHTML(m.content)}</td></tr>`;
    })
    .join('');

  const html = `
    <div style="font-family:-apple-system,BlinkMacSystemFont,sans-serif;max-width:600px">
      <h2 style="margin:0 0 6px;font-size:18px">Chat escalation, needs a human</h2>
      <p style="margin:0 0 16px;color:#666;font-size:13px">${new Date().toISOString()} · ${isCairns ? 'Cairns & Port Douglas' : 'Gold Coast'} site${page ? ' · ' + escapeHTML(page) : ''}</p>
      <table cellpadding="0" cellspacing="0" style="border-collapse:collapse;width:100%">${rows}</table>
      <p style="margin-top:20px;color:#666;font-size:12px">The visitor was told you'd be in touch, no phone number was collected, this is everything they typed.</p>
    </div>`;

  try {
    const res = await fetch('https://api.resend.com/emails', {
      method: 'POST',
      headers: { 'Authorization': `Bearer ${RESEND_KEY}`, 'Content-Type': 'application/json' },
      body: JSON.stringify({
        from: LEAD_FROM,
        to: [LEAD_TO],
        subject: `Chat escalation — ${isCairns ? 'Cairns' : 'Gold Coast'} visitor needs you`,
        html
      })
    });
    if (!res.ok) {
      const errBody = await res.text();
      console.error('[chat] escalation email failed', res.status, errBody);
      return { ok: false, status: res.status, _debug: errBody };
    }
    return { ok: true };
  } catch (e) {
    console.error('[chat] escalation email fetch failed', e.message);
    return { ok: false, error: e.message };
  }
}

function personalizForDevice(isMobile) {
  // Mobile users get shorter responses, call-to-action buttons
  return isMobile ? { maxTokens: 200, includePhone: true } : { maxTokens: 320, includePhone: false };
}

export default async function handler(req, res) {
  if (req.method !== 'POST') {
    return res.status(405).json({ error: 'Method not allowed' });
  }

  const MISTRAL_KEY = process.env.MISTRAL_API_KEY || '';
  const TAVILY_KEY  = process.env.TAVILY_API_KEY  || '';

  if (!MISTRAL_KEY) {
    return res.status(503).json({ error: 'AI service not configured. Set MISTRAL_API_KEY in Vercel env vars.' });
  }

  const { message, history = [], region, isMobile = false, page } = req.body || {};

  if (!message || typeof message !== 'string' || message.trim().length < 2) {
    return res.status(400).json({ error: 'message is required' });
  }

  const isCairns = region === 'cairns';
  const CHAT_SYSTEM = isCairns ? CHAT_SYSTEM_CAIRNS : CHAT_SYSTEM_GC;
  const regionQuery = isCairns ? ' Cairns Port Douglas real estate 2026' : ' Gold Coast real estate 2026';

  // ── ESCALATION DETECTION ──────────────────────────────────────
  const shouldEscalate = detectEscalation(message);
  if (shouldEscalate) {
    const emailResult = await sendEscalationEmail({ history, message, region, page });
    return res.status(200).json({
      reply: emailResult.ok
        ? "This sounds like something Bobby should look at directly. I've sent him the details of our chat, he'll be in touch shortly. If it's urgent, call or text +61 404 774 272."
        : "This sounds like something Bobby should look at directly. The fastest way to reach him is to call or text +61 404 774 272, or leave your details on the Free Valuation form and he'll follow up.",
      escalated: true,
      requiresAgent: true,
      quickReplies: ['Keep browsing', 'Ask something else'],
      _debug: emailResult
    });
  }

  // ── LEAD CAPTURE DETECTION ──────────────────────────────────────
  const leadCapture = detectLeadCapture(message, region);
  const deviceConfig = personalizForDevice(isMobile);

  // ── TAVILY, optional web grounding ──────────────────────
  let contextBlock = '';
  if (TAVILY_KEY) {
    try {
      const tavilyRes = await fetch('https://api.tavily.com/search', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          api_key: TAVILY_KEY,
          query: message.slice(0, 200) + regionQuery,
          search_depth: 'basic',
          max_results: 3,
          include_answer: true
        })
      });
      const tv = await tavilyRes.json();
      const snippet = tv.answer
        || (tv.results || []).slice(0, 2).map(r => r.content).join(' ').slice(0, 600);
      if (snippet) contextBlock = '\n\nCurrent context from web search:\n' + snippet;
    } catch (_) {
      // Tavily is optional, fail silently
    }
  }

  // ── MISTRAL ───────────────────────────────────────────────
  const messages = [
    { role: 'system', content: CHAT_SYSTEM + contextBlock },
    ...history.slice(-8).map(h => ({ role: h.role, content: String(h.content).slice(0, 500) })),
    { role: 'user', content: message.slice(0, 500) }
  ];

  try {
    const mistralRes = await fetch('https://api.mistral.ai/v1/chat/completions', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${MISTRAL_KEY}`
      },
      body: JSON.stringify({
        model: 'mistral-small-latest',
        messages,
        max_tokens: deviceConfig.maxTokens,
        temperature: 0.5
      })
    });

    if (!mistralRes.ok) {
      const err = await mistralRes.text();
      console.error('[chat] Mistral error:', mistralRes.status, err);
      return res.status(502).json({ error: 'AI service error' });
    }

    const data = await mistralRes.json();
    let reply = data.choices?.[0]?.message?.content?.trim()
      || 'Something went wrong, please try again.';

    // ── BUILD RESPONSE ──────────────────────────────────────────────
    const quickReplies = getQuickReplies(message, region);
    const response = {
      reply,
      quickReplies,
      suggestLeadForm: leadCapture.shouldCapture,
      leadType: leadCapture.type || null
    };

    // Add phone CTA for mobile users
    if (isMobile && deviceConfig.includePhone) {
      response.phoneCta = 'Call Bobby: +61 404 774 272';
    }

    // Analytics event
    console.log(`[chat] ${isCairns ? 'cairns' : 'gc'} | ${leadCapture.shouldCapture ? 'LEAD' : 'info'} | msg_len: ${message.length}`);

    return res.status(200).json(response);
  } catch (e) {
    console.error('[chat] error', e);
    return res.status(500).json({ error: 'Server error' });
  }
}
