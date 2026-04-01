#!/usr/bin/env python3

import json
import subprocess
import sys
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parent.parent
OUT_DIR = ROOT_DIR / "ops" / "prelaunch_artifacts" / "launch_gate"


def run_gate(base_url: str | None) -> tuple[int, dict]:
    cmd = [sys.executable, "scripts/final_launch_gate.py"]
    if base_url:
        cmd.append(base_url)
    proc = subprocess.run(cmd, cwd=ROOT_DIR, text=True, capture_output=True)
    try:
        data = json.loads(proc.stdout)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"launch gate output was not valid json: {exc}") from exc
    return proc.returncode, data


def build_markdown(data: dict) -> str:
    lines = [
        "# Launch Gate Snapshot",
        "",
        f"- checked_at: `{data.get('checked_at')}`",
        f"- base_url: `{data.get('base_url')}`",
        f"- overall_status: `{data.get('overall_status')}`",
        f"- launch_ready: `{data.get('launch_ready')}`",
        f"- runtime: `{data.get('runtime', {}).get('status')}`",
        f"- local_guardrails: `{data.get('local_guardrails', {}).get('status')}`",
        f"- live_smoke: `{data.get('live_smoke', {}).get('status')}`",
        f"- source_alignment: `{data.get('source_alignment', {}).get('status')}`",
        "",
        "## Blockers",
        "",
    ]
    blockers = data.get("blockers", [])
    if blockers:
        lines.extend([f"- {item}" for item in blockers])
    else:
        lines.append("- none")
    lines.extend(
        [
            "",
            "## Commands",
            "",
            "- `bash scripts/run_prelaunch_front.sh`",
            "- `python3 scripts/final_launch_gate.py`",
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> int:
    base_url = sys.argv[1] if len(sys.argv) > 1 else None
    code, data = run_gate(base_url)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    stamp = data.get("checked_at", "unknown").replace(":", "").replace("-", "")
    stamp = stamp.replace("T", "T").replace("Z", "Z")
    json_path = OUT_DIR / f"launch_gate_{stamp}.json"
    md_path = OUT_DIR / f"launch_gate_{stamp}.md"
    latest_json = OUT_DIR / "latest.json"
    latest_md = OUT_DIR / "latest.md"

    json_text = json.dumps(data, indent=2, ensure_ascii=False) + "\n"
    md_text = build_markdown(data)

    for path, text in [
        (json_path, json_text),
        (md_path, md_text),
        (latest_json, json_text),
        (latest_md, md_text),
    ]:
        path.write_text(text, encoding="utf-8")

    print(json.dumps({"json": str(json_path), "markdown": str(md_path), "overall_status": data.get("overall_status")}, indent=2))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
