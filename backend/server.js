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
