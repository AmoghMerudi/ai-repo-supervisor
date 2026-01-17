import os
from main import run_ai_analysis, PRRequest

payload = PRRequest(
    repo="demo/repo",
    pr_number=1,
    author="tester",
    additions=5,
    deletions=6,
    changed_files=1,
    diff="diff test",
    lint_passed=True
)

print(run_ai_analysis(payload))

