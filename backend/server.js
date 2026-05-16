const express = require('express');
const session = require('express-session');
const cors = require('cors');
const fs = require('fs');
const path = require('path');
const { v4: uuidv4 } = require('uuid');

const app = express();

// ── CONFIG ──────────────────────────────────────────────
const ADMIN_PASSWORD = process.env.ADMIN_PASSWORD || 'oneclub2026';
const SESSION_SECRET = process.env.SESSION_SECRET || 'oneclub-secret-xk92';
const PORT = process.env.PORT || 3001;
const PROPS_FILE = path.join(__dirname, 'data', 'properties.json');
const CHAT_FILE  = path.join(__dirname, 'data', 'chatbot.json');
const LEADS_FILE = path.join(__dirname, 'data', 'leads.json');
const email = require('./lib/email');

// ── MIDDLEWARE ───────────────────────────────────────────
app.use(cors({
  origin: true,
  credentials: true
}));
app.use(express.json());
app.use(session({
  secret: SESSION_SECRET,
  resave: false,
  saveUninitialized: false,
  cookie: { maxAge: 24 * 60 * 60 * 1000, httpOnly: true }
}));

// Serve admin panel
app.use('/admin', express.static(path.join(__dirname, 'admin')));

// ── HELPERS ──────────────────────────────────────────────
function readJSON(file) {
  return JSON.parse(fs.readFileSync(file, 'utf8'));
}
function writeJSON(file, data) {
  fs.writeFileSync(file, JSON.stringify(data, null, 2), 'utf8');
}
function requireAuth(req, res, next) {
  if (req.session && req.session.authenticated) return next();
  res.status(401).json({ error: 'Unauthorised' });
}

// ── AUTH ROUTES ──────────────────────────────────────────
app.post('/api/login', (req, res) => {
  const { password } = req.body;
  if (password === ADMIN_PASSWORD) {
    req.session.authenticated = true;
    res.json({ ok: true });
  } else {
    res.status(401).json({ error: 'Wrong password' });
  }
});

app.post('/api/logout', (req, res) => {
  req.session.destroy(() => res.json({ ok: true }));
});

app.get('/api/auth/check', (req, res) => {
  res.json({ authenticated: !!(req.session && req.session.authenticated) });
});

// ── PROPERTIES ───────────────────────────────────────────
// Public — frontend fetches this to render listings
app.get('/api/properties', (req, res) => {
  res.json(readJSON(PROPS_FILE));
});

// Create
app.post('/api/properties', requireAuth, (req, res) => {
  const props = readJSON(PROPS_FILE);
  const newProp = { ...req.body, id: uuidv4() };
  props.push(newProp);
  writeJSON(PROPS_FILE, props);
  res.status(201).json(newProp);
});

// Update
app.put('/api/properties/:id', requireAuth, (req, res) => {
  const props = readJSON(PROPS_FILE);
  const idx = props.findIndex(p => p.id === req.params.id);
  if (idx === -1) return res.status(404).json({ error: 'Property not found' });
  props[idx] = { ...req.body, id: req.params.id };
  writeJSON(PROPS_FILE, props);
  res.json(props[idx]);
});

// Delete
app.delete('/api/properties/:id', requireAuth, (req, res) => {
  const props = readJSON(PROPS_FILE);
  const filtered = props.filter(p => p.id !== req.params.id);
  if (filtered.length === props.length) return res.status(404).json({ error: 'Property not found' });
  writeJSON(PROPS_FILE, filtered);
  res.json({ ok: true });
});

// ── CHATBOT ──────────────────────────────────────────────
// Public — frontend fetches this to build knowledge base
app.get('/api/chatbot', (req, res) => {
  res.json(readJSON(CHAT_FILE));
});

// Add / update a single entry (key = topic slug e.g. "commission")
app.post('/api/chatbot/entry', requireAuth, (req, res) => {
  const { key, keywords, response } = req.body;
  if (!key || !response) return res.status(400).json({ error: 'key and response are required' });
  const chat = readJSON(CHAT_FILE);
  chat[key] = { keywords: keywords || [], response };
  writeJSON(CHAT_FILE, chat);
  res.json({ ok: true, key });
});

// Delete an entry
app.delete('/api/chatbot/entry/:key', requireAuth, (req, res) => {
  const chat = readJSON(CHAT_FILE);
  if (!chat[req.params.key]) return res.status(404).json({ error: 'Entry not found' });
  delete chat[req.params.key];
  writeJSON(CHAT_FILE, chat);
  res.json({ ok: true });
});

// ── LEADS ────────────────────────────────────────────────
// Required fields by source. Add new sources here and the validator picks them up.
const LEAD_REQUIRED = {
  valuation:    ['firstName', 'lastName', 'email', 'phone', 'address'],
  landlord:     ['firstName', 'lastName', 'email', 'phone', 'address'],
  tenant:       ['firstName', 'lastName', 'email', 'phone'],
  buyer:        ['firstName', 'lastName', 'email', 'phone'],
  'auction-buyer': ['firstName', 'lastName', 'email', 'phone']
};

const LEAD_LABEL = {
  valuation:    'Free Valuation',
  landlord:     'Landlord Register',
  tenant:       'Tenant Register',
  buyer:        'Buyer Interest',
  'auction-buyer': 'Auction Buyer Interest'
};

function escapeHTML(s) {
  return String(s).replace(/[&<>"']/g, c => (
    { '&':'&amp;', '<':'&lt;', '>':'&gt;', '"':'&quot;', "'":'&#39;' }[c]
  ));
}

function ensureLeadsFile() {
  if (!fs.existsSync(LEADS_FILE)) writeJSON(LEADS_FILE, []);
}

app.post('/api/lead', async (req, res) => {
  try {
    const body = req.body || {};
    const source = body.source;
    const fields = body.fields || {};
    const required = LEAD_REQUIRED[source];

    // Honeypot — silently accept and discard
    if (fields.hp_field) return res.json({ ok: true });

    if (!required) return res.status(400).json({ error: 'Unknown form source' });

    const missing = required.filter(k => !fields[k] || String(fields[k]).trim() === '');
    if (missing.length) return res.status(400).json({ error: 'Missing required fields', missing });

    // Basic email sanity
    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(String(fields.email))) {
      return res.status(400).json({ error: 'Invalid email' });
    }

    const lead = {
      id: uuidv4(),
      source,
      fields,
      page: body.page || null,
      userAgent: req.headers['user-agent'] || null,
      timestamp: new Date().toISOString()
    };

    ensureLeadsFile();
    const leads = readJSON(LEADS_FILE);
    leads.push(lead);
    writeJSON(LEADS_FILE, leads);

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

    // Fire internal notification + customer auto-reply in parallel.
    const tasks = [];
    tasks.push(email.send({
      subject: `New ${label} lead — ${escapeHTML(fields.firstName || '')} ${escapeHTML(fields.lastName || '')}`.trim(),
      html: internalHtml,
      replyTo: fields.email
    }));
    if (fields.email) {
      const greeting = fields.firstName ? `Hi ${escapeHTML(fields.firstName)},` : 'Hello,';
      const customerHtml = `
        <div style="font-family:-apple-system,BlinkMacSystemFont,sans-serif;max-width:560px;color:#222">
          <p>${greeting}</p>
          <p>Thanks for reaching out to The One Club. We've received your ${escapeHTML(label.toLowerCase())} enquiry and Bobby will be in touch within 24 hours.</p>
          <p>If anything is urgent, call or text <a href="tel:+61404774272">+61 404 774 272</a> or reply to this email.</p>
          <p style="margin-top:24px;color:#666;font-size:13px">— The One Club<br/>1% commission · marketing included · Gold Coast</p>
        </div>`;
      tasks.push(email.send({
        to: fields.email,
        subject: 'Thanks — we have your details',
        html: customerHtml
      }));
    }
    await Promise.all(tasks);

    res.json({ ok: true, id: lead.id });
  } catch (e) {
    console.error('[lead] error', e);
    res.status(500).json({ error: 'Server error' });
  }
});

app.get('/api/leads', requireAuth, (req, res) => {
  ensureLeadsFile();
  res.json(readJSON(LEADS_FILE));
});

// ── START ─────────────────────────────────────────────────
app.listen(PORT, () => {
  console.log(`
  ┌─────────────────────────────────────┐
  │   The One Club — Backend Running    │
  │   http://localhost:${PORT}              │
  │   Admin: http://localhost:${PORT}/admin │
  └─────────────────────────────────────┘
  `);
});
