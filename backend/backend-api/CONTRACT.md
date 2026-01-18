# AI Repo Supervisor – Backend Contract

## POST /analyze-pr

Analyze a pull request and return human-readable insights.

---

### Request Body

```json
{
  "repo": "owner/repo",
  "pr_number": 123,
  "author": "username",
  "additions": 25,
  "deletions": 10,
  "changed_files": 4,
  "diff": "git diff text",
  "lint_passed": true
}
```

### Response Body

```json
{
  "summary": "Plain-English summary",
  "structural_signals": ["Signal 1", "Signal 2"],
  "semantic_insights": ["Insight 1", "Insight 2"],
  "synthesis": "Why the reviewer should care",
  "risks": ["Risk 1", "Risk 2"],
  "suggestions": ["Suggestion 1"],
  "health_delta": -2,
  "baseline_score": 85,
  "semantic_score": 60
}
```