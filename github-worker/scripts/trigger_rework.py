#!/usr/bin/env python3
"""
trigger_rework.py - Move failed story back to In Progress for rework

This script is called when validation fails. It:
1. Moves the story back to "In Progress" column
2. Posts a comment with failure details
3. Notifies any assigned agent that rework is needed
"""

import argparse
import json
import os
import sys
from datetime import datetime, timezone

try:
    import requests
except ImportError:
    print("ERROR: requests module not installed")
    sys.exit(1)


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description='Trigger rework flow for failed validation'
    )
    parser.add_argument(
        '--story-id',
        required=True,
        help='Story ID that failed validation'
    )
    parser.add_argument(
        '--failures',
        required=False,
        default='',
        help='Failure details (newline-separated)'
    )
    parser.add_argument(
        '--api-url',
        required=False,
        default=os.environ.get(
            'KANBOARD_API_URL',
            'http://kanboard.hr-project-tracking.svc.cluster.local/api'
        ),
        help='Kanboard API URL'
    )
    return parser.parse_args()


def trigger_rework(story_id: str, failures: str, api_url: str) -> bool:
    """
    Trigger rework flow for a failed story.

    Args:
        story_id: The story that failed validation
        failures: Failure details
        api_url: Kanboard API endpoint

    Returns:
        True if successful, False otherwise
    """
    timestamp = datetime.now(timezone.utc).isoformat()

    # Build rework request
    payload = {
        "story_id": story_id,
        "action": "rework",
        "timestamp": timestamp,
        "comment": f"Validation failed. Rework needed.\n\nFailures:\n{failures}"
    }

    # Post to Maestro API
    rework_url = f"{api_url.replace('/api', '/maestro/stories')}/{story_id}/rework"

    try:
        print(f"Triggering rework for story: {story_id}")

        response = requests.post(
            rework_url,
            json=payload,
            headers={'Content-Type': 'application/json'},
            timeout=30
        )

        if response.status_code in [200, 201, 204]:
            print("Rework triggered successfully")
            return True
        else:
            print(f"API returned status {response.status_code}")

    except Exception as e:
        print(f"Error triggering rework: {e}")

    return False


def main():
    """Main entry point."""
    args = parse_args()

    print("=" * 60)
    print("Rework Trigger")
    print("=" * 60)
    print(f"Story ID: {args.story_id}")
    print("=" * 60)

    success = trigger_rework(
        story_id=args.story_id,
        failures=args.failures,
        api_url=args.api_url
    )

    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
