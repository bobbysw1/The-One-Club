// Vercel serverless function — admin API
// Reads and writes JSON data files in backend/data/ via the GitHub Contents API.
// Auth: password sent in X-Admin-Password header (checked on every request).

const ADMIN_PASSWORD = 'oneclub2026';

// Fine-grained Personal Access Token with Contents: Read & Write on this repo.
// Paste your token between the quotes below. Generate at:
//   https://github.com/settings/personal-access-tokens/new
//   Repository: bobbysw1/The-One-Club
//   Permissions: Contents → Read and write
const GITHUB_TOKEN = process.env.GITHUB_TOKEN || 'PASTE_YOUR_GITHUB_TOKEN_HERE';

const GITHUB_OWNER  = 'bobbysw1';
const GITHUB_REPO   = 'The-One-Club';
const GITHUB_BRANCH = 'main';

const FILES = {
  properties: 'backend/data/properties.json',
  chatbot:    'backend/data/chatbot.json',
  agents:     'backend/data/agents.json'
};

function ghHeaders() {
  return {
    'Authorization': `Bearer ${GITHUB_TOKEN}`,
    'Accept': 'application/vnd.github+json',
    'X-GitHub-Api-Version': '2022-11-28',
    'User-Agent': 'theoneclub-admin'
  };
}

async function ghGetFile(path) {
  const url = `https://api.github.com/repos/${GITHUB_OWNER}/${GITHUB_REPO}/contents/${path}?ref=${GITHUB_BRANCH}`;
  const r = await fetch(url, { headers: ghHeaders() });
  if (r.status === 404) return { content: null, sha: null };
  if (!r.ok) throw new Error(`GitHub GET ${path} → ${r.status}`);
  const j = await r.json();
  const decoded = Buffer.from(j.content, 'base64').toString('utf8');
  return { content: JSON.parse(decoded), sha: j.sha };
}

async function ghPutFile(path, dataObj, sha, message) {
  const url = `https://api.github.com/repos/${GITHUB_OWNER}/${GITHUB_REPO}/contents/${path}`;
  const body = {
    message: message || `admin: update ${path}`,
    content: Buffer.from(JSON.stringify(dataObj, null, 2), 'utf8').toString('base64'),
    branch: GITHUB_BRANCH
  };
  if (sha) body.sha = sha;
  const r = await fetch(url, {
    method: 'PUT',
    headers: { ...ghHeaders(), 'Content-Type': 'application/json' },
    body: JSON.stringify(body)
  });
  if (!r.ok) {
    const err = await r.text();
    throw new Error(`GitHub PUT ${path} → ${r.status}: ${err}`);
  }
  return r.json();
}

export default async function handler(req, res) {
  if (req.method !== 'POST') return res.status(405).json({ error: 'Method not allowed' });

  const { action, file, data, password } = req.body || {};

  // ── LOGIN ────────────────────────────────────────────────
  if (action === 'login') {
    if (password === ADMIN_PASSWORD) return res.status(200).json({ ok: true });
    return res.status(401).json({ error: 'Wrong password' });
  }

  // All other actions require the password header.
  const hdrPw = req.headers['x-admin-password'];
  if (hdrPw !== ADMIN_PASSWORD) return res.status(401).json({ error: 'Unauthorised' });

  if (!GITHUB_TOKEN || GITHUB_TOKEN === 'PASTE_YOUR_GITHUB_TOKEN_HERE') {
    return res.status(503).json({ error: 'GitHub token not configured. Paste your PAT into api/admin.js.' });
  }

  const filePath = FILES[file];
  if (!filePath) return res.status(400).json({ error: 'Unknown file' });

  try {
    if (action === 'get') {
      const { content } = await ghGetFile(filePath);
      return res.status(200).json({ data: content ?? (file === 'chatbot' ? {} : []) });
    }

    if (action === 'save') {
      if (data === undefined) return res.status(400).json({ error: 'data is required' });
      const { sha } = await ghGetFile(filePath);
      await ghPutFile(filePath, data, sha, `admin: update ${file}.json`);
      return res.status(200).json({ ok: true });
    }

    return res.status(400).json({ error: 'Unknown action' });
  } catch (e) {
    console.error('[admin] error', e);
    return res.status(500).json({ error: e.message || 'Server error' });
  }
}
