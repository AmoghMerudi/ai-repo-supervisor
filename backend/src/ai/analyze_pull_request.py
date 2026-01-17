# backend/src/ai/analyze_pull_request.py

def analyze_pull_request(input: dict) -> dict:
    additions = input.get("additions", 0)
    deletions = input.get("deletions", 0)
    changed_files = input.get("changed_files", 0)
    diff = input.get("diff", "")
    lint_passed = input.get("lint_passed", True)

    total_changes = additions + deletions
    lower_diff = diff.lower()

    # -----------------------------
    # Summary
    # -----------------------------
    summary = "This pull request makes small, focused changes."

    if total_changes > 300:
        summary = (
            "This pull request introduces a large set of changes across the codebase."
        )
    elif total_changes > 100:
        summary = (
            "This pull request introduces moderate changes affecting multiple areas."
        )

    # -----------------------------
    # Risks
    # -----------------------------
    risks = []

    if total_changes > 300:
        risks.append(
            "Large pull request increases review complexity and the risk of hidden bugs."
        )

    if changed_files > 5:
        risks.append(
            "Changes span many files, increasing the chance of integration issues."
        )

    if not lint_passed:
        risks.append(
            "Lint checks failed, indicating potential code quality problems."
        )

    if any(keyword in lower_diff for keyword in ["auth", "token", "login"]):
        risks.append(
            "Authentication-related logic was modified, which is security-sensitive."
        )

    # -----------------------------
    # Suggestions
    # -----------------------------
    suggestions = []

    if total_changes > 300:
        suggestions.append(
            "Consider splitting this pull request into smaller, focused changes."
        )

    if not lint_passed:
        suggestions.append(
            "Resolve lint issues before merging to maintain code quality."
        )

    if any(keyword in lower_diff for keyword in ["auth", "token", "login"]):
        suggestions.append(
            "Add or review tests covering authentication edge cases."
        )

    # -----------------------------
    # Semantic score
    # -----------------------------
    semantic_score = 50

    if any(keyword in lower_diff for keyword in ["auth", "token", "login"]):
        semantic_score += 20

    if changed_files > 5:
        semantic_score += 10

    if not lint_passed:
        semantic_score -= 10

    semantic_score = max(0, min(100, semantic_score))

    # -----------------------------
    # Health delta
    # -----------------------------
    health_delta = 0

    if total_changes > 300:
        health_delta -= 3
    if not lint_passed:
        health_delta -= 2
    if not risks:
        health_delta += 2

    baseline_score = max(0, 100 - min(total_changes / 10, 50))

    return {
        "summary": summary,
        "risks": risks,
        "suggestions": suggestions,
        "health_delta": health_delta,
        "baseline_score": baseline_score,
        "semantic_score": semantic_score,
    }
