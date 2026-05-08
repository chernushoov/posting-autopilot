"""Task 2.2: Listing Templates — pre-fill vacancy/listing forms for common use cases."""

TEMPLATES = {
    "recruitment": {
        "label": "Job Vacancy",
        "emoji": "👷",
        "listing_type": "recruitment",
        "bot_introduction": "Hi! I'm the assistant helping with this job opening. Let me answer your questions and check if you're a good fit.",
        "bot_faq_knowledge": "Position details, salary range, work schedule, location, required documents/permits.",
        "bot_qualifying_questions": [
            "What is your work experience? (briefly)",
            "What city are you in right now?",
            "Do you have a work permit / documents?",
            "When can you start?",
        ],
        "bot_hot_criteria": "Has relevant experience, documents ready, available soon, left phone number.",
        "bot_cold_criteria": "No documents, not in the area, rude or spam, not interested.",
    },
    "auto": {
        "label": "Car Sale",
        "emoji": "🚗",
        "listing_type": "auto",
        "bot_introduction": "Hi! I'm the assistant for this vehicle listing. Happy to answer your questions!",
        "bot_faq_knowledge": "Car make/model/year, mileage, condition, service history, price, location for viewing.",
        "bot_qualifying_questions": [
            "What is your approximate budget?",
            "When would you like to come see the car?",
            "Are you buying for yourself or reselling?",
        ],
        "bot_hot_criteria": "Budget matches, wants to schedule viewing, left phone number.",
        "bot_cold_criteria": "Budget way too low, just browsing with no intent, rude or spam.",
    },
    "realestate": {
        "label": "Apartment Rental",
        "emoji": "🏠",
        "listing_type": "realestate",
        "bot_introduction": "Hi! I'm the assistant for this property listing. Let me help with your questions!",
        "bot_faq_knowledge": "Number of rooms, floor, size (sqm), price per month, included utilities, parking, pet policy, move-in date.",
        "bot_qualifying_questions": [
            "How many people will live in the apartment?",
            "What is your monthly budget?",
            "When do you need to move in?",
            "Do you have pets?",
        ],
        "bot_hot_criteria": "Budget fits, timeline matches, wants to schedule viewing, left phone number.",
        "bot_cold_criteria": "Budget way too low, wrong area, spam or irrelevant.",
    },
    "services": {
        "label": "Service Offering",
        "emoji": "🔧",
        "listing_type": "services",
        "bot_introduction": "Hi! I'm the assistant for this service. How can I help?",
        "bot_faq_knowledge": "Service type, pricing, service area/cities, availability, payment methods.",
        "bot_qualifying_questions": [
            "What exactly do you need done?",
            "Where are you located?",
            "When do you need this done?",
        ],
        "bot_hot_criteria": "Clear need, in service area, reasonable timeline, left phone number.",
        "bot_cold_criteria": "Out of service area, not a real inquiry, spam.",
    },
    "custom": {
        "label": "Custom",
        "emoji": "✏️",
        "listing_type": "custom",
        "bot_introduction": "",
        "bot_faq_knowledge": "",
        "bot_qualifying_questions": [],
        "bot_hot_criteria": "",
        "bot_cold_criteria": "",
    },
    # ─── HR sub-templates for Israeli blue-collar market (Tamar use case) ───
    # These are recruitment-flavored shortcuts so the operator doesn't write
    # the same questions over and over for the 6 most common roles she hires
    # for. Click → form pre-filled in RU (operator can switch language).
    "hr_cook": {
        "label": "Повар / Cook",
        "emoji": "👨‍🍳",
        "listing_type": "recruitment",
        "bot_introduction": "Здравствуйте! Я ассистент по этой вакансии повара. Задам несколько коротких вопросов и оператор свяжется с подходящими.",
        "bot_faq_knowledge": "График: смены / часы. Кухня: тип кухни, объём. Зарплата: фикс и/или процент. Униформа предоставляется. Документы: на какой статус нанимаем.",
        "bot_qualifying_questions": [
            "Сколько лет работаете поваром? Какие кухни?",
            "В каком городе живёте и готовы ли ездить?",
            "Есть ли документы для работы в Израиле?",
            "Когда готовы выйти на смену?",
        ],
        "bot_hot_criteria": "2+ года опыта поваром, документы в порядке, готов выйти в течение недели.",
        "bot_cold_criteria": "Без опыта в общепите. Нет документов. Не готов работать в смены.",
    },
    "hr_waiter": {
        "label": "Официант / Waiter",
        "emoji": "🍽",
        "listing_type": "recruitment",
        "bot_introduction": "Здравствуйте! Это вакансия официанта. Задам пару вопросов и оператор перезвонит подходящим.",
        "bot_faq_knowledge": "Смены: дневные и/или вечерние. Зарплата: ставка + чаевые. Униформа предоставляется. Английский / иврит — какой нужен.",
        "bot_qualifying_questions": [
            "Сколько лет опыта в обслуживании?",
            "На каких языках говорите (русский / иврит / английский)?",
            "В каком городе живёте?",
            "Когда готовы выйти на работу?",
        ],
        "bot_hot_criteria": "Опыт официантом или в гостеприимстве, иврит или английский на уровне общения, документы в порядке.",
        "bot_cold_criteria": "Только русский без иврита/английского. Нет опыта обслуживания. Нет документов.",
    },
    "hr_cleaner": {
        "label": "Уборщик / Cleaner",
        "emoji": "🧹",
        "listing_type": "recruitment",
        "bot_introduction": "Здравствуйте! Вакансия по уборке. Задам несколько коротких вопросов.",
        "bot_faq_knowledge": "Объект: офис / квартира / стройка. Объём: часов в неделю. Оплата: за час или за объект. Транспорт от/до — кто оплачивает.",
        "bot_qualifying_questions": [
            "Где живёте и какой район готовы покрывать?",
            "Сколько часов в неделю готовы работать?",
            "Есть ли документы для работы в Израиле?",
            "Когда можете начать?",
        ],
        "bot_hot_criteria": "Локально доступен, готов 20+ часов в неделю, документы есть, может начать в течение недели.",
        "bot_cold_criteria": "Не может ездить в нужный район. Хочет только разовую подработку. Нет документов.",
    },
    "hr_welder": {
        "label": "Сварщик / Welder",
        "emoji": "🔥",
        "listing_type": "recruitment",
        "bot_introduction": "Здравствуйте! Это вакансия сварщика. Задам несколько коротких вопросов.",
        "bot_faq_knowledge": "Тип сварки (MIG/TIG/электродуговая). Объекты — стройка / производство. График — день / ночь / сменный. Свой инструмент — обязателен или нет.",
        "bot_qualifying_questions": [
            "Сколько лет работаете сварщиком? Какой тип сварки (MIG/TIG/электрод)?",
            "Есть ли свой инструмент или нужен от компании?",
            "В каком городе живёте, готовы ли ездить по объектам?",
            "Есть ли документы для работы в Израиле?",
        ],
        "bot_hot_criteria": "3+ года сварки, владеет 2+ типами, готов на объекты по стране, документы в порядке.",
        "bot_cold_criteria": "Без подтверждённого опыта. Не готов на стройку. Нет документов.",
    },
    "hr_security": {
        "label": "Охранник / Security",
        "emoji": "🛡",
        "listing_type": "recruitment",
        "bot_introduction": "Здравствуйте! Вакансия охранника. Задам короткие вопросы.",
        "bot_faq_knowledge": "Объект — ТЦ / стройка / частный. Смены — день/ночь/12 часов. Лицензия — нужна или будет получена. Униформа — за наш счёт.",
        "bot_qualifying_questions": [
            "Есть ли действующая лицензия охранника (Khovesh)?",
            "Готовы ли работать ночные смены?",
            "В каком городе живёте?",
            "Когда готовы выйти на смену?",
        ],
        "bot_hot_criteria": "Действующая лицензия, готов на ночные смены, документы в порядке, готов выйти в течение недели.",
        "bot_cold_criteria": "Лицензии нет и не готов учиться. Только дневные смены. Нет документов.",
    },
    "hr_caregiver": {
        "label": "Сиделка / Caregiver",
        "emoji": "🤝",
        "listing_type": "recruitment",
        "bot_introduction": "Здравствуйте! Это вакансия сиделки / помощника. Задам несколько коротких вопросов.",
        "bot_faq_knowledge": "Подопечный — пожилой / инвалид / ребёнок. График — несколько часов в день / 24-часовой / в смены. Зарплата — фикс + проживание (если есть).",
        "bot_qualifying_questions": [
            "Есть ли опыт с пожилыми / лежачими / детьми?",
            "На каких языках можете общаться (русский / иврит / английский)?",
            "Есть ли документы для работы в Израиле?",
            "Готовы ли проживать у клиента (если требуется)?",
        ],
        "bot_hot_criteria": "Опыт ухода 1+ год, базовый иврит для общения, документы в порядке, готов на проживание если нужно.",
        "bot_cold_criteria": "Без опыта ухода. Только русский без иврита. Нет документов. Не готов на проживание (если позиция требует).",
    },
}


def get_template(template_key: str) -> dict:
    return TEMPLATES.get(template_key, TEMPLATES["custom"])


def get_all_templates() -> dict:
    return TEMPLATES
