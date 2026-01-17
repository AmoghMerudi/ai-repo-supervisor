const express = require('express');
const fs = require('fs');
const http = require('http');
const https = require('https');

// Simple express app that accepts POST /analyze-pr and returns JSON analysis.
// Protects the endpoint with a shared secret in Authorization: Bearer <secret>
const app = express();
app.use(express.json({ limit: '2mb' }));

// Config via env
const PORT = Number(process.env.PORT || 3000);
const BACKEND_SECRET = process.env.BACKEND_SECRET || 'local-secret';
// TLS files (optional). For real deployments use real CA-signed certs and secure storage.
const TLS_KEY = process.env.TLS_KEY_PATH || 'backend/certs/privkey.pem';
const TLS_CERT = process.env.TLS_CERT_PATH || 'backend/certs/cert.pem';

// Basic auth guard
function checkAuth(req, res, next) {
  const auth = (req.get('authorization') || '');
  if (!auth.startsWith('Bearer ')) return res.status(401).json({ error: 'missing auth' });
  const token = auth.slice('Bearer '.length).trim();
  if (token !== BACKEND_SECRET) return res.status(403).json({ error: 'forbidden' });
  next();
}

// POST /analyze-pr
app.post('/analyze-pr', checkAuth, (req, res) => {
  const { repo, pr_number, additions = 0, deletions = 0, diff = '', lint_passed = true } = req.body || {};

  if (!repo || !pr_number) {
    return res.status(400).json({ error: 'missing repo or pr_number' });
  }

  // Minimal deterministic analysis for testing:
  const risks = [];
  if (!lint_passed) risks.push('Lint failures');
  if (diff.length > 5000) risks.push('Very large diff');
  if (additions - deletions > 500) risks.push('Many additions');

  const suggestions = [];
  if (!lint_passed) suggestions.push('Fix lint issues');
  if (risks.length === 0) suggestions.push('Add unit tests for changed code');

  const summary = `Mock analysis for ${repo} PR #${pr_number} — ${risks.length ? 'issues found' : 'looks low risk'}`;

  return res.json({
    summary,
    risks,
    suggestions,
    health_delta: risks.length ? -5 : 0
  });
});

// Start HTTPS if certs exist, otherwise start HTTP
if (fs.existsSync(TLS_KEY) && fs.existsSync(TLS_CERT)) {
  const key = fs.readFileSync(TLS_KEY);
  const cert = fs.readFileSync(TLS_CERT);
  https.createServer({ key, cert }, app).listen(PORT, () => {
    console.log(`Mock HTTPS backend listening on https://localhost:${PORT}/analyze-pr`);
  });
} else {
  http.createServer(app).listen(PORT, () => {
    console.log(`Mock HTTP backend listening on http://localhost:${PORT}/analyze-pr`);
    console.log('No TLS certs found; running HTTP fallback for local testing.');
  });
}

// Development notes (keep here for quick reference):
// - For CI testing with self-signed certs, set env NODE_TLS_REJECT_UNAUTHORIZED=0 when calling curl/node fetch (not for production).
// - To require more fields or run async analysis, accept the request and enqueue a job, then return 202 + job id.
// - Replace shared-secret logic with proper auth (JWT, API keys stored in secrets manager) for production.