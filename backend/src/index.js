const { getOctokit, context } = require("@actions/github");
const { execSync } = require("child_process");

const token = process.env.GITHUB_TOKEN;
const backendUrl = process.env.BACKEND_URL;
const backendSecret = process.env.BACKEND_SECRETS || process.env.BACKEND_SECRET;
const vercelBypass =
  process.env.VERCEL_PROTECTION_BYPASS || process.env.VERCEL_BYPASS_TOKEN;
if (!token) {
  console.error("GITHUB_TOKEN is not set");
  process.exit(1);
}
if (!backendUrl) {
  console.error("BACKEND_URL is not set");
  process.exit(1);
}

async function run() {
  const pr = context.payload && context.payload.pull_request;
  if (!pr) return;

  const octokit = getOctokit(token);

  const diff = await octokit.request(
    "GET /repos/{owner}/{repo}/pulls/{pull_number}",
    {
      owner: context.repo.owner,
      repo: context.repo.repo,
      pull_number: pr.number,
      headers: { accept: "application/vnd.github.v3.diff" },
    }
  );

  let lintPassed = true;
  try {
    execSync("npm run lint", { stdio: "ignore" });
  } catch {
    lintPassed = false;
  }

  const payload = {
    repo: `${context.repo.owner}/${context.repo.repo}`,
    pr_number: pr.number,
    author: pr.user && pr.user.login,
    additions: pr.additions,
    deletions: pr.deletions,
    changed_files: pr.changed_files,
    diff: diff.data,
    lint_passed: lintPassed,
  };

  if (typeof fetch !== "function") {
    console.error("global fetch is not available on this Node runtime");
    process.exit(1);
  }

  const headers = { "Content-Type": "application/json" };
  if (backendSecret) headers.Authorization = `Bearer ${backendSecret}`;
  if (vercelBypass) headers["x-vercel-protection-bypass"] = vercelBypass;

  console.log(
    "Posting analysis to backend:",
    backendUrl,
    "authPresent:",
    !!backendSecret,
    "vercelBypassPresent:",
    !!vercelBypass
  );

  const res = await fetch(backendUrl, {
    method: "POST",
    headers,
    body: JSON.stringify(payload),
  });

  if (!res.ok) {
    const text = await res.text().catch(() => '');
    throw new Error(`Backend responded with ${res.status}: ${text}`);
  }

  const analysis = await res.json();

  const risks = Array.isArray(analysis.risks) ? analysis.risks : [];
  const suggestions = Array.isArray(analysis.suggestions)
    ? analysis.suggestions
    : [];

  const commentBody = `
## 🤖 AI Repo Supervisor

### Summary
${analysis.summary || ""}

### Risk Indicators
${risks.map((r) => `- ⚠️ ${r}`).join("\n")}

### Suggested Actions (Human decides)
${suggestions.map((s) => `- 👉 ${s}`).join("\n")}

**Repo Risk Score Change:** ${analysis.health_delta ?? ""}
`;

  await octokit.rest.issues.createComment({
    owner: context.repo.owner,
    repo: context.repo.repo,
    issue_number: pr.number,
    body: commentBody,
  });
}

run().catch((err) => {
  console.error("Action failed:", err);
  process.exit(1);
});