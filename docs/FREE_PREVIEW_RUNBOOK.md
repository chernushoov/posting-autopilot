# Free customer preview

`render.yaml` defines an isolated preview of this Flask branch using only Render free instance
types: one web service, one Postgres database and one non-persistent Key Value instance.

## Validate locally

```bash
python scripts/test_render_preview_requirements.py
python scripts/test_render_preview_runtime.py
python scripts/customer_demo_flow_smoke.py
python scripts/customer_demo_browser_smoke.py
```

The Blueprint pins the tested Python runtime and installs only web dependencies. The startup
script rejects SQLite, local Redis, weak generated secrets and enabled billing. It waits for both
linked datastores, applies the idempotent schema bootstrap, optionally seeds demo data, and then
replaces itself with Gunicorn.

## Owner-approved launch

1. Push or merge the commit containing `render.yaml` to the selected GitHub branch.
2. In Render choose **New > Blueprint**, connect `chernushoov/posting-autopilot`, and select that
   exact branch.
3. Confirm all three resources say `free` before applying the Blueprint.
4. Read the generated `ADMIN_PASSWORD` from the web service environment. The login name is
   `pilot-admin`.
5. Verify `/health`, `/login`, then complete one marked test flow without starting external posts.

Creating the Blueprint is an external deploy action and requires explicit owner approval.

## Honest limits

- This is web-only. It does not start the bot, RQ worker, scheduler, Facebook browser or posting.
- A campaign can be configured for demonstration, but no external posting should be presented as
  active in this preview.
- The free web service spins down after 15 minutes without inbound traffic and cold-starts later.
- The free Postgres database expires after 30 days, has no backups and is limited to one per
  workspace. Export any pilot data before expiry.
- Free Key Value is in-memory only. Queue contents disappear on restart.
- Uploaded local files are ephemeral and disappear on restart or spin-down.
- Do not point production domains at this preview.
