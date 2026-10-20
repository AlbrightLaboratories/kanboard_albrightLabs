# GitHub Worker for Kanboard Validation

This module provides GitHub Actions workflows for validating Kanboard stories.

## Overview

When a story enters the "Validation" column, the GitHub worker:
1. Triggers a GitHub Actions workflow via `workflow_dispatch`
2. Checks out the story's linked repository and branch
3. Runs the `prove-it` validation script
4. Reports results back to the Kanboard API
5. Moves the story to Done (on pass) or back to In Progress (on fail)

## Acceptance Criteria

| AC ID | Description | Status |
|-------|-------------|--------|
| GW-01 | Workflow triggered via workflow_dispatch with story_id, repo, branch | proven |
| GW-02 | Checkout succeeds for any AlbrightLaboratories repo | proven |
| GW-03 | prove-it script runs test suite, captures exit code | proven |
| GW-04 | Results posted to Kanboard API via report_results.py | proven |
| GW-05 | Workflow runs on albright-runners (self-hosted) | proven |

## Files

```
github-worker/
├── workflows/
│   └── kanboard-validation.yml   # GitHub Actions workflow
├── scripts/
│   ├── run_prove_it.sh           # Test runner script
│   ├── report_results.py         # API result reporter
│   └── trigger_rework.py         # Rework flow trigger
└── README.md
```

## Usage

### Triggering Validation

The workflow is triggered via `workflow_dispatch` with the following inputs:

```bash
gh workflow run kanboard-validation.yml \
  --repo AlbrightLaboratories/kanboard_albrightLabs \
  -f story_id="123" \
  -f repo="AlbrightLaboratories/my-project" \
  -f branch="feature/my-feature"
```

### Workflow Inputs

| Input | Required | Description |
|-------|----------|-------------|
| `story_id` | Yes | Story ID being validated |
| `repo` | Yes | Repository to validate (owner/repo format) |
| `branch` | Yes | Branch to validate |
| `kanboard_api_url` | No | Kanboard API endpoint (default: cluster internal) |

## prove-it Validation

The `run_prove_it.sh` script performs the following checks:

1. **Test Suite Execution**
   - Detects project type (Python, Node, Rust, Go)
   - Runs appropriate test command
   - Captures exit code

2. **Modularity Constraints**
   - Checks for files exceeding 200 lines of code
   - Reports as warnings (non-blocking)

3. **Coverage Check** (optional)
   - Looks for coverage data
   - Reports if below 70% threshold

## Runner Requirements

The workflow runs on `albright-runners`, which must have:
- Python 3.11+
- Node.js 20+
- Network access to Kanboard API
- Access to AlbrightLaboratories repositories

## Environment Variables

| Variable | Description |
|----------|-------------|
| `KANBOARD_API_URL` | Kanboard API endpoint |
| `GITHUB_TOKEN` | Token for repository access |

## Deployment

To deploy this workflow to a repository:

1. Copy `workflows/kanboard-validation.yml` to `.github/workflows/`
2. Copy `scripts/` to a location accessible to the workflow
3. Ensure `albright-runners` are available
4. Configure Kanboard API access

## Integration with Kanboard

The Kanboard Maestro API triggers this workflow when:
1. A story is moved to the "Validation" column
2. The story has a linked repository and branch

Results are reported back via `report_results.py`, which:
1. Posts validation status to Maestro API
2. On failure, triggers rework flow
3. On success, story moves to Done column

## Local Testing

Test the prove-it script locally:

```bash
cd your-project
../github-worker/scripts/run_prove_it.sh
```

Test result reporting (dry run):

```bash
python scripts/report_results.py \
  --story-id 123 \
  --status passed \
  --message "All tests passed" \
  --api-url "http://localhost:8080/api"
```
