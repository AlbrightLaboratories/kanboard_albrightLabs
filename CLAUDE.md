# Kanboard AlbrightLabs - Claude Conventions

## Project Overview

Hybrid Kanboard system with stock PHP backend, custom React frontend, MCP Server for Claude integration, and AI agent orchestration via Maestro API.

## Namespace

All Kubernetes resources deploy to: `HR-project-tracking`

## Implementation Order (Dependencies Respected)

1. `kanboard_client` - Foundation (all modules depend on this)
2. `dependency_graph` - Needed for agent scheduling
3. `maestro_api` - Agent communication layer
4. `worker_registry` - Custom LLM worker management
5. `skill_framework` - Mandatory skills orchestration
6. `validation_worker` - GitHub Actions integration
7. `toc_integration` - Master TOC updates
8. `kanboard-mcp` - MCP Server for Claude
9. `kanboard-ui` - React frontend
10. `github-worker` - Validation automation

## Module Rules (repo-architecture)

- Each module in `backend/scripts/<module>/`
- Orchestration file calls into `scripts/` directory
- No file exceeds 200 LOC
- One function per file where practical
- Every module reusable and testable independently

## TDD Discipline

Every acceptance criterion requires:
1. Failing test FIRST (red)
2. Minimal implementation (green)
3. Refactor if needed
4. Prove on real surface

## Commit Format

```
feat(AC-ID): description
```

Example: `feat(KC-01): JSON-RPC client connects and authenticates`

## AC Checkbox Rule

A checkbox is checked ONLY with:
- `commit_link`: SHA of implementing commit
- `test_link`: CI run showing green tests

## Convergence Target

95 acceptance criteria → 0 unproven

Track progress in `prd.json` under `convergence.proven`
