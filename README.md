# PRISM – Pull Request Insight & Supervision Machine

PRISM is a human-in-the-loop AI system that helps engineering teams understand pull requests, track repository health over time, and make safer decisions during fast development.

It does not auto-merge code, spam PR comments, or blindly enforce rules.
PRISM analyzes, explains, and advises — humans stay in control.

⸻

## Inspiration

Modern teams move fast. Code review tools haven’t kept up.

Most existing tools:
	•	Dump lint errors
	•	Focus on a single PR in isolation
	•	Enforce rules without context
	•	Answer only: “Is this PR okay?”

They fail to answer:
	•	How is this repo evolving over time?
	•	Is our development getting riskier?
	•	Why does this PR matter in the bigger picture?

PRISM was built to fill that gap.

⸻

## What it does

PRISM provides repo-level supervision, not just PR checks.

🔍 Pull Request Analysis

For every PR, PRISM analyzes:
	•	Change size and surface area
	•	Files and directories touched
	•	Risk-sensitive domains (auth, infra, payments, etc.)
	•	Semantic intent using LLMs

It produces:
	•	A plain-English summary
	•	Key risks (if any)
	•	Actionable suggestions
	•	A quantified health delta

📊 Repository Health Scoring

Each repository maintains a rolling health score based on:
	•	Baseline risk heuristics
	•	Semantic risk from PR intent
	•	Directional changes over time

Health states:
	•	Healthy
	•	At Risk
	•	Critical

📈 Visual Health Trends

The dashboard shows:
	•	Current health score
	•	Repo-specific risk reasons
	•	Recent PR activity
	•	Health trends over time (demo visualization)

🧠 Human-in-the-Loop Design

PRISM:
	•	Never auto-merges
	•	Never blocks developers
	•	Never enforces rules blindly

It advises. Humans decide.

⸻

## How we built it

Backend
	•	Python + FastAPI – API layer
	•	Heuristic engine – Baseline risk scoring
	•	Gemini API – Semantic PR understanding
	•	MongoDB – PR history & repo health storage

Backend responsibilities:
	•	Analyze PR payloads
	•	Generate risk signals
	•	Compute health deltas
	•	Store and retrieve historical context

Frontend
	•	Next.js (App Router)
	•	TypeScript
	•	Tailwind CSS

Frontend responsibilities:
	•	Repo health dashboard
	•	Repo detail views
	•	PR summaries and insights
	•	Demo-friendly visualizations

Architecture Philosophy
	•	Clear backend / frontend contract
	•	Deterministic mocks for demos
	•	Human-readable outputs
	•	Scalable to GitHub Actions integration

⸻

## Challenges we ran into
	•	Designing a health score that is intuitive, directional, and explainable
	•	Avoiding noisy or repetitive AI output
	•	Mapping semantic risk into something engineers trust
	•	Frontend–backend integration under hackathon time pressure
	•	Git branch chaos (character-building experience)

⸻

## Accomplishments we’re proud of
	•	Built a repo-level supervision model, not just a PR checker
	•	Combined heuristics + LLM reasoning coherently
	•	Created an opinionated but non-blocking developer experience
	•	Delivered a clean, demo-ready UI
	•	Kept humans in control at every step

⸻

## What we learned
	•	AI is most effective when it augments judgment, not replaces it
	•	Context over time matters more than single-PR correctness
	•	Explainability builds trust faster than automation
	•	Clean contracts between systems save lives (and hackathons)

⸻

## What’s next for PRISM

Planned extensions:
	•	GitHub App + GitHub Actions integration
	•	Long-term health trend analytics
	•	Team-level risk dashboards
	•	Configurable risk sensitivity per repo
	•	PRISM comments as suggestions, not commands

PRISM aims to become a copilot for code review decisions, not a gatekeeper.

⸻

## Built with
	•	Python
	•	FastAPI
	•	MongoDB
	•	Google Gemini API
	•	Next.js
	•	TypeScript
	•	Tailwind CSS

⸻

PRISM is an experiment in responsible, human-centered AI for software engineering.
