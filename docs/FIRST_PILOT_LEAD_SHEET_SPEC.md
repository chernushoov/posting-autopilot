# First Pilot Lead Sheet Specification

---

## Purpose

A single Google Sheet (or Airtable) that tracks every prospect from discovery through pilot completion. Designed for a founder managing 20–40 leads manually.

---

## Sheet Structure

### Tab 1: Lead Tracker (Main)

| Column | Type | Description | Example |
|---|---|---|---|
| **#** | Auto | Row number | 1 |
| **Agency Name** | Text | Company name | "TechRecruit Ltd" |
| **Tier** | Dropdown: 1/2/3 | Priority tier | 1 |
| **Source** | Dropdown | Where you found them | "FB Group - Tech Jobs TLV" |
| **Sector** | Dropdown | Tech / Blue Collar / Service / Other | "Tech" |
| **Size (est.)** | Dropdown | 1–3 / 3–10 / 10–30 / 30+ recruiters | "3–10" |
| **FB Activity** | Dropdown | Confirmed posting / Likely / Unknown | "Confirmed posting" |
| **Pain Signal** | Text | What pain you observed | "Copy-paste same post to 20 groups" |
| **Contact Name** | Text | Primary contact | "Yossi Cohen" |
| **Role** | Text | Owner / Ops Manager / Recruiter | "Owner" |
| **WhatsApp** | Text | Phone number | "+972-50-1234567" |
| **Email** | Text | Email if found | "yossi@techrecruit.co.il" |
| **LinkedIn** | URL | Profile link | "linkedin.com/in/yossicohen" |
| **Status** | Dropdown | See status definitions below | "Demo Scheduled" |
| **Last Action** | Text | What you last did | "Sent WA pitch" |
| **Last Action Date** | Date | When | "2026-03-31" |
| **Next Step** | Text | What to do next | "Follow up Wed if no reply" |
| **Next Step Date** | Date | When to do it | "2026-04-02" |
| **Priority Score** | Number (auto) | Calculated from tier + signals | 15 |
| **Notes** | Text | Anything useful | "Mentioned they got banned 2 months ago" |

---

## Status Definitions

| Status | Meaning | Next Action |
|---|---|---|
| **New** | Found, not yet contacted | Research contact → outreach |
| **Researching** | Looking for contact info | Find WhatsApp/email |
| **Contacted** | First message sent | Wait 2 days → follow up |
| **Responded** | They replied | Qualify → book demo |
| **Qualified** | Confirmed FB group user, right size | Book demo |
| **Demo Scheduled** | Demo date confirmed | Prepare, show up |
| **Demo Done** | Demo completed | Send follow-up, offer pilot |
| **Pilot Offered** | Pilot offered, waiting for response | Follow up in 2 days |
| **Pilot Active** | Pilot running | Support + track KPIs |
| **Pilot Review** | Pilot ended, reviewing | Run review call, offer conversion |
| **Converted** | Paying customer | Onboard fully |
| **Lost — Not Interested** | Said no | Ask for referral, archive |
| **Lost — No Response** | Never responded after 3 touches | Archive, retry in 60 days |
| **Lost — Not Qualified** | Doesn't use FB groups / too small / too big | Archive |
| **Paused** | Asked to talk later | Set reminder date |

---

## Source Definitions

| Source Code | Meaning |
|---|---|
| FB Group — [name] | Found their post in a specific Facebook group |
| FB Profile | Found their Facebook profile/page while browsing |
| LinkedIn Search | Found via LinkedIn search |
| Google Search | Found via Google / Google Maps |
| AllJobs/Drushim | Found on a job board |
| Telegram | Found in Telegram HR channel |
| Referral — [name] | Referred by someone |
| Directory | Found in business directory (e.g., d.co.il, Zap) |
| Inbound | They contacted us |

---

## Priority Score Calculation

Score each lead 1–5 on these dimensions, then sum:

| Dimension | 5 (best) | 3 (ok) | 1 (weak) |
|---|---|---|---|
| **FB activity confirmed** | Seen their posts | Likely posts | Unknown |
| **Agency size fit** | 3–15 recruiters | 2–3 or 15–30 | 1 or 30+ |
| **Pain signal** | Ban history / complaints | Manual chaos visible | No signal |
| **Contact reachable** | WhatsApp found | Email only | No contact |
| **Sector fit** | Tech / blue collar / service | Mixed | Exec search / niche |

**Max score: 25. Minimum to contact: 10. Sweet spot: 15+.**

---

## Tab 2: Daily Action Queue

A filtered view of leads that need action today.

| Column | Source |
|---|---|
| Agency Name | From Tab 1 |
| Contact Name | From Tab 1 |
| Status | From Tab 1 |
| Next Step | From Tab 1 |
| Next Step Date | From Tab 1 — filter: = today |
| WhatsApp | From Tab 1 |
| Notes | From Tab 1 |

**Sort by: Priority Score (descending), then Next Step Date.**

**Morning routine:** Open Tab 2. Work top to bottom. Update Tab 1 after each action.

---

## Tab 3: Pilot Tracker

For leads that entered pilot stage.

| Column | Description |
|---|---|
| Agency Name | |
| Contact Name | |
| Pilot Start Date | |
| Pilot End Date | Start + 14 days |
| Day 0: First Post? | Yes/No |
| Day 3: Check-in Done? | Yes/No |
| Posts Published | Running total |
| Groups Used | Running total |
| CVs Received | Running total |
| Day 7: Mid-Review Done? | Yes/No |
| Day 12: Pre-Close Done? | Yes/No |
| Day 14: Review Call Done? | Yes/No |
| Converted? | Yes / No / Pending |
| Feedback Notes | Free text |

---

## Tab 4: Metrics Dashboard

Update weekly. 5 rows maximum.

| Metric | This Week | Total |
|---|---|---|
| Leads added | | |
| First contacts sent | | |
| Responses received | | |
| Demos completed | | |
| Pilots started | | |
| Pilots converted | | |
| Revenue (ILS) | | |

---

## Setup Instructions

1. Create a Google Sheet named "Recruit Autopilot — First Pilot Pipeline"
2. Create 4 tabs: "Lead Tracker", "Daily Actions", "Pilot Tracker", "Metrics"
3. Set up dropdowns for: Tier, Source, Sector, Size, FB Activity, Status
4. Add conditional formatting: Tier 1 = green row, Tier 2 = yellow, Tier 3 = no color
5. Add filter on Tab 2 for Next Step Date = TODAY()
6. Bookmark it. Open every morning.

**Time to set up: 20 minutes.**
