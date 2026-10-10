#!/data/data/com.termux/files/usr/bin/bash
set -u
export PATH="/data/data/com.termux/files/usr/bin:$PATH"
[ "${1:-}" = "--enable" ] && touch "$HOME/fleet/claude.ok"
[ -f "$HOME/fleet/claude.ok" ] || exit 0
tmux has-session -t claude 2>/dev/null && exit 0
mkdir -p "$HOME/agent"
tmux new-session -d -s claude \
  "proot-distro login ubuntu --termux-home --shared-tmp -- bash -lc 'export PATH=/root/.local/bin:\$PATH; cd /root/agent && while true; do claude remote-control; sleep 15; done'"
