// Vercel serverless function — lead capture.
// Browser posts here from assets/lead-form.js. Two independent effects on
// a valid submission: (1) email Bobby + auto-reply the customer via Resend,
// (2) append a durable record to backend/data/leads.json via the GitHub
// Contents API, so a lead is never lost even if email isn't configured yet
// or a send fails. Neither effect blocks the other.
//
// Required env vars (Vercel → Project → Settings → Environment Variables):
//   RESEND_API_KEY   — email sending (leads still get recorded without it)
//   GITHUB_TOKEN      — same fine-grained PAT used by api/admin.js
//   LEAD_TO_EMAIL     — optional, defaults to bobby@theoneclub.com.au
//   LEAD_FROM_EMAIL   — optional, defaults to leads@theoneclub.com.au

const RESEND_KEY  = process.env.RESEND_API_KEY || '';
const LEAD_TO     = process.env.LEAD_TO_EMAIL   || 'bobby@theoneclub.com.au';
const LEAD_FROM    = process.env.LEAD_FROM_EMAIL || 'leads@theoneclub.com.au';
const GITHUB_TOKEN = process.env.GITHUB_TOKEN    || '';

const GITHUB_OWNER  = 'bobbysw1';
const GITHUB_REPO   = 'The-One-Club';
const GITHUB_BRANCH = 'main';
const LEADS_PATH    = 'backend/data/leads.json';

const LEAD_REQUIRED = {
  valuation:       ['firstName', 'lastName', 'email', 'phone', 'address'],
  landlord:        ['firstName', 'lastName', 'email', 'phone', 'address'],
  tenant:          ['firstName', 'lastName', 'email', 'phone'],
  buyer:           ['firstName', 'lastName', 'email', 'phone'],
  'auction-buyer': ['firstName', 'lastName', 'email', 'phone'],
  'agent-bobby':   ['firstName', 'lastName', 'email']
};

const LEAD_LABEL = {
  valuation:       'Free Valuation',
  landlord:        'Landlord Register',
  tenant:          'Tenant Register',
  buyer:           'Buyer Interest',
  'auction-buyer': 'Auction Buyer Interest',
  'agent-bobby':   'Agent Enquiry'
};

function escapeHTML(s) {
  return String(s == null ? '' : s).replace(/[&<>"']/g, c => (
    { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]
  ));
}

async function sendEmail({ to, from, subject, html, replyTo }) {
  if (!RESEND_KEY) {
    console.warn('[lead] RESEND_API_KEY not set, skipping email:', subject);
    return { ok: false, simulated: true };
  }
  const payload = { from: from || LEAD_FROM, to: Array.isArray(to) ? to : [to || LEAD_TO], subject, html };
  if (replyTo) payload.reply_to = replyTo;
  try {
    const res = await fetch('https://api.resend.com/emails', {
      method: 'POST',
      headers: { 'Authorization': `Bearer ${RESEND_KEY}`, 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    if (!res.ok) {
      console.error('[lead] resend error', res.status, await res.text());
      return { ok: false, status: res.status };
    }
    return { ok: true };
  } catch (e) {
    console.error('[lead] email fetch failed', e.message);
    return { ok: false, error: e.message };
  }
}

async function appendLeadToGitHub(lead) {
  if (!GITHUB_TOKEN) {
    console.warn('[lead] GITHUB_TOKEN not set, skipping durable record for', lead.id);
    return { ok: false, simulated: true };
  }
  const headers = {
    'Authorization': `Bearer ${GITHUB_TOKEN}`,
    'Accept': 'application/vnd.github+json',
    'X-GitHub-Api-Version': '2022-11-28',
    'User-Agent': 'theoneclub-lead'
  };
  const url = `https://api.github.com/repos/${GITHUB_OWNER}/${GITHUB_REPO}/contents/${LEADS_PATH}?ref=${GITHUB_BRANCH}`;
  try {
    let leads = [];
    let sha = null;
    const getRes = await fetch(url, { headers });
    if (getRes.ok) {
      const j = await getRes.json();
      sha = j.sha;
      leads = JSON.parse(Buffer.from(j.content, 'base64').toString('utf8'));
      if (!Array.isArray(leads)) leads = [];
    } else if (getRes.status !== 404) {
      throw new Error(`GitHub GET ${LEADS_PATH} → ${getRes.status}`);
    }
    leads.push(lead);
    const putRes = await fetch(`https://api.github.com/repos/${GITHUB_OWNER}/${GITHUB_REPO}/contents/${LEADS_PATH}`, {
      method: 'PUT',
      headers: { ...headers, 'Content-Type': 'application/json' },
      body: JSON.stringify({
        message: `lead: ${lead.source} — ${lead.fields.firstName || ''} ${lead.fields.lastName || ''}`.trim(),
        content: Buffer.from(JSON.stringify(leads, null, 2), 'utf8').toString('base64'),
        branch: GITHUB_BRANCH,
        ...(sha ? { sha } : {})
      })
    });
    if (!putRes.ok) throw new Error(`GitHub PUT ${LEADS_PATH} → ${putRes.status}: ${await putRes.text()}`);
    return { ok: true };
  } catch (e) {
    console.error('[lead] GitHub persist failed', e.message);
    return { ok: false, error: e.message };
  }
}

export default async function handler(req, res) {
  if (req.method !== 'POST') return res.status(405).json({ error: 'Method not allowed' });

  const body = req.body || {};
  const source = body.source;
  const fields = body.fields || {};

  // Honeypot — silently accept and discard.
  if (fields.hp_field) return res.status(200).json({ ok: true });

  const required = LEAD_REQUIRED[source];
  if (!required) return res.status(400).json({ error: 'Unknown form source' });

  const missing = required.filter(k => !fields[k] || String(fields[k]).trim() === '');
  if (missing.length) return res.status(400).json({ error: 'Missing required fields', missing });

  if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(String(fields.email || ''))) {
    return res.status(400).json({ error: 'Invalid email' });
  }

  const lead = {
    id: crypto.randomUUID(),
    source,
    fields,
    page: body.page || null,
    userAgent: req.headers['user-agent'] || null,
    timestamp: new Date().toISOString()
  };

  const label = LEAD_LABEL[source] || source;
  const rows = Object.entries(fields)
    .filter(([k]) => k !== 'hp_field')
    .map(([k, v]) => `<tr><td style="padding:4px 12px 4px 0;color:#666;font-size:13px">${escapeHTML(k)}</td><td style="padding:4px 0;font-size:14px"><strong>${escapeHTML(v)}</strong></td></tr>`)
    .join('');

  const internalHtml = `
    <div style="font-family:-apple-system,BlinkMacSystemFont,sans-serif;max-width:560px">
      <h2 style="margin:0 0 6px;font-size:18px">New ${escapeHTML(label)} lead</h2>
      <p style="margin:0 0 16px;color:#666;font-size:13px">${escapeHTML(lead.timestamp)} · ${escapeHTML(lead.page || '')}</p>
      <table cellpadding="0" cellspacing="0" style="border-collapse:collapse">${rows}</table>
    </div>`;

  const tasks = [
    appendLeadToGitHub(lead),
    sendEmail({
      subject: `New ${label} lead — ${escapeHTML(fields.firstName || '')} ${escapeHTML(fields.lastName || '')}`.trim(),
      html: internalHtml,
      replyTo: fields.email
    })
  ];

  if (fields.email) {
    const isCairns = /cairns/i.test(lead.page || '');
    const greeting = fields.firstName ? `Hi ${escapeHTML(fields.firstName)},` : 'Hello,';
    const customerHtml = `
      <div style="font-family:-apple-system,BlinkMacSystemFont,sans-serif;max-width:560px;color:#222">
        <p>${greeting}</p>
        <p>Thanks for reaching out to The One Club. We've received your ${escapeHTML(label.toLowerCase())} enquiry and Bobby will be in touch within 24 hours.</p>
        <p>If anything is urgent, call or text <a href="tel:+61404774272">+61 404 774 272</a> or reply to this email.</p>
        <p style="margin-top:24px;color:#666;font-size:13px">— The One Club<br/>1% commission · marketing included · ${isCairns ? 'Cairns &amp; Port Douglas' : 'Gold Coast'}</p>
      </div>`;
    tasks.push(sendEmail({ to: fields.email, subject: 'Thanks — we have your details', html: customerHtml, replyTo: LEAD_TO }));
  }

  await Promise.all(tasks);

  return res.status(200).json({ ok: true, id: lead.id });
}
