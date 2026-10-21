# QA Checklist - Kanboard AlbrightLabs

**Generated:** 2026-10-21
**PRD Version:** 1.0.0
**Total ACs:** 118 | **Proven:** 103 | **Unproven:** 15

## Summary by Module

| Module | Total | PASS | FAIL | Status |
|--------|-------|------|------|--------|
| kanboard_client | 7 | 7 | 0 | GREEN |
| dependency_graph | 8 | 8 | 0 | GREEN |
| maestro_api | 9 | 9 | 0 | GREEN |
| worker_registry | 22 | 22 | 0 | GREEN |
| skill_framework | 10 | 10 | 0 | GREEN |
| validation_worker | 8 | 8 | 0 | GREEN |
| toc_integration | 4 | 4 | 0 | GREEN |
| kanboard-mcp | 8 | 8 | 0 | GREEN |
| kanboard-ui | 14 | 14 | 0 | GREEN |
| github-worker | 5 | 5 | 0 | GREEN |
| mobile | 10 | 0 | 10 | PENDING |
| shared | 5 | 0 | 5 | PENDING |
| agent-in-comments | 8 | 8 | 0 | GREEN |

---

## Detailed Checklist

### Module: kanboard_client (7/7)

| AC ID | Description | Test | Status | Proof |
|-------|-------------|------|--------|-------|
| KC-01 | JSON-RPC client connects and authenticates | test_client_auth.py | PASS | edb9538 |
| KC-02 | create_story() creates story in Backlog | test_create_story.py | PASS | eaa7b77 |
| KC-03 | move_story() moves between columns | test_move_story.py | PASS | e57c08d |
| KC-04 | list_stories() filters by column/project | test_list_stories.py | PASS | e57c08d |
| KC-05 | update_story() modifies fields | test_update_story.py | PASS | e57c08d |
| KC-06 | API timeout returns retry-able error | test_client_timeout.py | PASS | e57c08d |
| KC-07 | Invalid story ID returns 404 | test_invalid_story.py | PASS | e57c08d |

### Module: dependency_graph (8/8)

| AC ID | Description | Test | Status | Proof |
|-------|-------------|------|--------|-------|
| DG-01 | add_dependency() creates relationship | test_add_dependency.py | PASS | f39bab9 |
| DG-02 | get_graph() returns dependency tree | test_get_graph.py | PASS | f39bab9 |
| DG-03 | Circular dependency detected | test_circular_detect.py | PASS | f39bab9 |
| DG-04 | Blocked story cannot be claimed | test_blocked_claim.py | PASS | f39bab9 |
| DG-05 | Blocker completion unblocks stories | test_unblock.py | PASS | f39bab9 |
| DG-06 | find_repo() returns repo info | test_find_repo.py | PASS | f39bab9 |
| DG-07 | affected_files() discovers files | test_affected_files.py | PASS | f39bab9 |
| DG-08 | Cross-repo story links repos | test_cross_repo.py | PASS | f39bab9 |

### Module: maestro_api (9/9)

| AC ID | Description | Test | Status | Proof |
|-------|-------------|------|--------|-------|
| MA-01 | POST /agents/register returns agent_id | test_agent_register.py | PASS | 8b751e7 |
| MA-02 | GET /agents/{id}/heartbeat updates status | test_heartbeat.py | PASS | 8b751e7 |
| MA-03 | GET /stories/available returns unblocked | test_available_stories.py | PASS | 8b751e7 |
| MA-04 | POST /stories/{id}/claim prevents double-claim | test_claim_story.py | PASS | 8b751e7 |
| MA-05 | GET /stories/{id}/prompt returns structured | test_story_prompt.py | PASS | 8b751e7 |
| MA-06 | POST /stories/{id}/progress broadcasts | test_progress_update.py | PASS | 8b751e7 |
| MA-07 | WebSocket /stream delivers real-time | test_websocket_stream.py | PASS | 8b751e7 |
| MA-08 | Agent timeout marks stale | test_agent_timeout.py | PASS | 8b751e7 |
| MA-09 | Rate limiting returns 429 | test_rate_limit.py | PASS | 8b751e7 |

### Module: worker_registry (22/22)

| AC ID | Description | Test | Status | Proof |
|-------|-------------|------|--------|-------|
| WR-01 | register_worker() returns worker_id | test_register_worker.py | PASS | 313ed06 |
| WR-02 | list_workers() returns all workers | test_list_workers.py | PASS | 313ed06 |
| WR-03 | update_worker() modifies labels | test_update_worker.py | PASS | 313ed06 |
| WR-04 | deactivate_worker() marks offline | test_deactivate_worker.py | PASS | 313ed06 |
| WR-05 | delete_worker() removes and reassigns | test_delete_worker.py | PASS | 313ed06 |
| WR-06 | Heartbeat updates timestamp | test_heartbeat.py | PASS | 313ed06 |
| WR-07 | 3 missed heartbeats marks offline | test_missed_heartbeat.py | PASS | 313ed06 |
| WR-08 | Router matches worker_labels | test_label_matching.py | PASS | 313ed06 |
| WR-09 | Router respects preferred_worker | test_preferred_worker.py | PASS | 313ed06 |
| WR-10 | Router excludes excluded_workers | test_excluded_workers.py | PASS | 313ed06 |
| WR-11 | Router falls back to capable worker | test_fallback_routing.py | PASS | 313ed06 |
| WR-12 | Load balancer routes to lowest load | test_load_balancing.py | PASS | 313ed06 |
| WR-13 | GPU-aware routing checks VRAM | test_gpu_routing.py | PASS | 313ed06 |
| WR-14 | Ollama adapter works | test_ollama_adapter.py | PASS | 313ed06 |
| WR-15 | vLLM adapter works | test_vllm_adapter.py | PASS | 313ed06 |
| WR-16 | MCP adapter works | test_mcp_adapter.py | PASS | 313ed06 |
| WR-17 | Sandbox executes in Docker | test_sandbox_docker.py | PASS | 313ed06 |
| WR-18 | Sandbox captures stdout/stderr/exit | test_sandbox_output.py | PASS | 313ed06 |
| WR-19 | Sandbox enforces resource limits | test_sandbox_limits.py | PASS | 313ed06 |
| WR-20 | Sandbox mounts source read-only | test_sandbox_mounts.py | PASS | 313ed06 |
| WR-21 | Kubernetes sandbox runs as Job | test_sandbox_k8s.py | PASS | 313ed06 |
| WR-22 | Worker credentials from k8s secret | test_credentials.py | PASS | 313ed06 |

### Module: skill_framework (10/10)

| AC ID | Description | Test | Status | Proof |
|-------|-------------|------|--------|-------|
| SF-01 | skill_runner executes in order | test_skill_order.py | PASS | ba6067c |
| SF-02 | Skill gate blocks In Progress->Validation | test_skill_gate_block.py | PASS | ba6067c |
| SF-03 | Skill gate blocks Validation->Done | test_validation_gate.py | PASS | ba6067c |
| SF-04 | Failed skill allows retry | test_skill_failure.py | PASS | ba6067c |
| SF-05 | /plan generates steps | test_plan_skill.py | PASS | ba6067c |
| SF-06 | /design-a-prd decomposes | test_prd_skill.py | PASS | ba6067c |
| SF-07 | /tdd generates failing tests | test_tdd_skill.py | PASS | ba6067c |
| SF-08 | /prove-it runs validation | test_prove_it_skill.py | PASS | ba6067c |
| SF-09 | /release-it creates release | test_release_it_skill.py | PASS | ba6067c |
| SF-10 | Skill output stored/retrieved | test_skill_output.py | PASS | ba6067c |

### Module: validation_worker (8/8)

| AC ID | Description | Test | Status | Proof |
|-------|-------------|------|--------|-------|
| VW-01 | Story triggers GitHub workflow | test_validation_trigger.py | PASS | f8544b9 |
| VW-02 | Workflow checks out correct branch | test_checkout.py | PASS | f8544b9 |
| VW-03 | prove-it passes on green tests | test_prove_it_pass.py | PASS | f8544b9 |
| VW-04 | prove-it fails with log | test_prove_it_fail.py | PASS | f8544b9 |
| VW-05 | Result posted to Kanboard API | test_result_post.py | PASS | f8544b9 |
| VW-06 | Failed validation moves to In Progress | test_rework_flow.py | PASS | f8544b9 |
| VW-07 | Failed story carries comments | test_failure_comments.py | PASS | f8544b9 |
| VW-08 | Passed validation moves to Done | test_validation_done.py | PASS | f8544b9 |

### Module: toc_integration (4/4)

| AC ID | Description | Test | Status | Proof |
|-------|-------------|------|--------|-------|
| TI-01 | Story completion posts to issue #17 | test_toc_comment.py | PASS | dfe4614 |
| TI-02 | Comment includes story/commits | test_comment_format.py | PASS | dfe4614 |
| TI-03 | Commit subjects follow TOC format | test_commit_format.py | PASS | dfe4614 |
| TI-04 | gh CLI auth works from cluster | test_gh_auth.py | PASS | dfe4614 |

### Module: kanboard-mcp (8/8)

| AC ID | Description | Test | Status | Proof |
|-------|-------------|------|--------|-------|
| MCP-01 | MCP server starts and registers | mcp_start.test.ts | PASS | b8bf88e |
| MCP-02 | kanboard_create_story creates | create_story.test.ts | PASS | b8bf88e |
| MCP-03 | kanboard_claim_story claims | claim_story.test.ts | PASS | b8bf88e |
| MCP-04 | kanboard_get_story_prompt works | get_prompt.test.ts | PASS | b8bf88e |
| MCP-05 | kanboard_execute_skill triggers | execute_skill.test.ts | PASS | b8bf88e |
| MCP-06 | kanboard_submit_for_validation | submit_validation.test.ts | PASS | b8bf88e |
| MCP-07 | kanboard_rework_story works | rework_story.test.ts | PASS | b8bf88e |
| MCP-08 | Error handling for API down | api_down.test.ts | PASS | b8bf88e |

### Module: kanboard-ui (14/14)

| AC ID | Description | Test | Status | Proof |
|-------|-------------|------|--------|-------|
| UI-01 | Board renders draggable cards | Board.test.tsx | PASS | 7e99995 |
| UI-02 | Drag-and-drop calls API | Board.test.tsx | PASS | 7e99995 |
| UI-03 | Story modal shows JIRA fields | StoryModal.test.tsx | PASS | 7e99995 |
| UI-04 | SkillTracker shows progress | SkillTracker.test.tsx | PASS | 7e99995 |
| UI-05 | SkillTracker blocks Done | SkillTracker.test.tsx | PASS | 7e99995 |
| UI-06 | AgentStatus shows heartbeat | AgentStatus.test.tsx | PASS | 7e99995 |
| UI-07 | ValidationResult shows pass/fail | ValidationResult.test.tsx | PASS | 7e99995 |
| UI-08 | ReworkButton triggers flow | ReworkButton.test.tsx | PASS | 7e99995 |
| UI-09 | Dependency graph renders | DependencyGraph.test.tsx | PASS | 7e99995 |
| UI-10 | Mobile swipe between columns | MobileBoard.test.tsx | PASS | 7e99995 |
| UI-11 | WorkerList shows health | WorkerList.test.tsx | PASS | 7e99995 |
| UI-12 | WorkerRegistration validates | WorkerRegistration.test.tsx | PASS | 7e99995 |
| UI-13 | StoryWorkerPicker sets labels | StoryWorkerPicker.test.tsx | PASS | 7e99995 |
| UI-14 | WorkerAssignment allows change | WorkerAssignment.test.tsx | PASS | 7e99995 |

### Module: github-worker (5/5)

| AC ID | Description | Test | Status | Proof |
|-------|-------------|------|--------|-------|
| GW-01 | Workflow_dispatch with inputs | kanboard-validation.yml | PASS | 5808ff2 |
| GW-02 | Checkout succeeds | kanboard-validation.yml | PASS | 5808ff2 |
| GW-03 | prove-it captures exit code | run_prove_it.sh | PASS | 5808ff2 |
| GW-04 | Results posted via Python | report_results.py | PASS | 5808ff2 |
| GW-05 | Runs on albright-runners | kanboard-validation.yml | PASS | 5808ff2 |

### Module: mobile (0/10) - PENDING

| AC ID | Description | Test | Status | Proof |
|-------|-------------|------|--------|-------|
| MOB-01 | React Native project initializes | setup_test | PENDING | - |
| MOB-02 | BoardScreen with swipe navigation | BoardScreen.test.tsx | PENDING | - |
| MOB-03 | StoryCard displays info | StoryCard.test.tsx | PENDING | - |
| MOB-04 | AgentComments @mentions | AgentComments.test.tsx | PENDING | - |
| MOB-05 | Color scheme red/yellow/green | colors.test.ts | PENDING | - |
| MOB-06 | Dashboard blue/white/gold/black | theme.test.ts | PENDING | - |
| MOB-07 | Pull-to-refresh works | BoardScreen.test.tsx | PENDING | - |
| MOB-08 | Story modal opens | StoryModal.test.tsx | PENDING | - |
| MOB-09 | Offline mode caches | offline.test.ts | PENDING | - |
| MOB-10 | Push notifications | notifications.test.ts | PENDING | - |

### Module: shared (0/5) - PENDING

| AC ID | Description | Test | Status | Proof |
|-------|-------------|------|--------|-------|
| SH-01 | Shared types export interfaces | types.test.ts | PENDING | - |
| SH-02 | KanboardApi client cross-platform | api.test.ts | PENDING | - |
| SH-03 | Standardized response types | responses.test.ts | PENDING | - |
| SH-04 | Error codes include retryable | responses.test.ts | PENDING | - |
| SH-05 | Structured logging helper | responses.test.ts | PENDING | - |

### Module: agent-in-comments (8/8)

| AC ID | Description | Test | Status | Proof |
|-------|-------------|------|--------|-------|
| AIC-01 | @agent mention triggers notification | test_mention_trigger.py | PASS | 9101b95 |
| AIC-02 | Agent receives context | test_context_extraction.py | PASS | 9101b95 |
| AIC-03 | Agent response posted with badge | test_response_posting.py | PASS | 9101b95 |
| AIC-04 | [READY_TO_EXECUTE] marker works | test_execution_request.py | PASS | 9101b95 |
| AIC-05 | User approval triggers sandbox | test_sandbox_trigger.py | PASS | 9101b95 |
| AIC-06 | Sandbox results posted | test_sandbox_results.py | PASS | 9101b95 |
| AIC-07 | Successful sandbox creates PR | test_pr_creation.py | PASS | 9101b95 |
| AIC-08 | WebSocket broadcasts responses | test_websocket_broadcast.py | PASS | 9101b95 |

---

## Test Execution Summary

**Backend Tests:** 555 passed in 1.34s

```
pytest backend/scripts/ -v --tb=short
============================= 555 passed in 1.34s ==============================
```

## Deployment Ready

Repository: https://github.com/AlbrightLaboratories/kanboard_albrightLabs

**Status:** Ready for cluster deployment. 103/118 ACs proven. Mobile and shared modules pending (awaiting React Native setup).
