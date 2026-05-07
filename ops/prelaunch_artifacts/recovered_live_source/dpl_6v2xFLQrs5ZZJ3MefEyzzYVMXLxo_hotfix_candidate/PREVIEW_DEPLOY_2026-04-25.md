# Preview Deploy

- deployed_at: `2026-04-25`
- target_project: `posting-autopilot-next`
- deployment_type: `preview`
- preview_url: `https://posting-autopilot-next-ixm0lrp5x-chernushoovs-projects.vercel.app`
- inspect_url: `https://vercel.com/chernushoovs-projects/posting-autopilot-next/9D3VSG8g8hEpnTrTR4usm23yp8Bk`

## Metadata

- `source=recovered-live-hotfix`
- `base_deployment=dpl_6v2xFLQrs5ZZJ3MefEyzzYVMXLxo`
- `fix=detached-user-name`

## Notes

- This preview was deployed from the recovered live source hotfix candidate under:
  - `ops/prelaunch_artifacts/recovered_live_source/dpl_6v2xFLQrs5ZZJ3MefEyzzYVMXLxo_hotfix_candidate/src`
- Build completed successfully on Vercel.
- Production alias was not changed.

## Cleanup Note

- An earlier mistaken `vercel deploy` auto-linked the directory as a separate Vercel project named `src`.
- The correct candidate was then re-linked to `posting-autopilot-next` and deployed properly as the preview above.
- That stray `src` Vercel project was later removed after the correct production rollout was verified.

## Telegram Live-Links Preview

- later preview deployment: `https://posting-autopilot-next-npjwt3gu6-chernushoovs-projects.vercel.app`
- purpose:
  - replace misleading seeded Telegram UI values with the real bot link `https://t.me/AutopillotRecruit_bot`
  - blank the fake default test destination and add honest DM/channel instructions
- verification caveat:
  - this preview was protected by Vercel deployment auth, so ordinary public `curl` saw only the `401 Authentication Required` shell
  - the build completed successfully, but public operator verification had to happen on the production alias after rollout
