# AI 

A human-in-the-loop AI GitHub repo supervisor that helps teams understand
the identity of their codebase, track repo health over time, and make safer
decisions during fast development.

## Why
Most tools answer: "Is this PR okay?"
We answer: "What does this change say about the identity of this repo?"

## What it does
- Summarizes PRs in plain English
- Flags risky changes
- Tracks repo health trends over time
- Proposes actions while keeping humans in control

## Theme: Identity
We treat identity as behavioral:
- PR identity (size, risk, patterns)
- Repo identity (how it evolves over time)
- Contributor identity (lightweight patterns)

## Architecture
- GitHub Action (Node + TypeScript)
- Backend (FastAPI + Gemini)
- Dashboard (Next.js)

## Demo Flow
1. Open a PR
2. AI summary + risk appears
3. Repo health updates
4. Identity trends are visible
