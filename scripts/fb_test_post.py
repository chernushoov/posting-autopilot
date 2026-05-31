#!/usr/bin/env python3
"""Test the FB browser poster on ONE group.

DRY-RUN by default: opens the group, fills the composer, screenshots it, and does
NOT publish. Add --publish to actually post (real public post — use with care).

Run:  .venv-fb/bin/python scripts/fb_test_post.py [group_url] [--publish]
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from common.fb_browser_poster import post_to_group  # noqa: E402

DEFAULT_GROUP = "https://www.facebook.com/groups/143128243021491/"
DEFAULT_TEXT = "דרוש/ה עובד/ת לעבודה מיידית באזור המרכז — פרטים בהודעה פרטית."


def main() -> int:
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    publish = "--publish" in sys.argv
    group_url = args[0] if args else DEFAULT_GROUP
    text = args[1] if len(args) > 1 else DEFAULT_TEXT

    print(f"group : {group_url}")
    print(f"mode  : {'PUBLISH (REAL POST!)' if publish else 'DRY-RUN (no publish)'}")
    print(f"text  : {text}\n")

    res = post_to_group(
        session_name="floordsgn",
        group_url=group_url,
        text=text,
        dry_run=not publish,
    )
    print("ok           :", res.ok)
    print("error        :", res.error_kind, res.error_message or "")
    print("final_url    :", res.final_url)
    print("screenshot   :", res.screenshot_after or res.screenshot_before)
    print("notes        :", res.notes)
    print("duration_s   :", round(res.duration_seconds, 1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
