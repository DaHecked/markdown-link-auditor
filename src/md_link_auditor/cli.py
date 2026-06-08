from __future__ import annotations

import argparse
import json
from dataclasses import asdict

from .core import AuditReport, audit_paths


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Audit Markdown files for broken local links and anchors.")
    parser.add_argument("paths", nargs="+", help="Markdown files or directories to scan")
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON")
    return parser


def _report_to_dict(report: AuditReport) -> dict[str, object]:
    return {"ok": report.ok, "items": [asdict(item) for item in report.items]}


def _print_human(report: AuditReport) -> None:
    if report.ok:
        print("markdown-link-auditor: ok")
    else:
        print("markdown-link-auditor: broken links found")
    for item in report.items:
        print(f"- {item.source}:{item.line} {item.target} -> {item.status}")


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    report = audit_paths(args.paths)
    if args.json:
        print(json.dumps(_report_to_dict(report), indent=2, sort_keys=True))
    else:
        _print_human(report)
    return 0 if report.ok else 1
