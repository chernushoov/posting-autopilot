# Production Promotion

- promoted_at: `2026-04-25`
- project: `posting-autopilot-next`
- original_live_deployment: `dpl_6v2xFLQrs5ZZJ3MefEyzzYVMXLxo`
- preview_deployment: `dpl_9D3VSG8g8hEpnTrTR4usm23yp8Bk`
- production_deployment: `dpl_82qFWhwcBXfzaMYWzXC7HGTjHNYn`
- production_url: `https://posting-autopilot-next.vercel.app`
- production_runtime_url: `https://posting-autopilot-next-607jlmj30-chernushoovs-projects.vercel.app`

## Promotion Metadata

- `source=recovered-live-hotfix`
- `base_deployment=dpl_6v2xFLQrs5ZZJ3MefEyzzYVMXLxo`
- `fix=detached-user-name`
- `action=promote`
- `originalDeploymentId=dpl_9D3VSG8g8hEpnTrTR4usm23yp8Bk`

## Notes

- Production alias was switched by promoting the already-built preview deployment path, not by running a fresh production build from a different tree.
- Vercel project metadata confirms `targets.production.id = dpl_82qFWhwcBXfzaMYWzXC7HGTjHNYn`.
- Live HTTP smoke was run afterwards against the public production URL and returned `SMOKE OK`.
- The stray external Vercel project `src` created during the earlier mistaken deploy was removed after rollout verification.

## Telegram Live-Links Rollout

- a second rollout was later required because the public app still exposed misleading Telegram defaults:
  - fake bot username `@posting_autopilot_bot`
  - fake destination ref `@startup_hiring_alerts`
- first direct production deploy for that Telegram UX fix:
  - deployment id: `dpl_65GRBXRAtwum6RzEjDbs7BU4sBax`
  - result: public UI fixed, but lineage metadata was missing, so `final_launch_gate.py` went red on source-alignment truth
- final production deploy with preserved lineage metadata:
  - deployment id: `dpl_CxzVUMT6ur5WJhSUJRFYmujqXcSE`
  - metadata:
    - `source=recovered-live-hotfix`
    - `base_deployment=dpl_6v2xFLQrs5ZZJ3MefEyzzYVMXLxo`
    - `fix=telegram-live-links`
- final verified outcome:
  - public login page shows `https://t.me/AutopillotRecruit_bot`
  - `/facebook-connect` shows `@AutopillotRecruit_bot`
  - stale fake Telegram defaults are no longer visible in the operator-facing connect flow
  - public smoke stayed green
  - launch gate returned to `overall_status = green`

## CSS Route Hotfix

- deployed_at: `2026-04-30`
- production_deployment_url: `https://posting-autopilot-next-f8fk0ektu-chernushoovs-projects.vercel.app`
- production_alias: `https://posting-autopilot-next.vercel.app`
- metadata:
  - `source=recovered-live-hotfix`
  - `base_deployment=dpl_6v2xFLQrs5ZZJ3MefEyzzYVMXLxo`
  - `fix=css_app_route_hotfix`
- root cause:
  - public HTML linked `/app.css`
  - live `/app.css` returned `404`, so the operator UI rendered unstyled
- fix:
  - added an explicit Flask route for `/app.css`
  - route serves `src/public/app.css` when present and has an embedded fallback CSS response if Vercel static packaging omits the file again
- verified:
  - `https://posting-autopilot-next.vercel.app/app.css` returns `200` with `content-type: text/css`
  - `/login` returns `200`
  - demo login redirects to `/facebook-connect`
  - `/facebook-connect` returns `200` and contains the real Telegram bot link
