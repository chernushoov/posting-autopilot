"""
Multilingual messages for RecruitBot.
Supports: Russian (ru), Hebrew (he), English (en).
"""
import os

MESSAGES = {
    # --- Onboarding ---
    "welcome": {
        "ru": "Привет! Я помогаю найти работу в строительстве 🏗\n\nВыбери язык / בחר שפה / Choose language:",
        "he": "שלום! אני עוזר למצוא עבודה בבנייה 🏗\n\nבחר שפה / Выбери язык / Choose language:",
        "en": "Hi! I help find construction jobs 🏗\n\nChoose language / Выбери язык / בחר שפה:",
    },
    "language_set": {
        "ru": "✅ Язык: Русский\n\nЧто хочешь сделать?",
        "he": "✅ שפה: עברית\n\nמה תרצה לעשות?",
        "en": "✅ Language: English\n\nWhat would you like to do?",
    },

    # --- Role selection ---
    "choose_role": {
        "ru": "Кто ты?",
        "he": "?מי את/ה",
        "en": "Who are you?",
    },
    "role_worker": {
        "ru": "🔨 Ищу работу",
        "he": "🔨 מחפש/ת עבודה",
        "en": "🔨 Looking for work",
    },
    "role_client": {
        "ru": "🏢 Ищу работников",
        "he": "🏢 מחפש/ת עובדים",
        "en": "🏢 Looking for workers",
    },

    # --- Vacancies ---
    "no_vacancies": {
        "ru": "Пока нет активных вакансий. Попробуй позже!",
        "he": "אין משרות פעילות כרגע. נסה שוב מאוחר יותר!",
        "en": "No active vacancies right now. Try again later!",
    },
    "vacancies_header": {
        "ru": "📋 Доступные вакансии:",
        "he": "📋 :משרות פנויות",
        "en": "📋 Available vacancies:",
    },
    "apply_button": {
        "ru": "📝 Откликнуться",
        "he": "📝 להגיש מועמדות",
        "en": "📝 Apply",
    },

    # --- Screening interview ---
    "screening_start": {
        "ru": "Отлично! Начинаем короткое интервью по вакансии «{title}».\nОтвечай коротко, 1-2 предложения.",
        "he": "מעולה! מתחילים ראיון קצר למשרת «{title}».\nענה בקצרה, 1-2 משפטים.",
        "en": "Great! Starting a short interview for the «{title}» position.\nAnswer briefly, 1-2 sentences.",
    },
    "screening_progress": {
        "ru": "📊 Вопрос {current}/{total}",
        "he": "📊 {total}/{current} שאלה",
        "en": "📊 Question {current}/{total}",
    },
    "answer_accepted": {
        "ru": "✓ Принято",
        "he": "✓ התקבל",
        "en": "✓ Accepted",
    },

    # --- Default screening questions ---
    "q_experience": {
        "ru": "Какой у тебя опыт работы? (кратко)",
        "he": "?מה הניסיון שלך בעבודה (בקצרה)",
        "en": "What is your work experience? (briefly)",
    },
    "q_city": {
        "ru": "В каком ты городе сейчас?",
        "he": "?באיזו עיר את/ה נמצא/ת כרגע",
        "en": "What city are you in right now?",
    },
    "q_documents": {
        "ru": "Есть ли документы/разрешение на работу?",
        "he": "?יש לך אישור עבודה/מסמכים",
        "en": "Do you have work permit/documents?",
    },

    # --- Results ---
    "screening_passed": {
        "ru": "✅ Спасибо! Ты в шорт-листе. Скоро свяжемся с тобой.",
        "he": "✅ !תודה! את/ה ברשימה המקוצרת. ניצור קשר בקרוב",
        "en": "✅ Thanks! You're shortlisted. We'll contact you soon.",
    },
    "screening_rejected": {
        "ru": "Спасибо за ответы. К сожалению, в этот раз не подходит. Удачи!",
        "he": "תודה על התשובות. לצערנו, הפעם לא מתאים. בהצלחה!",
        "en": "Thanks for your answers. Unfortunately, not a match this time. Good luck!",
    },

    # --- Phone collection ---
    "ask_phone": {
        "ru": "Отлично! Оставьте номер телефона — мы свяжемся с вами.",
        "he": "מעולה! השאר מספר טלפון — ניצור איתך קשר.",
        "en": "Great! Leave your phone number — we'll contact you.",
    },
    "phone_accepted": {
        "ru": "📞 Записал! С вами свяжутся в ближайшее время. Спасибо! 🙏",
        "he": "📞 רשמנו! ניצור איתך קשר בהקדם. תודה! 🙏",
        "en": "📞 Got it! Someone will contact you soon. Thanks! 🙏",
    },
    "phone_invalid": {
        "ru": "Пожалуйста, отправьте номер телефона в формате 05X-XXXXXXX или поделитесь контактом.",
        "he": "אנא שלח מספר טלפון בפורמט 05X-XXXXXXX או שתף איש קשר.",
        "en": "Please send a phone number in format 05X-XXXXXXX or share your contact.",
    },
    "classification_cold_close": {
        "ru": "Спасибо за интерес. К сожалению, это предложение вам не подходит. Удачи!",
        "he": "תודה על ההתעניינות. לצערנו, ההצעה הזו לא מתאימה לך. בהצלחה!",
        "en": "Thanks for your interest. Unfortunately, this isn't a match. Good luck!",
    },

    # --- Errors / fallbacks ---
    "no_active_conversation": {
        "ru": "У тебя нет активного диалога.\n\nНапиши /start чтобы посмотреть вакансии.",
        "he": "אין לך שיחה פעילה.\n\nכתוב /start כדי לראות משרות.",
        "en": "You don't have an active conversation.\n\nType /start to see vacancies.",
    },
    "not_configured": {
        "ru": "Сервис временно недоступен. Попробуй позже.",
        "he": "השירות לא זמין כרגע. נסה שוב מאוחר יותר.",
        "en": "Service temporarily unavailable. Try again later.",
    },

    # --- Timeout & Resume ---
    "screening_expired": {
        "ru": "⏰ Время интервью истекло. Хочешь начать заново?",
        "he": "⏰ הזמן לראיון פג. רוצה להתחיל מחדש?",
        "en": "⏰ Interview time expired. Want to start over?",
    },
    "screening_resume": {
        "ru": "👋 С возвращением! У тебя есть незавершённое интервью.\nОтвечено {answered}/{total} вопросов.",
        "he": "👋 !ברוך שובך! יש לך ראיון שלא הסתיים\n.ענית על {answered} מתוך {total} שאלות",
        "en": "👋 Welcome back! You have an unfinished interview.\nAnswered {answered}/{total} questions.",
    },
    "resume_button": {
        "ru": "▶️ Продолжить",
        "he": "▶️ להמשיך",
        "en": "▶️ Continue",
    },
    "restart_button": {
        "ru": "🔄 Начать заново",
        "he": "🔄 להתחיל מחדש",
        "en": "🔄 Start over",
    },

    # --- Re-application ---
    "already_applied": {
        "ru": "Ты уже откликался на эту вакансию. Хочешь попробовать ещё раз?",
        "he": "כבר הגשת מועמדות למשרה הזו. רוצה לנסות שוב?",
        "en": "You already applied to this vacancy. Want to try again?",
    },
    "reapply_button": {
        "ru": "🔄 Откликнуться заново",
        "he": "🔄 להגיש שוב",
        "en": "🔄 Apply again",
    },
}

# --- Admin UI strings ---
UI = {
    # Layout / nav
    "app_name": {"ru": "Recruit Autopilot", "he": "Recruit Autopilot", "en": "Recruit Autopilot"},
    "nav_dashboard": {"ru": "Панель", "he": "לוח בקרה", "en": "Dashboard"},
    "nav_companies": {"ru": "Компании", "he": "חברות", "en": "Companies"},
    "nav_vacancies": {"ru": "Объявления", "he": "מודעות", "en": "Listings"},
    "nav_destinations": {"ru": "Каналы", "he": "יעדים", "en": "Destinations"},
    "nav_campaigns": {"ru": "Кампании", "he": "קמפיינים", "en": "Campaigns"},
    "nav_candidates": {"ru": "Лиды", "he": "לידים", "en": "Leads"},
    "nav_analytics": {"ru": "Аналитика", "he": "אנליטיקה", "en": "Analytics"},
    "nav_logout": {"ru": "Выход", "he": "יציאה", "en": "Logout"},
    "company_label": {"ru": "Компания", "he": "חברה", "en": "Company"},
    # Login
    "login_title": {"ru": "Вход", "he": "כניסה", "en": "Login"},
    "login_field": {"ru": "Логин", "he": "שם משתמש", "en": "Login"},
    "password_field": {"ru": "Пароль", "he": "סיסמה", "en": "Password"},
    "enter_btn": {"ru": "Войти", "he": "כניסה", "en": "Enter"},
    # Vacancies
    "vacancies_title": {"ru": "Объявления", "he": "מודעות", "en": "Listings"},
    "new_vacancy": {"ru": "+ Новое объявление", "he": "+ מודעה חדשה", "en": "+ New listing"},
    "title": {"ru": "Название", "he": "כותרת", "en": "Title"},
    "city": {"ru": "Город", "he": "עיר", "en": "City"},
    "posting_asset": {"ru": "Пост", "he": "פוסט", "en": "Posting asset"},
    "active": {"ru": "Активна", "he": "פעיל", "en": "Active"},
    "actions": {"ru": "Действия", "he": "פעולות", "en": "Actions"},
    "yes": {"ru": "да", "he": "כן", "en": "yes"},
    "no": {"ru": "нет", "he": "לא", "en": "no"},
    "toggle": {"ru": "Вкл/Выкл", "he": "הפעלה/כיבוי", "en": "Toggle"},
    # Vacancy form
    "new_vacancy_title": {"ru": "Новое объявление", "he": "מודעה חדשה", "en": "New listing"},
    "salary": {"ru": "Зарплата", "he": "שכר", "en": "Pay / salary"},
    "schedule": {"ru": "График", "he": "לוח זמנים", "en": "Schedule"},
    "contact": {"ru": "Контакт", "he": "איש קשר", "en": "Contact"},
    "apply_link": {"ru": "Ссылка для отклика", "he": "קישור להגשה", "en": "Apply link"},
    "body": {"ru": "Описание", "he": "תיאור", "en": "Body"},
    "final_post_title": {"ru": "Заголовок поста", "he": "כותרת הפוסט", "en": "Final post title"},
    "final_post_body": {"ru": "Текст поста", "he": "טקסט הפוסט", "en": "Final post body"},
    "questions": {"ru": "Вопросы (по одному на строку)", "he": "שאלות (אחת בשורה)", "en": "Interview questions (one per line)"},
    "create_vacancy_btn": {"ru": "Создать объявление", "he": "צור מודעה", "en": "Create listing"},
    "language": {"ru": "Язык", "he": "שפה", "en": "Language"},
    # Sources
    "destinations_title": {"ru": "Каналы публикации", "he": "יעדי פרסום", "en": "Destinations"},
    "platform": {"ru": "Платформа", "he": "פלטפורמה", "en": "Platform"},
    "dest_kind": {"ru": "Тип", "he": "סוג", "en": "Destination kind"},
    "dest_ref": {"ru": "Адрес", "he": "כתובת", "en": "Destination ref"},
    "posting_mode": {"ru": "Режим", "he": "מצב פרסום", "en": "Posting mode"},
    "label": {"ru": "Метка", "he": "תווית", "en": "Label"},
    "dest_url": {"ru": "URL", "he": "כתובת URL", "en": "Destination URL"},
    "add_dest_btn": {"ru": "Добавить канал", "he": "הוסף יעד", "en": "Add destination"},
    "ready": {"ru": "ГОТОВ", "he": "מוכן", "en": "READY"},
    "check_needed": {"ru": "ПРОВЕРИТЬ", "he": "לבדוק", "en": "CHECK NEEDED"},
    "check_btn": {"ru": "Проверить", "he": "בדוק", "en": "Check"},
    "test_msg_btn": {"ru": "Тест", "he": "בדיקה", "en": "Test msg"},
    "confirm_live_send": {"ru": "подтвердить отправку", "he": "אשר שליחה", "en": "confirm live send"},
    # Campaigns
    "campaigns_title": {"ru": "Кампании", "he": "קמפיינים", "en": "Pilot runs"},
    "new_campaign": {"ru": "+ Новая кампания", "he": "+ קמפיין חדש", "en": "+ New pilot run"},
    "name": {"ru": "Название", "he": "שם", "en": "Name"},
    "vacancy": {"ru": "Объявление", "he": "מודעה", "en": "Listing"},
    "interval": {"ru": "Интервал", "he": "מרווח", "en": "Interval"},
    "running": {"ru": "Работает", "he": "פעיל", "en": "Running"},
    "run_now": {"ru": "Запустить", "he": "הפעל עכשיו", "en": "Run now"},
    "pause": {"ru": "Пауза", "he": "השהה", "en": "Pause"},
    "start": {"ru": "Старт", "he": "התחל", "en": "Start"},
    "dest_log": {"ru": "Лог публикаций", "he": "יומן פרסומים", "en": "Destination log"},
    "when": {"ru": "Когда", "he": "מתי", "en": "When"},
    "destination": {"ru": "Канал", "he": "יעד", "en": "Destination"},
    "asset": {"ru": "Контент", "he": "תוכן", "en": "Asset"},
    "action": {"ru": "Действие", "he": "פעולה", "en": "Action"},
    "status": {"ru": "Статус", "he": "סטטוס", "en": "Status"},
    "error_notes": {"ru": "Ошибка / заметки", "he": "שגיאות / הערות", "en": "Error / notes"},
    "manual_result": {"ru": "Результат", "he": "תוצאה", "en": "Manual result"},
    "save_result": {"ru": "Сохранить", "he": "שמור", "en": "Save result"},
    # Candidates
    "candidates_title": {"ru": "Лиды", "he": "לידים", "en": "Leads"},
    "all": {"ru": "все", "he": "הכל", "en": "all"},
    "score": {"ru": "Балл", "he": "ציון", "en": "Score"},
    "open": {"ru": "Открыть", "he": "פתח", "en": "Open"},
    # Analytics
    "analytics_title": {"ru": "Аналитика", "he": "אנליטיקה", "en": "Analytics Dashboard"},
    "total_candidates": {"ru": "Всего лидов", "he": "סה\"כ לידים", "en": "Total Leads"},
    "passed": {"ru": "Прошли", "he": "עברו", "en": "Passed"},
    "rejected": {"ru": "Отклонены", "he": "נדחו", "en": "Rejected"},
    "hired": {"ru": "Наняты", "he": "גויסו", "en": "Hired"},
    "conversion_funnel": {"ru": "Воронка конверсии", "he": "משפך המרה", "en": "Conversion Funnel"},
    "stage": {"ru": "Этап", "he": "שלב", "en": "Stage"},
    "count": {"ru": "Кол-во", "he": "כמות", "en": "Count"},
    "languages_title": {"ru": "Языки", "he": "שפות", "en": "Languages"},
    "operations": {"ru": "Операции", "he": "פעולות", "en": "Operations"},
    "active_vacancies": {"ru": "Активных вакансий", "he": "משרות פעילות", "en": "Active Vacancies"},
    "active_campaigns": {"ru": "Активных кампаний", "he": "קמפיינים פעילים", "en": "Active Campaigns"},
    "active_sources": {"ru": "Активных каналов", "he": "יעדים פעילים", "en": "Active Sources"},
    "vacancy_performance": {"ru": "Эффективность вакансий", "he": "ביצועי משרות", "en": "Vacancy Performance"},
    "applicants": {"ru": "Отклики", "he": "מועמדויות", "en": "Applicants"},
    "avg_score": {"ru": "Ср. балл", "he": "ציון ממוצע", "en": "Avg Score"},
    "daily_candidates": {"ru": "Новые кандидаты (7 дней)", "he": "מועמדים חדשים (7 ימים)", "en": "Daily New Candidates (last 7 days)"},
    "no_data": {"ru": "Нет данных", "he": "אין נתונים", "en": "No data"},
    # Campaign form
    "new_campaign_title": {"ru": "Новая кампания", "he": "קמפיין חדש", "en": "New pilot run"},
    "interval_minutes": {"ru": "Интервал (мин)", "he": "מרווח (דק')", "en": "Interval minutes"},
    "safe_range": {"ru": "Безопасный диапазон", "he": "טווח בטוח", "en": "Safe range"},
    "active_start": {"ru": "Начало активности", "he": "שעת התחלה", "en": "Active start hour"},
    "active_end": {"ru": "Конец активности", "he": "שעת סיום", "en": "Active end hour"},
    "weekdays": {"ru": "Дни недели", "he": "ימי השבוע", "en": "Allowed weekdays"},
    "max_posts_day": {"ru": "Макс. постов в день", "he": "מקסימום פרסומים ביום", "en": "Max posts per day"},
    "destinations": {"ru": "Каналы", "he": "יעדים", "en": "Destinations"},
    "tg_auto_note": {"ru": "Telegram публикует автоматически. Facebook — ручной режим.", "he": "טלגרם מפרסם אוטומטית. פייסבוק — ידני.", "en": "Telegram can post automatically. Facebook is assisted/manual in pilot mode."},
    "create_campaign_btn": {"ru": "Создать кампанию", "he": "צור קמפיין", "en": "Create pilot run"},
    # Pricing
    "pricing_title": {"ru": "Тарифы", "he": "מחירים", "en": "Pricing"},
    "pricing_subtitle": {"ru": "Автоматизация публикации вакансий в Telegram и Facebook. AI-скрининг кандидатов.", "he": "אוטומציה של פרסום משרות בטלגרם ופייסבוק. סינון מועמדים עם AI.", "en": "Automated job posting to Telegram and Facebook. AI candidate screening."},
    # Prospecting
    "nav_prospecting": {"ru": "Поиск клиентов", "he": "חיפוש לקוחות", "en": "Prospecting"},
    "prospecting_title": {"ru": "Поиск клиентов", "he": "חיפוש לקוחות", "en": "Prospecting"},
    "total_prospects": {"ru": "Всего", "he": "סה\"כ", "en": "Total"},
    "with_email": {"ru": "С email", "he": "עם אימייל", "en": "With email"},
    "contacted": {"ru": "Отправлено", "he": "נשלח", "en": "Contacted"},
    "converted": {"ru": "Конверсия", "he": "המרה", "en": "Converted"},
    "find_businesses": {"ru": "Найти компании", "he": "מצא חברות", "en": "Find businesses"},
    "scrape_placeholder": {"ru": "напр. строительные компании Тель-Авив", "he": "למשל חברות בנייה תל אביב", "en": "e.g. construction companies Tel Aviv"},
    "scrape_btn": {"ru": "Искать", "he": "חפש", "en": "Search"},
    "add_manual": {"ru": "+ Добавить вручную", "he": "+ הוסף ידנית", "en": "+ Add manually"},
    "phone_label": {"ru": "Телефон", "he": "טלפון", "en": "Phone"},
    "rating_label": {"ru": "Рейтинг", "he": "דירוג", "en": "Rating"},
    "category": {"ru": "Категория", "he": "קטגוריה", "en": "Category"},
    "send_email_btn": {"ru": "Отправить email", "he": "שלח אימייל", "en": "Send email"},
    "sent_label": {"ru": "отправлено", "he": "נשלח", "en": "sent"},
    # --- Dashboard / Setup ---
    "control_center": {"ru": "Центр управления", "he": "מרכז בקרה", "en": "Control Center"},
    "welcome_back": {"ru": "Добро пожаловать", "he": "ברוך הבא", "en": "Welcome back"},
    "setup_subtitle": {"ru": "Завершите настройку для первого автоматического постинга.", "he": "השלם את ההגדרה כדי להתחיל את הפרסום האוטומטי הראשון.", "en": "Complete the setup to start your first automated posting run."},
    "steps_completed": {"ru": "шагов завершено", "he": "צעדים הושלמו", "en": "steps completed"},
    "completed": {"ru": "Готово", "he": "הושלם", "en": "Completed"},
    "required": {"ru": "Необходимо", "he": "נדרש", "en": "Required"},
    "company_profile": {"ru": "Профиль компании", "he": "פרופיל חברה", "en": "Company Profile"},
    "create_company_prompt": {"ru": "Создайте компанию для начала работы.", "he": "צור חברה כדי להתחיל.", "en": "Create your company to get started."},
    "create_company_btn": {"ru": "Создать компанию", "he": "צור חברה", "en": "Create Company"},
    "job_vacancy": {"ru": "Объявление", "he": "מודעה", "en": "Listing"},
    "create_vacancy_prompt": {"ru": "Добавьте первую вакансию с деталями и текстом поста.", "he": "הוסף משרה ראשונה עם פרטים וטקסט לפרסום.", "en": "Add your first job posting with details and posting asset."},
    "active_vacancies_count": {"ru": "активных объявлений", "he": "מודעות פעילות", "en": "active listings"},
    "connect_telegram_title": {"ru": "Подключить Telegram", "he": "חבר טלגרם", "en": "Connect Telegram"},
    "telegram_channels": {"ru": "Telegram каналы", "he": "ערוצי טלגרם", "en": "Telegram Channels"},
    "connect_telegram_desc": {"ru": "Добавьте Telegram группы или каналы для публикации вакансий.", "he": "הוסף קבוצות או ערוצי טלגרם לפרסום משרות.", "en": "Add Telegram groups or channels where vacancies will be posted."},
    "tg_destinations_ready": {"ru": "Telegram каналов подключено", "he": "יעדי טלגרם מוכנים", "en": "Telegram destinations ready"},
    "connect_facebook_title": {"ru": "Подключить Facebook", "he": "חבר פייסבוק", "en": "Connect Facebook"},
    "facebook_groups": {"ru": "Группы Facebook", "he": "קבוצות פייסבוק", "en": "Facebook Groups"},
    "connect_facebook_desc": {"ru": "Настройте группы Facebook для ручного постинга.", "he": "הגדר קבוצות פייסבוק לפרסום ידני מלווה.", "en": "Set up Facebook groups for assisted manual posting."},
    "fb_destinations_ready": {"ru": "Facebook групп подключено", "he": "יעדי פייסבוק מוכנים", "en": "Facebook destinations ready"},
    "posting_campaign": {"ru": "Кампания постинга", "he": "קמפיין פרסום", "en": "Posting Campaign"},
    "create_campaign_prompt": {"ru": "Настройте расписание постинга для вакансий.", "he": "הגדר לוח זמנים לפרסום משרות.", "en": "Set up a posting schedule for your vacancy across destinations."},
    "campaigns_configured": {"ru": "кампаний настроено", "he": "קמפיינים מוגדרים", "en": "campaigns configured"},
    "first_posting_run": {"ru": "Первый запуск", "he": "הפעלה ראשונה", "en": "First Posting Run"},
    "pilot_live_msg": {"ru": "Пилот запущен! Проверьте кампании.", "he": "הפיילוט פעיל! בדוק את הקמפיינים.", "en": "Your pilot is live! Check campaigns for posting logs."},
    "run_now_prompt": {"ru": "Нажмите «Запустить» в кампании.", "he": "לחץ על הפעל עכשיו בקמפיין.", "en": "Hit Run Now on your campaign to start the pilot."},
    "go_to_campaigns": {"ru": "К кампаниям", "he": "לקמפיינים", "en": "Go to Campaigns"},
    "recent_activity": {"ru": "Последняя активность", "he": "פעילות אחרונה", "en": "Recent Activity"},
    "view_all": {"ru": "Все", "he": "הצג הכל", "en": "View All"},
    "postings": {"ru": "Публикации", "he": "פרסומים", "en": "Postings"},
    "launch": {"ru": "Запуск", "he": "השקה", "en": "Launch"},
    "connected": {"ru": "Подключено", "he": "מחובר", "en": "Connected"},
    # --- Landing page ---
    "landing_tagline": {"ru": "Публикуйте вакансии в Telegram и Facebook автоматически.\nАI-скрининг кандидатов. Нанимайте быстрее.", "he": "פרסם משרות בטלגרם ובפייסבוק אוטומטית.\nסינון מועמדים עם AI. גייס מהר יותר.", "en": "Post job vacancies to Telegram and Facebook automatically.\nScreen candidates with AI. Hire faster."},
    "get_started": {"ru": "Начать", "he": "התחל", "en": "Get Started"},
    "how_it_works": {"ru": "Как это работает", "he": "איך זה עובד", "en": "How It Works"},
    "sign_in": {"ru": "Войти", "he": "כניסה", "en": "Sign In"},
    "feature_multichannel": {"ru": "Мультиканальный постинг", "he": "פרסום רב-ערוצי", "en": "Multi-Channel Posting"},
    "feature_multichannel_desc": {"ru": "Публикуйте в Telegram группы и Facebook из одной панели. По расписанию или мгновенно.", "he": "פרסם בקבוצות טלגרם ובפייסבוק מלוח בקרה אחד. לפי לוח זמנים או מיידית.", "en": "Post to Telegram groups, Facebook pages and groups from one dashboard. Schedule or post instantly."},
    "feature_screening": {"ru": "AI-скрининг кандидатов", "he": "סינון מועמדים עם AI", "en": "AI Candidate Screening"},
    "feature_screening_desc": {"ru": "Наш бот в Telegram проводит скрининг на иврите, русском и английском. Вы видите только подходящих.", "he": "הבוט שלנו בטלגרם מסנן מועמדים בעברית, רוסית ואנגלית. אתה רואה רק את המתאימים.", "en": "Our Telegram bot screens candidates in Hebrew, Russian and English. You only see the shortlist."},
    "feature_pipeline": {"ru": "Полная воронка", "he": "תצוגת צנרת מלאה", "en": "Full Pipeline View"},
    "feature_pipeline_desc": {"ru": "Отслеживайте каждую публикацию, каждого кандидата, каждый отклик. Статусы и аналитика в реальном времени.", "he": "עקוב אחר כל פרסום, כל מועמד, כל תגובה. סטטוסים ואנליטיקה בזמן אמת.", "en": "Track every posting, every candidate, every response. Real-time statuses and analytics."},
    "landing_footer": {"ru": "Posting Autopilot — Автоматизация рекрутинга для израильских кадровых агентств", "he": "Posting Autopilot — אוטומציה של גיוס לסוכנויות כוח אדם ישראליות", "en": "Posting Autopilot — Recruitment automation for Israeli staffing agencies"},
    # --- Connect Telegram ---
    "step_n_of_m": {"ru": "Шаг {n} из {m}", "he": "שלב {n} מתוך {m}", "en": "Step {n} of {m}"},
    "back_to_dashboard": {"ru": "Назад к панели", "he": "חזרה ללוח בקרה", "en": "Back to Dashboard"},
    "add_bot_title": {"ru": "Добавьте бота в группу/канал", "he": "הוסף את הבוט לקבוצה/ערוץ", "en": "Add the bot to your group/channel"},
    "add_bot_desc": {"ru": "Добавьте @AutopillotRecruit_bot как администратора в Telegram группу или канал для публикации вакансий.", "he": "הוסף את @AutopillotRecruit_bot כמנהל בקבוצת או ערוץ טלגרם שבו תרצה לפרסם.", "en": "Add @AutopillotRecruit_bot as an admin to any Telegram group or channel where you want to post vacancies."},
    "enter_dest_title": {"ru": "Введите адрес канала", "he": "הזן את כתובת היעד", "en": "Enter the destination below"},
    "enter_dest_desc": {"ru": "Вставьте имя группы (напр. @my_group) или числовой ID чата.", "he": "הדבק את שם הקבוצה (למשל @my_group) או מזהה צ'אט מספרי.", "en": "Paste the group/channel username (e.g. @my_group) or the numeric chat ID."},
    "verify_test_title": {"ru": "Проверьте и отправьте тест", "he": "אמת ושלח הודעת בדיקה", "en": "Verify and send a test message"},
    "verify_test_desc": {"ru": "Мы проверим доступ бота и отправим тестовое сообщение.", "he": "נבדוק שלבוט יש גישה ונשלח הודעת בדיקה.", "en": "We'll check that the bot has access and send a test message to confirm everything works."},
    "dest_type": {"ru": "Тип канала", "he": "סוג יעד", "en": "Destination type"},
    "group": {"ru": "Группа", "he": "קבוצה", "en": "Group"},
    "channel": {"ru": "Канал", "he": "ערוץ", "en": "Channel"},
    "tg_username_label": {"ru": "Telegram @имя или ID чата", "he": "טלגרם @שם או מזהה צ'אט", "en": "Telegram @username or chat ID"},
    "label_optional": {"ru": "Метка (необязательно)", "he": "תווית (אופציונלי)", "en": "Label (optional)"},
    "add_tg_dest_btn": {"ru": "Добавить Telegram канал", "he": "הוסף יעד טלגרם", "en": "Add Telegram Destination"},
    "your_tg_dests": {"ru": "Ваши Telegram каналы", "he": "יעדי הטלגרם שלך", "en": "Your Telegram Destinations"},
    "verify_btn": {"ru": "Проверить", "he": "אמת", "en": "Verify"},
    # --- Telegram workspace (connect_telegram.html) ---
    "tg_connect_title": {"ru": "Подключить Telegram", "he": "חבר טלגרם", "en": "Connect Telegram"},
    "tg_connect_desc": {"ru": "Подключите ваш аккаунт Telegram для автоматической публикации в группы и каналы.", "he": "חבר את חשבון הטלגרם שלך לפרסום אוטומטי בקבוצות וערוצים.", "en": "Connect your Telegram account to auto-post to groups and channels."},
    "tg_connect_desc_phone": {"ru": "Введите номер телефона — мы пришлём код в Telegram. Никаких API-ключей и разработчиков: подключение за 30 секунд.", "he": "הזן מספר טלפון — נשלח קוד בטלגרם. בלי מפתחות API ובלי הרשמת מפתחים: חיבור ב-30 שניות.", "en": "Enter your phone number — we'll send a code in Telegram. No API keys, no developer setup: connect in 30 seconds."},
    "tg_phone_only_hint": {"ru": "Используется ваш личный аккаунт Telegram для постинга в группы, где вы состоите. Код придёт в приложение Telegram.", "he": "נשתמש בחשבון הטלגרם האישי שלך לפרסום בקבוצות שאתה חבר בהן. הקוד יגיע לאפליקציית טלגרם.", "en": "We use your personal Telegram account to post to groups you're a member of. The code arrives in your Telegram app."},
    "tg_advanced_creds": {"ru": "Дополнительно: использовать свои API-ключи", "he": "מתקדם: להשתמש במפתחות API משלך", "en": "Advanced: use my own API credentials"},
    "tg_advanced_creds_hint": {"ru": "Не обязательно. Если хотите подключиться через собственное приложение my.telegram.org, укажите API ID и API Hash.", "he": "לא חובה. אם ברצונך להתחבר דרך אפליקציה משלך ב-my.telegram.org, הזן API ID ו-API Hash.", "en": "Optional. If you prefer to connect via your own my.telegram.org app, enter your API ID and API Hash."},
    "tg_credentials": {"ru": "Данные аккаунта", "he": "פרטי חשבון", "en": "Account credentials"},
    "tg_credentials_desc": {"ru": "Перейдите на my.telegram.org, раздел API development tools, скопируйте API ID и API Hash.", "he": "עבור ל-my.telegram.org, API development tools, והעתק API ID ו-API Hash.", "en": "Go to my.telegram.org, API development tools, copy your API ID and API Hash."},
    "tg_send_code_btn": {"ru": "Отправить код подтверждения", "he": "שלח קוד אימות", "en": "Send verification code"},
    "tg_step2": {"ru": "Подтверждение", "he": "אימות", "en": "Verification"},
    "tg_code_sent": {"ru": "Код отправлен в ваш Telegram. Введите его ниже.", "he": "קוד נשלח לטלגרם שלך. הזן אותו למטה.", "en": "A code was sent to your Telegram app. Enter it below."},
    "tg_code_label": {"ru": "Код подтверждения", "he": "קוד אימות", "en": "Verification code"},
    "tg_2fa_label": {"ru": "Двухфакторный пароль (если включен)", "he": "סיסמה דו-שלבית (אם מופעלת)", "en": "Two-factor password (if enabled)"},
    "tg_2fa_hint": {"ru": "Оставьте пустым если не установлен", "he": "השאר ריק אם לא הוגדר", "en": "Leave empty if not set"},
    "tg_verify_btn": {"ru": "Подтвердить", "he": "אמת", "en": "Verify"},
    "tg_connected": {"ru": "Telegram подключен", "he": "טלגרם מחובר", "en": "Telegram connected"},
    "tg_destinations": {"ru": "Каналы публикации", "he": "יעדי פרסום", "en": "Destinations"},
    "tg_sync_btn": {"ru": "Синхронизировать", "he": "סנכרן", "en": "Sync"},
    "tg_add_btn": {"ru": "Добавить", "he": "הוסף", "en": "Add"},
    "tg_ungrouped": {"ru": "Без папки", "he": "ללא תיקייה", "en": "Ungrouped"},
    "tg_manage_folders": {"ru": "Управление папками", "he": "ניהול תיקיות", "en": "Manage folders"},
    "tg_available_groups": {"ru": "Доступные группы", "he": "קבוצות זמינות", "en": "Available groups"},
    "tg_select_groups_desc": {"ru": "Выберите группы для публикации", "he": "בחר קבוצות לפרסום", "en": "Select groups to add as posting destinations"},
    "tg_add_selected": {"ru": "Добавить выбранные", "he": "הוסף נבחרים", "en": "Add selected"},
    "tg_sort_name": {"ru": "По имени", "he": "לפי שם", "en": "Sort: Name"},
    "tg_sort_members": {"ru": "По участникам", "he": "לפי חברים", "en": "Sort: Members"},
    "tg_select_all": {"ru": "Выбрать все", "he": "בחר הכל", "en": "Select all"},
    "tg_new_listing": {"ru": "Новое объявление", "he": "מודעה חדשה", "en": "New listing"},
    "tg_conversations": {"ru": "Последние разговоры бота", "he": "שיחות בוט אחרונות", "en": "Recent bot conversations"},
    "tg_conversations_desc": {"ru": "Лента взаимодействий бота с респондентами", "he": "פיד של אינטראקציות בוט עם מגיבים", "en": "Live feed of bot interactions"},
    "tg_no_conversations": {"ru": "Пока нет разговоров.", "he": "אין שיחות עדיין.", "en": "No conversations yet."},
    "tg_no_destinations": {"ru": "Нет каналов. Нажмите Синхронизировать или Добавить.", "he": "אין יעדים. לחץ סנכרן או הוסף.", "en": "No destinations yet. Click Sync or Add."},
    "tg_add_dest_title": {"ru": "Добавить канал", "he": "הוסף יעד", "en": "Add destination"},
    "tg_post_text": {"ru": "Текст объявления", "he": "טקסט המודעה", "en": "Post text"},
    "tg_post_text_placeholder": {"ru": "Полный текст объявления для публикации в группах...", "he": "טקסט מלא של המודעה לפרסום בקבוצות...", "en": "Full text of the post that will go to groups..."},
    "tg_start_posting": {"ru": "Начать публикацию", "he": "התחל פרסום", "en": "Start posting"},
    "tg_immediately": {"ru": "Сразу", "he": "מיד", "en": "Immediately"},
    "tg_tomorrow_morning": {"ru": "Завтра утром (09:00)", "he": "מחר בבוקר (09:00)", "en": "Tomorrow morning (09:00)"},
    "tg_custom": {"ru": "Настроить", "he": "מותאם", "en": "Custom"},
    "tg_every_hour": {"ru": "Каждый час", "he": "כל שעה", "en": "Every hour"},
    "tg_every_3h": {"ru": "Каждые 3 часа", "he": "כל 3 שעות", "en": "Every 3 hours"},
    "tg_every_6h": {"ru": "Каждые 6 часов", "he": "כל 6 שעות", "en": "Every 6 hours"},
    "tg_days": {"ru": "Дни", "he": "ימים", "en": "Days"},
    "tg_active_hours": {"ru": "Рабочие часы", "he": "שעות פעילות", "en": "Active hours"},
    "tg_create_and_post": {"ru": "Создать и начать публикацию", "he": "צור והתחל לפרסם", "en": "Create and start posting"},
    "tg_folder": {"ru": "Папка", "he": "תיקייה", "en": "Folder"},
    "tg_set": {"ru": "Задать", "he": "קבע", "en": "Set"},
    "tg_remove_confirm": {"ru": "Удалить этот канал?", "he": "להסיר יעד זה?", "en": "Remove this destination?"},
    "tg_added": {"ru": "Добавлено", "he": "נוסף", "en": "Added"},
    "tg_phone": {"ru": "Номер телефона", "he": "מספר טלפון", "en": "Phone number"},
    "tg_all_candidates": {"ru": "Все кандидаты", "he": "כל המועמדים", "en": "All candidates"},
    "photo_label": {"ru": "Фото", "he": "תמונה", "en": "Photo"},
    # --- Facebook connect ---
    "fb_connect_title": {"ru": "Подключить Facebook", "he": "חבר פייסבוק", "en": "Connect Facebook"},
    "fb_connect_desc": {"ru": "Подключите Facebook для публикации в группах. Система найдет ваши группы автоматически.", "he": "חבר פייסבוק לפרסום בקבוצות. המערכת תמצא את הקבוצות שלך אוטומטית.", "en": "Connect Facebook to post in groups. The system will find your groups automatically."},
    "fb_login_btn": {"ru": "Войти через Facebook", "he": "התחבר דרך פייסבוק", "en": "Login with Facebook"},
    "fb_connected": {"ru": "Facebook подключен", "he": "פייסבוק מחובר", "en": "Facebook connected"},
    "fb_sync_btn": {"ru": "Синхронизировать группы", "he": "סנכרן קבוצות", "en": "Sync groups"},
    "fb_groups_title": {"ru": "Ваши группы Facebook", "he": "קבוצות הפייסבוק שלך", "en": "Your Facebook groups"},
    "fb_groups_desc": {"ru": "Выберите группы для публикации", "he": "בחר קבוצות לפרסום", "en": "Select groups for posting"},
    "fb_add_selected": {"ru": "Добавить выбранные", "he": "הוסף נבחרים", "en": "Add selected"},
    "fb_members": {"ru": "участников", "he": "חברים", "en": "members"},
    "fb_admin": {"ru": "Администратор", "he": "מנהל", "en": "Admin"},
    "fb_not_configured": {"ru": "Facebook App не настроен. Добавьте FB_APP_ID и FB_APP_SECRET в .env", "he": "אפליקציית פייסבוק לא מוגדרת. הוסף FB_APP_ID ו-FB_APP_SECRET ל-.env", "en": "Facebook App not configured. Add FB_APP_ID and FB_APP_SECRET to .env"},
    "fb_destinations": {"ru": "Добавленные группы", "he": "קבוצות שנוספו", "en": "Added groups"},
    "fb_added": {"ru": "Добавлено", "he": "נוסף", "en": "Added"},
    "fb_add_manual": {"ru": "Добавить вручную", "he": "הוסף ידנית", "en": "Add manually"},
    "continue_to_facebook": {"ru": "Продолжить к Facebook", "he": "המשך לפייסבוק", "en": "Continue to Facebook"},
    # --- Connect Facebook ---
    "assisted_mode_title": {"ru": "Ручной режим постинга", "he": "מצב פרסום מלווה", "en": "Assisted posting mode"},
    "assisted_mode_desc": {"ru": "Facebook не позволяет автоматический постинг в группы. Мы подготовим текст — вы копируете и вставляете. Мы отслеживаем каждый шаг.", "he": "פייסבוק לא מאפשר פרסום אוטומטי בקבוצות. אנחנו מכינים את הטקסט — אתה מעתיק ומדביק. אנחנו עוקבים אחרי כל שלב.", "en": "Facebook does not allow automated group posting. We help you post quickly: the system prepares the content, you copy and paste into each group. We track every step."},
    "add_fb_groups_title": {"ru": "Добавьте группы Facebook", "he": "הוסף קבוצות פייסבוק", "en": "Add your Facebook groups"},
    "add_fb_groups_desc": {"ru": "Введите название и URL групп Facebook для постинга вакансий.", "he": "הזן שם וכתובת URL של קבוצות פייסבוק לפרסום משרות.", "en": "Enter the name and URL of Facebook groups where you want to post."},
    "generate_asset_title": {"ru": "Создайте текст поста", "he": "צור נכס פרסום", "en": "Generate a posting asset"},
    "generate_asset_desc": {"ru": "AI создаст оптимизированные посты на иврите/русском/английском.", "he": "ה-AI יצור פוסטים מותאמים בעברית/רוסית/אנגלית.", "en": "Our AI creates optimized posts for each vacancy with the right tone and CTA."},
    "use_queue_title": {"ru": "Используйте очередь постинга", "he": "השתמש בתור הפרסום", "en": "Use the posting queue"},
    "use_queue_desc": {"ru": "Откройте группу, скопируйте текст, вставьте и опубликуйте. Отметьте выполнение.", "he": "פתח קבוצה, העתק טקסט, הדבק ופרסם. סמן כהושלם.", "en": "Open each group, copy the prepared text, paste and post. Mark each one as done."},
    "group_name": {"ru": "Название группы", "he": "שם הקבוצה", "en": "Group name"},
    "fb_group_url": {"ru": "URL группы Facebook", "he": "כתובת קבוצת פייסבוק", "en": "Facebook group URL"},
    "add_fb_group_btn": {"ru": "Добавить группу Facebook", "he": "הוסף קבוצת פייסבוק", "en": "Add Facebook Group"},
    "your_fb_dests": {"ru": "Ваши группы Facebook", "he": "קבוצות הפייסבוק שלך", "en": "Your Facebook Destinations"},
    "no_url_set": {"ru": "URL не указан", "he": "לא הוגדר URL", "en": "No URL set"},
    "assisted_manual": {"ru": "ручной режим", "he": "מצב ידני מלווה", "en": "assisted manual"},
    "create_campaign_link": {"ru": "Создать кампанию", "he": "צור קמפיין", "en": "Create Campaign"},
    # --- Companies ---
    "companies_title": {"ru": "Компании", "he": "חברות", "en": "Companies"},
    "new_btn": {"ru": "+ Новая", "he": "+ חדש", "en": "+ New"},
    "id_col": {"ru": "ID", "he": "ID", "en": "ID"},
    "status_active": {"ru": "активна", "he": "פעילה", "en": "active"},
    "status_disabled": {"ru": "отключена", "he": "מושבתת", "en": "disabled"},
    "select_btn": {"ru": "Выбрать", "he": "בחר", "en": "Select"},
    "ai_settings_link": {"ru": "AI настройки", "he": "הגדרות AI", "en": "AI Settings"},
    "disable_btn": {"ru": "Отключить", "he": "השבת", "en": "Disable"},
    "new_company_title": {"ru": "Новая компания", "he": "חברה חדשה", "en": "New company"},
    "description_label": {"ru": "Описание", "he": "תיאור", "en": "Description"},
    "create_btn": {"ru": "Создать", "he": "צור", "en": "Create"},
    # --- Candidate view ---
    "candidate_heading": {"ru": "Лид", "he": "ליד", "en": "Lead"},
    "name_label": {"ru": "Имя", "he": "שם", "en": "Name"},
    "tg_label": {"ru": "Telegram", "he": "טלגרם", "en": "Telegram"},
    "status_label": {"ru": "Статус", "he": "סטטוס", "en": "Status"},
    "score_label": {"ru": "Балл", "he": "ציון", "en": "Score"},
    "vacancy_label": {"ru": "Объявление", "he": "מודעה", "en": "Listing"},
    "summary_label": {"ru": "Резюме", "he": "סיכום", "en": "Summary"},
    "save_btn": {"ru": "Сохранить", "he": "שמור", "en": "Save"},
    "chat_log": {"ru": "Лог чата", "he": "יומן שיחה", "en": "Chat log"},
    "back_btn": {"ru": "Назад", "he": "חזרה", "en": "Back"},
    # --- AI Settings ---
    "ai_settings_title": {"ru": "AI настройки", "he": "הגדרות AI", "en": "AI Settings"},
    "tone_label": {"ru": "Тон", "he": "טון", "en": "Tone"},
    "positive_prompt": {"ru": "Позитивный промпт", "he": "פרומפט חיובי", "en": "Positive prompt"},
    "negative_prompt": {"ru": "Негативный промпт", "he": "פרומפט שלילי", "en": "Negative prompt"},
    "greeting_template": {"ru": "Шаблон приветствия", "he": "תבנית ברכה", "en": "Greeting template"},
    "rejection_template": {"ru": "Шаблон отказа", "he": "תבנית דחייה", "en": "Rejection template"},
    "success_template": {"ru": "Шаблон успеха", "he": "תבנית הצלחה", "en": "Success template"},
    "test_ai": {"ru": "Тест AI", "he": "בדיקת AI", "en": "Test AI"},
    "test_message": {"ru": "Тестовое сообщение", "he": "הודעת בדיקה", "en": "Test message"},
    "run_btn": {"ru": "Запустить", "he": "הפעל", "en": "Run"},
    "ai_test_title": {"ru": "Тест AI", "he": "בדיקת AI", "en": "AI test"},
    "input_label": {"ru": "Ввод", "he": "קלט", "en": "Input"},
    "output_label": {"ru": "Результат", "he": "פלט", "en": "Output"},
    # --- Misc ---
    "email_label": {"ru": "Email", "he": "אימייל", "en": "Email"},
    "phone_label_full": {"ru": "Телефон", "he": "טלפון", "en": "Phone"},
    "most_popular": {"ru": "Популярный", "he": "הפופולרי", "en": "Most Popular"},
    "faq_title": {"ru": "FAQ", "he": "שאלות נפוצות", "en": "FAQ"},
    "saved_label": {"ru": "Сохранено", "he": "נשמר", "en": "Saved"},
    "business_type_label": {"ru": "Тип бизнеса", "he": "סוג עסק", "en": "Business type"},
    "business_type_company": {"ru": "Компания", "he": "חברה", "en": "Company"},
    "business_type_individual": {"ru": "Частный специалист", "he": "עצמאי", "en": "Individual"},
    "profile_description_placeholder": {
        "ru": "Чем занимается ваш бизнес?",
        "he": "במה העסק שלך עוסק?",
        "en": "What does your business do?",
    },
    "contact_person_label": {"ru": "Контактное лицо", "he": "איש קשר", "en": "Contact person"},
    "contact_person_placeholder": {"ru": "Полное имя", "he": "שם מלא", "en": "Full name"},
    "website_label": {"ru": "Сайт", "he": "אתר", "en": "Website"},
    "owner_telegram_id_label": {
        "ru": "Telegram ID для HOT lead уведомлений",
        "he": "Telegram ID להתראות לידים חמים",
        "en": "Telegram ID for HOT lead alerts",
    },
    "owner_telegram_id_hint": {
        "ru": "Куда слать мгновенные HOT lead уведомления. Укажите numeric user/chat ID; если пусто, останется env/legacy fallback.",
        "he": "לאן לשלוח התראות מיידיות על לידים חמים. הזן מזהה מספרי של משתמש/צ'אט; אם ריק, יישאר fallback של env/legacy.",
        "en": "Where instant HOT lead alerts should be sent. Enter a numeric Telegram user/chat ID; leave blank to keep env/legacy fallback.",
    },
    "telegram_connected_hint": {
        "ru": "Telegram client подключён (API ID:",
        "he": "לקוח Telegram מחובר (API ID:",
        "en": "Telegram client connected (API ID:",
    },
    # Vacancy form placeholders (Tamar reported English placeholders inside RU UI as "выглядит как незаконченный продукт")
    "ph_body": {
        "ru": "Опишите вакансию: что делать, где, требования, условия...",
        "he": "תאר את ההצעה: מה לעשות, איפה, דרישות, תנאים...",
        "en": "Listing description: what to do, where, requirements, terms...",
    },
    "ph_final_post_title": {
        "ru": "По умолчанию — заголовок объявления",
        "he": "ברירת מחדל — כותרת המודעה",
        "en": "Defaults to listing title",
    },
    "ph_final_post_body": {
        "ru": "Если пусто, текст поста соберётся из полей объявления.",
        "he": "אם ריק, טקסט הפוסט נבנה משדות המודעה.",
        "en": "If empty, the system builds the posting asset from the listing fields.",
    },
    "ph_bot_intro": {
        "ru": "Что бот скажет соискателю первым (приветствие, контекст вакансии)…",
        "he": "מה הבוט אומר ראשון (ברכה, הקשר המשרה)…",
        "en": "How the bot introduces itself to respondents…",
    },
    "ph_bot_faq": {
        "ru": "Факты для бота (зарплата, график, локация, требования) — отвечает сам, не отвлекая оператора…",
        "he": "עובדות לבוט (שכר, לו״ז, מיקום, דרישות) — עונה לבד בלי להפריע למפעיל…",
        "en": "Facts the bot can answer by itself (price, schedule, location, etc.)…",
    },
    "ph_bot_qq": {
        "ru": "Сколько лет опыта работы?\nВ каком городе живёте?\nЕсть ли документы для работы в Израиле?",
        "he": "כמה שנות ניסיון?\nבאיזו עיר אתה גר?\nיש לך מסמכים לעבודה בישראל?",
        "en": "What's your budget?\nWhen are you available?\nDo you have experience?",
    },
    "ph_bot_hot": {
        "ru": "Кого считаем горячим лидом: ответил на все вопросы, оставил телефон, опыт совпадает.",
        "he": "מי נחשב ליד חם: ענה על כל השאלות, השאיר טלפון, ניסיון מתאים.",
        "en": "Answered all questions + left phone number",
    },
    "ph_bot_cold": {
        "ru": "Что считаем холодным: спам, грубит, не подходит по требованиям.",
        "he": "מה נחשב קר: ספאם, גס, לא עומד בדרישות.",
        "en": "Spam, rude, irrelevant, doesn't meet criteria",
    },
    # Vacancy form labels (was hardcoded English even when locale=RU)
    "bot_settings_title": {"ru": "Настройки бота", "he": "הגדרות בוט", "en": "AI Bot Settings"},
    "listing_type_label": {"ru": "Тип объявления", "he": "סוג מודעה", "en": "Listing Type"},
    "listing_type_recruitment": {"ru": "Вакансия (наём)", "he": "משרה (גיוס)", "en": "Job Vacancy"},
    "listing_type_auto": {"ru": "Продажа авто", "he": "מכירת רכב", "en": "Car Sale"},
    "listing_type_realestate": {"ru": "Аренда квартиры", "he": "השכרת דירה", "en": "Apartment Rental"},
    "listing_type_services": {"ru": "Услуги", "he": "שירותים", "en": "Service Offering"},
    "listing_type_custom": {"ru": "Своё", "he": "מותאם אישית", "en": "Custom"},
    "bot_intro_label": {"ru": "Приветствие бота", "he": "ברכת הבוט", "en": "Bot Introduction"},
    "bot_faq_label": {"ru": "FAQ для бота", "he": "FAQ לבוט", "en": "Bot FAQ Knowledge"},
    "bot_qq_label": {"ru": "Уточняющие вопросы (по одному на строку)", "he": "שאלות מסננות (אחת בשורה)", "en": "Bot Qualifying Questions (one per line)"},
    "bot_hot_label": {"ru": "Считать ГОРЯЧИМ если", "he": "סמן כחם אם", "en": "Mark as HOT when"},
    "bot_cold_label": {"ru": "Считать ХОЛОДНЫМ если", "he": "סמן כקר אם", "en": "Mark as COLD when"},
    "edit_vacancy_title": {"ru": "Редактировать объявление", "he": "עריכת מודעה", "en": "Edit listing"},
    "what_posting": {"ru": "Что публикуем?", "he": "מה מפרסמים?", "en": "What are you posting?"},
    "ph_title": {
        "ru": "Например: Укладчик бетона — Тель-Авив",
        "he": "למשל: רצף בטון — תל אביב",
        "en": "e.g. Construction worker — Tel Aviv",
    },
    "ph_city": {
        "ru": "Например: Тель-Авив или 'По всей стране'",
        "he": "למשל: תל אביב או 'כל הארץ'",
        "en": "e.g. Tel Aviv",
    },
    "ph_salary": {
        "ru": "Например: 55 ₪/час или 12000 ₪/мес",
        "he": "למשל: 55 ₪/שעה או 12000 ₪/חודש",
        "en": "e.g. 55 ₪/hour",
    },
    "ph_schedule": {
        "ru": "Например: Вс-Чт 07:00–16:00 или 'Свободный график'",
        "he": "למשל: א׳-ה׳ 07:00–16:00",
        "en": "e.g. Sun-Thu, 07:00-16:00",
    },
    "ph_contact": {
        "ru": "Например: Telegram @recruiter или +972...",
        "he": "למשל: Telegram @recruiter או +972...",
        "en": "e.g. Telegram @recruiter or phone",
    },
    "whatsapp_label": {"ru": "WhatsApp номер", "he": "מספר WhatsApp", "en": "WhatsApp Number"},
    "ph_whatsapp": {
        "ru": "Например: 972541234567 (без +)",
        "he": "למשל: 972541234567",
        "en": "e.g. 972541234567",
    },
    "save_changes_btn": {"ru": "Сохранить изменения", "he": "שמור שינויים", "en": "Save changes"},
    "photo_label": {"ru": "Фото", "he": "תמונה", "en": "Photo"},
    "photo_existing": {"ru": "Текущее фото", "he": "תמונה נוכחית", "en": "Current photo"},
    "edit_vacancy_action": {"ru": "Редактировать", "he": "ערוך", "en": "Edit"},
    "cls_hot": {"ru": "Горячие", "he": "חמים", "en": "Hot"},
    "cls_warm": {"ru": "Тёплые", "he": "פושרים", "en": "Warm"},
    "cls_cold": {"ru": "Холодные", "he": "קרים", "en": "Cold"},
    "cls_duplicate": {"ru": "Дубли", "he": "כפילויות", "en": "Duplicate"},
    "class_label": {"ru": "Класс", "he": "סוג", "en": "Class"},
    "all": {"ru": "Все", "he": "הכל", "en": "All"},
    # Vacancy wizard
    "wiz_step_1": {"ru": "Что публикуем", "he": "מה מפרסמים", "en": "What"},
    "wiz_step_2": {"ru": "Условия и контакты", "he": "תנאים ופרטים", "en": "Terms & contacts"},
    "wiz_step_3": {"ru": "Бот скрининг", "he": "סינון בוט", "en": "Bot screening"},
    "wiz_back": {"ru": "Назад", "he": "חזרה", "en": "Back"},
    "wiz_next": {"ru": "Далее", "he": "הבא", "en": "Next"},
    "wiz_validation_step1": {
        "ru": "Заполни название и описание перед переходом к следующему шагу.",
        "he": "מלא כותרת ותיאור לפני המעבר לשלב הבא.",
        "en": "Fill in title and description before moving to the next step.",
    },
    "wiz_step_3_intro": {
        "ru": "Бот будет задавать эти вопросы соискателям, оценивать ответы и присылать тебе горячие лиды.",
        "he": "הבוט ישאל את השאלות האלה את המועמדים, יעריך את התשובות וישלח אליך לידים חמים.",
        "en": "The bot will ask candidates these questions, score answers, and forward hot leads.",
    },
    "wiz_post_text_override": {
        "ru": "Текст поста (если хочешь переписать вручную)",
        "he": "טקסט הפוסט (אם רוצים לשכתב ידנית)",
        "en": "Post text override (only if you want to write it manually)",
    },
    "apply_link_helper": {
        "ru": "Если пусто — система подставит ссылку на бота автоматически.",
        "he": "אם ריק — המערכת תשלים את הקישור לבוט אוטומטית.",
        "en": "If left empty, Posting Autopilot uses the connected RecruitBot deep link automatically.",
    },
    "vac_funnel_title": {
        "ru": "Воронка кандидатов по этой вакансии",
        "he": "משפך מועמדים למודעה זו",
        "en": "Candidate funnel for this listing",
    },
    "vac_funnel_empty": {
        "ru": "Кандидатов по этой вакансии пока нет. Запусти кампанию или дождись первых откликов.",
        "he": "עדיין אין מועמדים למודעה זו. הפעל קמפיין או המתן לפניות הראשונות.",
        "en": "No candidates yet for this listing. Activate a campaign or wait for first applicants.",
    },
    "vac_funnel_avg_score": {"ru": "Средний балл", "he": "ציון ממוצע", "en": "Average score"},
    "vac_funnel_last_at": {"ru": "Последний отклик", "he": "פנייה אחרונה", "en": "Last applicant"},
    "view_all": {"ru": "Смотреть всех", "he": "הצג הכל", "en": "View all"},
    "when": {"ru": "Когда", "he": "מתי", "en": "When"},
    # Campaigns + posting attempts (i18n leaks Tamar caught in re-test)
    "manual_action_hint": {
        "ru": "Открой канал, опубликуй вручную, потом сохрани результат ниже.",
        "he": "פתח את היעד, פרסם ידנית, ושמור את התוצאה למטה.",
        "en": "Open destination, publish manually, then save the result below.",
    },
    "campaign_pilot_focus": {
        "ru": "Telegram авто + Facebook ручная публикация",
        "he": "טלגרם אוטומטי + פייסבוק פרסום ידני",
        "en": "Telegram auto + Facebook assisted/manual",
    },
    "ph_operator_notes": {
        "ru": "Заметки оператора или причина ошибки",
        "he": "הערות מפעיל או סיבת הכשל",
        "en": "Paste operator notes or failure details",
    },
    "retry_btn": {"ru": "↻ Повторить", "he": "↻ נסה שוב", "en": "↻ Retry"},
    "retry_hint": {
        "ru": "Повторить попытку постинга для этой записи",
        "he": "נסה שוב לפרסם את הרשומה הזו",
        "en": "Retry this posting attempt now",
    },
    "retry_confirm": {
        "ru": "Запустить повторную попытку постинга? Эта запись будет включена в следующий цикл и попытка отправится в течение минуты.",
        "he": "להפעיל ניסיון פרסום נוסף? הרשומה הזו תיכנס למחזור הבא ותישלח תוך דקה.",
        "en": "Retry posting now? This entry will be queued and the attempt will fire within a minute.",
    },
    # Duplicate cross-ref
    "dup_of_label": {
        "ru": "Дубль от",
        "he": "כפילות של",
        "en": "Duplicate of",
    },
    # Multi-photo for real estate / cars listings
    "photos_label": {"ru": "Фото", "he": "תמונות", "en": "Photos"},
    "photos_helper": {
        "ru": "Можно выбрать несколько файлов сразу. Для квартир рекомендуем 8–15 фото, для авто 6–10.",
        "he": "ניתן לבחור מספר קבצים בבת אחת. לדירות מומלץ 8–15 תמונות, לרכב 6–10.",
        "en": "Pick multiple files at once. 8–15 recommended for apartments, 6–10 for cars.",
    },
    "photos_existing_count": {"ru": "Сейчас прикреплено", "he": "מצורפות כעת", "en": "Currently attached"},
    "photos_replace_helper": {
        "ru": "Удалить старые и заменить на новые загруженные",
        "he": "מחק את הישנות והחלף בחדשות",
        "en": "Delete the existing photos and replace with newly uploaded",
    },
    # Listing-type-driven label overrides — Tamar's "Зарплата" makes no sense for rentals,
    # Misha's complaint about "vacancy/candidate" terminology, Boris's "schedule" for cars.
    # Form labels remap based on form_values.listing_type (or the active template).
    "salary_recruitment": {"ru": "Зарплата", "he": "שכר", "en": "Salary"},
    "salary_realestate":  {"ru": "Цена / месяц",     "he": "מחיר / חודש",        "en": "Rent / month"},
    "salary_auto":        {"ru": "Цена",              "he": "מחיר",                "en": "Price"},
    "salary_services":    {"ru": "Стоимость услуги",  "he": "עלות השירות",         "en": "Service price"},

    "schedule_recruitment": {"ru": "График",              "he": "לוח זמנים",        "en": "Schedule"},
    "schedule_realestate":  {"ru": "Свободна с",          "he": "פנויה מ-",          "en": "Available from"},
    "schedule_auto":        {"ru": "Год / Пробег",        "he": "שנה / קילומטראז'",  "en": "Year / Mileage"},
    "schedule_services":    {"ru": "Доступность",         "he": "זמינות",            "en": "Availability"},

    "ph_salary_recruitment": {"ru": "Например: 55 ₪/час или 12000 ₪/мес", "he": "למשל: 55 ₪/שעה", "en": "e.g. 55 ₪/hour"},
    "ph_salary_realestate":  {"ru": "Например: 7500 ₪/мес",                "he": "למשל: 7500 ₪/חודש", "en": "e.g. 7500 ₪/month"},
    "ph_salary_auto":        {"ru": "Например: 62000 ₪",                   "he": "למשל: 62000 ₪",     "en": "e.g. 62000 ₪"},
    "ph_salary_services":    {"ru": "Например: 350 ₪ / выезд",             "he": "למשל: 350 ₪",        "en": "e.g. 350 ₪ / visit"},

    "ph_schedule_recruitment": {"ru": "Например: Вс-Чт 07:00–16:00", "he": "למשל: א׳-ה׳ 07:00–16:00", "en": "e.g. Sun-Thu, 07:00-16:00"},
    "ph_schedule_realestate":  {"ru": "Например: с 1 июля 2026",      "he": "למשל: מ-1 ביולי 2026",     "en": "e.g. from 1 July 2026"},
    "ph_schedule_auto":        {"ru": "Например: 2019 / 80,000 км",   "he": "למשל: 2019 / 80,000 ק״מ", "en": "e.g. 2019 / 80,000 km"},
    "ph_schedule_services":    {"ru": "Например: с понедельника",     "he": "למשל: מיום שני",            "en": "e.g. starting Monday"},
}

def ui(key: str, lang: str = "en", **kwargs) -> str:
    """Get UI translation for admin templates."""
    msg = UI.get(key, {})
    text = msg.get(lang) or msg.get("en") or key
    if kwargs:
        text = text.format(**kwargs)
    return text

RTL_LANGUAGES = {"he", "ar"}

def is_rtl(lang: str) -> bool:
    """Check if language requires RTL direction."""
    return lang in RTL_LANGUAGES

# Fallback questions when vacancy has no custom questions
DEFAULT_QUESTIONS = {
    "ru": ["Какой у тебя опыт работы? (кратко)", "В каком ты городе сейчас?", "Есть ли документы/разрешение на работу?"],
    "he": ["מה הניסיון שלך בעבודה? (בקצרה)", "באיזו עיר את/ה נמצא/ת כרגע?", "יש לך אישור עבודה/מסמכים?"],
    "en": ["What is your work experience? (briefly)", "What city are you in right now?", "Do you have work permit/documents?"],
}

# Telegram language_code → our language
LANG_MAP = {
    "ru": "ru", "uk": "ru", "be": "ru",  # Ukrainian, Belarusian → Russian
    "he": "he", "iw": "he",               # Hebrew (iw is legacy code)
    "en": "en",
}
# Safe fallback chain: explicit user lang -> mapped lang -> DEFAULT_LANG (env) -> "ru".
# Operator can override via DEFAULT_LANG env var (set in docker-compose.yml runtime-env)
# without code changes — useful for HE-first or EN-first pilots.
DEFAULT_LANG = os.getenv("DEFAULT_LANG", "ru")
_HARD_FALLBACK = "ru"


def detect_language(telegram_language_code: str | None) -> str:
    """Detect language from Telegram's language_code field.

    Fallback chain: explicit user lang → mapped lang → DEFAULT_LANG (env) → "ru".
    """
    if not telegram_language_code:
        return DEFAULT_LANG or _HARD_FALLBACK
    code = telegram_language_code.lower().split("-")[0]  # "en-US" → "en"
    return LANG_MAP.get(code, DEFAULT_LANG or _HARD_FALLBACK)


def t(key: str, lang: str = "ru", **kwargs) -> str:
    """Get translated message by key and language."""
    msg = MESSAGES.get(key, {})
    text = msg.get(lang) or msg.get(DEFAULT_LANG) or key
    if kwargs:
        text = text.format(**kwargs)
    return text


def get_questions(lang: str = "ru") -> list[str]:
    """Get default screening questions for a language."""
    return DEFAULT_QUESTIONS.get(lang, DEFAULT_QUESTIONS[DEFAULT_LANG])
