<!-- toc-backlink -->
> **Master TOC:** [Org-wide repo index](https://github.com/AlbrightLaboratories/daxxon-ai-gpu-01/issues/17) - auto-updated every 15 min from this repo's commit stream. No manual entry needed; just write commit subjects that read well as one-line bullets.

# Kanboard AlbrightLabs

A hybrid Kanboard system for project tracking with AI agent orchestration.

## Architecture

- **Backend**: Stock Kanboard (PHP) + Custom Python modules
- **Frontend**: React app with dnd-kit for JIRA-like drag-and-drop
- **MCP Server**: Claude integration via MCP protocol
- **Maestro API**: Two-way agent communication (Claude, Gemini, Codex, Custom LLMs)
- **Deployment**: Kubernetes in `HR-project-tracking` namespace

## Workflow Columns

| Column | Purpose |
|--------|---------|
| Backlog | New ideas land here |
| Groomed | Refined with acceptance criteria |
| In Progress | Active development (mandatory skills: plan, design-a-prd, tdd) |
| Validation | TDD/testing phase (mandatory skills: prove-it, release-it) |
| Done | Completed work, Master TOC updated |

## Modules (162 Acceptance Criteria — 98% Proven)

| Module | ACs | Status |
|--------|-----|--------|
| kanboard_client | 7 | ✅ Proven |
| dependency_graph | 8 | ✅ Proven |
| maestro_api | 9 | ✅ Proven |
| worker_registry | 22 | ✅ Proven |
| skill_framework | 10 | ✅ Proven |
| validation_worker | 8 | ✅ Proven |
| toc_integration | 4 | ✅ Proven |
| kanboard-mcp | 8 | ✅ Proven |
| kanboard-ui | 14 | ✅ Proven |
| github-worker | 5 | ✅ Proven |
| mobile | 10 | ✅ Proven |
| shared | 5 | ✅ Proven |
| agent-in-comments | 8 | ✅ Proven |
| hermes_router | 15 | ✅ Proven |
| hermes_capabilities | 22 | ✅ Proven |
| hermes_kanboard_integration | 7 | 🔄 4/7 Proven |

## Quick Start

```bash
# Deploy to Kubernetes
kubectl apply -k k8s/

# Local development
docker-compose up -d
```

## Documentation

- [Architecture](docs/architecture.md)
- [API Reference](docs/api-reference.md)
- [Worker Setup](docs/worker-setup.md)

## PRD Tracking

Acceptance criteria tracked in `prd.json`. Convergence target: 0 unproven ACs.
