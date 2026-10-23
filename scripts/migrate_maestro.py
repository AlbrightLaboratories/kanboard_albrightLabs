#!/usr/bin/env python3
"""
Migrate projects and work items from Maestro PostgreSQL to Kanboard.

Usage:
  python migrate_maestro.py

Environment:
  KANBOARD_URL: URL of Kanboard instance (default: http://172.100.10.98:30088)
  KANBOARD_USER: Kanboard admin user (default: admin)
  KANBOARD_PASSWORD: Kanboard admin password (default: admin)
"""

import json
import os
import subprocess
import sys
import time
from typing import Any

# Delay between API calls to avoid SQLite locking
API_DELAY = 0.5  # seconds

# Kanboard connection
KANBOARD_URL = os.getenv("KANBOARD_URL", "http://172.100.10.98:30088")
KANBOARD_USER = os.getenv("KANBOARD_USER", "admin")
KANBOARD_PASSWORD = os.getenv("KANBOARD_PASSWORD", "admin")

# Column mapping: Maestro status -> Kanboard column
STATUS_TO_COLUMN = {
    "backlog": "Backlog",
    "in_progress": "In Progress",
    "done": "Done",
    "blocked": "Validation",  # Use Validation for blocked items
}

# Priority mapping: Maestro priority -> Kanboard priority (1=low, 3=high)
PRIORITY_MAP = {
    "P1": 3,
    "P2": 2,
    "P3": 1,
}


def kanboard_rpc(method: str, params: dict = None) -> Any:
    """Call Kanboard JSON-RPC API."""
    import urllib.request
    import base64

    payload = {
        "jsonrpc": "2.0",
        "method": method,
        "id": 1,
        "params": params or {}
    }

    auth = base64.b64encode(f"{KANBOARD_USER}:{KANBOARD_PASSWORD}".encode()).decode()

    req = urllib.request.Request(
        f"{KANBOARD_URL}/jsonrpc.php",
        data=json.dumps(payload).encode(),
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Basic {auth}"
        }
    )

    with urllib.request.urlopen(req, timeout=30) as resp:
        result = json.loads(resp.read().decode())
        if "error" in result:
            raise Exception(f"Kanboard API error: {result['error']}")
        time.sleep(API_DELAY)  # Delay to avoid SQLite locking
        return result.get("result")


def get_maestro_projects() -> list:
    """Fetch projects from Maestro PostgreSQL via kubectl."""
    cmd = [
        "kubectl", "exec", "-n", "albrightlabs-dot-com",
        "postgres-7bfdc879b8-fxj6x", "--",
        "psql", "-U", "postgres", "-d", "albright", "-t", "-A", "-F", "|",
        "-c", "SELECT id, name, description FROM maestro.projects;"
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)

    projects = []
    for line in result.stdout.strip().split("\n"):
        if line:
            parts = line.split("|")
            if len(parts) >= 2:
                projects.append({
                    "id": parts[0],
                    "name": parts[1],
                    "description": parts[2] if len(parts) > 2 else ""
                })
    return projects


def get_maestro_work_items() -> list:
    """Fetch work items from Maestro PostgreSQL via kubectl."""
    cmd = [
        "kubectl", "exec", "-n", "albrightlabs-dot-com",
        "postgres-7bfdc879b8-fxj6x", "--",
        "psql", "-U", "postgres", "-d", "albright", "-t", "-A", "-F", "|",
        "-c", "SELECT id, project_id, title, description, status, priority FROM maestro.work_items;"
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)

    items = []
    for line in result.stdout.strip().split("\n"):
        if line:
            parts = line.split("|")
            if len(parts) >= 4:
                items.append({
                    "id": parts[0],
                    "project_id": parts[1],
                    "title": parts[2],
                    "description": parts[3] if len(parts) > 3 else "",
                    "status": parts[4] if len(parts) > 4 else "backlog",
                    "priority": parts[5] if len(parts) > 5 else "P3",
                })
    return items


def create_kanboard_project(name: str, description: str = "") -> int:
    """Create a project in Kanboard, return project ID."""
    # Check if project already exists
    projects = kanboard_rpc("getAllProjects")
    for p in projects:
        if p["name"] == name:
            print(f"  Project '{name}' already exists (ID: {p['id']})")
            return int(p["id"])

    # Create new project
    project_id = kanboard_rpc("createProject", {"name": name, "description": description})
    print(f"  Created project '{name}' (ID: {project_id})")
    return project_id


def create_kanboard_task(
    project_id: int,
    title: str,
    description: str = "",
    priority: int = 1,
    maestro_id: str = ""
) -> int:
    """Create a task in Kanboard, return task ID."""
    # Add maestro ID reference to description
    if maestro_id:
        description = f"[Migrated from Maestro: {maestro_id}]\n\n{description}"

    # Create task - Kanboard will put it in the first column (Backlog) by default
    task_id = kanboard_rpc("createTask", {
        "project_id": project_id,
        "title": title,
        "description": description,
        "priority": priority,
    })

    print(f"    Created task '{title[:50]}...'")
    return task_id


def main():
    print("=" * 60)
    print("Maestro to Kanboard Migration")
    print("=" * 60)

    # Test Kanboard connection
    print("\n[1/4] Testing Kanboard connection...")
    try:
        version = kanboard_rpc("getVersion")
        print(f"  Connected to Kanboard {version}")
    except Exception as e:
        print(f"  ERROR: Cannot connect to Kanboard: {e}")
        sys.exit(1)

    # Fetch Maestro data
    print("\n[2/4] Fetching Maestro projects...")
    projects = get_maestro_projects()
    print(f"  Found {len(projects)} projects")

    print("\n[3/4] Fetching Maestro work items...")
    work_items = get_maestro_work_items()
    print(f"  Found {len(work_items)} work items")

    # Create mapping of Maestro project ID -> Kanboard project ID
    print("\n[4/4] Migrating to Kanboard...")
    project_map = {}  # maestro_id -> kanboard_id

    for project in projects:
        kb_project_id = create_kanboard_project(
            name=project["name"],
            description=project.get("description", "")
        )
        project_map[project["id"]] = kb_project_id

    # Migrate work items
    print("\n  Migrating work items...")
    migrated = 0
    skipped = 0

    for item in work_items:
        maestro_project_id = item["project_id"]
        if maestro_project_id not in project_map:
            print(f"    SKIP: No project mapping for {maestro_project_id}")
            skipped += 1
            continue

        kb_project_id = project_map[maestro_project_id]
        priority = PRIORITY_MAP.get(item.get("priority", "P3"), 1)

        create_kanboard_task(
            project_id=kb_project_id,
            title=item["title"],
            description=item.get("description", ""),
            priority=priority,
            maestro_id=item["id"]
        )
        migrated += 1

    print("\n" + "=" * 60)
    print("Migration Complete!")
    print(f"  Projects: {len(projects)}")
    print(f"  Tasks migrated: {migrated}")
    print(f"  Tasks skipped: {skipped}")
    print("=" * 60)


if __name__ == "__main__":
    main()
