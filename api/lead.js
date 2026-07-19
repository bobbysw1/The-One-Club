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

// Brand shell for outbound emails — deep green + gold, table-based layout
// so it renders reliably in iOS Mail / Apple Mail (and degrades gracefully
// everywhere else). Serif/sans fallback stacks approximate the site's
// Fraunces + Inter pairing since webfonts aren't reliable in email clients.
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
          <img src="https://www.theoneclub.com.au/logo.png" width="176" alt="The One Club" style="display:block;width:176px;max-width:176px;height:auto;border:0;outline:none"/>
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
  const isCairns = /cairns/i.test(lead.page || '');
  const timestamp = new Date(lead.timestamp).toLocaleString('en-AU', {
    dateStyle: 'medium', timeStyle: 'short', timeZone: 'Australia/Brisbane'
  });

  const rows = Object.entries(fields)
    .filter(([k]) => k !== 'hp_field')
    .map(([k, v]) => `
      <tr>
        <td style="padding:11px 0;border-bottom:1px solid rgba(26,38,32,.08);font-family:${BRAND.sans};font-size:10.5px;font-weight:700;letter-spacing:.6px;text-transform:uppercase;color:${BRAND.muted};width:120px;vertical-align:top">${escapeHTML(k)}</td>
        <td style="padding:11px 0;border-bottom:1px solid rgba(26,38,32,.08);font-family:${BRAND.sans};font-size:15px;color:${BRAND.greenDark};font-weight:600;vertical-align:top">${escapeHTML(v)}</td>
      </tr>`)
    .join('');

  const internalHtml = emailShell({
    badge: 'New Lead',
    headline: `New ${escapeHTML(label)}`,
    meta: `${escapeHTML(timestamp)}&nbsp;&nbsp;&middot;&nbsp;&nbsp;${escapeHTML(lead.page || 'unknown page')}`,
    bodyHtml: `<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="border-collapse:collapse">${rows}</table>`,
    ctaHtml: fields.email
      ? `<a href="mailto:${escapeHTML(fields.email)}" style="display:inline-block;background-color:${BRAND.gold};color:${BRAND.greenDark};text-decoration:none;font-family:${BRAND.sans};font-size:14px;font-weight:700;padding:14px 26px;border-radius:8px">Reply to ${escapeHTML(fields.firstName || 'them')} &rarr;</a>`
      : ''
  });

  const tasks = [
    appendLeadToGitHub(lead),
    sendEmail({
      subject: `New ${label} lead — ${escapeHTML(fields.firstName || '')} ${escapeHTML(fields.lastName || '')}`.trim(),
      html: internalHtml,
      replyTo: fields.email
    })
  ];

  if (fields.email) {
    const greeting = fields.firstName ? `Hi ${escapeHTML(fields.firstName)},` : 'Hello,';
    const customerHtml = emailShell({
      badge: isCairns ? 'Cairns & Port Douglas' : 'Gold Coast',
      headline: 'Got it, thank you.',
      meta: null,
      bodyHtml: `
        <p style="margin:0 0 16px;font-family:${BRAND.sans};font-size:15px;line-height:1.6;color:${BRAND.greenDark}">${greeting}</p>
        <p style="margin:0 0 16px;font-family:${BRAND.sans};font-size:15px;line-height:1.6;color:${BRAND.greenDark}">Thanks for reaching out to The One Club. We've received your ${escapeHTML(label.toLowerCase())} enquiry and Bobby will be in touch within 24 hours.</p>
        <p style="margin:0;font-family:${BRAND.sans};font-size:15px;line-height:1.6;color:${BRAND.greenDark}">If anything is urgent, call or text any time.</p>`,
      ctaHtml: `
        <a href="tel:+61404774272" style="display:inline-block;background-color:${BRAND.gold};color:${BRAND.greenDark};text-decoration:none;font-family:${BRAND.sans};font-size:14px;font-weight:700;padding:14px 26px;border-radius:8px">Call or text Bobby &rarr;</a>
        <div style="margin-top:14px;font-family:${BRAND.sans};font-size:12px;color:${BRAND.muted}">Or simply reply to this email.</div>`
    });
    tasks.push(sendEmail({ to: fields.email, subject: 'Thanks — we have your details', html: customerHtml, replyTo: LEAD_TO }));
  }

  await Promise.all(tasks);

  return res.status(200).json({ ok: true, id: lead.id });
}
