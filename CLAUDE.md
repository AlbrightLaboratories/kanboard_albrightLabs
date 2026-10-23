# Kanboard AlbrightLabs - Claude Code Conventions

## Repository Info

- **URL**: https://github.com/AlbrightLaboratories/kanboard_albrightLabs
- **Visibility**: Public
- **Branch Protection**: `main` branch requires `build` CI to pass
- **Runners**: `albright-runners` (self-hosted)

## Branch Protection Rules

The `main` branch is protected:
- **Required status checks**: `build` must pass
- **No force pushes**: Disabled
- **No deletions**: Disabled
- **Enforce admins**: Disabled (admins can bypass)

**Only GitHub Actions can effectively update main** - all changes must go through PR with passing CI.

## Architecture

```
kanboard_albrightLabs/
├── backend/               # Python backend (555 tests)
│   └── scripts/
│       ├── kanboard_client/    # JSON-RPC client for Kanboard PHP API
│       ├── maestro_api/        # Two-way agent communication (REST + WebSocket)
│       ├── skill_framework/    # Mandatory skills (plan/prd/tdd/prove-it/release-it)
│       ├── worker_registry/    # Custom LLM worker management
│       ├── agent_comments/     # Agent-in-comments feature
│       ├── dependency_graph/   # Story dependencies + repo awareness
│       ├── validation_worker/  # GitHub Actions integration
│       ├── toc_integration/    # Master TOC updates
│       ├── hermes_comment_listener/  # Hermes router with question classification
│       └── hermes_capabilities/      # MCP toolbox + skill pipeline orchestration
├── kanboard-mcp/          # MCP Server for Claude integration
├── kanboard-ui/           # React frontend with dnd-kit
├── mobile/                # React Native mobile app
├── shared/                # Shared types and API client
├── github-worker/         # GitHub Actions validation workflow
└── k8s/                   # Kubernetes manifests
```

## Acceptance Criteria Tracking

All work is tracked via `prd.json` at repo root:
- **Total ACs**: 162
- **Proven**: 159 (98%)
- **Remaining**: 3 (hermes_kanboard_integration UI tests)

Every AC must have:
- Passing test (commit link + test file link)
- Status: `proven` when complete

## Color Scheme

| Color | Hex | Meaning |
|-------|-----|---------|
| Red | `#DC2626` | Failure, serious warning, money loss |
| Yellow | `#F59E0B` | Warning, may impact performance |
| Green | `#10B981` | Success, money making, working |
| Blue | `#2563EB` | Primary brand (dashboard) |
| White | `#FFFFFF` | Background |
| Gold | `#D4AF37` | Accent, highlights |
| Black | `#111827` | Text, borders |

## Agent-in-Comments Feature

Users can @mention agents in story comments:
- `@claude`, `@gemini`, `@codex`, `@corey-coder`
- Agent responds in thread
- `[READY_TO_EXECUTE]` marker requests sandbox execution
- Sandbox results posted back as comments
- Successful runs create PRs automatically

## Commands

```bash
# Backend tests (555 tests)
cd backend && python3 -m pytest scripts/ -v

# MCP server tests
cd kanboard-mcp && npm test

# UI tests
cd kanboard-ui && npm test

# Mobile tests
cd mobile && npm test
```

## Deployment

Kubernetes namespace: `HR-project-tracking`

```bash
kubectl apply -k k8s/
```

## Workflow

1. Create feature branch from `main`
2. Implement with TDD (failing test first)
3. Update `prd.json` ACs to `proven`
4. Push and create PR
5. CI must pass (`build` workflow)
6. Merge to `main`

## Related Resources

- **Master TOC**: https://github.com/AlbrightLaboratories/daxxon-ai-gpu-01/issues/17
- **Corey-coder cluster**: Services in `corey-coder` namespace
- **GPU routing**: Through `corey-router:8081`
