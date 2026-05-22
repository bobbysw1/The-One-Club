// Vercel serverless function — proxy for Mistral + Tavily
// Browser calls /api/chat; this function runs server-side so API keys are never exposed.

const CHAT_SYSTEM = `You are the AI assistant for The One Club, a Gold Coast real estate agency charging 1% commission. The lead agent is Bobby — 10+ years experience across London and the Gold Coast. Everything is included in the 1%: professional AI-enhanced photography, floor plans, interactive 3D walkthrough (captured in-house using PlayCanvas SuperSplat technology), digital marketing on Meta and Google, signboard, and settlement coordination. The only extra is the portal listing on REA and Domain (seller chooses Standard, Feature or Premiere level).

Answer questions about: Gold Coast real estate; buying or selling property; the 1% commission model and what is included; photography, 3D walkthroughs, floor plans; Gold Coast suburbs including Burleigh Heads, Palm Beach, Surfers Paradise, Broadbeach, Hope Island, Robina, Mermaid Beach, Coolangatta, Mudgeeraba, Currumbin, Kirra, Southport, Coomera, Varsity Lakes, Bilinga, Tugun, Miami; QLD school catchment zones; body corporate fees; settlement process; mortgages at a high level.

For school catchment questions: give your best answer for the suburb or address, then always end with — Confirm the exact zone at edmap.eq.edu.au as boundaries do change.

For anything unrelated to property: reply with exactly — That sits outside what I can help with. For any Gold Coast property question I'm here — otherwise the Free Valuation form at the bottom of the page is the fastest way to reach Bobby directly.

Keep all answers under 150 words. Plain English. Never invent specific listing addresses, prices, or sale results.`;

export default async function handler(req, res) {
  // Only accept POST
  if (req.method !== 'POST') {
    return res.status(405).json({ error: 'Method not allowed' });
  }

  const MISTRAL_KEY = process.env.MISTRAL_API_KEY;
  const TAVILY_KEY  = process.env.TAVILY_API_KEY;

  if (!MISTRAL_KEY) {
    return res.status(503).json({ error: 'AI not configured' });
  }

  const { message, history = [] } = req.body || {};

  if (!message || typeof message !== 'string' || message.trim().length < 2) {
    return res.status(400).json({ error: 'message is required' });
  }

  // ── TAVILY — optional web grounding ──────────────────────
  let contextBlock = '';
  if (TAVILY_KEY) {
    try {
      const tavilyRes = await fetch('https://api.tavily.com/search', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          api_key: TAVILY_KEY,
          query: message.slice(0, 200) + ' Gold Coast real estate 2026',
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
      // Tavily is optional — fail silently
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
        max_tokens: 320,
        temperature: 0.5
      })
    });

    if (!mistralRes.ok) {
      const err = await mistralRes.text();
      console.error('[chat] Mistral error:', mistralRes.status, err);
      return res.status(502).json({ error: 'AI service error' });
    }

    const data = await mistralRes.json();
    const reply = data.choices?.[0]?.message?.content?.trim()
      || 'Something went wrong — please try again.';

    return res.status(200).json({ reply });
  } catch (e) {
    console.error('[chat] error', e);
    return res.status(500).json({ error: 'Server error' });
  }
}
