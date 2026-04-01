# Facebook Safe Workflow — MVP Screen Specifications

---

## Screen Map

```
Dashboard
    │
    ├── Vacancy List ──→ Vacancy Detail ──→ Generate Post
    │                                           │
    │                                           ▼
    │                                    Post Editor ──→ Group Selector
    │                                                        │
    │                                                        ▼
    │                                                  Posting Queue
    │
    ├── Group Directory ──→ Group Detail / Edit
    │
    ├── Results ──→ Vacancy Results ──→ Group Results
    │
    └── Settings (users, billing, preferences)
```

---

## Screen 1: Dashboard

**Purpose:** Daily overview and quick actions

**Layout:**

```
┌─────────────────────────────────────────────────────┐
│  Recruit Autopilot — Facebook Posting Assistant      │
├──────────────┬──────────────┬───────────────────────┤
│  Today       │  This Week   │  Quick Actions        │
│              │              │                       │
│  Posts: 23   │  Posts: 89   │  [+ New Post]         │
│  Groups: 15  │  Groups: 34  │  [Resume Queue]       │
│  CVs: 8     │  CVs: 31    │  [View Results]       │
│              │              │                       │
├──────────────┴──────────────┴───────────────────────┤
│  Active Queues                                       │
│  ┌─────────────────────────────────────────────┐    │
│  │ Senior Java Dev — 5/12 groups posted        │    │
│  │ Sales Manager — ready, 8 groups             │    │
│  │ QA Engineer — completed, 15 groups          │    │
│  └─────────────────────────────────────────────┘    │
│                                                      │
│  Top Groups This Week                                │
│  1. Tech Jobs TLV — 12 CVs                          │
│  2. Hi-Tech Israel — 8 CVs                          │
│  3. Jobs Haifa — 6 CVs                              │
└─────────────────────────────────────────────────────┘
```

**Data:**
- Today's stats: posts published, groups posted to, CVs received
- Week stats: same, rolling 7 days
- Active queues: in-progress and ready-to-post queues
- Top groups: by CV count this week

**Actions:**
- New Post: opens vacancy selector → post generator
- Resume Queue: opens most recent unfinished queue
- View Results: navigates to Results screen

---

## Screen 2: Vacancy List

**Purpose:** Browse and select vacancies for Facebook posting

**Layout:**

```
┌─────────────────────────────────────────────────────┐
│  Vacancies                          [Filter] [Sort]  │
├─────────────────────────────────────────────────────┤
│  Search: [________________________]                  │
│                                                      │
│  ┌──────────────────────────────────────────────┐   │
│  │ ★ Senior Java Developer                      │   │
│  │   Tel Aviv │ 30-35K NIS │ TechCorp           │   │
│  │   FB Status: Posted to 12 groups │ 4 CVs     │   │
│  │   [Generate Post]  [View Results]            │   │
│  ├──────────────────────────────────────────────┤   │
│  │   Sales Manager                               │   │
│  │   Herzliya │ 20-25K NIS │ SalesCo            │   │
│  │   FB Status: Not yet posted                   │   │
│  │   [Generate Post]  [View Results]            │   │
│  ├──────────────────────────────────────────────┤   │
│  │   QA Engineer                                 │   │
│  │   Remote │ 22-28K NIS │ StartupX             │   │
│  │   FB Status: Posted to 8 groups │ 11 CVs     │   │
│  │   [Generate Post]  [View Results]            │   │
│  └──────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────┘
```

**Columns/Data per vacancy:**
- Vacancy title
- Location, salary range, client
- Facebook posting status (not posted / posted to N groups / N CVs)
- Quick actions: Generate Post, View Results

**Filters:**
- Status: All / Not Posted / Posted / Has CVs
- Location
- Category (Tech, Finance, etc.)
- Date added

---

## Screen 3: Post Generator

**Purpose:** AI-generate and approve a Facebook post for a vacancy

**Layout:**

```
┌─────────────────────────────────────────────────────┐
│  Generate Facebook Post                              │
│  Vacancy: Senior Java Developer — Tel Aviv           │
├────────────────────────┬────────────────────────────┤
│  Vacancy Details       │  Generated Post            │
│                        │                            │
│  Title: Senior Java    │  ┌──────────────────────┐  │
│  Location: Tel Aviv    │  │                      │  │
│  Salary: 30-35K NIS    │  │  🔥 מחפשים Senior    │  │
│  Requirements:         │  │  Java Developer       │  │
│  - 5+ yrs Java        │  │  בתל אביב!           │  │
│  - Spring Boot         │  │                      │  │
│  - Microservices       │  │  מה אנחנו מציעים:   │  │
│  Benefits:             │  │  ✅ שכר 30-35K       │  │
│  - Hybrid work         │  │  ✅ עבודה היברידית   │  │
│  - Stock options       │  │  ✅ אופציות          │  │
│                        │  │                      │  │
│  Tone:                 │  │  שלחו קורות חיים     │  │
│  [Prof][Casual]        │  │  בפרטי 📩            │  │
│  [Urgent][Young]       │  │                      │  │
│                        │  │  [Edit Post]         │  │
│  [🔄 Regenerate]      │  └──────────────────────┘  │
│                        │                            │
│                        │  [✓ Approve & Select Groups]│
└────────────────────────┴────────────────────────────┘
```

**Left Panel — Vacancy Details:**
- Read-only view of vacancy data used for generation
- Tone selector (4 buttons, one active)
- Regenerate button

**Right Panel — Generated Post:**
- Editable text area with the AI-generated post
- Character count (target: under 500)
- Preview of how it will look in a Facebook group feed
- "Approve & Select Groups" button

**Logic:**
- On tone change → regenerate automatically
- On "Regenerate" → new variation with same tone
- On "Approve" → save post, navigate to Group Selector
- Post saved to database linked to vacancy

---

## Screen 4: Group Directory

**Purpose:** Manage the library of Facebook groups

**Layout:**

```
┌─────────────────────────────────────────────────────┐
│  Group Directory                     [+ Add Group]   │
├─────────────────────────────────────────────────────┤
│  Filters: [Category ▼] [City ▼] [Activity ▼]       │
│  Search: [________________________]                  │
│                                                      │
│  ┌────┬──────────────────┬────────┬──────┬───────┐  │
│  │ ☑  │ Group Name       │ City   │ Size │ Score │  │
│  ├────┼──────────────────┼────────┼──────┼───────┤  │
│  │ ☑  │ Tech Jobs TLV    │ TLV    │ 85K  │ ★★★★★ │  │
│  │ ☑  │ Hi-Tech Israel   │ All    │ 120K │ ★★★★  │  │
│  │ ☐  │ Jobs Haifa       │ Haifa  │ 45K  │ ★★★★  │  │
│  │ ☐  │ סטארטאפ ניישן   │ TLV    │ 62K  │ ★★★   │  │
│  │ ☐  │ דרושים באר שבע  │ B.Shva │ 28K  │ ★★★   │  │
│  └────┴──────────────────┴────────┴──────┴───────┘  │
│                                                      │
│  Showing 5 of 347 groups          [1] [2] [3] ...   │
│                                                      │
│  Selected: 2 groups    [Create Queue with Selected]  │
└─────────────────────────────────────────────────────┘
```

**Per-Group Data:**
- Checkbox (for batch selection)
- Group name (clickable → Group Detail)
- Facebook URL (icon link)
- Category tags
- City
- Member count
- Activity rating (1–5 stars)
- Last posted date
- Performance score (calculated: CVs per post average)
- Posting rules (tooltip or detail view)

**Actions:**
- Add Group: manual form (name, URL, category, city, size, rules)
- Edit Group: inline or detail view
- Bulk import: paste list of group URLs
- Export: CSV of group list with performance data

---

## Screen 5: Group Selector (within posting flow)

**Purpose:** Select groups for a specific vacancy posting

**Layout:**

Same as Group Directory but with:
- Vacancy context shown at top ("Posting: Senior Java Developer — Tel Aviv")
- Smart suggestions highlighted ("Recommended for this vacancy" badge)
- Warning indicators on recently-posted groups
- "Select Top N" quick button
- "Create Queue" button (replaces "Create Queue with Selected")

**Smart Suggestions Logic:**
1. Match vacancy category to group category
2. Match vacancy city to group city
3. Rank by group performance score
4. Exclude groups posted to < 24h ago
5. Show top 10 as "Recommended"

---

## Screen 6: Posting Queue

**Purpose:** Execute the posting flow — copy, open, post, mark

**Layout:**

```
┌─────────────────────────────────────────────────────┐
│  Posting Queue — Senior Java Developer               │
│  Progress: 3 / 8 groups posted                       │
├───────────────────────┬─────────────────────────────┤
│  Your Post            │  Groups                      │
│                       │                              │
│  🔥 מחפשים Senior    │  ✅ Tech Jobs TLV    14:32  │
│  Java Developer       │  ✅ Hi-Tech Israel   14:33  │
│  בתל אביב!           │  ✅ Jobs Center      14:35  │
│                       │  ➡️ סטארטאפ ניישן  [NEXT]  │
│  מה אנחנו מציעים:   │  ⬜ Dev Jobs Israel          │
│  ✅ שכר 30-35K       │  ⬜ Full Stack TLV          │
│  ✅ עבודה היברידית   │  ⬜ Junior Tech IL          │
│  ✅ אופציות          │  ⬜ React Israel             │
│                       │                              │
│  שלחו קורות חיים     │                              │
│  בפרטי 📩            │                              │
│                       │                              │
│  [📋 Copy Post]      │  [🔗 Open Group] [✓ Done]  │
│                       │  [⏭ Skip]                   │
└───────────────────────┴─────────────────────────────┘
```

**Left Panel:**
- Full post text (read-only)
- Large "Copy Post" button (copies to clipboard, shows confirmation toast)

**Right Panel:**
- Ordered list of groups
- Status per group: ✅ Posted (with timestamp) / ➡️ Current / ⬜ Pending / ⏭ Skipped
- For current group:
  - "Open Group" button (opens Facebook URL in new tab)
  - "Done" button (marks as posted, advances to next)
  - "Skip" button (skips with optional reason)
- Progress bar at top

**Keyboard Shortcuts:**
- `C` — Copy post
- `O` — Open group
- `D` — Mark as done
- `S` — Skip
- `N` — Next (same as Done)

**Logic:**
- On "Copy Post": copy text to clipboard, show toast "Copied!"
- On "Open Group": window.open(groupURL), focus returns to app
- On "Done": mark group as posted with current timestamp, highlight next group
- On "Skip": mark as skipped, optional reason prompt, advance
- Queue auto-saves progress — can close and resume later

---

## Screen 7: Results View

**Purpose:** Track posting results and group performance

**Layout:**

```
┌─────────────────────────────────────────────────────┐
│  Results                    [This Week ▼] [Export]   │
├─────────────────────────────────────────────────────┤
│  Summary: 89 posts │ 34 groups │ 31 CVs │ 3 hires  │
├─────────────────────────────────────────────────────┤
│                                                      │
│  By Vacancy:                                         │
│  ┌──────────────────┬───────┬─────┬──────┬───────┐  │
│  │ Vacancy          │ Posts │ CVs │ Qual │ Status│  │
│  ├──────────────────┼───────┼─────┼──────┼───────┤  │
│  │ Sr Java Dev      │ 12    │ 11  │ 4/5  │ Hired │  │
│  │ Sales Manager    │ 8     │ 4   │ 3/5  │ Open  │  │
│  │ QA Engineer      │ 15    │ 9   │ 3/5  │ Open  │  │
│  └──────────────────┴───────┴─────┴──────┴───────┘  │
│                                                      │
│  By Group (Top Performers):                          │
│  ┌──────────────────┬───────┬─────┬──────────────┐  │
│  │ Group            │ Posts │ CVs │ CVs/Post Avg │  │
│  ├──────────────────┼───────┼─────┼──────────────┤  │
│  │ Tech Jobs TLV    │ 23    │ 12  │ 0.52         │  │
│  │ Hi-Tech Israel   │ 19    │ 8   │ 0.42         │  │
│  │ Jobs Center      │ 15    │ 6   │ 0.40         │  │
│  └──────────────────┴───────┴─────┴──────────────┘  │
│                                                      │
└─────────────────────────────────────────────────────┘
```

**Views:**
1. **By Vacancy** — for each vacancy: groups posted, total CVs, quality rating, funnel status
2. **By Group** — for each group: total posts, total CVs, CVs-per-post average, trend
3. **Timeline** — calendar view of posting activity and results

**Per-Post Detail (drill-down):**
- Post text used
- Group posted to
- Timestamp
- Response count (comments, DMs)
- CV count
- Quality rating (1–5, recruiter-set)
- Notes

**Actions:**
- Update status (dropdown per row)
- Rate quality (star selector)
- Add response/CV counts
- Export to CSV
- Filter by date range, vacancy, group, status

---

## MVP Scope Definition

### Must Have (v1.0)
- [ ] Post Generator with 4 tones
- [ ] Group Directory with categories, cities, ratings
- [ ] Posting Queue with copy/open/mark flow
- [ ] Basic Results tracking (posted / got CVs / hired)
- [ ] Dashboard with daily stats

### Should Have (v1.1)
- [ ] Smart group suggestions per vacancy
- [ ] Group performance scoring (auto-calculated)
- [ ] Keyboard shortcuts in posting queue
- [ ] Team view (multiple recruiters)
- [ ] Batch mode for multiple vacancies

### Nice to Have (v1.2+)
- [ ] Post scheduling reminders
- [ ] Facebook Page posting (official API, where compliant)
- [ ] Group auto-discovery suggestions
- [ ] A/B testing for post variations
- [ ] Analytics dashboard with charts
