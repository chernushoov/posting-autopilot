# Quick Fix Priority

Top friction points in the 6-step flow, ranked by likelihood and severity.

---

## Step 2: Generate Post

| # | Friction Point | Likelihood | Severity | Fix |
|---|---|---|---|---|
| 1 | AI generates English instead of Hebrew | HIGH | 🔴 | Force Hebrew in prompt. Add language parameter. |
| 2 | Post is too long / gets cut off in Facebook preview | HIGH | 🟡 | Enforce 500-char limit. Show character count in editor. |
| 3 | Post tone doesn't match what they expected | MEDIUM | 🟡 | Improve prompt per tone. Let them see the prompt is "Casual" not "Slang." |
| 4 | Generation takes more than 5 seconds | MEDIUM | 🟡 | Add loading indicator. Optimize API call. |
| 5 | Generated post includes company name they want hidden | MEDIUM | 🔴 | Add "hide company name" toggle. Default to hidden. |

## Step 3: Pick Groups

| # | Friction Point | Likelihood | Severity | Fix |
|---|---|---|---|---|
| 6 | Their groups aren't in the directory | HIGH | 🔴 | Show "Add your own group" button prominently. Or pre-load their groups before the test. |
| 7 | Filters don't return useful results | MEDIUM | 🟡 | Default view should show all groups. Filters narrow, not gate. |
| 8 | Group data is stale (wrong member count, dead groups) | MEDIUM | 🟡 | Mark data as approximate. Let users flag bad data. |

## Step 4: Post to Groups

| # | Friction Point | Likelihood | Severity | Fix |
|---|---|---|---|---|
| 9 | Copy to clipboard doesn't work | HIGH | 🔴 | Test clipboard API across browsers. Show fallback: "select all + copy" text box. |
| 10 | Group link opens wrong page or 404s | MEDIUM | 🔴 | Validate all group URLs before the test. Check for login-required redirects. |
| 11 | Customer can't find their way back to the tool after posting on FB | HIGH | 🟡 | Open group in new tab (target="_blank"). Add "Come back to mark as done" instruction. |
| 12 | "Mark as Done" button unclear or hard to find | MEDIUM | 🟡 | Make it large, green, obvious. Add visual state change (row turns green). |

## Step 5: Track Results

| # | Friction Point | Likelihood | Severity | Fix |
|---|---|---|---|---|
| 13 | Tracking feels like extra work with no payoff yet | HIGH | 🟡 | Show sample insight: "After a few posts, you'll see which groups bring CVs." Pre-fill "Posted" status automatically. |
| 14 | Status options are confusing | MEDIUM | 🟢 | Keep it to 3 statuses for now: Posted / Got CVs / Hired. |

## General

| # | Friction Point | Likelihood | Severity | Fix |
|---|---|---|---|---|
| 15 | Page loads slowly or errors on mobile | MEDIUM | 🔴 | Test on mobile before the customer test. If not ready, tell them to use desktop. |
| 16 | Customer doesn't understand what the tool does before starting | LOW | 🟡 | The operator script handles this. No in-app fix needed for today. |

---

## Pre-Test Checklist (Run 1 Hour Before)

```
□ Generate a test post — does it come out in Hebrew?
□ Copy a post to clipboard — does it paste correctly?
□ Click 3 group links — do they open the right Facebook groups?
□ Mark a group as Done — does the UI update?
□ Check on Chrome + one other browser
□ Check on mobile (or decide: desktop only today)
□ Customer's groups pre-loaded in directory? If not, add 5 manually.
□ One test vacancy pre-loaded so you have a backup if their input fails
```

**If any checkbox fails: fix it before the test. Don't let the customer hit a known broken step.**
