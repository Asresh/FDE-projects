"""Command-line interface for scanning and sharing a deployment profile."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .report import render_html, render_json, render_markdown
from .scanner import ProfileError, SEVERITY_ORDER, scan_profile


RENDERERS = {"json": render_json, "markdown": render_markdown, "html": render_html}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="boundarycheck", description="Review an AI deployment profile before launch.")
    subparsers = parser.add_subparsers(dest="command", required=True)
    scan = subparsers.add_parser("scan", help="scan a local JSON deployment profile")
    scan.add_argument("profile", type=Path, help="path to a customer deployment profile")
    scan.add_argument("--format", choices=sorted(RENDERERS), default="markdown")
    scan.add_argument("--output", type=Path, help="write report to a file instead of stdout")
    scan.add_argument("--fail-on", choices=["critical", "high", "medium", "low", "never"], default="critical",
                      help="exit with code 1 if this severity or higher appears (default: critical)")
    args = parser.parse_args(argv)
    try:
        profile = json.loads(args.profile.read_text(encoding="utf-8"))
        result = scan_profile(profile)
    except FileNotFoundError:
        print(f"Profile not found: {args.profile}", file=sys.stderr)
        return 2
    except json.JSONDecodeError as exc:
        print(f"Invalid JSON in {args.profile}: {exc}", file=sys.stderr)
        return 2
    except (OSError, ProfileError) as exc:
        print(f"Cannot scan profile: {exc}", file=sys.stderr)
        return 2

    rendered = RENDERERS[args.format](result)
    try:
        if args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(rendered, encoding="utf-8")
            print(f"Report written to {args.output}")
            print(f"{result['status']} · score {result['score']}/100 · {result['finding_count']} finding(s)")
        else:
            print(rendered, end="")
    except OSError as exc:
        print(f"Cannot write report: {exc}", file=sys.stderr)
        return 2

    if args.fail_on != "never":
        threshold = SEVERITY_ORDER[args.fail_on.upper()]
        if any(SEVERITY_ORDER[item["severity"]] >= threshold for item in result["findings"]):
            return 1
    return 0
