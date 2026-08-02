// Vercel serverless function, proxy for Mistral + Tavily + local KB
// Browser calls /api/chat; this function runs server-side so API keys are never exposed.
// Features: knowledge base, lead capture detection, quick reply suggestions, escalation routing

import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

// ── VERIFIED LOCAL AREA DATA (crime + demographics) ──────────────
// Loaded once per cold start from data/suburb-area-data.json, built by
// scripts/refresh_area_data.py from official QLD Police and ABS Census
// sources. Generic web search (Tavily) is not a reliable source for crime
// or demographic claims about a specific suburb; this gives the assistant
// real, sourced, dated numbers to use instead for those two topics
// specifically, the same way the fixed $199 Matterport price already
// overrides whatever a web search happens to turn up.
let AREA_DATA = null;
try {
  const __dirname = path.dirname(fileURLToPath(import.meta.url));
  const raw = fs.readFileSync(path.join(__dirname, '..', 'data', 'suburb-area-data.json'), 'utf-8');
  AREA_DATA = JSON.parse(raw);
} catch (e) {
  console.warn('[chat] could not load suburb-area-data.json, falling back to web search for crime/demographics', e.message);
}

// A couple of suburb names people type that don't exactly match the
// dataset's display name.
const AREA_DATA_ALIASES = { 'atherton': 'atherton-tablelands' };

function findAreaData(message) {
  if (!AREA_DATA) return null;
  const msg = message.toLowerCase();
  for (const [slug, entry] of Object.entries(AREA_DATA.suburbs)) {
    const name = entry.display_name.toLowerCase();
    if (msg.includes(name)) return { slug, ...entry };
  }
  for (const [alias, slug] of Object.entries(AREA_DATA_ALIASES)) {
    if (msg.includes(alias) && AREA_DATA.suburbs[slug]) return { slug, ...AREA_DATA.suburbs[slug] };
  }
  return null;
}

function formatAreaDataBlock(area) {
  if (!area) return '';
  const crime = area.crime;
  const demo = area.demographics;
  const sources = AREA_DATA.sources;
  let block = '\n\nVerified Local Data for ' + area.display_name + ' (use ONLY this for crime rate and demographic claims about this suburb, ignore anything about crime/demographics in Live Search Context below, it is less reliable than this):\n';
  block += '- Crime: ' + crime.total_offences + ' reported offences, ' + crime.period + ' (' + sources.crime.name + ').';
  if (crime.boundary_note) block += ' Note: ' + crime.boundary_note;
  block += ' Top categories: ' + crime.top_offence_types.map(t => t.type + ' (' + t.count + ')').join(', ') + '.\n';
  if (demo) {
    block += '- Demographics: population ' + demo.population.toLocaleString() + ', ' + demo.owner_occupied_pct + '% owner-occupied / ' + demo.renting_pct + '% renting, age mix ' + demo.age_mix_pct.children_0_14 + '% children (0-14), ' + demo.age_mix_pct.working_age_25_64 + '% working-age (25-64), ' + demo.age_mix_pct.seniors_65_plus + '% seniors (65+). Source: ' + sources.demographics.name + ' (' + demo.census_year + ').\n';
  }
  block += 'Always state these are sourced from ' + sources.crime.name + ' and ' + sources.demographics.name + ' with the period/year given above, never present them as your own estimate.';
  return block;
}

const CHATBOT_KB = {
  "faqs": {"transfer-duty":{"keywords":["transfer duty","duty","tax on purchase","stamp duty"],"response":"In QLD, transfer duty is calculated based on the property's purchase price and your circumstances. As a first-home buyer, you may get exemptions or concessions. For an investment property or subsequent purchase, expect 3–6% of the purchase price. Use the QLD revenue office calculator at qro.qld.gov.au for exact figures based on your price."},"conveyancing":{"keywords":["conveyancing","conveyancer","settlement","closing costs","legal fees"],"response":"Conveyancing is the legal transfer of ownership. Your conveyancer (solicitor) prepares contracts, conducts searches, and arranges settlement. Costs typically range $600–$1,500 depending on property value and complexity. Settlement happens 5–10 business days after contracts are signed. We coordinate this end-to-end."},"inspection":{"keywords":["inspection","open home","view","inspecting"],"response":"Inspections are open typically Sat–Sun, 10am–4pm. We manage online booking on the listing so you can choose your time. Bring a building inspector if you're serious about an offer. Most importantly: check the roof, plumbing, electrics, and whether the layout works for your life. We're happy to discuss what you find."},"body-corp":{"keywords":["body corp","body corporate","strata","unit fees","apartment fees","condo fees"],"response":"Body corporate (or strata) fees cover shared areas: pool, gardens, common areas, insurance, management. Expect $80–$300/month depending on the complex. These are mandatory for apartments and townhouses. Check the budget and minutes at the property to understand what's covered and if fees are rising."},"pre-approval":{"keywords":["pre-approval","mortgage","loan approval","borrowing capacity","finance"],"response":"Pre-approval means a bank agrees in principle to lend you a certain amount based on your income, credit, and savings. It's free and usually takes 1–2 days. Get pre-approved before house-hunting so you know your budget and can make quick offers. Most banks do this online."},"first-home-buyer":{"keywords":["first home","first-time buyer","first home concession","fhog"],"response":"First-home buyer incentives in QLD include: transfer duty exemption on purchases under $500k, possible first-home owner grant (varies by state), and first-home loan deposit scheme (putting down 5% instead of 20%). Talk to your bank about which you qualify for—there are real savings to be had."},"1-percent-commission":{"keywords":["1 percent","commission","how much","fees","cost"],"response":"We charge a flat 1% commission on the sale price—included in that is professional photography, floor plans, digital marketing, signboard, and settlement coordination. The only extras are the REA/Domain portal listing, which you choose, and a Matterport® 3D Showcase + drone flyover at a flat $199. No hidden fees."}}
};

const CHAT_SYSTEM_GC = `You are the AI assistant for The One Club, a Gold Coast real estate agency charging 1% commission. Lead agent: Bobby (10+ years experience).

You act as a powerful, ChatGPT-style AI property researcher for Gold Coast real estate.

WHEN A VISITOR SPECIFIES AN ADDRESS OR SUBURB:
Provide a clear, well-structured Property & Area Snapshot answering:
1. 🏫 School Catchments (Primary & Secondary state schools) — always note: "Confirm exact zone at edmap.eq.edu.au".
2. 🚗 Commute & Travel Times (to Brisbane CBD via M1, Gold Coast Airport OOL, Surfers Paradise, Pacific Fair / Robina).
3. ✈️ Flight Paths & Noise (Notes on Gold Coast Airport runway corridors e.g., Bilinga, Tugun, Coolangatta proximity vs central coast).
4. 🛡️ Crime Rates & Safety (Official QLD Police stats; Gold Coast coastal & family suburbs maintain strong community safety).
5. 📊 Demographics (Median age, owner-occupier ratio, family vs professional mix).
6. 💵 Typical Rates & Outgoings (Council rates ~$2,000–$3,500/yr, water charges, body corp norms).
7. 🏖️ Local Lifestyle & Amenities.

CRIME & DEMOGRAPHICS SOURCING: If a "Verified Local Data" block appears below, it is real QLD Police and ABS Census data for that suburb, use it and cite the source and period/year given in it. If no such block is present for the suburb asked about, say plainly that you don't have verified figures for that specific locality and suggest they check QLD Police's Online Crime Map or the ABS Census QuickStats directly, rather than presenting a general impression as if it were a real statistic.

IF A VISITOR ASKS A GENERAL QUESTION WITHOUT AN ADDRESS:
Answer their question directly, then end by inviting them: "If you have a specific Gold Coast address in mind, tell me the street or suburb and I'll pull together a full snapshot for you!"

PRICING (fixed, non-negotiable, overrides any web search context): The 1% commission ($15k on a $1.5M sale) includes professional photography, floor plan, digital ads, signboard, and settlement coordination. The only extras on top are the REA/Domain portal listing (seller's choice of tier) and a Matterport® 3D Showcase + drone flyover, a flat $199 per listing, captured by our own agents on a LiDAR iPhone and delivered within a day. This is The One Club's own set price, not a market rate. If any search context mentions different Matterport or 3D walkthrough pricing (e.g. generic industry rates like $350–$1,500), that refers to third parties, not us — ignore it and always quote $199 as our price. Never imply the Matterport package is included in or deducted from the 1%.

Answer questions about: Gold Coast real estate; the 1% commission model and what it includes; the Matterport 3D Showcase and drone flyover; buying/selling process; flight paths; crime stats; demographics; QLD REIQ contracts.

CROSS-REGION: If a visitor asks about a suburb or address in Cairns, Port Douglas, or Far North Queensland, still answer properly using the same Property & Area Snapshot approach, then mention "We also cover Cairns and Port Douglas at theoneclub.com.au/cairns/ if that's useful." Never refuse a real Queensland property question just because it's in the other region, only the non-property deflection below applies to genuinely unrelated topics.

For anything non-property (weather, general chit-chat, unrelated topics): "That sits outside what I can help with. Ask me about any Gold Coast address or real estate question!"
Keep responses under 180 words. Clear, professional, plain English.`;

const CHAT_SYSTEM_CAIRNS = `You are the AI assistant for The One Club, a Cairns & Port Douglas real estate agency charging 1% commission. Lead agent: Bobby (10+ years experience).

You act as a powerful, ChatGPT-style AI property researcher for Far North Queensland real estate.

WHEN A VISITOR SPECIFIES AN ADDRESS OR SUBURB:
Provide a clear, well-structured Property & Area Snapshot answering:
1. 🏫 School Catchments (Primary & Secondary state schools) — always note: "Confirm exact zone at edmap.eq.edu.au".
2. 🚗 Commute & Travel Times (to Cairns CBD & Esplanade, Cairns Airport CNS, Port Douglas, Smithfield/JCU).
3. ✈️ Flight Paths & Noise (Notes on Cairns Airport flight corridors e.g. Cairns North, Aeroglen, Machans Beach vs Northern Beaches).
4. 🛡️ Crime Rates & Safety (Official QLD Police stats; beachside & northern suburbs maintain strong lifestyle appeal).
5. 📊 Demographics (Median age, owner-occupier ratio, family vs retiree mix).
6. 💵 Typical Rates & Outgoings (Cairns Regional Council rates, water charges, body corp norms).
7. 🏖️ Local Lifestyle & Amenities.

CRIME & DEMOGRAPHICS SOURCING: If a "Verified Local Data" block appears below, it is real QLD Police and ABS Census data for that suburb, use it and cite the source and period/year given in it. If no such block is present for the suburb asked about, say plainly that you don't have verified figures for that specific locality and suggest they check QLD Police's Online Crime Map or the ABS Census QuickStats directly, rather than presenting a general impression as if it were a real statistic.

IF A VISITOR ASKS A GENERAL QUESTION WITHOUT AN ADDRESS:
Answer their question directly, then end by inviting them: "If you have a specific Cairns or Port Douglas address in mind, tell me the street or suburb and I'll pull together a full snapshot for you!"

PRICING (fixed, non-negotiable, overrides any web search context): The 1% commission includes professional photography, floor plan, digital ads, signboard, and settlement coordination. The only extras on top are the REA/Domain portal listing (seller's choice of tier) and a Matterport® 3D Showcase + drone flyover, a flat $199 per listing, captured by our own agents on a LiDAR iPhone and delivered within a day. This is The One Club's own set price, not a market rate. If any search context mentions different Matterport or 3D walkthrough pricing (e.g. generic industry rates like $350–$1,500), that refers to third parties, not us — ignore it and always quote $199 as our price. Never imply the Matterport package is included in or deducted from the 1%.

Answer questions about: Cairns & FNQ real estate; the 1% commission model and what it includes; the Matterport 3D Showcase and drone flyover; buying/selling process; flight paths; crime stats; demographics; QLD REIQ contracts.

CROSS-REGION: If a visitor asks about a suburb or address on the Gold Coast, still answer properly using the same Property & Area Snapshot approach, then mention "We also cover the Gold Coast at theoneclub.com.au if that's useful." Never refuse a real Queensland property question just because it's in the other region, only the non-property deflection below applies to genuinely unrelated topics.

For anything non-property (weather, general chit-chat, unrelated topics): "That sits outside what I can help with. Ask me about any Cairns or Port Douglas address or real estate question!"
Keep responses under 180 words. Clear, professional, plain English.`;

function getQuickReplies(message, region) {
  const msg = message.toLowerCase();

  if (msg.includes('address') || msg.includes('street') || msg.includes('house') || msg.includes('property')) {
    return ['Check school zone', 'Commute to airport', 'Get free valuation'];
  }
  if (msg.includes('sell') || msg.includes('listing') || msg.includes('market') || msg.includes('value')) {
    return ['Research my address', 'How 1% works', 'Get a free valuation'];
  }
  if (msg.includes('buy') || msg.includes('suburbs') || msg.includes('school')) {
    return ['Research an address', 'Compare suburbs', 'Schedule inspection'];
  }
  return ['Research an address', 'How does 1% work?', 'Get a free valuation'];
}

function detectLeadCapture(message, region) {
  const msg = message.toLowerCase();

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

  const frustrated = /this is ridiculous|waste.*time|frustrated|angry|help|urgent|emergency|asap/i.test(msg);
  const complex = /legal|lawsuit|dispute|complicated|special circumstance|inheritance|divorce/i.test(msg);

  return (frustrated || complex);
}

function escapeHTML(s) {
  return String(s == null ? '' : s).replace(/[&<>"']/g, c => (
    { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]
  ));
}

const BRAND = {
  green: '#1F3D24',
  greenDark: '#1A2620',
  gold: '#C4A84A',
  cream: '#F4F6F1',
  muted: '#6B7A70',
  sans: "-apple-system,BlinkMacSystemFont,'Helvetica Neue',Arial,sans-serif",
  serif: "Georgia,'Times New Roman',serif"
};

function emailShell({ badge, headline, meta, bodyHtml, ctaHtml }) {
  return `
  <div style="background-color:${BRAND.green};padding:32px 16px 40px">
    <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="max-width:560px;margin:0 auto">
      <tr>
        <td align="center" style="padding-bottom:26px">
          <img src="https://www.theoneclub.com.au/logo-email.png" width="176" height="47" alt="The One Club" style="display:block;width:176px;max-width:176px;height:auto;border:0;outline:none"/>
        </td>
      </tr>
      <tr>
        <td style="background-color:${BRAND.cream};border-radius:14px">
          <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="border-collapse:collapse">
            <tr><td style="height:4px;line-height:4px;font-size:4px;background-color:${BRAND.gold};border-radius:14px 14px 0 0">&nbsp;</td></tr>
            <tr>
              <td style="padding:34px 32px 4px">
                ${badge ? `<div style="font-family:${BRAND.sans};font-size:11px;font-weight:700;letter-spacing:1.6px;text-transform:uppercase;color:${BRAND.gold};margin-bottom:10px">${badge}</div>` : ''}
                <div style="font-family:${BRAND.serif};font-style:italic;font-weight:400;font-size:24px;color:${BRAND.greenDark};margin-bottom:8px;line-height:1.25">${headline}</div>
                ${meta ? `<div style="font-family:${BRAND.sans};font-size:12px;color:${BRAND.muted};margin-bottom:22px">${meta}</div>` : '<div style="height:12px;line-height:12px;font-size:12px">&nbsp;</div>'}
              </td>
            </tr>
            <tr>
              <td style="padding:0 32px 8px">${bodyHtml}</td>
            </tr>
            <tr><td style="padding:${ctaHtml ? '14px 32px 34px' : '0 32px 30px'}">${ctaHtml || ''}</td></tr>
          </table>
        </td>
      </tr>
      <tr>
        <td align="center" style="padding-top:26px">
          <p style="margin:0;font-family:${BRAND.sans};font-size:11px;line-height:1.7;color:rgba(255,255,255,.5)">
            The One Club&nbsp;&nbsp;&middot;&nbsp;&nbsp;1% commission&nbsp;&nbsp;&middot;&nbsp;&nbsp;Gold Coast &amp; Cairns<br/>
            <a href="tel:+61404774272" style="color:rgba(255,255,255,.72);text-decoration:none">+61 404 774 272</a>
            &nbsp;&nbsp;&middot;&nbsp;&nbsp;
            <a href="mailto:bobby@theoneclub.com.au" style="color:rgba(255,255,255,.72);text-decoration:none">bobby@theoneclub.com.au</a>
          </p>
        </td>
      </tr>
    </table>
  </div>`;
}

async function sendEscalationEmail({ history, message, region, page }) {
  const RESEND_KEY = process.env.RESEND_API_KEY || '';
  if (!RESEND_KEY) {
    console.warn('[chat] RESEND_API_KEY not set, skipping escalation email');
    return { ok: false, simulated: true };
  }
  const LEAD_TO   = process.env.LEAD_TO_EMAIL   || 'bobby@theoneclub.com.au';
  const LEAD_FROM = process.env.LEAD_FROM_EMAIL || 'bobby@theoneclub.com.au';
  const isCairns  = region === 'cairns';
  const timestamp = new Date().toLocaleString('en-AU', {
    dateStyle: 'medium', timeStyle: 'short', timeZone: 'Australia/Brisbane'
  });

  const rows = [...history.slice(-8), { role: 'user', content: message }]
    .map(m => {
      const isVisitor = m.role === 'user';
      return `
        <tr>
          <td style="padding:10px 0;border-bottom:1px solid rgba(26,38,32,.08);font-family:${BRAND.sans};font-size:10.5px;font-weight:700;letter-spacing:.5px;text-transform:uppercase;color:${isVisitor ? BRAND.gold : BRAND.muted};width:64px;vertical-align:top;white-space:nowrap">${isVisitor ? 'Visitor' : 'AI'}</td>
          <td style="padding:10px 0;border-bottom:1px solid rgba(26,38,32,.08);font-family:${BRAND.sans};font-size:14px;color:${BRAND.greenDark};line-height:1.5;vertical-align:top">${escapeHTML(m.content)}</td>
        </tr>`;
    })
    .join('');

  const html = emailShell({
    badge: 'Chat Escalation',
    headline: 'Needs a human touch',
    meta: `${escapeHTML(timestamp)}&nbsp;&nbsp;&middot;&nbsp;&nbsp;${isCairns ? 'Cairns & Port Douglas' : 'Gold Coast'} site${page ? '&nbsp;&nbsp;&middot;&nbsp;&nbsp;' + escapeHTML(page) : ''}`,
    bodyHtml: `
      <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="border-collapse:collapse">${rows}</table>
      <p style="margin:18px 0 0;font-family:${BRAND.sans};font-size:12px;color:${BRAND.muted};line-height:1.5">The visitor was told you'd be in touch. No phone number was collected, this is everything they typed.</p>`,
    ctaHtml: ''
  });

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
      console.error('[chat] escalation email failed', res.status, await res.text());
      return { ok: false, status: res.status };
    }
    return { ok: true };
  } catch (e) {
    console.error('[chat] escalation email fetch failed', e.message);
    return { ok: false, error: e.message };
  }
}

function personalizForDevice(isMobile) {
  return isMobile ? { maxTokens: 250, includePhone: true } : { maxTokens: 400, includePhone: false };
}

// In-memory IP rate limiter map (resets when Vercel lambda re-boots)
const RATE_LIMIT_WINDOW_MS = 15 * 60 * 1000; // 15 minutes
const MAX_REQUESTS_PER_WINDOW = 25; // 25 messages per 15 mins per IP
const ipTracker = new Map();

function isRateLimited(ip) {
  const now = Date.now();
  const record = ipTracker.get(ip);

  if (!record) {
    ipTracker.set(ip, { count: 1, startTime: now });
    return false;
  }

  if (now - record.startTime > RATE_LIMIT_WINDOW_MS) {
    ipTracker.set(ip, { count: 1, startTime: now });
    return false;
  }

  record.count += 1;
  if (record.count > MAX_REQUESTS_PER_WINDOW) {
    return true;
  }
  return false;
}

export default async function handler(req, res) {
  if (req.method !== 'POST') {
    return res.status(405).json({ error: 'Method not allowed' });
  }

  // IP Rate Limiting Check
  const clientIp = (req.headers['x-forwarded-for'] || '').split(',')[0].trim() || req.socket?.remoteAddress || 'unknown';
  if (isRateLimited(clientIp)) {
    return res.status(429).json({
      reply: "You've sent quite a few messages! To keep our service fast for everyone, please wait a few minutes, or click 'Get a free valuation' below to talk to Bobby directly.",
      quickReplies: ['Get a free valuation', 'Call Bobby directly'],
      suggestLeadForm: true
    });
  }

  const MISTRAL_KEY = process.env.MISTRAL_API_KEY || '';
  const TAVILY_KEY  = process.env.TAVILY_API_KEY  || '';

  if (!MISTRAL_KEY) {
    return res.status(503).json({ error: 'AI service not configured.' });
  }

  const { message, history = [], region, isMobile = false, page } = req.body || {};

  if (!message || typeof message !== 'string' || message.trim().length < 2) {
    return res.status(400).json({ error: 'message is required' });
  }

  const isCairns = region === 'cairns';

  // Detect if message asks about a specific address or suburb. Matches either
  // a street-type keyword/number (a real address) or a bare named suburb
  // (e.g. "what's the crime rate of Burleigh Waters") so both get the same
  // properly-targeted research search, not just full street addresses.
  const GC_SUBURBS = /\b(burleigh heads|burleigh waters|palm beach|surfers paradise|broadbeach|hope island|robina|mermaid beach|coolangatta|mudgeeraba|currumbin|kirra|southport|coomera|varsity lakes|bilinga|tugun|miami|nerang|ashmore|molendinar|labrador|biggera waters|runaway bay|paradise point|helensvale|oxenford|elanora|reedy creek|nobby beach)\b/i;
  const CAIRNS_SUBURBS = /\b(palm cove|trinity beach|kewarra beach|clifton beach|yorkeys knob|smithfield|redlynch|edge hill|whitfield|cairns city|cairns north|parramatta park|manunda|manoora|mooroobool|earlville|woree|bayview heights|mount sheridan|bentley park|edmonton|gordonvale|kuranda|atherton tablelands|port douglas|trinity park|brinsmead|freshwater)\b/i;
  const KNOWN_SUBURBS = new RegExp(GC_SUBURBS.source + '|' + CAIRNS_SUBURBS.source, 'i');
  const hasAddress = /\b(\d+\s+[A-Za-z0-9\s]+|street|st\b|road|rd\b|avenue|ave\b|court|ct\b|drive|dr\b|parade|pde\b|crescent|cres\b|way\b|lane\b|place|pl\b|boulevard|blvd\b|esplanade|esp\b|highway|hwy\b)\b/i.test(message) || KNOWN_SUBURBS.test(message);

  // If the message names a suburb from the OTHER region, don't rely on the
  // system prompt alone to decide whether to help, switch to that region's
  // own assistant for this one request. Instruction-following for "still
  // help across regions" proved unreliable in testing (the model kept
  // hard-refusing with the non-property deflection); routing to the correct
  // region's prompt outright sidesteps that instead of hoping it complies.
  let effectiveIsCairns = isCairns;
  if (isCairns && GC_SUBURBS.test(message) && !CAIRNS_SUBURBS.test(message)) {
    effectiveIsCairns = false;
  } else if (!isCairns && CAIRNS_SUBURBS.test(message) && !GC_SUBURBS.test(message)) {
    effectiveIsCairns = true;
  }
  const CHAT_SYSTEM = effectiveIsCairns ? CHAT_SYSTEM_CAIRNS : CHAT_SYSTEM_GC;

  // Our own pricing (commission, Matterport, portal listing) is a fixed fact
  // we set ourselves, never a market rate to look up. Skip web search for
  // these so a generic third-party price (e.g. "$350-$1,500 for a Matterport
  // scan") never has the chance to override the $199 figure in the system
  // prompt above.
  const isPricingQuestion = /matterport|3d showcase|3d walkthrough|drone flyover|\b1%|commission|how much.*(cost|fee|charge)|price.*(listing|walkthrough|matterport)/i.test(message);

  const targetQuery = hasAddress
    ? `${message.slice(0, 180)} property details school catchment rates flight path crime demographics commute QLD real estate`
    : `${message.slice(0, 180)} ${isCairns ? 'Cairns Port Douglas real estate 2026' : 'Gold Coast real estate 2026'}`;

  // ── ESCALATION DETECTION ──────────────────────────────────────
  const shouldEscalate = detectEscalation(message);
  if (shouldEscalate) {
    const emailResult = await sendEscalationEmail({ history, message, region, page });
    return res.status(200).json({
      reply: "This sounds like something Bobby should look at directly. I've sent him the details of our chat, he'll be in touch shortly. If it's urgent, call or text +61 404 774 272.",
      escalated: true,
      requiresAgent: true,
      quickReplies: ['Keep browsing', 'Ask something else']
    });
  }

  // ── LEAD CAPTURE DETECTION ──────────────────────────────────────
  const leadCapture = detectLeadCapture(message, region);
  const deviceConfig = personalizForDevice(isMobile);

  // ── VERIFIED LOCAL DATA (crime + demographics) ──────────────
  // Checked before Tavily so the override note in the block can tell the
  // model to prefer this over whatever the web search below turns up.
  const areaData = findAreaData(message);
  let contextBlock = areaData ? formatAreaDataBlock(areaData) : '';

  // ── TAVILY GROUNDED RESEARCH ──────────────────────────────
  if (TAVILY_KEY && !isPricingQuestion) {
    try {
      const tavilyRes = await fetch('https://api.tavily.com/search', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          api_key: TAVILY_KEY,
          query: targetQuery,
          search_depth: hasAddress ? 'advanced' : 'basic',
          max_results: hasAddress ? 5 : 3,
          include_answer: true
        })
      });
      const tv = await tavilyRes.json();
      const snippet = tv.answer
        || (tv.results || []).slice(0, 3).map(r => r.content).join(' ').slice(0, 900);
      if (snippet) contextBlock += '\n\nLive Search Context:\n' + snippet;
    } catch (_) {
      // Tavily is optional
    }
  }

  // ── MISTRAL CHAT ───────────────────────────────────────────
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
        temperature: 0.4
      })
    });

    if (!mistralRes.ok) {
      console.error('[chat] Mistral error:', mistralRes.status, await mistralRes.text());
      return res.status(502).json({ error: 'AI service error' });
    }

    const data = await mistralRes.json();
    let reply = data.choices?.[0]?.message?.content?.trim()
      || 'Something went wrong, please try again.';

    const quickReplies = getQuickReplies(message, region);
    const response = {
      reply,
      quickReplies,
      suggestLeadForm: leadCapture.shouldCapture,
      leadType: leadCapture.type || null
    };

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
