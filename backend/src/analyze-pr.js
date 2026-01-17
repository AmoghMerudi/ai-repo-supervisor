export function analyzePullRequest(payload) {
  const {
    repo = "unknown-repo",
    additions = 0,
    deletions = 0,
    lint_passed = true,
  } = payload;

  let risk = 0;
  const size = additions + deletions;

  if (size > 500) risk += 30;
  if (!lint_passed) risk += 25;

  const healthScore = Math.max(100 - risk, 40);

  let status = "Healthy";
  if (healthScore < 80) status = "At Risk";
  if (healthScore < 65) status = "Critical";

  return {
    name: repo,
    healthScore,
    status,
    reason:
      status === "Healthy"
        ? "Changes are within safe limits"
        : "Large PR or failed checks increased risk",
    prs: [
      {
        title: "Automated PR Analysis",
        summary: `Diff size ${size} · ${
          lint_passed ? "Lint passed" : "Lint failed"
        }`,
      },
    ],
  };
}