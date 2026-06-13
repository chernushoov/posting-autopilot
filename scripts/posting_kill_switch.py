#!/usr/bin/env python3
"""Operator kill switch for ALL autonomous posting + DM sending (C4).

Usage (from the repo root, or inside any service container):
  python -m scripts.posting_kill_switch pause  ["reason"]   # stop everything NOW
  python -m scripts.posting_kill_switch resume               # allow posting again
  python -m scripts.posting_kill_switch status               # show current state

It sets a flag in the shared data volume that EVERY send site checks immediately
before posting — Telegram Telethon (common/tg_client.post_to_group), Telegram Bot
API (worker/tasks._send_telegram_post), and the Facebook browser poster
(worker/fb_auto_post.auto_post_queue_item). Takes effect on the NEXT send, no
restart needed.

A job that is already mid-flight (e.g. inside an anti-spam sleep) will finish its
current external call. To also abort queued / in-flight jobs, stop the workers:
  docker compose -f docker-compose.yml -f docker-compose.prod.yml stop worker scheduler bot listener
"""
import sys

from common import posting_guard


def main(argv) -> int:
    cmd = (argv[1] if len(argv) > 1 else "status").lower()
    if cmd == "pause":
        reason = argv[2] if len(argv) > 2 else ""
        marker = posting_guard.pause(reason=reason, actor="cli")
        print("PAUSED — all posting + DM sending halted.")
        print(marker)
        print("To abort in-flight/queued jobs too, stop the worker/scheduler/bot/listener containers.")
        return 0
    if cmd == "resume":
        was = posting_guard.resume(actor="cli")
        print("RESUMED — posting allowed again." + ("" if was else " (it was not paused)"))
        return 0
    if cmd == "status":
        if posting_guard.is_paused():
            print(f"PAUSED — {posting_guard.pause_info()}")
        else:
            print("ACTIVE — posting allowed (still subject to quiet hours + rate limits).")
        return 0
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv))
