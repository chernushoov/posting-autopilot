# Device fleet

Transport: Tailscale tailnet (one account, MagicDNS on). Control: Claude Code Remote Control (bridge environments) + Claude app.

| Node | Tailnet name | Kind | Role | Status |
|---|---|---|---|---|
| iMac-AgentMachine-2 | `imac-agent` | macOS, bridge env `iMac-AgentMachine-2` | OpenClaw gateway :18789, n8n, ollama, moltbot-dashboard | active |
| MacBook Air | `macbook-air` | macOS, bridge env `MacBook-Air-Alexey` | owner workstation, prod SSH key holder | active |
| Hetzner CPX22 `167.233.98.210` | `pa-prod` | Ubuntu, docker | Posting Autopilot prod (`/opt/posting-autopilot`) | live, NOT yet on tailnet |
| Windows PC | `pc` | Windows | — | blocked: SSH firewall, not on tailnet |
| **Android phone** | `android-agent` | Android + Termux, bridge env (after setup) | **FB mobile egress proxy, external watchdog, Claude bridge host** | **NEW — setup in `android/SETUP.md`** |
| Cloud | — | `anthropic_cloud` env | repo work, routines | active |

## Android phone — duties

| ID | Duty | Runs as | Closes |
|---|---|---|---|
| A1 | Mobile-IP HTTP proxy `:8888` (tailnet-only, BasicAuth) for FB capture + posting | tinyproxy, runit service | Roadmap O3, abort criterion #3 |
| A2 | External watchdog every 5 min: prod `/health`, `/ready`, marketing, proxy egress → Telegram alert on state change | cron | Roadmap E3 (outside-in part) |
| A3 | Daily device report 08:50: battery, temp, egress IP/ASN, proxy, tailnet, incidents | cron | — |
| A4 | Claude Code bridge host (`claude remote-control` in tmux, autostart) | Termux:Boot | phone appears in Claude app env list |
| A5 | SIM for Telegram 2nd posting account (SMS code read by owner, never auto-forwarded) | manual | Roadmap O2 / multi-account |

Not phone duties: Instagram/FB posting via on-device automation (ban risk), OTP forwarding, storing prod secrets.

## Wiring prod to the phone proxy

1. `ops/fleet/hetzner_join_tailnet.sh <TS_AUTHKEY>` on prod.
2. Script verifies `curl -x http://USER:PASS@android-agent:8888 https://api.ipify.org` returns a mobile-carrier IP.
3. Append to `/opt/posting-autopilot/.env.prod` (and `.env` copy, see DO_NOT.md):
   ```
   FB_PROXY_SERVER=http://<android tailnet IP>:8888
   FB_PROXY_USERNAME=<PROXY_USER>
   FB_PROXY_PASSWORD=<PROXY_PASS>
   ```
   Use the 100.x IP, not MagicDNS: containers do not resolve tailnet names.
4. Recreate only `web worker`:
   `APP_ENV_FILE=.env.prod docker compose --env-file .env.prod -f docker-compose.yml -f docker-compose.prod.yml up -d --force-recreate web worker`
5. FB login capture (secondary account only) AFTER step 4 — capture and posting must share the same egress.

## Tailnet ACL (paste into Tailscale admin → Access controls)

```json
{
  "tagOwners": { "tag:prod": ["autogroup:admin"], "tag:agent": ["autogroup:admin"] },
  "acls": [
    { "action": "accept", "src": ["autogroup:member"], "dst": ["*:*"] },
    { "action": "accept", "src": ["tag:prod"], "dst": ["tag:agent:8888"] }
  ]
}
```
Tag the phone `tag:agent`, prod `tag:prod`. Prod reaches only the proxy port; nothing reaches prod from the phone.
