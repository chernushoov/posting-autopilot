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
    "login_id_label": {"ru": "Email или логин", "he": "אימייל או שם משתמש", "en": "Email or username"},
    "login_id_placeholder": {"ru": "you@company.com", "he": "you@company.com", "en": "you@company.com"},
    "password_field": {"ru": "Пароль", "he": "סיסמה", "en": "Password"},
    "enter_btn": {"ru": "Войти", "he": "כניסה", "en": "Sign In"},
    "login_no_account": {"ru": "Нет аккаунта?", "he": "אין חשבון?", "en": "No account?"},
    "login_register_cta": {"ru": "Создать — 14 дней бесплатно", "he": "צור חשבון — 14 ימים בחינם", "en": "Create one — 14 days free"},
    "login_have_account": {"ru": "Уже есть аккаунт?", "he": "כבר יש לך חשבון?", "en": "Already have an account?"},
    "login_invalid": {"ru": "Неверный email или пароль", "he": "אימייל או סיסמה שגויים", "en": "Invalid email or password"},
    "login_missing_fields": {"ru": "Заполните email и пароль", "he": "נא למלא אימייל וסיסמה", "en": "Email and password are required"},
    "login_rate_limited": {"ru": "Слишком много попыток. Подождите 5 минут.", "he": "יותר מדי ניסיונות. נסה שוב בעוד 5 דקות.", "en": "Too many attempts. Please wait 5 minutes."},
    # Register
    "register_title": {"ru": "Создать аккаунт", "he": "צור חשבון", "en": "Create Account"},
    "register_subtitle": {"ru": "14 дней бесплатно. Без карты.", "he": "14 ימי ניסיון חינם. ללא כרטיס אשראי.", "en": "14-day free trial. No credit card required."},
    "register_email_label": {"ru": "Email", "he": "אימייל", "en": "Email"},
    "register_email_ph": {"ru": "you@company.com", "he": "you@company.com", "en": "you@company.com"},
    "register_password_label": {"ru": "Пароль", "he": "סיסמה", "en": "Password"},
    "register_password_ph": {"ru": "Минимум 6 символов", "he": "לפחות 6 תווים", "en": "Min 6 characters"},
    "register_company_label": {"ru": "Название компании", "he": "שם העסק", "en": "Company name"},
    "register_company_ph": {"ru": "Ваш бизнес", "he": "העסק שלך", "en": "Your business name"},
    "register_submit": {"ru": "Начать бесплатно", "he": "התחל ניסיון חינם", "en": "Start Free Trial"},
    "register_email_taken": {"ru": "Этот email уже зарегистрирован.", "he": "האימייל הזה כבר רשום.", "en": "Email already registered."},
    "register_email_invalid": {"ru": "Неверный формат email.", "he": "כתובת אימייל לא חוקית.", "en": "Invalid email address."},
    "register_password_short": {"ru": "Пароль не короче 6 символов.", "he": "הסיסמה חייבת להיות לפחות 6 תווים.", "en": "Password must be at least 6 characters."},
    "register_required": {"ru": "Все поля обязательны.", "he": "כל השדות חובה.", "en": "All fields are required."},
    # Terms of service
    "terms_title": {"ru": "Условия использования", "he": "תנאי שימוש", "en": "Terms of Service"},
    "terms_updated": {"ru": "Обновлено: апрель 2026", "he": "עודכן: אפריל 2026", "en": "Last updated: April 2026"},
    "terms_h1": {"ru": "1. Описание сервиса", "he": "1. תיאור השירות", "en": "1. Service Description"},
    "terms_p1": {"ru": "Posting Autopilot — автоматизация публикации объявлений и AI-скрининг лидов для бизнеса. Сервис публикует ваши объявления в Telegram-группы и Facebook-сообщества и обрабатывает входящие отклики через AI-помощника.", "he": "Posting Autopilot מספק פרסום אוטומטי וסינון לידים מבוסס-AI לעסקים. השירות מפרסם את המודעות שלך בקבוצות טלגרם ופייסבוק ומטפל בתגובות באמצעות עוזר AI.", "en": "Posting Autopilot provides automated posting and AI-powered lead screening for businesses. The service posts your listings to Telegram groups and Facebook communities, and processes incoming responses through an AI assistant."},
    "terms_h2": {"ru": "2. Аккаунт и пробный период", "he": "2. חשבון וניסיון", "en": "2. Account & Trial"},
    "terms_p2": {"ru": "Новые аккаунты получают 14 дней бесплатного пробного периода. После — требуется платная подписка. Вы отвечаете за безопасность ваших учётных данных.", "he": "חשבונות חדשים מקבלים תקופת ניסיון של 14 ימים בחינם. לאחר מכן נדרש מנוי בתשלום. אתה אחראי לאבטחת פרטי הכניסה שלך.", "en": "New accounts receive a 14-day free trial. After the trial, a paid subscription is required. You are responsible for maintaining the security of your account credentials."},
    "terms_h3": {"ru": "3. Допустимое использование", "he": "3. שימוש מותר", "en": "3. Acceptable Use"},
    "terms_p3": {"ru": "Запрещено использовать сервис для спама, незаконного контента, вводящих в заблуждение постов или нарушающих правила Telegram/Facebook действий. Мы вправе приостановить аккаунт за нарушения.", "he": "אסור להשתמש בשירות לספאם, תוכן בלתי חוקי, פוסטים מטעים או כל פעילות שמפרה את תנאי טלגרם או פייסבוק. אנו שומרים לעצמנו את הזכות להשעות חשבונות.", "en": "You agree not to use the service for spam, illegal content, misleading posts, or any activity that violates Telegram's or Facebook's terms of service. We reserve the right to suspend accounts that violate these terms."},
    "terms_h4": {"ru": "4. Анти-спам", "he": "4. מדיניות אנטי-ספאם", "en": "4. Anti-Spam Policy"},
    "terms_p4": {"ru": "Система применяет лимиты публикаций для предотвращения спама. Попытки обхода лимитов могут привести к блокировке аккаунта.", "he": "המערכת אוכפת מגבלות קצב פרסום למניעת ספאם. ניסיונות לעקוף את המגבלות עלולים לגרום להשעיית חשבון.", "en": "The system enforces posting rate limits to prevent spam. Attempts to circumvent these limits may result in account suspension."},
    "terms_h5": {"ru": "5. Данные и приватность", "he": "5. נתונים ופרטיות", "en": "5. Data & Privacy"},
    "terms_p5": {"ru": "Мы храним данные ваших объявлений, зашифрованные Telegram-сессии и логи диалогов. Данные лидов (имя, телефон, переписка) хранятся для вашего использования. Мы не продаём персональные данные третьим сторонам.", "he": "אנו שומרים את נתוני המודעות, פרטי סשן הטלגרם המוצפנים ויומני שיחות. נתוני לידים (שמות, טלפונים, הודעות) נשמרים לשימוש העסקי שלך. אנו לא מוכרים נתונים אישיים לצדדים שלישיים.", "en": "We store your listing data, Telegram session credentials (encrypted), and conversation logs. Lead data (names, phones, messages) is stored for your business use. We do not sell personal data to third parties."},
    "terms_h6": {"ru": "6. Ограничение ответственности", "he": "6. הגבלת אחריות", "en": "6. Limitation of Liability"},
    "terms_p6": {"ru": "Сервис предоставляется «как есть». Мы не отвечаем за блокировки Telegram-аккаунтов в результате публикаций, хотя анти-спам-меры минимизируют этот риск.", "he": "השירות מסופק \"כמו שהוא\". איננו אחראים להשעיות חשבונות טלגרם כתוצאה מפעילות פרסום, אך אמצעי האנטי-ספאם שלנו מפחיתים את הסיכון.", "en": "The service is provided \"as is.\" We are not responsible for Telegram account bans resulting from posting activity, though our anti-spam measures are designed to minimize this risk."},
    "terms_h7": {"ru": "7. Отмена подписки", "he": "7. ביטול", "en": "7. Cancellation"},
    "terms_p7": {"ru": "Вы можете отменить подписку в любой момент. Данные хранятся 30 дней после отмены.", "he": "ניתן לבטל את המנוי בכל עת. הנתונים יישמרו 30 ימים לאחר הביטול.", "en": "You may cancel your subscription at any time. Your data will be retained for 30 days after cancellation."},
    "terms_h8": {"ru": "8. Контакты", "he": "8. צור קשר", "en": "8. Contact"},
    "terms_p8": {"ru": "По вопросам — пишите через панель управления.", "he": "לשאלות לגבי תנאים אלה, פנה אלינו דרך לוח הבקרה.", "en": "For questions about these terms, contact us through the platform dashboard."},
    # Pricing FAQ
    "faq_q1": {"ru": "Как работает AI-скрининг?", "he": "איך עובד סינון ה-AI?", "en": "How does the AI screening work?"},
    "faq_a1": {"ru": "Кандидаты нажимают «Откликнуться» в посте Telegram. Бот проводит короткое интервью (3-5 вопросов), оценивает ответы AI и присваивает балл. Вы видите только подходящих.", "he": "מועמדים לוחצים \"הגש מועמדות\" בפוסט בטלגרם. הבוט מנהל ראיון קצר (3-5 שאלות), מעריך את התשובות עם AI ונותן ציון. אתה רואה רק את המתאימים.", "en": "Candidates click \"Apply\" on your job posting in Telegram. The bot conducts a short interview (3-5 questions), evaluates answers with AI, and gives each candidate a score. You only see qualified candidates."},
    "faq_q2": {"ru": "Какие языки поддерживаются?", "he": "אילו שפות נתמכות?", "en": "What languages are supported?"},
    "faq_a2": {"ru": "Русский, иврит и английский. Бот определяет язык кандидата автоматически.", "he": "רוסית, עברית ואנגלית. הבוט מזהה את שפת המועמד אוטומטית מהטלגרם.", "en": "Russian, Hebrew, and English. The bot auto-detects the candidate's language from their Telegram settings."},
    "faq_q3": {"ru": "Можно попробовать бесплатно?", "he": "אפשר לנסות בחינם?", "en": "Can I try it for free?"},
    "faq_a3": {"ru": "Да, 14 дней бесплатно. Создайте объявление, опубликуйте в Telegram-группу и смотрите как идут лиды.", "he": "כן! 14 ימי ניסיון חינם. צור מודעה, פרסם בקבוצת טלגרם וראה לידים נכנסים.", "en": "Yes! Free 2-week trial. Create one listing, post to a Telegram group, and see candidates flowing in."},
    "faq_q4": {"ru": "Нужны технические навыки?", "he": "צריך ידע טכני?", "en": "Do I need technical skills?"},
    "faq_a4": {"ru": "Нет. Всё управляется через веб-панель: настройка объявления, вопросы для скрининга, остальное делает AI.", "he": "לא. הכל מנוהל דרך לוח בקרה: הגדרת מודעה, שאלות סינון, וה-AI עושה את השאר.", "en": "No. Everything is managed through a web dashboard. Set up a listing, write screening questions, and the AI handles the rest."},
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
    "tg_credentials": {"ru": "Данные аккаунта", "he": "פרטי חשבון", "en": "Account credentials"},
    "tg_credentials_desc": {"ru": "Перейдите на my.telegram.org, раздел API development tools, скопируйте API ID и API Hash.", "he": "עבור ל-my.telegram.org, API development tools, והעתק API ID ו-API Hash.", "en": "Go to my.telegram.org, API development tools, copy your API ID and API Hash."}
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
