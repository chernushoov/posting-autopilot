# Facebook Safe Workflow — Operator Flow

---

## End-to-End Workflow

```
Vacancy Created
    │
    ▼
AI Generates Post (Hebrew, tailored tone)
    │
    ▼
Recruiter Reviews & Approves Post
    │
    ▼
Recruiter Selects Target Groups (from directory)
    │
    ▼
Posting Queue Created
    │
    ▼
For each group:
    ├── Copy post to clipboard
    ├── Open group in browser (direct link)
    ├── Paste & post on Facebook (manual)
    └── Mark as posted in system
    │
    ▼
Track Results (responses, CVs, hires)
    │
    ▼
Group Intelligence Builds Over Time
```

---

## Step-by-Step Operator Guide

### Step 1: Create or Select a Vacancy

**Trigger:** New vacancy intake or existing vacancy needs Facebook distribution.

**Actions:**
1. Open vacancy in Recruit Autopilot
2. Verify details are complete: title, description, location, salary range, benefits, requirements
3. Click **"Distribute → Facebook Groups"**

**Requirements:**
- Vacancy must have: title, location, at least 3 requirements, contact method
- Salary can be hidden (post will say "competitive salary")

---

### Step 2: Generate AI Post

**Trigger:** Recruiter clicks "Generate Facebook Post"

**Actions:**
1. System generates Hebrew post using vacancy data
2. Post includes:
   - Attention-grabbing first line (optimized for Facebook feed preview)
   - Role summary (2–3 sentences)
   - Key requirements (bullet points, max 5)
   - What's offered (salary hint, benefits, growth)
   - Call to action (DM, comment, link)
   - Appropriate emoji and formatting
3. Recruiter selects **tone**: Professional / Casual / Urgent / Young Audience
4. Recruiter can **edit** the generated text
5. Recruiter clicks **"Approve"**

**AI Generation Rules:**
- Max length: 500 characters (Facebook preview cutoff)
- First line must hook attention (question, bold statement, or emoji opener)
- Never include client company name unless explicitly allowed
- Always include location and general salary range
- CTA must be clear and actionable
- Hebrew with optional English job title

**Tone Profiles:**

| Tone | Style | Best For |
|---|---|---|
| Professional | Formal, structured, detailed | Senior roles, finance, legal |
| Casual | Friendly, conversational, emoji-light | Tech, startups, marketing |
| Urgent | Bold, time-pressure, direct | High-volume, immediate hiring |
| Young Audience | Slang-friendly, emoji-heavy, short | Junior roles, students, service |

---

### Step 3: Select Target Groups

**Trigger:** Post approved, system opens Group Selector

**Actions:**
1. Group Directory loads with filters:
   - **Category:** Tech, Finance, Blue Collar, Service, General, City-specific, Industry-specific
   - **City:** Tel Aviv, Jerusalem, Haifa, Beer Sheva, Center, North, South, Remote
   - **Size:** Small (<5K), Medium (5K–20K), Large (20K–100K), Mega (100K+)
   - **Activity:** 1–5 rating (based on post frequency and engagement)
   - **Last Posted:** Never / >7 days / >3 days / <3 days (warning)
2. Recruiter applies filters relevant to vacancy
3. System suggests top groups based on:
   - Vacancy category match
   - Historical performance for similar vacancies
   - Time since last post
4. Recruiter selects groups (checkbox)
5. **Smart warnings:**
   - "You posted to this group less than 24 hours ago" (yellow)
   - "This group has a no-duplicate-posts rule" (red)
   - "This group requires admin approval — post may be delayed" (info)
6. Click **"Create Posting Queue"**

**Group Data Model:**

| Field | Source |
|---|---|
| Group name | Manual entry / import |
| Facebook URL | Manual entry |
| Category | Operator-assigned |
| City | Operator-assigned |
| Member count | Manual entry (updated periodically) |
| Activity rating | Operator-rated (1–5) |
| Posting rules | Operator notes (free text) |
| Last posted date | Auto-tracked |
| Performance score | Calculated from results history |

---

### Step 4: Execute Posting Queue

**Trigger:** Posting queue created with N groups

**Screen Layout:**
- **Left panel:** Approved post with large "Copy to Clipboard" button
- **Right panel:** Ordered list of groups to post to

**Per-Group Flow:**
1. Group name and link displayed prominently
2. Click **"Copy Post"** — post text copied to clipboard (visual confirmation)
3. Click **"Open Group"** — Facebook group opens in new browser tab
4. Recruiter pastes post in Facebook's post composer
5. Recruiter clicks Facebook's "Post" button
6. Recruiter returns to Recruit Autopilot
7. Click **"Mark as Posted"** — group row turns green, timestamp recorded
8. Next group auto-highlights
9. Repeat until queue complete

**Queue Management:**
- **Skip** — skip a group (with optional reason)
- **Reorder** — drag groups to change posting order
- **Pause** — save queue progress, continue later
- **Post variant** — use a different post text for specific groups (e.g., more casual for younger audience groups)

**Speed Target:** 15 seconds per group for experienced operators

---

### Step 5: Track Results

**Trigger:** Ongoing, after posts are live

**Actions (same day or next day):**
1. Open **Results** view
2. For each posted group, update status:
   - **Posted** (auto-set) — post was published
   - **Got Responses** — comments or reactions observed
   - **Got CVs** — candidates sent CVs via DM or link
   - **Interview Scheduled** — at least one candidate moved to interview
   - **Hired** — vacancy filled (partially or fully) via this group
3. Add response count (comments, DMs)
4. Rate quality: 1–5 (were the responses relevant?)

**Result Tracking Cadence:**
- Day 0: Post published, status = "Posted"
- Day 1: Check comments and DMs, update response count
- Day 3: Update CV count, rate quality
- Day 7+: Update hire status if applicable

---

### Step 6: Review Group Intelligence

**Trigger:** Weekly or when planning new campaigns

**Actions:**
1. Open **Group Analytics** view
2. Review:
   - Top performing groups (by CVs per post)
   - Groups with declining performance
   - Groups not posted to recently
   - New groups to add to directory
3. Update group ratings and categories as needed
4. Archive dead groups
5. Share top-performing group lists across team

---

## Operator Roles

| Role | Permissions |
|---|---|
| **Recruiter** | Generate posts, select groups, execute queue, track own results |
| **Team Lead** | All recruiter permissions + view team results + manage group directory |
| **Admin** | All permissions + manage users + billing + export data |

---

## Daily Operator Routine

| Time | Action | Duration |
|---|---|---|
| 09:00 | Review new vacancies, generate posts for today | 10 min |
| 09:15 | Select groups and create queues for all vacancies | 10 min |
| 09:30 | Execute posting queues | 15–30 min |
| 14:00 | Check results from morning posts, update statuses | 10 min |
| 16:00 | Second posting round (if needed for urgent vacancies) | 15 min |
| **Total** | | **45–75 min/day** |

Compare: current manual process = **2–4 hours/day**

---

## Edge Cases

### Post gets rejected by group admin
- Mark as "Rejected" in queue
- Add note about rejection reason
- System learns: flag this group's rules for future posts

### Facebook group is private and recruiter isn't a member
- Group marked as "Requires Membership" in directory
- Recruiter can request to join (manual)
- Group stays in directory but excluded from auto-suggestions until membership confirmed

### Same vacancy needs different post for different audience
- Use **"Post Variant"** feature
- Generate multiple posts with different tones
- Assign variants to specific groups in the queue

### Recruiter is posting for 10+ vacancies today
- Use **"Batch Mode"**: system creates separate queues per vacancy
- Queues can be interleaved by group (post all vacancies to Group A, then Group B)
- Or sequential by vacancy (all groups for Vacancy 1, then Vacancy 2)
