# RecruitBot — Known Limitations

## 1. Localhost Only

**Impact**: Dashboard accessible only from local machine. Cannot share URL with clients.
**Workaround**: Use VPS deployment (Dockerfile ready in moltbot-dashboard) or Cloudflare Tunnel for temporary public access. For demos, screen share.

## 2. Bot Cannot Post to Channels Without Admin Access

**Impact**: Campaign posting fails with 403 if bot is not added as admin to target Telegram channels.
**Workaround**: Before activating a campaign, manually add `@AutopillotRecruit_bot` as admin to each target channel/group. Use "Check" button in Sources to verify.

## 3. No Real-Time AI Conversation — Screening is Question-Based

**Impact**: Bot asks pre-defined questions sequentially, not free-form AI conversation. AI is only used for scoring after all questions are answered.
**Workaround**: This is by design for MVP. Sufficient for screening. Custom questions per vacancy are supported.

## 4. Single Company at a Time for Bot

**Impact**: Bot uses the first active company (by ID). Cannot serve multiple companies simultaneously from one bot instance.
**Workaround**: Deactivate other companies. For multi-tenant, deploy separate bot instances with separate tokens.

## 5. No Duplicate Candidate Prevention Across Vacancies

**Impact**: Same Telegram user applying to different vacancies creates separate candidate records.
**Workaround**: Filter by `tg_user_id` in dashboard to find duplicate entries. Manual review required.

## 6. Campaign Posting Has No Duplicate Prevention Per Interval

**Impact**: If scheduler restarts mid-interval, may re-post to the same channels.
**Workaround**: Set reasonable intervals (4+ hours). Monitor channel for duplicates after scheduler restart.

## 7. OpenAI API Cost

**Impact**: Each candidate scoring costs ~$0.001 (gpt-4o-mini). At scale, costs accumulate.
**Workaround**: Rule-based fallback activates automatically if OpenAI fails. Monitor API usage via OpenAI dashboard.

## 8. No Email/WhatsApp Notifications

**Impact**: Recruiter must check dashboard manually for new candidates.
**Workaround**: Set browser bookmark, check periodically. Future: add Telegram notification to owner.

## 9. No HTTPS on Dashboard

**Impact**: Login credentials sent in plain HTTP over localhost.
**Workaround**: Acceptable for localhost. For VPS: nginx + Let's Encrypt (documented in deploy-vps.sh).

## 10. Bot Restart Policy

**Impact**: Bot container has `restart: no`. If it crashes, it stays down until manually restarted.
**Workaround**: Monitor with `docker compose ps bot`. Change to `restart: unless-stopped` for production. Currently set to `no` to prevent 409 restart loops during setup.
