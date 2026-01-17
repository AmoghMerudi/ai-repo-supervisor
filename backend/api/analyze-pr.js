module.exports = (req, res) => {
  // Only allow POST
  if (req.method !== 'POST') return res.status(405).json({ error: 'method not allowed' });

  // Simple shared-secret auth via Authorization: Bearer <secret>
  const auth = (req.headers.authorization || '');
  const secret = process.env.BACKEND_SECRET || 'local-secret';
  if (!auth.startsWith('Bearer ') || auth.slice('Bearer '.length).trim() !== secret) {
    return res.status(401).json({ error: 'unauthorized' });
  }

  const { repo, pr_number, additions = 0, deletions = 0, diff = '', lint_passed = true } = req.body || {};
  if (!repo || !pr_number) return res.status(400).json({ error: 'missing repo or pr_number' });

  // Minimal deterministic analysis
  const risks = [];
  if (!lint_passed) risks.push('Lint failures');
  if (diff.length > 5000) risks.push('Very large diff');
  if (additions - deletions > 500) risks.push('Many additions');

  const suggestions = [];
  if (!lint_passed) suggestions.push('Fix lint issues');
  if (risks.length === 0) suggestions.push('Add unit tests for changed code');

  const summary = `Mock analysis for ${repo} PR #${pr_number} — ${risks.length ? 'issues found' : 'low risk'}`;

  return res.json({
    summary,
    risks,
    suggestions,
    health_delta: risks.length ? -5 : 0
  });
};