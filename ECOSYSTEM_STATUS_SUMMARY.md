# Ecosystem Status Summary

## What Was Discovered
- GitHub account `chernushoov` currently exposes 10 repos relevant to this machine, with 5 directly relevant product families.
- Vercel team `chernushoov's projects` currently has 10 projects, but only 3 of them clearly deserve ongoing attention.
- The cleanest product/deployment pairs are:
- `floordsgn-site`
- `moltbot-dashboard`
- The strongest commercial repo surface is `recruitment-bot`, while this machine currently holds a non-git execution copy in `../recruit-autopilot-core`.
- Connector is the noisiest cluster by far, with duplicate repos, duplicate deployments, and dirty-branch deploy history.

## What Is Clearly Active
- `recruitment-bot` on GitHub, updated 2026-03-27
- local `../recruit-autopilot-core`, actively used on 2026-03-30
- `floordsgn-site` repo and Vercel deployment, both updated/deployed on 2026-03-27
- `moltbot-dashboard` Vercel dashboard, production deployed on 2026-03-27
- local `../strategist`, modified 2026-03-26, though not cleanly repo-backed on this machine

## What Looks Stale, Duplicate, Or Misleading
- `connectorwebtest`: Vercel-created test repo/project
- `connector_deploy`: empty Vercel placeholder with no deployments
- `workspace`: live Vercel project that returns 404
- `site`: old FloorDSGN duplicate deployment
- `backup_rezerv`: Connector duplicate deployment
- `connector-free-mvp`: older duplicate Connector deployment/repo branch
- local `../connector-web`: explicitly labeled backup copy, not canonical
- local `../TELEGRAM BOT`: risky legacy ad hoc folder

## What Remains Uncertain
- Whether local `../recruit-autopilot-core` is a direct export of `recruitment-bot` or a sibling fork
- Which exact local repo produced the latest dirty-branch `connector-web` production deployments
- Whether any real traffic or external links still point to `site`, `backup_rezerv`, or `connector-free-mvp`
- Whether `../strategist` is still the active local-core runtime or only a precursor alongside MeltBot dashboard

## Five Highest-Value Next Actions

1. Recruit source-of-truth cleanup:
- link `../recruit-autopilot-core` to its canonical git remote or explicitly document that it is a deployment/export copy of `recruitment-bot`

2. Connector lineage cleanup:
- pick one canonical repo for Connector web work and one Vercel project to keep
- freeze all other Connector surfaces until mapping is cleaned

3. FloorDSGN duplication cleanup:
- confirm that no traffic or backlinks still rely on Vercel project `site`
- then archive or deprecate it

4. Recruit commercial execution:
- continue building pilot runbooks, smoke validation, demo flow, and offer packaging in the Recruit lane

5. MeltBot operational hardening:
- keep `moltbot-dashboard` readable and trustworthy
- avoid expanding local-core complexity unless there is a direct operational need
