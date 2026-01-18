# backend/src/ai/analyze_pull_request.py

def _extract_changed_files(diff: str) -> list:
    paths = []
    for line in diff.splitlines():
        if line.startswith("diff --git "):
            parts = line.split()
            if len(parts) >= 4:
                a_path = parts[2][2:] if parts[2].startswith("a/") else parts[2]
                b_path = parts[3][2:] if parts[3].startswith("b/") else parts[3]
                paths.append(b_path or a_path)
        elif line.startswith("+++ b/"):
            paths.append(line[6:])
    # Preserve order, drop duplicates
    seen = set()
    unique_paths = []
    for path in paths:
        if path and path not in seen:
            seen.add(path)
            unique_paths.append(path)
    return unique_paths


def _count_added_conditionals(diff: str) -> int:
    count = 0
    for line in diff.splitlines():
        if not line.startswith("+") or line.startswith("+++"):
            continue
        lowered = line.lower()
        if "if " in lowered or "elif " in lowered or "switch" in lowered:
            count += 1
    return count


def analyze_pull_request(input: dict) -> dict:
    additions = input.get("additions", 0)
    deletions = input.get("deletions", 0)
    changed_files = input.get("changed_files", 0)
    diff = input.get("diff", "")
    lint_passed = input.get("lint_passed", True)

    total_changes = additions + deletions
    lower_diff = diff.lower()
    file_paths = _extract_changed_files(diff)
    top_dirs = sorted({path.split("/")[0] for path in file_paths if "/" in path})
    extensions = sorted({path.split(".")[-1] for path in file_paths if "." in path})
    added_conditionals = _count_added_conditionals(diff)
    tests_touched = any(
        "test" in path.lower() or "spec" in path.lower() for path in file_paths
    )

    touches_auth = any(keyword in lower_diff for keyword in ["auth", "token", "login"])
    touches_db = any(keyword in lower_diff for keyword in ["db", "database", "schema"])
    touches_infra = any(
        keyword in lower_diff for keyword in ["docker", "k8s", "terraform", "infra"]
    )
    touches_config = any(
        keyword in lower_diff for keyword in ["config", "env", ".yml", ".yaml"]
    )

    # -----------------------------
    # Structural pass
    # -----------------------------
    size_bucket = "small"
    if total_changes > 300:
        size_bucket = "large"
    elif total_changes > 100:
        size_bucket = "medium"

    structural_signals = [
        f"Change size: {size_bucket} ({additions} additions, {deletions} deletions).",
        f"Files changed: {changed_files}.",
    ]

    if top_dirs:
        structural_signals.append(f"Directories touched: {', '.join(top_dirs)}.")
    if extensions:
        structural_signals.append(f"File types: {', '.join(extensions)}.")

    # -----------------------------
    # Semantic pass
    # -----------------------------
    semantic_insights = []

    if added_conditionals > 0:
        semantic_insights.append(
            f"Added {added_conditionals} new conditional branches, which can introduce new logic paths."
        )

    if touches_auth:
        semantic_insights.append(
            "Authentication-related logic appears in the diff (auth/token/login)."
        )

    if touches_db:
        semantic_insights.append(
            "Data persistence signals detected (db/database/schema)."
        )

    if touches_infra or touches_config:
        semantic_insights.append(
            "Operational configuration or infrastructure may be affected."
        )

    if tests_touched:
        semantic_insights.append("Test files were modified, indicating potential coverage updates.")
    else:
        semantic_insights.append("No test files detected in the diff.")

    if not lint_passed:
        semantic_insights.append(
            "Lint checks failed; treat other risks as higher confidence."
        )

    # -----------------------------
    # Synthesis pass
    # -----------------------------
    synthesis = "Changes appear low risk based on size and surface area."
    if touches_auth:
        synthesis = (
            "This change touches authentication-sensitive logic. A small diff can still introduce"
            " high-impact failure modes (e.g., auth bypass or token handling errors)."
        )
    elif touches_db:
        synthesis = (
            "This change touches data persistence. Review for schema drift, migrations, or"
            " backward compatibility issues."
        )
    elif touches_infra or touches_config:
        synthesis = (
            "This change affects operational configuration. Misconfiguration can lead to"
            " service instability or deployment issues."
        )
    elif added_conditionals > 0:
        synthesis = (
            "New conditional logic was added. Review edge cases and ensure new branches"
            " are exercised by tests."
        )

    # -----------------------------
    # Summary
    # -----------------------------
    summary = "This pull request makes small, focused changes."
    if size_bucket == "large":
        summary = "This pull request introduces a large set of changes across the codebase."
    elif size_bucket == "medium":
        summary = "This pull request introduces moderate changes affecting multiple areas."

    # -----------------------------
    # Risks + suggestions
    # -----------------------------
    risks = []
    if size_bucket == "large":
        risks.append(
            "Large pull request increases review complexity and the risk of hidden bugs."
        )
    if changed_files > 5:
        risks.append(
            "Changes span many files, increasing the chance of integration issues."
        )
    if touches_auth:
        risks.append(
            "Authentication-related logic was modified, which is security-sensitive."
        )
    if touches_db:
        risks.append("Data persistence changes can introduce migration or integrity risk.")
    if not lint_passed:
        risks.append("Lint checks failed, indicating potential code quality problems.")

    suggestions = []
    if size_bucket == "large":
        suggestions.append("Consider splitting this pull request into smaller changes.")
    if not lint_passed:
        suggestions.append("Resolve lint issues before merging to maintain code quality.")
    if touches_auth and not tests_touched:
        suggestions.append("Add or review tests covering authentication edge cases.")
    if touches_db and not tests_touched:
        suggestions.append("Add or review tests covering data migrations and queries.")
    if added_conditionals > 0 and not tests_touched:
        suggestions.append("Add tests for new logic branches and edge cases.")

    # -----------------------------
    # Scores
    # -----------------------------
    semantic_score = 50
    if touches_auth:
        semantic_score += 20
    if touches_db:
        semantic_score += 10
    if changed_files > 5:
        semantic_score += 10
    if not lint_passed:
        semantic_score -= 10
    semantic_score = max(0, min(100, semantic_score))

    # -----------------------------
    # Health delta
    # -----------------------------
    health_delta = 0
    if size_bucket == "large":
        health_delta -= 3
    if not lint_passed:
        health_delta -= 2
    if not risks:
        health_delta += 2

    baseline_score = max(0, 100 - min(total_changes / 10, 50))

    return {
        "summary": summary,
        "structural_signals": structural_signals,
        "semantic_insights": semantic_insights,
        "synthesis": synthesis,
        "risks": risks,
        "suggestions": suggestions,
        "health_delta": health_delta,
        "baseline_score": baseline_score,
        "semantic_score": semantic_score,
    }
