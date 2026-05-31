# FB window redesign — groups + Marketplace, category-synced
# Self-prompt. Goal (owner): make the Facebook section clear, simple, "works great",
# with everything organized BY CATEGORY, and Marketplace synced to FB categories.

## CORE CONCEPT: categories unify everything
Categories = the "folders" the owner asked for. Map to his niches + FB Marketplace:
  - jobs        (Работа / משרות)        → FB Marketplace "Jobs"
  - vehicles    (Авто / רכב)            → FB Marketplace "Vehicles"
  - property    (Недвижимость / דירות)  → FB Marketplace "Property Rentals/Sales"
  - general     (Объявления / общее)    → FB Marketplace "Classifieds/Misc"

A GROUP has a category (inferred from its name). MARKETPLACE posts to a FB category.
When the owner posts an ad: pick category → system auto-targets matching groups +
the right Marketplace category. One simple flow.

## CURRENT STATE (analysis)
- ✅ Browser session + 263 groups imported + listed on FB page.
- ✅ Real group posting works end-to-end (published a live vacancy).
- ⚠️ Many group names are "FB Group <id>" placeholders (scraper missed names).
- ⚠️ No member counts → can't sort by members.
- ⚠️ No category on groups → no folders/filtering.
- ⚠️ Marketplace = just saved bookmark URLs, not category-based.
- ⚠️ FB page has leftover "Facebook not connected" red banners (OAuth-token check) + messy panels.

## PLAN (do in order, commit per step, screenshot-verify each UI step)
- [ ] S1 SCRAPER v2: re-read groups capturing REAL name + member count; infer category
      from name keywords. Update the 263 FacebookGroup rows (name, member_count_estimate,
      primary_category). File: scripts/fb_list_groups.py (+ a re-import that UPDATES).
- [ ] S2 GROUPS UI: clean list — Name | Members | Category — with:
        · category filter tabs (Все / Работа / Авто / Недвижимость / Общее) = folders
        · sort by members (desc) / name
        · search box
      File: app/templates/connect_facebook.html + route passes richer fb_groups_list.
- [ ] S3 MARKETPLACE UI: list FB Marketplace categories as post targets (Vehicles/
      Property/Jobs/Classifieds), each maps to the FB Marketplace compose for that category.
- [ ] S4 CLEANUP: remove the leftover "Facebook not connected" red banners + collapse the
      old confusing panels so the page reads: status → groups (by category) → marketplace.
- [ ] S5 (later) POST FLOW: pick ad → category → auto-select matching groups + marketplace
      category → post with anti-ban pacing.

## CATEGORY INFERENCE (keywords, RU/HE/EN)
- jobs:     работа|вакансия|דרוש|משרה|job|work|требу|трудоустр
- vehicles: авто|машин|רכב|car|vehicle|транспорт|מכונית
- property: квартир|аренда|דירה|נדל|property|rent|жиль|сдам|сниму
- general:  (default)

## VERIFY
After S1: query shows real names + members + category populated (spot-check 10).
After S2/S3/S4: restart server, screenshot FB page, eyes-on before telling owner.
