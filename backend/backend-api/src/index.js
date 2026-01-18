const core = require('@actions/core');
const github = require('@actions/github');
const { spawn } = require('child_process');

const BACKEND_URL =
  process.env.BACKEND_URL ||
  'https://ai-repo-supervisor-zljk.onrender.com/analyze-pr';

/**
 * Simple local linter
 */
function runBasicLint(diffText) {
  const forbiddenPatterns = ['console.log', 'FIXME', 'debugger'];
  for (const pattern of forbiddenPatterns) {
    if (diffText.includes(pattern)) {
      console.log(`❌ Lint failed: Found forbidden pattern '${pattern}'`);
      return false;
    }
  }
  return true;
}

async function run() {
  try {
    const SIMULATE = process.env.SIMULATE === '1';
    const isGitHubAction = process.env.GITHUB_ACTIONS === 'true';

    const startPythonApi = () => {
      const port = process.env.PORT || '8000';
      console.log('Starting FastAPI backend on port', port);
      const child = spawn(
        'python3',
        [
          '-m',
          'uvicorn',
          'src.main:app',
          '--host',
          '0.0.0.0',
          '--port',
          port,
        ],
        { stdio: 'inherit' }
      );

      child.on('exit', code => {
        process.exit(code ?? 0);
      });
    };

    let owner;
    let repo;
    let prNumber;
    let prData;
    let diffText;
    let octokit; // 👈 declared once, used later

    // ---------------------------------------------------------
    // 1. LOAD PR DATA
    // ---------------------------------------------------------
    if (!isGitHubAction && !SIMULATE) {
      startPythonApi();
      return;
    }

    if (SIMULATE) {
      owner = process.env.SIM_OWNER || 'demo-owner';
      repo = process.env.SIM_REPO || 'demo-repo';
      prNumber = Number(process.env.SIM_PR_NUMBER || 1);

      prData = {
        user: { login: 'local-user' },
        additions: 5,
        deletions: 2,
        changed_files: 1,
      };

      diffText = `--- a/file.txt
+++ b/file.txt
@@ -1 +1 @@
-old
+new
`;

      console.log('🧪 SIMULATE mode: using mock PR data');
    } else {
      const token = process.env.GITHUB_TOKEN;
      if (!token) {
        core.setFailed('GITHUB_TOKEN not set in runner.');
        return;
      }

      octokit = github.getOctokit(token);
      const context = github.context;

      if (!context.payload.pull_request) {
        core.setFailed('No pull request found in GitHub context.');
        return;
      }

      owner = context.repo.owner;
      repo = context.repo.repo;
      prNumber = context.payload.pull_request.number;

      const { data: fullPr } = await octokit.rest.pulls.get({
        owner,
        repo,
        pull_number: prNumber,
      });

      prData = fullPr;

      const { data: diff } = await octokit.rest.pulls.get({
        owner,
        repo,
        pull_number: prNumber,
        mediaType: { format: 'diff' },
      });

      diffText = diff;
    }

    // ---------------------------------------------------------
    // 2. BUILD PAYLOAD FOR BACKEND
    // ---------------------------------------------------------
    const payload = {
      repo: `${owner}/${repo}`,
      pr_number: prNumber,
      author: prData.user?.login,
      additions: prData.additions || 0,
      deletions: prData.deletions || 0,
      changed_files: prData.changed_files || 0,
      diff: diffText || '',
      lint_passed: runBasicLint(diffText || ''),
    };

    // ---------------------------------------------------------
    // 3. SEND TO BACKEND
    // ---------------------------------------------------------
    const res = await fetch(BACKEND_URL, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });

    const text = await res.text();

    if (!res.ok) {
      core.error(`Backend failed with status ${res.status}: ${text}`);
      throw new Error(`Backend failed with status ${res.status}`);
    }

    const analysis = JSON.parse(text);
    console.log('📥 Received analysis:', analysis);

    // ---------------------------------------------------------
    // 4. SKIP COMMENTING IN SIMULATE MODE
    // ---------------------------------------------------------
    if (SIMULATE) {
      console.log('🧪 SIMULATE mode: skipping GitHub PR comment');
      return;
    }

    // ---------------------------------------------------------
    // 5. BUILD PR COMMENT (FINAL)
    // ---------------------------------------------------------

    const {
      summary,
      structural_signals = [],
      semantic_insights = [],
      synthesis,
      risks = [],
      suggestions = [],
      health_delta = 0,
      baseline_score,
      semantic_score,
    } = analysis;

    const structuralList =
      structural_signals.length > 0
        ? structural_signals.map(s => `- ${s}`).join('\n')
        : '- No structural signals detected.';

    const semanticList =
      semantic_insights.length > 0
        ? semantic_insights.map(s => `- ${s}`).join('\n')
        : '- No semantic insights detected.';

    const suggestionList =
      suggestions.length > 0
        ? suggestions.map(s => `- ${s}`).join('\n')
        : '- No immediate actions suggested.';

    const baselineLine =
      typeof baseline_score === 'number'
        ? `- Baseline risk score: ${baseline_score}`
        : '- Baseline risk score: unavailable';

    const semanticLine =
      typeof semantic_score === 'number'
        ? `- Semantic risk score: ${semantic_score}`
        : '- Semantic risk score: unavailable';

    const healthImpact = health_delta > 0 ? `+${health_delta}` : `${health_delta}`;

    const commentBody = `
## 🤖 Repo Supervisor

### What changed
${summary}

### Structural signals (size, surface area)
${structuralList}

### Semantic insights (behavioral intent)
${semanticList}

### Why this matters
${synthesis || 'No synthesized narrative available.'}

### Risk signals
${baselineLine}
${semanticLine}

### Suggested actions (human decides)
${suggestionList}

📊 **Repo health impact:** ${healthImpact}
`;

    await octokit.rest.issues.createComment({
      owner,
      repo,
      issue_number: prNumber,
      body: commentBody,
    });

    console.log('✅ PR comment posted successfully');
  } catch (err) {
    core.error(err);
    core.setFailed(err.message);
  }
}

run();
