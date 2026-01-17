const core = require('@actions/core');
const github = require('@actions/github');

// ---------------------------------------------------------
// 1. CONFIGURATION
// ---------------------------------------------------------
// REPLCE THIS with your actual Render/Ngrok URL
// Example: 'https://my-backend.onrender.com/analyze-pr'
const BACKEND_URL = 'https://YOUR-APP-URL.com/analyze-pr'; 

/**
 * A simple local linter to determine if "lint_passed" is true or false.
 * For the hackathon, we fail lint if we see 'console.log' or 'FIXME'.
 */
function runBasicLint(diffText) {
  const forbiddenPatterns = ['console.log', 'FIXME', 'debugger'];
  for (const pattern of forbiddenPatterns) {
    if (diffText.includes(pattern)) {
      console.log(`❌ Lint failed: Found forbidden pattern '${pattern}'`);
      return false; // Lint Failed
    }
  }
  return true; // Lint Passed
}

async function run() {
  try {
    const token = process.env.GITHUB_TOKEN;
    const octokit = github.getOctokit(token);
    const context = github.context;

    // ---------------------------------------------------------
    // 2. GATHER DATA (The "Extract" Phase)
    // ---------------------------------------------------------
    if (!context.payload.pull_request) {
      core.setFailed("No pull request found.");
      return;
    }

    const prNumber = context.payload.pull_request.number;
    const owner = context.repo.owner;
    const repo = context.repo.repo;
    
    // We need to fetch the FULL PR object to get accurate line counts (additions/deletions)
    // The default context.payload sometimes has old cached data.
    const { data: prData } = await octokit.rest.pulls.get({
      owner,
      repo,
      pull_number: prNumber,
    });

    // We fetch the raw diff separately to scan the text
    const { data: diffText } = await octokit.rest.pulls.get({
      owner,
      repo,
      pull_number: prNumber,
      mediaType: { format: 'diff' }
    });

    // ---------------------------------------------------------
    // 3. RUN LOCAL CHECKS
    // ---------------------------------------------------------
    const isLintClean = runBasicLint(diffText);

    // ---------------------------------------------------------
    // 4. PREPARE PAYLOAD (Matching your Python Pydantic Model)
    // ---------------------------------------------------------
    const payload = {
      repo: `${owner}/${repo}`,        // Matches Python: repo: str
      pr_number: prNumber,             // Matches Python: pr_number: int
      author: prData.user.login,       // Matches Python: author: str
      additions: prData.additions,     // Matches Python: additions: int
      deletions: prData.deletions,     // Matches Python: deletions: int
      changed_files: prData.changed_files, // Matches Python: changed_files: int
      diff: diffText,                  // Matches Python: diff: str
      lint_passed: isLintClean         // Matches Python: lint_passed: bool
    };

    console.log("📤 Sending data to backend:", JSON.stringify(payload, null, 2));

    // ---------------------------------------------------------
    // 5. CALL THE BACKEND
    // ---------------------------------------------------------
    const response = await fetch(BACKEND_URL, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });

    if (!response.ok) {
      throw new Error(`Backend failed with status ${response.status}: ${response.statusText}`);
    }

    const analysis = await response.json();
    console.log("📥 Received analysis:", analysis);

    // ---------------------------------------------------------
    // 6. POST COMMENT TO PR
    // ---------------------------------------------------------
    // We build the message using the data your Python backend returned
    
    // Create a list of bullet points for risks
    const riskList = analysis.risks.length > 0 
      ? analysis.risks.map(r => `- 🔴 ${r}`).join('\n') 
      : "- ✅ No significant risks detected.";

    const suggestionList = analysis.suggestions.length > 0
      ? analysis.suggestions.map(s => `- 💡 ${s}`).join('\n')
      : "- No immediate suggestions.";

    const commentBody = `
## 🤖 Repo Supervisor Report

${analysis.summary}

### 🛡️ Risk Assessment
${riskList}

### 📝 Suggestions
${suggestionList}

---
**Health Impact:** ${analysis.health_score_impact > 0 ? '+' : ''}${analysis.health_score_impact} pts
    `;

    await octokit.rest.issues.createComment({
      owner,
      repo,
      issue_number: prNumber,
      body: commentBody,
    });

  } catch (error) {
    core.setFailed(error.message);
  }
}

run();