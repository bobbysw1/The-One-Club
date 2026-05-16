// Resend email wrapper. Uses HTTPS fetch (Node 18+) to avoid adding
// a dependency. To enable in production set:
//   RESEND_API_KEY    – your Resend API key
//   LEAD_TO_EMAIL     – recipient (defaults to bobby@theoneclub.com.au)
//   LEAD_FROM_EMAIL   – verified sender (e.g. leads@theoneclub.com.au)
// If RESEND_API_KEY is unset, send() logs and resolves so dev never breaks.

const KEY  = process.env.RESEND_API_KEY || '';
const TO   = process.env.LEAD_TO_EMAIL  || 'bobby@theoneclub.com.au';
const FROM = process.env.LEAD_FROM_EMAIL || 'leads@theoneclub.com.au';

async function send({ to, from, subject, html, replyTo }) {
  to      = to      || TO;
  from    = from    || FROM;
  if (!KEY) {
    console.warn('[email] RESEND_API_KEY not set — would have sent:', { to, subject });
    return { ok: false, simulated: true };
  }
  const payload = { from, to: Array.isArray(to) ? to : [to], subject, html };
  if (replyTo) payload.reply_to = replyTo;
  try {
    const res = await fetch('https://api.resend.com/emails', {
      method: 'POST',
      headers: {
        'Authorization': 'Bearer ' + KEY,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(payload)
    });
    if (!res.ok) {
      const text = await res.text();
      console.error('[email] resend error', res.status, text);
      return { ok: false, status: res.status, body: text };
    }
    return { ok: true };
  } catch (e) {
    console.error('[email] fetch failed', e.message);
    return { ok: false, error: e.message };
  }
}

module.exports = { send, TO, FROM };
