# Root Cause Analysis: Hermes-Kanboard Visibility Issue

**Date:** 2026-10-23
**Investigator:** Claude (via SSH to Mac Mini 172.100.10.21)
**Status:** Complete

## Problem Statement

Hermes can respond when tagged at `https://maestro-kanboard.albrightlab.com/task/17` but does NOT see Kanboard when interacting via the desktop UI.

## Investigation Summary

### Environment

| Component | Details |
|-----------|---------|
| Mac Mini IP | 172.100.10.21 |
| User | a-guy |
| Hermes Gateway | Port 8642 |
| Kanboard URL | http://172.100.10.235:30088 (internal) |
| Kanboard Public | https://maestro-kanboard.albrightlab.com |

### Components Verified Working

1. **Kanboard API Connectivity**
   ```bash
   ~/.local/bin/kanboard-api getVersion
   # Returns: {"jsonrpc":"2.0","result":"v1.2.36","id":1}
   ```

2. **Credentials**
   - Location: `~/.config/kanboard/credentials`
   - Contains: KANBOARD_URL, KANBOARD_USER, KANBOARD_TOKEN
   - Status: Valid (API calls succeed)

3. **Kanboard Plugin**
   - Location: `~/.hermes/plugins/kanboard/`
   - Files: `__init__.py`, `plugin.yaml`
   - Status: Loads successfully per agent.log

4. **Kanboard Tool**
   ```bash
   hermes tools list | grep kanboard
   # ✓ enabled  kanboard  🔌 Kanboard
   ```

5. **Kanboard Skill**
   - Location: `~/.hermes/skills/kanboard/SKILL.md`
   - Triggers: kanboard, maestro-kanboard, board status, etc.

## Root Causes

### RC-1: Tool Search Tiering (Primary)

The agent logs show:
```
tool_search activated (tier 1): 18 core/visible tools kept, 8 deferred (~5640 tokens)
```

The kanboard tool may not be in the "visible" tier when the user asks generic questions. Tool visibility is dynamic per turn.

**Impact:** Kanboard tool not presented to the model, so it can't be invoked.

### RC-2: Skill Trigger Mismatch

The skill triggers are:
```yaml
triggers:
  - kanboard
  - do you see our kanboard
  - what's on the board
  - show my tasks
  - maestro-kanboard
```

User queries like "does it see the kanboard" or "check the board" may not match these exact triggers.

**Impact:** Skill not activated, no context provided to model.

### RC-3: Desktop Session Issues

Desktop logs show:
```
Gateway ticket control socket missing
session_busy
revision_conflict
```

The desktop UI has intermittent connectivity issues with the gateway.

**Impact:** Tool calls may fail silently or session state may be inconsistent.

### RC-4: Context Gap

When tagged at `/task/17`, Hermes receives:
- Task title and description
- Project context
- Kanboard URL in the mention

From the desktop UI, none of this context is present.

**Impact:** Model lacks signals to invoke kanboard tool/skill.

## Evidence

### Agent Log (tool_search)
```
2026-10-23 07:47:24,335 INFO tools.tool_search: tool_search activated (tier 1):
  18 core/visible tools kept, 8 deferred (~5640 tokens)
```

### Agent Log (plugin load)
```
2026-10-23 07:47:20,790 INFO hermes_cli.plugin_capabilities:
  capability_check plugin=kanboard capability=tools.override decision=deny
2026-10-23 07:47:20,793 INFO hermes_plugins.kanboard: kanboard plugin loaded
```

### Desktop Log (session errors)
```
2026-10-23 07:47:09,416 Error: Gateway ticket control socket missing
```

## Recommendations

### Fix 1: Pin Kanboard Tool as Always-Visible

Modify the plugin to request `tools.always_visible` or configure tool_search to always include kanboard.

### Fix 2: Expand Skill Triggers

Add more natural language triggers to the skill:
```yaml
triggers:
  - kanboard
  - maestro-kanboard
  - the board
  - our board
  - project board
  - check kanboard
  - see kanboard
  - access kanboard
  - albrightlab.com board
  - HR project tracking
```

### Fix 3: Add Plugin Capability Declarations

Update `plugin.yaml`:
```yaml
manifest_version: 1
name: kanboard
version: 1.0.1
capabilities_required:
  - tools.always_visible
provides_tools:
  - kanboard
```

### Fix 4: Create Explicit Instruction in System Prompt

Add to Hermes configuration:
```
When the user asks about projects, tasks, cards, boards, or mentions
kanboard/maestro-kanboard, ALWAYS use the kanboard tool first.
```

## Next Steps

1. Implement Fix 2 (expand triggers) - lowest risk, immediate impact
2. Implement Fix 4 (system prompt) - medium effort
3. Investigate Fix 1/3 (tool visibility) - requires Hermes internals knowledge
4. Monitor desktop session errors - may require Hermes update

## Related Files

- `~/.hermes/plugins/kanboard/__init__.py`
- `~/.hermes/plugins/kanboard/plugin.yaml`
- `~/.hermes/skills/kanboard/SKILL.md`
- `~/.config/kanboard/credentials`
- `~/.local/bin/kanboard-api`
