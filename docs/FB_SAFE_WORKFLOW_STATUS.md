# Facebook Safe Workflow — Status & Dependencies

---

## Overall Status: PRODUCT DEFINED — READY FOR BUILD

| Area | Status |
|---|---|
| Product definition | ✅ Complete |
| User workflow | ✅ Complete |
| Demo narrative | ✅ Complete |
| Screen specifications | ✅ Complete |
| Sales & outreach materials | ✅ Complete |
| Pilot offer | ✅ Complete |
| Engineering implementation | ⬜ Not started |

---

## Deliverables Created

| # | File | Contents | Status |
|---|---|---|---|
| 1 | `FB_SAFE_WORKFLOW_PRODUCT.md` | Product definition, positioning, pricing | ✅ |
| 2 | `FB_SAFE_WORKFLOW_DEMO.md` | Short pitch, long pitch, 5-min demo script, objection handling | ✅ |
| 3 | `FB_SAFE_WORKFLOW_OPERATOR_FLOW.md` | End-to-end operator workflow, daily routine, edge cases | ✅ |
| 4 | `FB_SAFE_WORKFLOW_SCREEN_SPEC.md` | 7 screen specs with wireframes, logic, MVP scope | ✅ |
| 5 | `FB_SAFE_WORKFLOW_SALES_PACK.md` | WhatsApp/Telegram/email pitches, discovery questions, follow-ups, cadences | ✅ |
| 6 | `FB_SAFE_WORKFLOW_PILOT_OFFER.md` | 14-day pilot structure, pricing, signup flow, tracking | ✅ |
| 7 | `FB_SAFE_WORKFLOW_STATUS.md` | This file — status tracking and dependencies | ✅ |

---

## Remaining Dependencies for Launch

### Must Resolve Before Pilot

| # | Dependency | Owner | Notes |
|---|---|---|---|
| 1 | **Group Directory seed data** | Ops | Need initial list of 200+ Israeli Facebook recruitment groups with categories, cities, member counts |
| 2 | **AI post generation model** | Eng | Hebrew-language vacancy-to-post generation. Needs: prompt engineering, tone profiles, character limit enforcement |
| 3 | **MVP frontend build** | Eng | 7 screens as specified. Recommend: React + simple state management |
| 4 | **Vacancy data integration** | Eng | Connect to existing vacancy data model in Recruit Autopilot core |
| 5 | **Clipboard API** | Eng | Reliable copy-to-clipboard across browsers |
| 6 | **Persistence layer** | Eng | Store: groups, posts, queue state, results, user data |
| 7 | **User auth & multi-tenancy** | Eng | Agency accounts with recruiter seats |

### Must Resolve Before Paid Launch

| # | Dependency | Owner | Notes |
|---|---|---|---|
| 8 | **Payment integration** | Eng | ILS billing, likely Stripe or local provider |
| 9 | **Usage metering** | Eng | Track posts/month for Starter tier limits |
| 10 | **Onboarding flow** | Product | In-app guided first-run experience |
| 11 | **Group import tool** | Eng | Let agencies bulk-import their own groups |
| 12 | **Export/reporting** | Eng | CSV export of results data |

### Nice to Have for Launch

| # | Dependency | Owner | Notes |
|---|---|---|---|
| 13 | **Facebook Page API integration** | Eng | For compliant Page posting (not groups). Research API requirements |
| 14 | **Analytics dashboard** | Eng | Charts, trends, group comparison views |
| 15 | **Team management UI** | Eng | Invite recruiters, view team stats |
| 16 | **Mobile-responsive queue** | Eng | Some recruiters may post from phone |

---

## Recommended Build Order

```
Phase 1 — Core (2-3 weeks)
├── Group Directory (data model + UI)
├── Post Generator (AI + UI)
├── Posting Queue (copy/open/mark flow)
└── Basic Results tracking

Phase 2 — Polish (1-2 weeks)
├── Dashboard
├── Vacancy list integration
├── Group selector with smart suggestions
└── Onboarding flow

Phase 3 — Scale (2-3 weeks)
├── User auth & multi-tenancy
├── Payment integration
├── Usage metering
└── Team features
```

---

## Risks

| Risk | Impact | Mitigation |
|---|---|---|
| Group directory goes stale | Low engagement | Assign ops resource for monthly curation. Add user-contributed group ratings |
| AI posts feel generic | Low post quality, poor results | Invest in Hebrew prompt engineering. A/B test tones. Let users edit |
| Recruiters resist manual posting | Low adoption | Emphasize speed (15 sec/group). Show ban risk data. Track and share time savings |
| Facebook changes group posting rules | Feature disruption | Monitor Facebook policy updates. Workflow is inherently adaptive since human posts |
| Low pilot conversion | Revenue delay | Optimize onboarding. Ensure first-post happens on Day 0. Follow up aggressively |

---

## Decision Log

| Date | Decision | Rationale |
|---|---|---|
| 2026-03-30 | No automatic group posting | Facebook ToS violation risk. Compliance-safe workflow chosen instead |
| 2026-03-30 | Human always clicks "Post" | Core product principle. Zero automation touching Facebook |
| 2026-03-30 | Hebrew-first content generation | Primary market is Israeli recruitment agencies |
| 2026-03-30 | 14-day free pilot model | Low-friction entry. Builds usage data before conversion |
| 2026-03-30 | Group directory as managed asset | Pre-loaded with 200+ groups. Competitive moat through curation |
