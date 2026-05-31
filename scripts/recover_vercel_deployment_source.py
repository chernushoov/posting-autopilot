#!/usr/bin/env python3

from __future__ import annotations

import argparse
import base64
import json
import os
import subprocess
import sys
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parent.parent
DEFAULT_DEPLOYMENT_ID = "dpl_6v2xFLQrs5ZZJ3MefEyzzYVMXLxo"
DEFAULT_OUT_DIR = ROOT_DIR / "ops" / "prelaunch_artifacts" / "recovered_live_source"


def extract_json(text: str) -> object:
    for idx, char in enumerate(text):
        if char not in "[{":
            continue
        chunk = text[idx:]
        try:
            return json.loads(chunk)
        except json.JSONDecodeError:
            continue
    raise ValueError("could not find json payload in vercel api output")


def run_vercel_api(endpoint: str) -> object:
    env = os.environ.copy()
    if env.get("POSTING_AUTOPILOT_VERCEL_INSECURE", "1") != "0":
        env["NODE_TLS_REJECT_UNAUTHORIZED"] = "0"
    proc = subprocess.run(
        ["vercel", "api", endpoint],
        cwd=ROOT_DIR,
        text=True,
        capture_output=True,
        env=env,
    )
    if proc.returncode != 0:
        sys.stderr.write(proc.stdout)
        sys.stderr.write(proc.stderr)
        raise RuntimeError(f"vercel api failed for {endpoint}")
    return extract_json(proc.stdout)


def walk_tree(nodes: list[dict], parents: list[str] | None = None):
    parents = parents or []
    for node in nodes:
        path_parts = parents + [node["name"]]
        if node.get("type") == "directory":
            yield {
                "path": "/".join(path_parts),
                "type": "directory",
                "mode": node.get("mode"),
            }
            yield from walk_tree(node.get("children", []), path_parts)
            continue
        yield {
            "path": "/".join(path_parts),
            "type": node.get("type"),
            "mode": node.get("mode"),
            "uid": node.get("uid"),
        }


def recover_source(deployment_id: str, out_dir: Path) -> dict:
    tree = run_vercel_api(f"/v13/deployments/{deployment_id}/files")
    if not isinstance(tree, list):
        raise RuntimeError("unexpected deployment tree payload")

    out_dir.mkdir(parents=True, exist_ok=True)
    manifest_entries = []
    recovered_files = 0

    for entry in walk_tree(tree):
        manifest_entries.append(entry)
        if entry.get("type") != "file" or not entry.get("uid"):
            continue

        file_payload = run_vercel_api(f"/v8/deployments/{deployment_id}/files/{entry['uid']}")
        data = file_payload.get("data") if isinstance(file_payload, dict) else None
        if not data:
            continue

        target = out_dir / entry["path"]
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(base64.b64decode(data))
        recovered_files += 1

    manifest = {
        "deployment_id": deployment_id,
        "output_dir": str(out_dir),
        "recovered_files": recovered_files,
        "entries": manifest_entries,
    }
    (out_dir / "manifest.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser(description="Recover Vercel deployment source files into local artifacts.")
    parser.add_argument("deployment_id", nargs="?", default=DEFAULT_DEPLOYMENT_ID)
    parser.add_argument(
        "--out-dir",
        default=None,
        help="Custom output directory. Defaults to ops/prelaunch_artifacts/recovered_live_source/<deployment_id>",
    )
    args = parser.parse_args()

    out_dir = Path(args.out_dir) if args.out_dir else DEFAULT_OUT_DIR / args.deployment_id
    manifest = recover_source(args.deployment_id, out_dir)
    print(json.dumps(manifest, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
