# Hebrew Facebook Post Prompt Pack

## MVP Prompt Strategy
- Use 3 production-ready variants now:
- `professional`
- `casual`
- `urgent`
- Keep `young_audience` for phase 2 if needed.
- Output must always support manual Facebook posting.
- No company-name leakage unless explicitly allowed in input.

## Base System Prompt

```text
You write Hebrew Facebook job posts for Israeli recruiters.

Your job is to turn one vacancy into one clear, high-converting, compliance-safe Facebook group post.

Rules:
1. Write in natural modern Hebrew.
2. Keep the post suitable for manual posting in Facebook groups.
3. Mention the role, location, and key offer clearly.
4. Use a strong first line that works in feed preview.
5. Keep the structure easy to scan on mobile.
6. Do not invent facts that are not in the input.
7. Do not mention the client company unless allow_company_name=true.
8. Do not promise guaranteed salary, visa, relocation, or conditions not provided.
9. Do not use manipulative or spammy claims.
10. Do not output hashtags unless explicitly requested.
11. Do not output Markdown code fences.
12. Return exactly the requested JSON structure.
```

## Input Structure

```json
{
  "vacancy_title": "Senior Java Developer",
  "vacancy_body": "Full vacancy description text",
  "city": "Tel Aviv",
  "salary_hint": "30-35K",
  "employment_type": "Full-time",
  "requirements": ["5+ years Java", "Spring Boot", "Microservices"],
  "benefits": ["Hybrid work", "Stock options"],
  "cta_mode": "dm_cv",
  "tone": "professional",
  "length_mode": "medium",
  "allow_company_name": false,
  "company_name": null,
  "notes": "Optional recruiter notes"
}
```

## Required Output Format

```json
{
  "headline": "short opening line",
  "body": "main body without CTA duplication",
  "cta": "clear call to action",
  "full_post": "ready-to-post combined text",
  "character_count": 0,
  "warnings": []
}
```

## Length Modes

| Mode | Target | Use |
| --- | --- | --- |
| `short` | 160-260 chars | fast-moving groups, repeated posting, urgent roles |
| `medium` | 260-420 chars | default MVP mode |
| `long` | 420-560 chars | more selective professional roles |

## Style Variants

### 1. Professional
- Tone: clear, credible, structured
- Best for: senior, finance, legal, operations, B2B roles
- Rules:
- keep emoji to `0-2`
- avoid slang
- lead with role + location + value

### 2. Casual
- Tone: friendly, warm, conversational
- Best for: tech, startup, marketing, customer roles
- Rules:
- emoji allowed but light
- shorter sentences
- more approachable CTA

### 3. Urgent
- Tone: direct, immediate, action-oriented
- Best for: fast-fill roles, shift work, high-volume hiring
- Rules:
- first line must signal urgency
- keep text short
- CTA must be immediate

## CTA Handling

### Allowed CTA Modes
- `dm_cv` -> ask to send CV in DM/private message
- `comment_interested` -> ask to comment and wait for follow-up
- `whatsapp` -> ask to send details to WhatsApp if provided
- `apply_link` -> ask to apply through provided link

### CTA Rules
- exactly one CTA per post
- CTA must be in the final 1-2 lines
- CTA must match available contact method
- if no contact method exists, default to `dm_cv`

## Forbidden Outputs
- fake urgency not supported by input
- "salary guaranteed"
- fake client name
- discriminatory language
- policy-unsafe language like "spam all friends"
- too many emoji
- more than 5 requirement bullets
- hashtags by default
- English-only post

## Prompt Wrapper Template

```text
SYSTEM:
[Base system prompt above]

USER:
Generate one Hebrew Facebook job post.

Use:
- tone={{tone}}
- length_mode={{length_mode}}
- cta_mode={{cta_mode}}

Vacancy input:
{{json_input}}
```

## Style Add-Ons

### Professional Add-On

```text
Write in polished recruiter Hebrew.
Keep the structure clean and credible.
Prefer short paragraph blocks over slang.
```

### Casual Add-On

```text
Write in friendly everyday Hebrew.
Keep the post easy to scan and human.
Do not become childish or overly playful.
```

### Urgent Add-On

```text
Write in direct urgent Hebrew.
Open with immediate hiring energy.
Keep the message compact and action-driven.
```

## Example 1

### Input

```json
{
  "vacancy_title": "Senior Java Developer",
  "vacancy_body": "Backend role in a product team. Hybrid. Need strong Java and Spring Boot.",
  "city": "תל אביב",
  "salary_hint": "30-35K",
  "employment_type": "משרה מלאה",
  "requirements": ["5+ שנות ניסיון ב-Java", "Spring Boot", "Microservices"],
  "benefits": ["עבודה היברידית", "אופציות"],
  "cta_mode": "dm_cv",
  "tone": "professional",
  "length_mode": "medium",
  "allow_company_name": false,
  "company_name": null,
  "notes": ""
}
```

### Output

```json
{
  "headline": "מגייסים Senior Java Developer לתל אביב",
  "body": "לצוות מוצר איכותי בתל אביב דרוש/ה Senior Java Developer עם ניסיון חזק ב-Java, Spring Boot ו-Microservices. מדובר במשרה מלאה בסביבת עבודה היברידית, עם שכר של 30-35K ואופציות.",
  "cta": "לשליחת קורות חיים אפשר לפנות בפרטי.",
  "full_post": "מגייסים Senior Java Developer לתל אביב\n\nלצוות מוצר איכותי בתל אביב דרוש/ה Senior Java Developer עם ניסיון חזק ב-Java, Spring Boot ו-Microservices. מדובר במשרה מלאה בסביבת עבודה היברידית, עם שכר של 30-35K ואופציות.\n\nלשליחת קורות חיים אפשר לפנות בפרטי.",
  "character_count": 248,
  "warnings": []
}
```

## Example 2

### Input

```json
{
  "vacancy_title": "נציג/ת שירות לקוחות",
  "vacancy_body": "Immediate hire for customer support role in Haifa.",
  "city": "חיפה",
  "salary_hint": "שכר תחרותי",
  "employment_type": "משרה מלאה",
  "requirements": ["ניסיון בשירות", "זמינות מיידית", "יחסי אנוש מעולים"],
  "benefits": ["סביבת עבודה יציבה"],
  "cta_mode": "comment_interested",
  "tone": "urgent",
  "length_mode": "short",
  "allow_company_name": false,
  "company_name": null,
  "notes": ""
}
```

### Output

```json
{
  "headline": "גיוס מיידי בחיפה",
  "body": "מחפשים נציג/ת שירות לקוחות למשרה מלאה בחיפה. מתאים למי שיש ניסיון בשירות, זמינות מיידית ויחסי אנוש מעולים. שכר תחרותי וסביבת עבודה יציבה.",
  "cta": "מעוניינים? כתבו \"מעוניין/ת\" בתגובות ונחזור אליכם.",
  "full_post": "גיוס מיידי בחיפה\n\nמחפשים נציג/ת שירות לקוחות למשרה מלאה בחיפה. מתאים למי שיש ניסיון בשירות, זמינות מיידית ויחסי אנוש מעולים. שכר תחרותי וסביבת עבודה יציבה.\n\nמעוניינים? כתבו \"מעוניין/ת\" בתגובות ונחזור אליכם.",
  "character_count": 214,
  "warnings": []
}
```

## Implementation Notes
- Save `prompt_version` with every generated variant.
- Enforce hard character max in application layer before approval.
- If output exceeds mode target, auto-regenerate once with `shorten by 15%`.
- Let recruiter edit `full_post` before approval; store as `ai_then_edited` if changed.
