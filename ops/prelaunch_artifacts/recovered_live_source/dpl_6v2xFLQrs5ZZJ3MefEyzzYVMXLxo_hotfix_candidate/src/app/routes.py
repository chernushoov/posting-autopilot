from __future__ import annotations

from datetime import datetime

from flask import flash, redirect, render_template, request, session, url_for
from sqlalchemy.orm import joinedload

from .auth import login_required
from .config import Config
from .db import db_session
from .models import (
    Ad,
    AdGroupTarget,
    AdStatus,
    ConnectionStatus,
    FacebookAccount,
    Group,
    HistoryStatus,
    PostHistoryItem,
    PostingRun,
    ProfileSetting,
    RunStatus,
    Schedule,
    ScheduleStatus,
    TelegramAccount,
    User,
)
from .telegram import telegram_send_message_safe

SAMPLE_TELEGRAM_REFS = {"@startup_hiring_alerts", "@telaviv_job_drops", "@remote_ops_broadcast"}


def telegram_public_context() -> dict[str, str]:
    return {
        "telegram_bot_handle": Config.TELEGRAM_BOT_PUBLIC_HANDLE,
        "telegram_bot_url": Config.TELEGRAM_BOT_PUBLIC_URL,
    }


def register_routes(app):
    @app.get("/")
    def home():
        if session.get("user_id"):
            return redirect(url_for("channel_connect"))
        return redirect(url_for("login"))

    @app.route("/login", methods=["GET", "POST"])
    def login():
        if request.method == "POST":
            email = request.form.get("email", "").strip().lower()
            password = request.form.get("password", "").strip()
            db = db_session()
            user = db.query(User).filter(User.email == email, User.password == password).first()
            if user:
                user_id = user.id
                user_name = user.full_name
                db.close()
                session["user_id"] = user_id
                session["user_name"] = user_name
                return redirect(url_for("channel_connect"))
            db.close()
            return render_template("login.html", error="Wrong email or password.", **telegram_public_context())
        return render_template(
            "login.html",
            demo_email=Config.DEMO_EMAIL,
            demo_password=Config.DEMO_PASSWORD,
            **telegram_public_context(),
        )

    @app.get("/logout")
    def logout():
        session.clear()
        return redirect(url_for("login"))

    @app.route("/connect", methods=["GET", "POST"])
    @app.route("/facebook-connect", methods=["GET", "POST"])
    @login_required
    def channel_connect():
        db = db_session()
        account = db.query(FacebookAccount).filter(FacebookAccount.user_id == session["user_id"]).order_by(FacebookAccount.id.desc()).first()
        telegram_account = (
            db.query(TelegramAccount)
            .filter(TelegramAccount.user_id == session["user_id"])
            .order_by(TelegramAccount.id.desc())
            .first()
        )
        telegram_destinations = (
            db.query(Group)
            .filter(Group.platform == "telegram", Group.is_active == True)
            .order_by(Group.activity_score.desc(), Group.name.asc())
            .all()
        )
        if request.method == "POST":
            provider = request.form.get("provider", "facebook").strip()
            if provider == "facebook":
                if not account:
                    account = FacebookAccount(user_id=session["user_id"])
                    db.add(account)
                account.account_name = request.form.get("account_name", "").strip() or "Demo Facebook Account"
                account.page_name = request.form.get("page_name", "").strip() or None
                account.connection_status = request.form.get("connection_status", ConnectionStatus.connected.value)
                account.connected_at = datetime.utcnow()
                account.last_checked_at = datetime.utcnow()
                flash("Facebook connection state saved.", "success")
            elif provider == "telegram":
                if not telegram_account:
                    telegram_account = TelegramAccount(user_id=session["user_id"])
                    db.add(telegram_account)
                telegram_account.bot_name = request.form.get("bot_name", "").strip() or "Posting Autopilot Bot"
                telegram_account.bot_username = request.form.get("bot_username", "").strip() or None
                telegram_account.default_chat_ref = request.form.get("default_chat_ref", "").strip() or None
                telegram_account.connection_status = request.form.get("connection_status", ConnectionStatus.attention.value)
                telegram_account.token_state = "configured" if Config.TELEGRAM_BOT_TOKEN else "demo_stub"
                telegram_account.connected_at = telegram_account.connected_at or datetime.utcnow()
                telegram_account.last_checked_at = datetime.utcnow()
                flash("Telegram connection state saved.", "success")
            db.commit()
            db.close()
            return redirect(url_for("channel_connect"))
        db.close()
        return render_template(
            "facebook_connect.html",
            account=account,
            telegram_account=telegram_account,
            telegram_destinations=telegram_destinations,
            telegram_token_configured=bool(Config.TELEGRAM_BOT_TOKEN),
            **telegram_public_context(),
        )

    @app.post("/telegram/test-message")
    @login_required
    def telegram_test_message():
        db = db_session()
        telegram_account = (
            db.query(TelegramAccount)
            .filter(TelegramAccount.user_id == session["user_id"])
            .order_by(TelegramAccount.id.desc())
            .first()
        )
        chat_ref = request.form.get("chat_ref", "").strip()
        text = request.form.get("text", "").strip() or "Test message from Posting Autopilot."
        if not chat_ref:
            db.close()
            flash("Enter a real Telegram destination: your chat ID after /start, or a channel/group where the bot is admin.", "error")
            return redirect(url_for("channel_connect"))
        if Config.TELEGRAM_BOT_PUBLIC_HANDLE and chat_ref.lstrip("@").lower() == Config.TELEGRAM_BOT_PUBLIC_HANDLE.lstrip("@").lower():
            db.close()
            flash("Use your own chat ID or a channel/group where the bot is admin. The bot cannot send a test message to itself.", "error")
            return redirect(url_for("channel_connect"))
        if chat_ref in SAMPLE_TELEGRAM_REFS:
            db.close()
            flash("The seeded sample refs are not real live destinations. Use your own chat ID or a channel/group where the bot is admin.", "error")
            return redirect(url_for("channel_connect"))
        ok, message = telegram_send_message_safe(chat_ref, text)
        if telegram_account:
            telegram_account.default_chat_ref = chat_ref or telegram_account.default_chat_ref
            telegram_account.last_checked_at = datetime.utcnow()
            telegram_account.connection_status = ConnectionStatus.connected.value if ok else ConnectionStatus.attention.value
            db.commit()
        db.close()
        flash("Telegram test sent." if ok else f"Telegram test failed: {message}", "success" if ok else "error")
        return redirect(url_for("channel_connect"))

    @app.route("/ads/new", methods=["GET", "POST"])
    @login_required
    def create_ad():
        db = db_session()
        search = request.args.get("search", "").strip()
        category = request.args.get("category", "").strip()
        platform = request.args.get("platform", "").strip()
        groups_query = db.query(Group).filter(Group.is_active == True)
        if search:
            like = f"%{search}%"
            groups_query = groups_query.filter((Group.name.ilike(like)) | (Group.external_ref.ilike(like)))
        if category:
            groups_query = groups_query.filter(Group.category == category)
        if platform:
            groups_query = groups_query.filter(Group.platform == platform)
        groups = groups_query.order_by(Group.platform.asc(), Group.activity_score.desc(), Group.name.asc()).all()
        categories_query = db.query(Group.category).filter(Group.is_active == True)
        if platform:
            categories_query = categories_query.filter(Group.platform == platform)
        categories = [row[0] for row in categories_query.distinct().order_by(Group.category.asc()).all()]

        if request.method == "POST":
            title = request.form.get("title", "").strip()
            primary_text = request.form.get("primary_text", "").strip()
            cta_text = request.form.get("cta_text", "").strip() or "Send details in DM"
            audience = request.form.get("audience", "").strip() or None
            selected_group_ids = [int(group_id) for group_id in request.form.getlist("group_ids")]
            if not title or not primary_text or not selected_group_ids:
                db.close()
                return render_template(
                    "ad_builder.html",
                    groups=groups,
                    categories=categories,
                    search=search,
                    category=category,
                    platform=platform,
                    error="Ad title, copy, and at least one destination are required.",
                )
            ad = Ad(
                user_id=session["user_id"],
                title=title,
                primary_text=primary_text,
                cta_text=cta_text,
                audience=audience,
                status=AdStatus.ready.value,
            )
            db.add(ad)
            db.flush()
            ad_id = ad.id
            for group_id in selected_group_ids:
                db.add(AdGroupTarget(ad_id=ad.id, group_id=group_id))
            db.commit()
            db.close()
            flash("Ad saved with selected destinations.", "success")
            return redirect(url_for("schedule_ad", ad_id=ad_id))

        db.close()
        return render_template("ad_builder.html", groups=groups, categories=categories, search=search, category=category, platform=platform)

    @app.route("/schedule", methods=["GET", "POST"])
    @login_required
    def schedule_ad():
        db = db_session()
        selected_ad_id = request.args.get("ad_id", type=int)
        ads = (
            db.query(Ad)
            .options(joinedload(Ad.groups).joinedload(AdGroupTarget.group))
            .filter(Ad.user_id == session["user_id"])
            .order_by(Ad.id.desc())
            .all()
        )
        selected_ad = next((ad for ad in ads if ad.id == selected_ad_id), ads[0] if ads else None)

        if request.method == "POST":
            ad_id = int(request.form.get("ad_id"))
            title = request.form.get("title", "").strip() or "Primary schedule"
            start_at_raw = request.form.get("start_at", "").strip()
            cadence = request.form.get("cadence", "").strip() or "daily"
            timezone = request.form.get("timezone", "").strip() or "Asia/Jerusalem"
            notes = request.form.get("notes", "").strip() or None
            if not start_at_raw:
                db.close()
                return render_template("schedule.html", ads=ads, selected_ad=selected_ad, error="Start time is required.")
            start_at = datetime.fromisoformat(start_at_raw)
            ad = db.query(Ad).filter(Ad.id == ad_id, Ad.user_id == session["user_id"]).first()
            if not ad:
                db.close()
                return render_template("schedule.html", ads=ads, selected_ad=selected_ad, error="Select an ad first.")

            schedule = Schedule(
                user_id=session["user_id"],
                ad_id=ad.id,
                title=title,
                start_at=start_at,
                cadence=cadence,
                timezone=timezone,
                status=ScheduleStatus.scheduled.value,
                notes=notes,
            )
            db.add(schedule)
            db.flush()

            targets = db.query(AdGroupTarget).filter(AdGroupTarget.ad_id == ad.id).order_by(AdGroupTarget.id.asc()).all()
            run = PostingRun(
                user_id=session["user_id"],
                ad_id=ad.id,
                schedule_id=schedule.id,
                title=f"{ad.title} — {title}",
                status=RunStatus.scheduled.value,
                selected_group_count=len(targets),
                last_updated_at=datetime.utcnow(),
            )
            db.add(run)
            db.flush()

            for target in targets:
                db.add(
                    PostHistoryItem(
                        user_id=session["user_id"],
                        ad_id=ad.id,
                        group_id=target.group_id,
                        posting_run_id=run.id,
                        status=HistoryStatus.scheduled.value,
                        scheduled_for=start_at,
                        operator_note=notes,
                        updated_at=datetime.utcnow(),
                    )
                )
            db.commit()
            db.close()
            flash("Schedule saved and posting run created.", "success")
            return redirect(url_for("history"))

        db.close()
        return render_template("schedule.html", ads=ads, selected_ad=selected_ad)

    @app.route("/history", methods=["GET"])
    @login_required
    def history():
        db = db_session()
        status_filter = request.args.get("status", "").strip()
        query = (
            db.query(PostHistoryItem)
            .options(
                joinedload(PostHistoryItem.ad),
                joinedload(PostHistoryItem.group),
                joinedload(PostHistoryItem.posting_run),
            )
            .filter(PostHistoryItem.user_id == session["user_id"])
            .order_by(PostHistoryItem.updated_at.desc(), PostHistoryItem.id.desc())
        )
        if status_filter:
            query = query.filter(PostHistoryItem.status == status_filter)
        items = query.all()
        db.close()
        return render_template("history.html", items=items, status_filter=status_filter)

    @app.post("/history/<int:item_id>/status")
    @login_required
    def update_history_status(item_id: int):
        db = db_session()
        item = db.query(PostHistoryItem).filter(PostHistoryItem.id == item_id, PostHistoryItem.user_id == session["user_id"]).first()
        if item:
            item.status = request.form.get("status", HistoryStatus.ready.value)
            item.operator_note = request.form.get("operator_note", "").strip() or item.operator_note
            item.updated_at = datetime.utcnow()
            if item.status == HistoryStatus.posted.value:
                item.published_at = datetime.utcnow()
            item.posting_run.last_updated_at = datetime.utcnow()
            if item.status == HistoryStatus.posted.value and item.posting_run.status == RunStatus.scheduled.value:
                item.posting_run.status = RunStatus.active.value
            db.commit()
        db.close()
        flash("CRM item updated.", "success")
        return redirect(url_for("history"))

    @app.route("/settings", methods=["GET", "POST"])
    @login_required
    def settings():
        db = db_session()
        user = db.query(User).filter(User.id == session["user_id"]).first()
        settings_row = db.query(ProfileSetting).filter(ProfileSetting.user_id == session["user_id"]).first()
        if not settings_row:
            settings_row = ProfileSetting(user_id=session["user_id"])
            db.add(settings_row)
            db.commit()
            db.refresh(settings_row)

        if request.method == "POST":
            updated_name = request.form.get("full_name", "").strip() or user.full_name
            user.full_name = updated_name
            settings_row.timezone = request.form.get("timezone", "").strip() or settings_row.timezone
            settings_row.default_cta = request.form.get("default_cta", "").strip() or settings_row.default_cta
            settings_row.posting_window = request.form.get("posting_window", "").strip() or settings_row.posting_window
            settings_row.notifications_enabled = request.form.get("notifications_enabled") == "on"
            settings_row.updated_at = datetime.utcnow()
            db.commit()
            session["user_name"] = updated_name
            db.close()
            flash("Profile settings saved.", "success")
            return redirect(url_for("settings"))

        db.close()
        return render_template(
            "settings.html",
            user=user,
            settings_row=settings_row,
            telegram_token_configured=bool(Config.TELEGRAM_BOT_TOKEN),
            **telegram_public_context(),
        )
