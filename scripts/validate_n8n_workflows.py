"""Validate the exported n8n workflow archives.

Checks performed:
  1. every *.json file is valid JSON;
  2. required workflow keys exist (name / nodes / connections);
  3. node ids and node names are unique;
  4. every connection edge points at an existing node;
  5. each workflow contains at least one trigger node;
  6. no real DingTalk access token is committed (placeholder only).

Usage:
    python scripts/validate_n8n_workflows.py
Exit code 0 means all checks passed.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW_DIR = ROOT / "sentiment-project" / "n8n-workflows"
TRIGGER_TYPES = {
    "n8n-nodes-base.webhook",
    "n8n-nodes-base.scheduleTrigger",
    "n8n-nodes-base.manualTrigger",
}
TOKEN_RE = re.compile(r"access_token=(?!YOUR_DINGTALK_ACCESS_TOKEN)[A-Za-z0-9_\-]{8,}")
errors: list[str] = []


def check(path: Path) -> None:
    try:
        wf = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        errors.append(f"{path.name}: invalid JSON -> {exc}")
        return

    for key in ("name", "nodes", "connections"):
        if key not in wf:
            errors.append(f"{path.name}: missing required key '{key}'")
    if errors:
        return

    nodes = wf["nodes"]
    names = [n.get("name") for n in nodes]
    ids = [n.get("id") for n in nodes]
    if len(set(names)) != len(names):
        errors.append(f"{path.name}: duplicate node names {names}")
    if len(set(ids)) != len(ids):
        errors.append(f"{path.name}: duplicate node ids")

    for source, conn in wf["connections"].items():
        if source not in names:
            errors.append(f"{path.name}: connection from unknown node '{source}'")
        for branches in conn.get("main", []):
            for link in branches:
                if link.get("node") not in names:
                    errors.append(
                        f"{path.name}: connection to unknown node '{link.get('node')}'"
                    )

    types = {n.get("type") for n in nodes}
    if not types & TRIGGER_TYPES:
        errors.append(f"{path.name}: no trigger node found")

    raw = path.read_text(encoding="utf-8")
    if TOKEN_RE.search(raw):
        errors.append(f"{path.name}: real DingTalk access token detected")

    print(f"OK  {path.name}: {wf['name']} ({len(nodes)} nodes)")


def main() -> int:
    files = sorted(WORKFLOW_DIR.glob("*.json"))
    if not files:
        print(f"No workflow JSON found in {WORKFLOW_DIR}", file=sys.stderr)
        return 1
    for path in files:
        check(path)
    if errors:
        print("\nValidation failed:", file=sys.stderr)
        for err in errors:
            print(f"  - {err}", file=sys.stderr)
        return 1
    print(f"\nAll {len(files)} workflows passed validation.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
