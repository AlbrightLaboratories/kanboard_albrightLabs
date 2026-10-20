# Changelog

All notable changes to Kanboard AlbrightLabs are documented in this file.

## [1.0.0] - 2026-10-20

### Overview
Initial release of Kanboard AlbrightLabs - a hybrid Kanboard system with AI agent orchestration.

**95/95 acceptance criteria PROVEN**

### Architecture
- **Backend**: Modular Python backend with 8 modules
- **Frontend**: React UI with @dnd-kit drag-and-drop
- **MCP Server**: Claude integration via kanboard-mcp
- **GitHub Worker**: Validation workflow via GitHub Actions
- **Deployment**: Kubernetes in HR-project-tracking namespace

### Modules Implemented

#### Backend Modules (Python)

| Module | ACs | Description |
|--------|-----|-------------|
| kanboard_client | 7/7 | JSON-RPC client for Kanboard PHP API |
| dependency_graph | 8/8 | Story dependencies and repo awareness |
| maestro_api | 9/9 | Two-way agent communication (REST + WebSocket) |
| worker_registry | 22/22 | Custom LLM worker management with sandboxing |
| skill_framework | 10/10 | Mandatory skills (plan/prd/tdd/prove-it/release-it) |
| validation_worker | 8/8 | GitHub workflow integration |
| toc_integration | 4/4 | Master TOC updates via gh CLI |

#### Frontend (TypeScript/React)

| Module | ACs | Description |
|--------|-----|-------------|
| kanboard-mcp | 8/8 | MCP Server for Claude integration |
| kanboard-ui | 14/14 | React frontend with full JIRA-like features |

#### GitHub Worker

| Module | ACs | Description |
|--------|-----|-------------|
| github-worker | 5/5 | GitHub Actions for story validation |

### Features

#### Board & Stories
- Drag-and-drop board with columns (Backlog → Groomed → In Progress → Validation → Done)
- Story modal with JIRA-like fields (title, description, assignee, priority, labels)
- Story dependencies with visual graph
- Mobile-responsive with swipe navigation

#### AI Agent Integration
- Multi-agent support (Claude, Gemini, Codex, custom LLMs)
- Agent status monitoring with heartbeat indicator
- Story claiming and prompt extraction
- Progress reporting via WebSocket

#### Custom LLM Workers
- Worker registration with labels and capabilities
- Label-based story routing
- GPU-aware load balancing
- Sandboxed terminal execution (Docker/Kubernetes)
- Adapters: Ollama, vLLM, OpenAI-compatible, MCP

#### Skill Framework
- Mandatory skills: /plan, /design-a-prd, /tdd, /prove-it, /release-it
- Skill gates blocking column transitions
- Skill progress tracking UI

#### Validation
- GitHub Actions workflow for story validation
- prove-it runs tests, checks coverage, verifies modularity
- Automatic rework flow on failure
- Results posted back to Kanboard API

#### Integration
- Master TOC updates on story completion
- GitHub PR/commit linking
- Maestro API for agent communication

### Commits

```
e809cd2 docs(prd): all 95 acceptance criteria proven
5808ff2 feat(GW-01..05): github-worker for Kanboard story validation
7e99995 feat(UI-01..14): kanboard-ui React frontend
b8bf88e feat(kanboard-mcp): MCP Server for Claude integration
dfe4614 feat(toc_integration): TOC integration module
f8544b9 feat(validation_worker): GitHub Actions integration
ba6067c feat(skill_framework): mandatory skills orchestration
313ed06 feat(WR-01-22): worker_registry with LLM adapters
8b751e7 feat(MA-01-09): maestro_api with WebSocket streaming
f39bab9 feat(DG-01..DG-08): dependency_graph module
e57c08d feat(KC-03-07): complete kanboard_client module
```

### Test Coverage

- **Backend**: 271 pytest tests passing
- **kanboard-mcp**: 86 vitest tests passing
- **kanboard-ui**: 185 vitest tests passing
- **Total**: 542 tests

### Deployment

Kubernetes manifests available in `k8s/` for:
- kanboard (PHP backend)
- kanboard-ui (React frontend)
- kanboard-mcp (MCP server)
- backend (Python services)

### Breaking Changes
None (initial release)

### Migration Guide
N/A (initial release)

---

## [Unreleased]

No unreleased changes.
