# Posting Autopilot: Gap Summary + Implementation Prompt

## Current Product Gaps

Observed from live `https://posting-autopilot-next.vercel.app` and local audit:

1. `facebook-connect` is not a real Facebook integration flow.
- It currently saves demo-style state fields like `account_name`, `page_name`, `connection_state`.
- There is no real Meta OAuth connect button.
- There is no permission grant flow.
- There is no page/account fetch from Facebook.

2. There is no destination picker.
- No clear choice of where to post:
  - Facebook Page feed
  - Facebook Groups
  - Marketplace
- No UI for selecting one or many destinations.
- No distinction between destination types and their posting rules.

3. There is no real group discovery/import flow.
- The UI does not show groups the user belongs to.
- There is no fetch/import/sync state for connected destinations.
- No visible source list with `connected / available / selected / blocked`.

4. Marketplace flow is absent.
- No Marketplace-specific toggle, form, category, location, or listing mode.
- No UI explaining whether Marketplace is supported, manual, or out of scope.

5. Language support is missing in the live operator UI.
- No visible language switcher.
- No `en / ru / he` UI localization.
- No Hebrew RTL handling.

6. Settings/profile path is not trustworthy enough.
- Live `/settings` was previously reproduced as failing with `500`.
- Even where operator flow works, settings/profile state is not reliable enough to trust for launch.

7. Local repo and live deploy do not fully match.
- Controlled local Flask repo uses a different route family.
- Live app route family is:
  - `/facebook-connect`
  - `/ads/new`
  - `/schedule`
  - `/history`
  - `/settings`
- This means implementation must happen in the real source repo/branch for the Vercel app, not by patching the wrong local surface.

8. Posting workflow lacks explicit safety UX.
- No clear preview of what will be posted.
- No explicit dry-run / test-mode / publish-now vs schedule choice.
- No visible confirmation of exact destinations before publishing.
- No visible proof/status per destination.

9. Real Facebook/operator readiness is unclear.
- The current product does not clearly tell the user:
  - what is connected
  - what is fetched from Meta
  - what is selected for publishing
  - what will happen on publish

10. Current experience is too demo-like for real use.
- A user cannot confidently understand how to connect a page, discover groups, select targets, or know whether posting will go to page/group/marketplace.

## Implementation Goal

Turn the current Posting Autopilot live app into a usable operator workflow for:

- connecting a real Facebook account/page
- discovering available destinations
- choosing where to post
- preparing a construction vacancy
- previewing the post
- publishing or scheduling safely
- seeing result status per destination

## Copy-Paste Implementation Prompt

```text
You are the implementation owner for the live Posting Autopilot operator app that powers:

https://posting-autopilot-next.vercel.app

Your job is to implement the missing real operator workflow for Facebook posting.

IMPORTANT
- Work in the actual source repo/branch behind the live Vercel app.
- Do not patch the wrong local repo if it does not back the deploy.
- Do not redesign the whole product.
- Do not add unrelated architecture work.
- Do not produce mock-only UI.
- Implement the actual operator path.

PRIMARY GOAL
Make the app understandable and usable for a real first Facebook posting test.

REQUIRED OUTCOME
The operator must be able to:
1. connect Facebook properly
2. see connected account/page state
3. fetch and see destinations
4. choose where to post
5. distinguish Page / Group / Marketplace modes
6. create a vacancy/posting asset
7. preview the final post
8. publish now or schedule later
9. see posting status/results

IMPLEMENT ONLY WHAT IS NEEDED FOR THIS FLOW.

CURRENT GAPS TO FIX
1. `facebook-connect` is demo-like and not a real connect flow.
2. There is no destination picker.
3. There is no visible group discovery/import state.
4. Marketplace is not represented in the UI at all.
5. No visible language support for `en / ru / he`.
6. Operator settings/profile path is unstable or incomplete.
7. Current UI does not clearly show what will be posted where.

PHASE 1 — FIND THE REAL SOURCE
Before coding, confirm the exact repo/branch/file tree behind the live Vercel deploy.
Output the exact files that back:
- `/facebook-connect`
- `/ads/new`
- `/schedule`
- `/history`
- `/settings`

PHASE 2 — REAL FACEBOOK CONNECT STATE
Implement a real and explicit connect screen.

Minimum UI requirements:
- A visible `Connect Facebook` button or equivalent entrypoint
- Connected account summary
- Connected page summary
- Clear connection status badges:
  - not_connected
  - connected
  - error
- A visible note if group discovery or marketplace is limited/manual

If full OAuth is not available yet, do not fake it silently.
Show explicit status and support only the real implemented path.

PHASE 3 — DESTINATION PICKER
Add a dedicated destination selection section.

Must support visible categories:
- Facebook Page
- Facebook Groups
- Marketplace

Requirements:
- show each destination type separately
- show available destinations fetched/imported from the connected account, or clearly show if manual entry is required
- allow selecting one or many destinations
- show selected count
- show destination readiness state
- do not let the operator publish without at least one valid destination

PHASE 4 — CONSTRUCTION VACANCY POST FLOW
Make it possible to prepare a real construction vacancy post.

Minimum fields:
- title
- body / primary text
- CTA / response text
- city / area
- salary/pay if applicable
- employment type
- shift/schedule
- contact/apply path

Add a `Construction vacancy` example preset or template if useful, but keep it small.

PHASE 5 — PREVIEW + PUBLISH CHOICE
Before publish, show:
- final post preview
- selected destinations
- posting mode:
  - publish now
  - schedule
- operator confirmation

The operator must understand exactly where the post will go.

PHASE 6 — HISTORY / RESULT CLARITY
Improve history so it shows:
- posting title
- destination(s)
- current state per run
- scheduled / posted / failed
- operator notes or error summary

PHASE 7 — LANGUAGE SUPPORT
Add visible operator UI support for:
- English
- Russian
- Hebrew

Requirements:
- simple language switcher in the header
- translated operator chrome for these key routes:
  - `/facebook-connect`
  - `/ads/new`
  - `/schedule`
  - `/history`
  - `/settings`
- Hebrew must switch page direction to RTL
- do not redesign the whole visual system
- translate only the operator-facing copy needed for this flow

PHASE 8 — SAFETY RULES
Implement these guardrails:
- cannot publish without connected account/page state
- cannot publish without selected destination(s)
- cannot publish without required vacancy fields
- clearly label unimplemented destination types
- if Marketplace is not truly supported yet, say so clearly instead of pretending it works

DELIVERABLES
1. Actual code changes in the real live app source
2. A clear route-by-route summary of what changed
3. A short operator test checklist
4. A proof run showing:
   - connect screen works
   - destination selection works
   - construction vacancy can be created
   - preview is visible
   - schedule/publish path is understandable

DO NOT
- do not add unrelated infra work
- do not add abstract frameworks
- do not add fake integrations without explicit labeling
- do not leave the app in a half-demo, half-real state

SUCCESS CONDITION
The operator can open the app and clearly understand:
- how to connect Facebook
- where the post will go
- how to select Page / Groups / Marketplace
- how to create and preview a construction vacancy post
- how to schedule or publish it safely
```

## Immediate Execution Order

1. Identify the exact live source repo/branch.
2. Patch the real operator app, not the unrelated Flask repo.
3. Implement destination selection before any real posting attempt.
4. Add language switcher and `he` RTL for the operator routes.
5. Only then run a real construction vacancy posting test.
