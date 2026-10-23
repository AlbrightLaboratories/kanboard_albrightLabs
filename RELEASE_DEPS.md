# Release v1.1.0 Dependency Map

## Components Touched

### Backend Modules
- `hermes_router` — Question classification routing to corey-router (HR-01..HR-15)
- `hermes_capabilities` — MCP toolbox bridge + skill pipeline (HC-01..HC-22)
- `hermes_adapter` — Client updates for model selection
- `agent_comments` — @hermes mention detection and response (AIC-01..AIC-08)
- `model_selector` — Routes GENERAL/CODING/TOOL_REQUIRED questions

### Frontend/Mobile
- `shared` — TypeScript types, KanboardApi client, error handling (SH-01..SH-05)
- `mobile` — React Native app with swipe navigation, offline, notifications (MOB-01..MOB-10)

### Infrastructure
- `k8s/hermes-listener` — COREY_ROUTER_URL env var, poll interval tuning
- `k8s/postgres` — PostgreSQL deployment for Kanboard
- `k8s/kanboard` — Configmap and deployment updates

## Services Affected

| Service | Action | Notes |
|---------|--------|-------|
| hermes-comment-listener | Rolling restart | New routing logic via corey-router |
| corey-router | No change | Upstream dependency (in corey-coder namespace) |
| mcp-hub | No change | NetworkPolicy updated to allow hr-project-tracking |
| kanboard | Rolling restart | PostgreSQL backend config |

## External Dependencies

- `corey-router.corey-coder.svc.cluster.local:8081` — Model routing endpoint
- `mcp-hub.corey-coder.svc.cluster.local:8080` — MCP tool discovery
- `hermes-memory.hermes-tools.svc.cluster.local:8080` — Memory persistence

## Breaking Changes

None. This release is backward compatible.

## Rollback Considerations

1. **If Hermes routing fails**: Revert hermes-comment-listener deployment to v1.0.0 tag
2. **If tests fail post-deploy**: Check `COREY_ROUTER_URL` env var is set
3. **If mobile crashes**: Clear AsyncStorage cache first

## Verified Tests

- Backend: 704 passed
- Shared: 74 passed
- MCP: 86 passed
- Mobile: 93 passed (11 mock limitations in React Native)
- E2E Routing: 23 passed

## PRD Status

- **155/155 acceptance criteria proven (100%)**
- All modules validated with TDD
