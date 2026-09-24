#!/usr/bin/env python3
"""CLI for Pathly GitLab CI components: ping | ensure-scenario."""

from __future__ import annotations

import argparse
import json
import os
import sys

from pathly_api import PathlyClient, PathlyError, client_from_env


def cmd_ping(client: PathlyClient) -> int:
    result = client.ping()
    print(json.dumps(result))
    print("Pathly token verified.", file=sys.stderr)
    return 0


def cmd_ensure_scenario(client: PathlyClient, scenario_json: str) -> int:
    body = json.loads(scenario_json)
    if not isinstance(body, dict) or "name" not in body or "url" not in body:
        raise SystemExit('scenario JSON must be an object with "name" and "url"')
    result = client.ensure_scenario(body)
    scenario = result["scenario"]
    print(
        json.dumps(
            {
                "id": scenario.get("id"),
                "name": scenario.get("name"),
                "created": result["created"],
            }
        )
    )
    action = "Created" if result["created"] else "Ensured"
    print(f"{action} Pathly scenario {scenario.get('id')}", file=sys.stderr)
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Pathly GitLab CI helper")
    p.add_argument(
        "command",
        choices=["ping", "ensure-scenario"],
        help="Operation to run",
    )
    p.add_argument(
        "--scenario-json",
        default=os.environ.get("PATHLY_SCENARIO_JSON", ""),
        help="JSON body for ensure-scenario (or PATHLY_SCENARIO_JSON)",
    )
    p.add_argument(
        "--api-token",
        default="",
        help="Override PATHLY_API_TOKEN",
    )
    p.add_argument(
        "--api-url",
        default="",
        help="Override PATHLY_API_URL",
    )
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.api_token:
        os.environ["PATHLY_API_TOKEN"] = args.api_token
    if args.api_url:
        os.environ["PATHLY_API_URL"] = args.api_url

    try:
        client = client_from_env()
        if args.command == "ping":
            return cmd_ping(client)
        return cmd_ensure_scenario(client, args.scenario_json)
    except PathlyError as e:
        print(f"Pathly error: {e.message} (HTTP {e.status})", file=sys.stderr)
        return 1
    except (ValueError, json.JSONDecodeError) as e:
        print(f"Pathly helper error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
