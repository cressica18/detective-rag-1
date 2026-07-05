# DetectiveRAG — Progress Log

## Stage 0 — Security Fix + .gitignore — PASSED
Date: 2026-07-06
What was verified: `git rm --cached` removed backend/.env, detective.db*, __pycache__ .pyc files; .gitignore created at repo root; .env already has PLACEHOLDER key (prior account swapped it)
Files touched: .gitignore (NEW), PROGRESS_LOG.md (NEW)
Deviations: None. NOTE: Original key was committed in git history — user MUST revoke the old key at Google AI Studio even though current .env is safe.

## Stage 1 — Frontend Entry Point + Router — IN PROGRESS
Date: 2026-07-06
Status: Creating main.tsx, App.tsx, router.tsx, fixing package.json reactflow dependency, 3 missing pages
