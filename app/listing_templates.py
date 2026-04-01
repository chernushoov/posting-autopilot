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
}


def get_template(template_key: str) -> dict:
    return TEMPLATES.get(template_key, TEMPLATES["custom"])


def get_all_templates() -> dict:
    return TEMPLATES
