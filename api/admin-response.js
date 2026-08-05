// Email response sender for admin responses to leads
// Uses the same beautiful email template as lead.js

const RESEND_KEY = process.env.RESEND_API_KEY || '';
const LEAD_FROM  = process.env.LEAD_FROM_EMAIL || 'bobby@theoneclub.com.au';
const GITHUB_TOKEN = process.env.GITHUB_TOKEN || '';

const GITHUB_OWNER  = 'bobbysw1';
const GITHUB_REPO   = 'The-One-Club';
const GITHUB_BRANCH = 'main';
const SENT_PATH     = 'backend/data/sent.json';

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

async function sendEmail({ to, subject, html }) {
  if (!RESEND_KEY) {
    console.warn('[admin-response] RESEND_API_KEY not set');
    return { ok: false, simulated: true };
  }
  try {
    const res = await fetch('https://api.resend.com/emails', {
      method: 'POST',
      headers: { 'Authorization': `Bearer ${RESEND_KEY}`, 'Content-Type': 'application/json' },
      body: JSON.stringify({ from: LEAD_FROM, to: [to], subject, html })
    });
    if (!res.ok) {
      console.error('[admin-response] resend error', res.status, await res.text());
      return { ok: false, status: res.status };
    }
    return { ok: true };
  } catch (e) {
    console.error('[admin-response] email fetch failed', e.message);
    return { ok: false, error: e.message };
  }
}

async function saveSentEmail(record) {
  if (!GITHUB_TOKEN) {
    console.warn('[admin-response] GITHUB_TOKEN not set, skipping sent email record');
    return { ok: false, simulated: true };
  }
  const headers = {
    'Authorization': `Bearer ${GITHUB_TOKEN}`,
    'Accept': 'application/vnd.github+json',
    'X-GitHub-Api-Version': '2022-11-28',
    'User-Agent': 'theoneclub-admin'
  };
  const url = `https://api.github.com/repos/${GITHUB_OWNER}/${GITHUB_REPO}/contents/${SENT_PATH}?ref=${GITHUB_BRANCH}`;
  try {
    let sentEmails = [];
    let sha = null;
    const getRes = await fetch(url, { headers });
    if (getRes.ok) {
      const j = await getRes.json();
      sha = j.sha;
      sentEmails = JSON.parse(Buffer.from(j.content, 'base64').toString('utf8'));
      if (!Array.isArray(sentEmails)) sentEmails = [];
    } else if (getRes.status !== 404) {
      throw new Error(`GitHub GET ${SENT_PATH} → ${getRes.status}`);
    }
    sentEmails.push(record);
    const putRes = await fetch(`https://api.github.com/repos/${GITHUB_OWNER}/${GITHUB_REPO}/contents/${SENT_PATH}`, {
      method: 'PUT',
      headers: { ...headers, 'Content-Type': 'application/json' },
      body: JSON.stringify({
        message: `sent: email to ${record.to}`,
        content: Buffer.from(JSON.stringify(sentEmails, null, 2), 'utf8').toString('base64'),
        branch: GITHUB_BRANCH,
        ...(sha ? { sha } : {})
      })
    });
    if (!putRes.ok) throw new Error(`GitHub PUT ${SENT_PATH} → ${putRes.status}: ${await putRes.text()}`);
    return { ok: true };
  } catch (e) {
    console.error('[admin-response] GitHub persist failed', e.message);
    return { ok: false, error: e.message };
  }
}

export default async function handler(req, res) {
  if (req.method !== 'POST') return res.status(405).json({ error: 'Method not allowed' });

  const { to, subject, message, firstName } = req.body || {};

  if (!to || !subject || !message) {
    return res.status(400).json({ error: 'Missing required fields: to, subject, message' });
  }

  const greeting = firstName ? `Hi ${firstName},` : 'Hello,';
  const bodyHtml = `
    <p style="margin:0 0 16px;font-family:${BRAND.sans};font-size:15px;line-height:1.6;color:${BRAND.greenDark}">${greeting}</p>
    <p style="margin:0 0 16px;font-family:${BRAND.sans};font-size:15px;line-height:1.6;color:${BRAND.greenDark};white-space:pre-wrap">${message.replace(/</g, '&lt;').replace(/>/g, '&gt;')}</p>
    <p style="margin:0;font-family:${BRAND.sans};font-size:15px;line-height:1.6;color:${BRAND.greenDark}">Bobby</p>`;

  const html = emailShell({
    badge: 'Message from Bobby',
    headline: 'Your valuation details',
    meta: null,
    bodyHtml,
    ctaHtml: `<a href="tel:+61404774272" style="display:inline-block;background-color:${BRAND.gold};color:${BRAND.greenDark};text-decoration:none;font-family:${BRAND.sans};font-size:14px;font-weight:700;padding:14px 26px;border-radius:8px">Call or text Bobby &rarr;</a>`
  });

  const result = await sendEmail({ to, subject, html });
  if (!result.ok) {
    return res.status(500).json({ error: result.error || 'Failed to send email' });
  }

  const sentRecord = {
    id: crypto.randomUUID(),
    to,
    subject,
    message,
    timestamp: new Date().toISOString()
  };
  await saveSentEmail(sentRecord);

  return res.status(200).json({ ok: true });
}
