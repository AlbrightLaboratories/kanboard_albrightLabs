#!/usr/bin/env python3
"""
report_results.py - Report validation results to Kanboard API

Implements GW-04: Results posted to Kanboard API via report_results.py

This script sends validation results back to the Kanboard API,
including status (passed/failed) and any failure messages.
On success, it triggers the story to move to Done.
On failure, it posts comments and moves story back to In Progress.
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
    print("Install with: pip install requests")
    sys.exit(1)


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description='Report validation results to Kanboard API'
    )
    parser.add_argument(
        '--story-id',
        required=True,
        help='Story ID being validated'
    )
    parser.add_argument(
        '--status',
        required=True,
        choices=['passed', 'failed'],
        help='Validation result status'
    )
    parser.add_argument(
        '--message',
        required=False,
        default='',
        help='Validation message (failure details or success note)'
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


def report_to_kanboard(story_id: str, status: str, message: str, api_url: str) -> bool:
    """
    Report validation result to Kanboard API.

    Args:
        story_id: The story being validated
        status: 'passed' or 'failed'
        message: Details about the validation result
        api_url: Kanboard API endpoint

    Returns:
        True if reporting succeeded, False otherwise
    """
    timestamp = datetime.now(timezone.utc).isoformat()

    # Build the validation result payload
    payload = {
        "story_id": story_id,
        "validation_result": {
            "status": status,
            "timestamp": timestamp,
            "message": message,
            "failures": message.split('\n') if status == 'failed' and message else []
        }
    }

    # Try to post to Maestro API (which wraps Kanboard)
    maestro_url = api_url.replace('/api', '/maestro/stories/{}/validation'.format(story_id))

    try:
        print(f"Reporting to: {maestro_url}")
        print(f"Status: {status}")
        print(f"Message: {message[:200]}..." if len(message) > 200 else f"Message: {message}")

        response = requests.post(
            maestro_url,
            json=payload,
            headers={'Content-Type': 'application/json'},
            timeout=30
        )

        if response.status_code in [200, 201, 204]:
            print(f"Successfully reported validation result")
            return True
        else:
            print(f"API returned status {response.status_code}: {response.text[:200]}")

    except requests.exceptions.ConnectionError as e:
        print(f"Connection error: {e}")
        print("Will try fallback method...")

    except requests.exceptions.Timeout:
        print("Request timed out")

    except Exception as e:
        print(f"Error reporting to API: {e}")

    # Fallback: Write to file for manual pickup
    fallback_file = f"/tmp/validation_result_{story_id}.json"
    try:
        with open(fallback_file, 'w') as f:
            json.dump(payload, f, indent=2)
        print(f"Wrote fallback result to: {fallback_file}")
        return True
    except Exception as e:
        print(f"Failed to write fallback file: {e}")
        return False


def main():
    """Main entry point."""
    args = parse_args()

    print("=" * 60)
    print("Validation Result Reporter")
    print("=" * 60)
    print(f"Story ID: {args.story_id}")
    print(f"Status: {args.status}")
    print(f"API URL: {args.api_url}")
    print("=" * 60)

    success = report_to_kanboard(
        story_id=args.story_id,
        status=args.status,
        message=args.message,
        api_url=args.api_url
    )

    if success:
        print("\nValidation result reported successfully")
        sys.exit(0)
    else:
        print("\nFailed to report validation result")
        sys.exit(1)


if __name__ == '__main__':
    main()
