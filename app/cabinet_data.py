"""Tenant-safe bootstrap data for the white SPA cabinet (design from claude.ai/design).

`build_cabinet_boot()` reads the REAL database, strictly scoped to one company_id,
and returns a plain dict shaped exactly like the SPA's `window.PA.*` arrays so the
beautiful design renders real data instead of the mock fixtures in app-data.js.

Security: every query is filtered by the company_id that the caller already
validated against the signed session (see auth.revalidate_company). This module
never reads company_id from request input and never falls back to another tenant.
Secrets (tg_api_hash / fb_access_token) are only ever tested for presence — their
plaintext is never placed in the boot payload.
"""
import json
from datetime import datetime, timedelta

from .models import (
    Company, User, Vacancy, Source, Campaign, CampaignSource, Candidate,
    CandidateStatus, PostingAttempt, UserRole,
)

# CandidateStatus (DB) -> design status token (localised client-side via ls.*)
_STATUS_MAP = {
    "new": "opened",
    "qualifying": "opened",
    "interviewing": "interview_scheduled",
    "passed": "got_responses",
    "hired": "hired",
    "rejected": "cancelled",
}

# listing_type -> sidebar/vertical icon name + label key handled client-side
_VERT_MAP = {
    "recruitment": ("users", "Вакансия"),
    "job": ("users", "Вакансия"),
    "real_estate": ("home", "Недвижимость"),
    "rental": ("home", "Недвижимость"),
    "property": ("home", "Недвижимость"),
    "auto": ("car", "Авто"),
    "car": ("car", "Авто"),
    "service": ("wrench", "Услуга"),
}

_RU_DOW = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"]


def _classify(c):
    """Real classification or derived from score; always one of hot/warm/cold."""
    v = (c.classification or "").lower()
    if v in ("hot", "warm", "cold"):
        return v
    s = c.score if c.score is not None else 0
    if s >= 70:
        return "hot"
    if s >= 40:
        return "warm"
    return "cold"


def _parse_chat(raw):
    """chat_log_json [{role,text,ts}] -> design [[who, text]] (who = bot|lead)."""
    out = []
    try:
        rows = json.loads(raw or "[]")
    except Exception:
        return out
    if not isinstance(rows, list):
        return out
    for r in rows:
        if isinstance(r, dict):
            role = str(r.get("role") or r.get("from") or "").lower()
            text = r.get("text") or r.get("content") or r.get("message") or ""
        elif isinstance(r, (list, tuple)) and len(r) >= 2:
            role, text = str(r[0]).lower(), r[1]
        else:
            continue
        who = "bot" if role in ("bot", "assistant", "system", "ai") else "lead"
        if text:
            out.append([who, str(text)])
    return out


def _vert(listing_type):
    return _VERT_MAP.get((listing_type or "recruitment").lower(), ("doc", "Объявление"))


def _ico_initial(name):
    name = (name or "").strip()
    return name[0].upper() if name else "•"


def build_cabinet_boot(db, owner_id, company_id, user=None):
    """Return the full PA_BOOT dict for one tenant. Safe for company_id=None."""
    companies = (
        db.query(Company)
        .filter(Company.owner_id == owner_id, Company.is_active == True)  # noqa: E712
        .order_by(Company.id.asc())
        .all()
    )
    boot = {
        "current_company": str(company_id) if company_id is not None else None,
        "companies": [
            {
                "id": str(co.id),
                "name": co.name,
                "type": (co.logo_emoji and "") or "",  # filled below
                "logo": co.logo_emoji or _ico_initial(co.name),
                "active": (co.id == company_id),
            }
            for co in companies
        ],
    }

    company = None
    if company_id is not None:
        company = db.query(Company).get(company_id)
        # belt-and-suspenders: never serve a company the owner doesn't own
        if company and str(company.owner_id) != str(owner_id):
            company = None

    # ── Trial (from the logged-in user row) ──────────────────────────────────
    trial = {"days": None, "plan": "Pro", "expired": False}
    if user is not None and getattr(user, "trial_expires_at", None):
        delta = user.trial_expires_at - datetime.utcnow()
        trial = {
            "days": max(0, delta.days),
            "plan": "Pro",
            "expired": delta.total_seconds() <= 0,
        }
    boot["trial"] = trial

    # company subtitle (vertical · plan) once we know plan/trial
    plan_label = "Pro"  # plan name only; trial state is shown via the localized trial chip (foot.trial)
    for c in boot["companies"]:
        c["type"] = plan_label

    # static plan catalogue (billing screen); current = Pro for now
    # Literals are the RU source/fallback; tk/fk are i18n keys (cabinet-i18n.js)
    # so the billing screen re-translates on every live RU/EN/HE switch.
    boot["plans"] = [
        {"id": "starter", "name": "Starter", "price": "299₪", "tagline": "Одно объявление, ручной постинг",
         "tk": "pl.starter.tag",
         "feats": ["1 активное объявление", "10 каналов постинга", "AI-бот скрининга", "Лиды и базовый дашборд"],
         "fk": ["pl.starter.f1", "pl.starter.f2", "pl.starter.f3", "pl.starter.f4"]},
        {"id": "pro", "name": "Pro", "price": "899₪", "tagline": "Активный мультиканальный постинг",
         "tk": "pl.pro.tag",
         "featured": True, "current": True,
         "feats": ["5 активных объявлений", "50 каналов постинга", "Планировщик и ночной режим",
                   "Аналитика и воронка", "Приоритетная поддержка"],
         "fk": ["pl.pro.f1", "pl.pro.f2", "pl.pro.f3", "pl.pro.f4", "pl.pro.f5"]},
        {"id": "agency", "name": "Agency", "price": "1999₪", "tagline": "Агентствам и нескольким компаниям",
         "tk": "pl.agency.tag",
         "feats": ["Безлимит объявлений", "Мультикомпания", "API и вебхуки",
                   "White-label кабинет", "Персональный менеджер"],
         "fk": ["pl.agency.f1", "pl.agency.f2", "pl.agency.f3", "pl.agency.f4", "pl.agency.f5"]},
    ]
    boot["ad_limit"] = 5  # Pro plan

    if company is None:
        # Honest empty state — valid arrays, zero rows.
        boot.update({
            "leads": [], "counts": {"hot": 0, "warm": 0, "withPhone": 0, "all": 0, "spam": 0, "processed": 0},
            "campaigns": [], "attempts": [], "queue": [], "ads": [],
            "tg_groups": [], "fb_sources": [], "sources": [],
            "funnel": [], "onboard": _onboard(False, False, False, False, False, False),
            "bot": {"tone": "friendly", "lang": "auto", "positive": "", "negative": "",
                    "greet": "", "reject": "", "success": ""},
            "analytics": _empty_analytics(), "team": [],
            "screens": _screens(0, 0, 0, 0, 0, 0, 0, False, trial),
        })
        return boot

    cid = company.id

    # ── Candidates / leads ───────────────────────────────────────────────────
    cands = (
        db.query(Candidate)
        .filter(Candidate.company_id == cid)
        .order_by(Candidate.score.is_(None), Candidate.score.desc(), Candidate.created_at.desc())
        .limit(200)
        .all()
    )
    leads = []
    for c in cands:
        cls = _classify(c)
        leads.append({
            "id": c.id,
            "name": c.full_name or (c.tg_username or f"Лид #{c.id}"),
            "user": ("@" + c.tg_username.lstrip("@")) if c.tg_username else "",
            "cls": cls,
            "score": c.score if c.score is not None else 0,
            "status": _STATUS_MAP.get(c.status.value if c.status else "new", "opened"),
            "phone": c.phone or "—",
            "ad": (c.vacancy.title if c.vacancy else "—"),
            "summary": c.summary or "",
            "chat": _parse_chat(c.chat_log_json),
        })
    hot = sum(1 for l in leads if l["cls"] == "hot")
    warm = sum(1 for l in leads if l["cls"] == "warm")
    with_phone = sum(1 for l in leads if l["cls"] == "hot" and l["phone"] and l["phone"] != "—")
    boot["leads"] = leads
    boot["counts"] = {
        "hot": hot, "warm": warm, "withPhone": with_phone,
        "all": len(leads), "spam": 0, "processed": len(leads),
    }

    # ── Vacancies / ads ──────────────────────────────────────────────────────
    vacs = (
        db.query(Vacancy)
        .filter(Vacancy.company_id == cid)
        .order_by(Vacancy.is_active.desc(), Vacancy.created_at.desc())
        .all()
    )
    lead_by_vac = {}
    for c in cands:
        if c.vacancy_id:
            lead_by_vac[c.vacancy_id] = lead_by_vac.get(c.vacancy_id, 0) + 1
    ads = []
    for v in vacs:
        ic, vlabel = _vert(v.listing_type)
        preview = (v.final_post_body or v.body or "").strip().replace("\n", " ")
        if len(preview) > 180:
            preview = preview[:177] + "…"
        ads.append({
            "id": f"v{v.id}", "vid": v.id, "title": v.title,
            "vert": ic, "vertLabel": vlabel,
            "city": v.city or "", "price": v.salary_text or "",
            "active": bool(v.is_active), "leads": lead_by_vac.get(v.id, 0),
            "views": 0, "preview": preview or "—",
        })
    boot["ads"] = ads
    active_ads = sum(1 for a in ads if a["active"])

    # ── Sources (unified) + TG / FB split ────────────────────────────────────
    srcs = (
        db.query(Source)
        .filter(Source.company_id == cid, Source.is_active == True)  # noqa: E712
        .order_by(Source.platform.asc(), Source.id.asc())
        .all()
    )

    def _ready(s):
        if s.platform == "facebook":
            return "format" if (s.posting_mode or "auto") != "auto" else ("ready" if s.last_check_ok else "check")
        return "ready" if s.last_check_ok else "check"

    sources, tg_groups, fb_sources = [], [], []
    for s in srcs:
        nm = s.label or s.tg_ref
        mode = "Авто" if (s.posting_mode or "auto") == "auto" else "Ручной"
        kind = {"group": "Группа", "channel": "Канал", "chat": "Чат"}.get(
            (s.source_type.value if s.source_type else "group"), "Группа")
        plat = "Telegram" if s.platform == "telegram" else "Facebook"
        sources.append({"name": nm, "platform": plat, "kind": kind, "mode": mode, "ready": _ready(s)})
        if s.platform == "telegram":
            tg_groups.append({"name": nm, "members": "", "folder": s.folder or "—", "on": True})
        else:
            fb_sources.append({"name": nm, "mode": mode, "ready": _ready(s)})
    boot["sources"] = sources
    boot["tg_groups"] = tg_groups
    boot["fb_sources"] = fb_sources
    tg_count = len(tg_groups)
    fb_count = len(fb_sources)

    has_company = True
    has_vacancy = len(vacs) > 0
    has_telegram = bool(company.tg_api_id) or tg_count > 0
    has_facebook = bool(company.fb_access_token) or fb_count > 0

    # ── Campaigns + posting attempts ─────────────────────────────────────────
    camps = (
        db.query(Campaign)
        .filter(Campaign.company_id == cid)
        .order_by(Campaign.created_at.desc())
        .all()
    )
    campaigns = []
    for cm in camps:
        nch = db.query(CampaignSource).filter(CampaignSource.campaign_id == cm.id).count()
        campaigns.append({
            "name": cm.name or (cm.vacancy.title if cm.vacancy else "Кампания"),
            "ad": (cm.vacancy.title if cm.vacancy else "—"),
            "channels": f"{nch} назнач." if nch else "—",
            "leads": lead_by_vac.get(cm.vacancy_id, 0),
            "status": "posted" if cm.is_running else "pending",
            "statusLabel": "Активна" if cm.is_running else "На паузе",
        })
    boot["campaigns"] = campaigns
    active_camps = sum(1 for c in camps if c.is_running)

    attempts_rows = (
        db.query(PostingAttempt)
        .filter(PostingAttempt.company_id == cid)
        .order_by(PostingAttempt.created_at.desc())
        .limit(12)
        .all()
    )
    attempts = []
    posted_count = 0
    manual_count = 0
    for a in attempts_rows:
        rs = (a.result_status or "pending")
        if rs == "posted":
            posted_count += 1
        if (a.action_taken or "") in ("manual_action_required", "manual"):
            manual_count += 1
        attempts.append({
            "group": a.destination or a.destination_ref or "—",
            "ch": "Telegram" if a.platform == "telegram" else "Facebook",
            "time": a.created_at.strftime("%H:%M") if a.created_at else "",
            "status": rs,
            "label": {"posted": "Опубликовано", "pending": "В очереди",
                      "manual_action_required": "Ручное действие"}.get(rs, rs),
        })
    boot["attempts"] = attempts
    boot["queue"] = [
        {"title": a["group"] + " (Facebook)", "sub": "Подтвердите публикацию вручную", "ic": "fb"}
        for a in attempts if a["ch"] == "Facebook" and a["status"] != "posted"
    ][:5]

    posts_total = (
        db.query(PostingAttempt)
        .filter(PostingAttempt.company_id == cid, PostingAttempt.result_status == "posted")
        .count()
    )
    closed = sum(1 for l in leads if l["status"] == "hired")
    has_campaign = len(camps) > 0
    has_posted = posts_total > 0

    # ── Funnel + analytics (real, best-effort) ───────────────────────────────
    passed_bot = sum(1 for l in leads if l["score"] and l["score"] > 0)
    boot["funnel"] = [
        {"label": "Все отклики", "lk": "cb.fn.all", "val": len(leads), "color": "#0071e3"},
        {"label": "Прошли бота", "lk": "cb.fn.bot", "val": passed_bot, "color": "#3a8dff"},
        {"label": "Тёплые", "lk": "cb.fn.warm", "val": warm + hot, "color": "var(--warning)"},
        {"label": "Горячие", "lk": "cb.fn.hot", "val": hot, "color": "var(--danger)"},
        {"label": "Закрыто", "lk": "cb.fn.closed", "val": closed, "color": "var(--success)"},
    ]

    # 7-day activity from candidate created_at
    today = datetime.utcnow().date()
    day_counts = {today - timedelta(days=i): 0 for i in range(7)}
    for c in cands:
        if c.created_at and c.created_at.date() in day_counts:
            day_counts[c.created_at.date()] += 1
    days = [{"d": _RU_DOW[(today - timedelta(days=i)).weekday()],
             "dk": "cb.dow.%d" % (today - timedelta(days=i)).weekday(),
             "v": day_counts[today - timedelta(days=i)]}
            for i in range(6, -1, -1)]

    langs_map = {}
    for c in cands:
        lg = (c.language or "ru").lower()[:2]
        langs_map[lg] = langs_map.get(lg, 0) + 1
    total_lg = sum(langs_map.values()) or 1
    lg_label = {"ru": "Русский", "he": "עברית", "en": "English"}
    lg_color = {"ru": "#0071e3", "he": "var(--warning)", "en": "var(--success)"}
    _lg_lk = {"ru": "bot.la.ru", "he": "bot.la.he", "en": "bot.la.en"}
    langs = [{"label": lg_label.get(k, k), "lk": _lg_lk.get(k), "val": v, "pct": round(v * 100 / total_lg),
              "color": lg_color.get(k, "#3a8dff")}
             for k, v in sorted(langs_map.items(), key=lambda kv: -kv[1])]

    conv = (closed * 100.0 / len(leads)) if leads else 0
    boot["analytics"] = {
        "kpi": [
            {"ic": "send", "label": "Публикаций", "lk": "cb.k.posts", "val": str(posts_total),
             "sub": "за всё время", "sk": "cb.ks.alltime", "up": posts_total > 0},
            {"ic": "bot", "label": "Обработано ботом", "lk": "cb.k.processed", "val": str(len(leads)),
             "sub": "лидов от бота", "sk": "cb.ks.frombot"},
            {"ic": "flame", "label": "Горячих лидов", "lk": "cb.k.hot", "val": str(hot),
             "sub": f"{with_phone} с телефоном", "sk": "cb.ks.withphone", "sv": {"n": with_phone}, "up": hot > 0},
            {"ic": "check", "label": "Закрыто сделок", "lk": "cb.k.closed", "val": str(closed),
             "sub": f"конверсия {conv:.1f}%", "sk": "cb.ks.conv", "sv": {"x": f"{conv:.1f}"}},
        ],
        "funnel": boot["funnel"],
        "langs": langs,
        "days": days,
        "ops": [
            {"label": "Постов опубликовано", "lk": "cb.ops.posts", "val": str(posts_total)},
            {"label": "Ручных действий", "lk": "cb.ops.manual", "val": str(manual_count)},
            {"label": "Кампаний активно", "lk": "cb.ops.camps", "val": str(active_camps)},
            {"label": "Назначений", "lk": "cb.ops.sources", "val": str(len(sources))},
        ],
        "ads": [{"title": a["title"], "leads": a["leads"],
                 "conv": "—", "pct": min(100, a["leads"] * 10)} for a in ads[:6]],
    }

    # ── Onboard + bot config + team ──────────────────────────────────────────
    boot["onboard"] = _onboard(has_company, has_vacancy, has_telegram, has_facebook, has_campaign, has_posted)
    boot["bot"] = {
        "tone": company.ai_tone.value if company.ai_tone else "friendly",
        "lang": company.ai_language.value if company.ai_language else "auto",
        "positive": company.ai_positive_prompt or "",
        "negative": company.ai_negative_prompt or "",
        "greet": company.ai_greeting_template or "",
        "reject": company.ai_rejection_template or "",
        "success": company.ai_success_template or "",
    }

    team_users = (
        db.query(User)
        .filter(User.company_id == cid)
        .order_by(User.id.asc())
        .all()
    )
    team = []
    for u in team_users:
        is_owner = u.role in (UserRole.owner, UserRole.admin)
        team.append({
            "name": (u.email.split("@")[0] if u.email else "—"),
            "email": u.email or "",
            "role": "Владелец" if is_owner else "Оператор",
            "rk": "role.owner" if is_owner else "role.operator",
            "you": bool(user and u.id == getattr(user, "id", None)),
            "active": bool(u.is_active),
        })
    boot["team"] = team

    boot["screens"] = _screens(hot, with_phone, active_ads, len(ads), tg_count, fb_count,
                               posts_total, has_facebook, trial,
                               has_telegram=has_telegram, manual=manual_count,
                               active_camps=active_camps)
    return boot


def _onboard(has_company, has_vacancy, has_tg, has_fb, has_campaign, has_posted):
    return [
        {"n": "01", "t": "Компания", "lk": "cb.ob.company", "done": has_company, "go": "company"},
        {"n": "02", "t": "Объявление", "lk": "cb.ob.ad", "done": has_vacancy, "go": "ads"},
        {"n": "03", "t": "Telegram", "done": has_tg, "go": "channel-tg"},
        {"n": "04", "t": "Facebook", "done": has_fb, "go": "channel-fb"},
        {"n": "05", "t": "Кампания", "lk": "cb.ob.campaign", "done": has_campaign, "go": "campaigns"},
        {"n": "06", "t": "Первый постинг", "lk": "cb.ob.first", "done": has_posted, "go": "campaigns"},
    ]


def _empty_analytics():
    return {"kpi": [], "funnel": [], "langs": [], "days": [], "ops": [], "ads": []}


def _fact(ic, tone, label, val, lk=None, vk=None):
    """Copilot fact. label/val are RU fallbacks; lk/vk are i18n keys the client
    resolves via t() so the panel re-translates on language switch."""
    f = {"ic": ic, "tone": tone, "label": label, "val": str(val)}
    if lk:
        f["lk"] = lk
    if vk:
        f["vk"] = vk
    return f


def _act(label, lk, go, ico):
    return {"label": label, "lk": lk, "go": go, "ico": ico}


def _warn(text, lk):
    return {"tone": "warn", "text": text, "lk": lk}


def _summary(ru, sk, sv=None):
    """Copilot summary: RU fallback + i18n key (+ template vars) for EN/HE."""
    s = {"summary": ru, "sk": sk}
    if sv:
        s["sv"] = sv
    return s


def _screens(hot, with_phone, active_ads, total_ads, tg_count, fb_count,
             posts, has_fb, trial, has_telegram=False, manual=0, active_camps=0):
    """Real Operator-Copilot content per screen. RU text is the fallback; lk/sk/vk
    are i18n keys (see cabinet-i18n.js) the client resolves via t() so the whole
    panel re-translates on language switch — no Russian leak in EN/HE."""
    td = trial.get("days")
    yn = lambda b: ("да" if b else "нет")
    ynk = lambda b: ("cb.v.yes" if b else "cb.v.no")
    rk = lambda b: ("cb.v.ready" if b else "cb.v.no")
    leads_cp = dict(tone=("running" if hot else "setup"),
        facts=[_fact("flame", "bad", "Горячих", hot, "cb.f.hot"),
               _fact("phone", "ok", "С телефоном", with_phone, "cb.f.withphone")],
        warn=[], action=_act("Открыть первого", "cb.a.open_first", "leads", "flame"))
    leads_cp.update(_summary(f"{hot} горячих лидов ждут ответа — звоните тем, кто оставил телефон, пока контакт «тёплый»."
                             if hot else "Пока нет горячих лидов. Запустите постинг — отклики появятся здесь.",
                             "cb.cps.leads" if hot else "cb.cps.leads0", {"hot": hot} if hot else None))

    dash_cp = dict(tone="setup",
        facts=[_fact("doc", "ok" if active_ads else "warn", "Объявлений", active_ads, "cb.f.ads"),
               _fact("send", "ok" if has_telegram else "warn", "Telegram", yn(has_telegram), None, rk(has_telegram)),
               _fact("fb", "ok" if has_fb else "warn", "Facebook", yn(has_fb), None, rk(has_fb))],
        warn=([] if has_fb else [_warn("Facebook не подключён — половина каналов недоступна.", "cb.w.fb_half")]),
        action=(_act("Подключить Facebook", "cb.a.connect_fb", "channel-fb", "fb") if not has_fb
                else _act("К объявлениям", "cb.a.to_ads", "ads", "doc")))
    dash_cp.update(_summary("Подключите Facebook и запустите кампанию — постинг пойдёт автоматически." if not has_fb
                            else "Каналы на месте. Следите за горячими лидами на экране «Лиды».",
                            "cb.cps.dash_fb" if not has_fb else "cb.cps.dash_ok"))

    camp_cp = dict(tone=("manual" if manual else "running"),
        facts=[_fact("rocket", "ok", "Активны", active_camps, "cb.f.active"),
               _fact("alert", "warn" if manual else "ok", "Ручных", manual, "cb.f.manual")],
        warn=[], action=_act("Обновить", "cb.a.refresh", "campaigns", "refresh"))
    camp_cp.update(_summary(f"Активных кампаний: {active_camps}." + (f" Ручных действий по Facebook: {manual}." if manual else ""),
                            "cb.cps.campaigns_m" if manual else "cb.cps.campaigns",
                            {"active": active_camps, "manual": manual} if manual else {"active": active_camps}))

    ads_cp = dict(tone=("running" if active_ads else "setup"),
        facts=[_fact("doc", "ok", "Активных", active_ads, "cb.f.active"),
               _fact("lock", "warn", "Лимит Pro", f"{active_ads} / 5", "cb.f.limit")],
        warn=[], action=_act("Создать объявление", "cb.a.create_ad", "ads", "plus"))
    ads_cp.update(_summary(f"Активны {active_ads} из {total_ads} объявлений (лимит Pro 5)." if total_ads
                           else "Создайте первое объявление — одно объявление публикуется во все каналы.",
                           "cb.cps.ads" if total_ads else "cb.cps.ads0",
                           {"active": active_ads, "total": total_ads} if total_ads else None))

    tg_cp = dict(tone=("running" if has_telegram else "setup"),
        facts=[_fact("check", "ok" if has_telegram else "bad", "Подключено", yn(has_telegram), "cb.f.connected", ynk(has_telegram)),
               _fact("send", "ok", "Групп", tg_count, "cb.f.groups")],
        warn=[], action=_act("К назначениям", "cb.a.to_sources", "sources", "target"))
    tg_cp.update(_summary(f"Telegram подключён, групп для постинга: {tg_count}." if has_telegram
                          else "Подключите Telegram, чтобы постить в группы автоматически.",
                          "cb.cps.tg" if has_telegram else "cb.cps.tg0", {"n": tg_count} if has_telegram else None))

    fb_cp = dict(tone=("running" if has_fb else "setup"),
        facts=[_fact("fb", "ok" if has_fb else "bad", "Подключено", yn(has_fb), "cb.f.connected", ynk(has_fb)),
               _fact("target", "warn", "FB-групп", fb_count, "cb.f.fbgroups")],
        warn=([] if has_fb else [_warn("Без Facebook доступна только половина охвата.", "cb.w.fb_reach")]),
        action=_act("Подключить Facebook", "cb.a.connect_fb", "channel-fb", "fb"))
    fb_cp.update(_summary(f"Facebook подключён, источников: {fb_count}." if has_fb
                          else "Facebook ещё не подключён. Подключите через OAuth или вставьте ссылки на группы.",
                          "cb.cps.fb" if has_fb else "cb.cps.fb0", {"n": fb_count} if has_fb else None))

    src_cp = dict(tone="manual",
        facts=[_fact("send", "ok", "TG", tg_count), _fact("fb", "warn", "FB", fb_count)],
        warn=[], action=_act("Проверить все", "c.check_all", "sources", "refresh"))
    src_cp.update(_summary(f"Назначений: Telegram {tg_count}, Facebook {fb_count}.", "cb.cps.sources",
                           {"tg": tg_count, "fb": fb_count}))

    bot_cp = dict(tone="running",
        facts=[_fact("bot", "ok", "Статус", "активен", "cb.f.status", "cb.v.active"),
               _fact("flame", "bad", "Горячих", hot, "cb.f.hot")],
        warn=[], action=_act("Протестировать бота", "cb.a.test_bot", "bot", "bot"))
    bot_cp.update(_summary("Бот общается с откликами, отсеивает спам и помечает горячих лидов. Проверьте критерии «горячий».",
                           "cb.cps.bot"))

    an_cp = dict(tone="running",
        facts=[_fact("send", "ok", "Публикаций", posts, "cb.f.posts"),
               _fact("flame", "bad", "Горячих", hot, "cb.f.hot")],
        warn=[], action=_act("К объявлениям", "cb.a.to_ads", "ads", "doc"))
    an_cp.update(_summary(f"Публикаций {posts}, горячих лидов {hot}." if posts else "Данных пока мало — запустите постинг.",
                          "cb.cps.analytics" if posts else "cb.cps.analytics0",
                          {"posts": posts, "hot": hot} if posts else None))

    co_cp = dict(tone="setup",
        facts=[_fact("users", "ok", "Команда", "—", "cb.f.team")],
        warn=[], action=_act("Сохранить профиль", "cb.a.save_profile", "company", "users"))
    co_cp.update(_summary("Профиль компании и маршрутизация горячих лидов. Укажите, куда слать горячих, чтобы не упустить контакт.",
                          "cb.cps.company"))

    bl_active = td is not None and not trial.get("expired")
    bl_cp = dict(tone="setup",
        facts=[_fact("card", "ok", "Тариф", "Pro", "cb.f.plan"),
               _fact("clock", "warn", "Осталось", (str(td) if td is not None else "—"), "cb.f.left")],
        warn=[], action=_act("Перейти на Pro", "cb.a.to_pro", "billing", "card"))
    bl_cp.update(_summary(
        (f"Пробный период Pro — осталось {td} дней. После окончания автопостинг встанет на паузу." if bl_active
         else ("Пробный период истёк — выберите тариф, чтобы возобновить автопостинг." if trial.get("expired")
               else "Тариф Pro активен.")),
        ("cb.cps.billing" if bl_active else ("cb.cps.billing_exp" if trial.get("expired") else "cb.cps.billing_paid")),
        {"days": td} if bl_active else None))

    return {
        "leads": {"cp": leads_cp}, "dashboard": {"cp": dash_cp}, "campaigns": {"cp": camp_cp},
        "ads": {"cp": ads_cp}, "channel-tg": {"cp": tg_cp}, "channel-fb": {"cp": fb_cp},
        "sources": {"cp": src_cp}, "bot": {"cp": bot_cp}, "analytics": {"cp": an_cp},
        "company": {"cp": co_cp}, "billing": {"cp": bl_cp},
    }
