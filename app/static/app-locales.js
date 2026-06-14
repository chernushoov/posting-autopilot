/* ════════════════════════════════════════════════════════════════════════════
   Posting Autopilot — content locale packs (EN · HE overlays)
   RU is the inline source in app-data.js. applyLang(lang) overlays these.
   Structural fields (ids, numbers, classes, icons, who-sequence) stay in app-data.
   Chat is text-only here, zipped against the RU who-sequence at merge time.
   ════════════════════════════════════════════════════════════════════════════ */
window.PA_LOC = (function(){
"use strict";

var en={
 companies:[
  {name:'Dirot TLV',type:'Real estate · Pro'},
  {name:'Cafe Norm',type:'Hiring · Starter'},
  {name:'AutoDeal',type:'Auto · Pro'}
 ],
 leads:{
  1:{name:'Alex M.',ad:'Rental · Florentin',summary:'Looking for a 3-room in Florentin, budget up to ₪6,000, ready to move within 2 weeks. Left a phone number — high priority.',
     chat:['Hi! Looking for an apartment?','Yes, 3 rooms in Florentin','What’s your budget?','up to ₪6,000','I have 3 matches! Will you leave a phone number?','054-555-1234','Thanks! Passed it to the agent.']},
  2:{name:'Avital R.',ad:'Rental · Florentin',summary:'Couple without kids, budget ₪6,000, move-in from the 1st. Available for a viewing any day.',
     chat:['Hi! Looking for an apartment?','Yes, for two, move-in from the 1st','What’s the budget?','₪6,000. Phone 050-220-4417']},
  3:{name:'Dina K.',ad:'Rental · Florentin',summary:'Urgent request: moving in this week, two people, budget ₪5,500. Phone received.',
     chat:['Hi! Looking for an apartment?','Yes, can I move in this week?','Yes! What’s the budget and how many people?','₪5,500, two','052-880-7711']},
  4:{name:'Shira B.',ad:'Rental · Florentin',summary:'Student, looking long-term, budget ₪5,800. Asked about pets — a cat is fine.',
     chat:['Hi! Looking for an apartment?','Yes, for a year. Is a cat okay?','Yes, that’s fine. Budget?','up to ₪5,800. 054-771-9920']},
  5:{name:'Yossi B.',ad:'Rental · Florentin',summary:'Budget ₪6,200, parking matters. Ready to pay a deposit right after a viewing.',
     chat:['Hi! Looking for an apartment?','Yes, I need parking','We have options with parking. Budget?','up to ₪6,200. 053-660-1185']},
  6:{name:'Ronen G.',ad:'Job · Barista',summary:'3 years of coffee-shop experience, looking for full-time. Left a phone, waiting for a call.',
     chat:['Hi! The barista role is open. Any experience?','3 years','Would full-time work for you?','Yes. 052-339-7740']},
  7:{name:'Maya T.',ad:'Job · Barista',summary:'No experience but eager to learn, lives nearby. Left a phone number.',
     chat:['Hi! The barista role is open. Any experience?','No experience, but I learn fast, I live nearby','Great, leave a phone number','054-118-3302']},
  8:{name:'Lena G.',ad:'Job · Barista',summary:'2 years of experience, can start tomorrow. Didn’t specify schedule — needs a call.',
     chat:['Hi! The barista role is still open. Any experience?','Yes, 2 years','When can you start?','Tomorrow if needed. 053-401-2290']},
  9:{name:'Tom K.',ad:'Rental · Florentin',summary:'Interested, but budget below market (₪4,500). Hasn’t left a phone yet.',
     chat:['Hi! Looking for an apartment?','Yes, budget ₪4,500','That’s below current prices, but I’ll send whatever comes up.']},
  10:{name:'Igor P.',ad:'Rental · Florentin',summary:'Just browsing, didn’t give a budget, no phone. Low priority.',
     chat:['Hi! Looking for an apartment?','Just browsing for now','Once you settle on a budget — write to me, I’ll find options.']},
  11:{name:'Duplicate · Alex',ad:'Rental · Florentin',summary:'Repeat enquiry from the same user on another listing. Muted, merged with original #1.',
     chat:['It’s me again, about another apartment','Recognized you! Merged with your previous enquiry.']},
  12:{name:'Promo Bot',ad:'—',summary:'Promotional message, flagged as spam by the bot and hidden from the feed.',
     chat:['💰 ONLINE CASINO EARNINGS JOIN NOW','Message flagged as spam and hidden.']}
 },
 campaigns:[
  {name:'Rental · Florentin',ad:'3-room Florentin',channels:'TG · FB · 48 groups',statusLabel:'Active'},
  {name:'Job · Barista',ad:'Barista, center',channels:'TG · 30 groups',statusLabel:'Active'},
  {name:'Car sale · Mazda',ad:'Mazda 3, 2019',channels:'FB · 22 groups',statusLabel:'Paused'}
 ],
 attempts:[
  {group:'Rentals TLV · center',label:'Posted'},
  {group:'Apartments Florentin',label:'Posted'},
  {group:'Rent/Let TLV',label:'Manual action'},
  {group:'Rentals no agents',label:'Scheduled'},
  {group:'Housing south TLV',label:'Blocked'}
 ],
 queue:[
  {title:'Rent/Let TLV (Facebook)',sub:'Paste the ready text into the group and mark the result'},
  {title:'Housing center TLV (Facebook)',sub:'The group requires moderator approval'}
 ],
 ads:{
  a1:{title:'3-room for rent in Florentin',vertLabel:'Real estate',city:'Tel Aviv',price:'₪6,000/mo',preview:'Bright 3-room after renovation. Cafés and transit nearby. Budget up to ₪6,000. Message the bot.'},
  a2:{title:'Barista for a coffee shop (center)',vertLabel:'Job',city:'Tel Aviv',price:'₪45/hr',preview:'Looking for a full-time barista. Experience welcome, we train. Flexible schedule. Message the bot.'},
  a3:{title:'Mazda 3, 2019, 78,000 km',vertLabel:'Auto',city:'Tel Aviv',price:'₪72,000',preview:'One owner, service book, no accidents. Price negotiable in person. Message the bot — I’ll answer questions.'}
 },
 tg_groups:[
  {name:'Rentals TLV · center',folder:'Rentals'},
  {name:'Apartments Florentin',folder:'Rentals'},
  {name:'Rent/Let TLV',folder:'Rentals'},
  {name:'Rentals no agents',folder:'Rentals'},
  {name:'Jobs in Tel Aviv',folder:'Jobs'},
  {name:'Café & bar vacancies',folder:'Jobs'}
 ],
 fb_sources:[
  {name:'Apartment rentals Tel Aviv',mode:'Manual'},
  {name:'Florentin Apartments',mode:'Manual'}
 ],
 sources:[
  {name:'Rentals TLV · center',kind:'Group',mode:'Auto'},
  {name:'Apartments Florentin',kind:'Group',mode:'Auto'},
  {name:'Rent/Let TLV',kind:'Group',mode:'Auto'},
  {name:'Apartment rentals Tel Aviv',kind:'Group',mode:'Manual'},
  {name:'Florentin Apartments',kind:'Group',mode:'Manual'}
 ],
 funnel:[{label:'All replies'},{label:'Passed the bot'},{label:'Warm'},{label:'Hot'},{label:'Closed'}],
 onboard:[{t:'Company'},{t:'Listing'},{t:'Telegram'},{t:'Facebook'},{t:'Campaign'},{t:'First post'}],
 bot:{
  positive:'Named a budget, left a phone, ready for a viewing or to start work within a week, answers to the point.',
  negative:'Asks only about price without interest, refuses to leave contact, rude, spam, budget far below market.',
  greet:'Hi! Glad it caught your eye 🙂 I’ll ask a couple of quick questions to find the best option.',
  reject:'Thanks for your interest! There’s nothing matching your request right now — I’ll write as soon as something comes up.',
  success:'Great, I’ve passed your contact to the agent — they’ll reach out within an hour. Have a good day!'
 },
 bot_demo:[
  {kw:['budget','6000','5000','phone','054','050','052','053'],a:'Thanks! I’ve passed your contact to the agent — they’ll reach out within an hour. 🔥'},
  {kw:['browsing','prices','just','looking'],a:'Got it! Once you settle on a budget — write to me, I’ll find options.'},
  {kw:['3-room','apartment','rental','job','vacancy','experience'],a:'Great choice! Tell me your budget and preferred area — and leave a number so the agent can reach you.'}
 ],
 bot_default:'Hi! To find an option, tell me the budget, area and leave a phone number.',
 fill_hot:'Looking for a 3-room, budget ₪6,000, phone 054-555-1234',
 fill_cold:'Just browsing prices',
 analytics:{
  kpi:[{label:'Posts',sub:'+12 this week'},{label:'Handled by bot',sub:'81% spam filtered'},{label:'Hot leads',sub:'+3 this week'},{label:'Deals closed',sub:'1.9% conversion'}],
  funnel:[{label:'All replies'},{label:'Passed the bot'},{label:'Warm'},{label:'Hot'},{label:'Closed'}],
  langs:[{label:'Russian'},{label:'Hebrew'},{label:'English'}],
  days:[{d:'Mon'},{d:'Tue'},{d:'Wed'},{d:'Thu'},{d:'Fri'},{d:'Sat'},{d:'Sun'}],
  ops:[{label:'Posts published'},{label:'Manual FB confirmations'},{label:'Blocked by groups'},{label:'Avg. bot reply time'}],
  ads:[{title:'Rental · Florentin'},{title:'Barista · center'},{title:'Mazda 3, 2019'}]
 },
 team:[
  {name:'Dmitry V.',role:'Owner'},
  {name:'Anna K.',role:'Operator'},
  {name:'Mikhail R.',role:'Operator'}
 ],
 plans:[
  {tagline:'One listing, manual posting',feats:['1 active listing','10 posting channels','AI screening bot','Leads and basic dashboard']},
  {tagline:'Active multi-channel posting',feats:['5 active listings','50 posting channels','Scheduler and night mode','Analytics and funnel','Priority support']},
  {tagline:'Agencies and multiple companies',feats:['Unlimited listings','Multi-company','API and webhooks','White-label cabinet','Dedicated manager']}
 ],
 cp:{
  leads:{summary:'7 hot leads are waiting for a reply. Avital R. and Alex M. left phone numbers — call them first while contact is warm.',
    facts:[{label:'Hot',val:'7'},{label:'With phone',val:'6'},{label:'Spam filtered',val:'173'}],warn:[],action:{label:'Open the first'}},
  dashboard:{summary:'Setup is almost done: 3 of 6 steps. Connect Facebook and launch the first campaign — and posting goes automatic.',
    facts:[{label:'Listing',val:'yes'},{label:'Telegram',val:'ready'},{label:'Facebook',val:'no'}],warn:[{text:'Facebook isn’t connected — half the channels are unavailable.'}],action:{label:'Connect Facebook'}},
  campaigns:{summary:'2 campaigns active. There are 2 manual Facebook actions — do them so the posts reach the FB groups.',
    facts:[{label:'Active',val:'2'},{label:'Manual',val:'2'},{label:'Night mode',val:'23:00'}],warn:[{text:'Night mode: auto-posting paused 23:00–07:00.'}],action:{label:'Go to the action queue'}},
  ads:{summary:'2 of 5 listings active on the Pro plan. “Rental · Florentin” brings the most hot leads — keep it at the top of campaigns.',
    facts:[{label:'Active',val:'2'},{label:'Leads from them',val:'9'},{label:'Pro limit',val:'3 / 5'}],warn:[],action:{label:'Create a listing'}},
  'channel-tg':{summary:'Telegram is connected, 64 groups synced, 48 selected for posting. You can add more — the Pro limit of 50 channels is nearly reached.',
    facts:[{label:'Connected',val:'yes'},{label:'Groups selected',val:'48'},{label:'Pro limit',val:'48 / 50'}],warn:[],action:{label:'Go to destinations'}},
  'channel-fb':{summary:'Facebook isn’t connected yet. Connect via OAuth or paste group links — and the second half of channels becomes available.',
    facts:[{label:'Connected',val:'no'},{label:'FB groups',val:'0'}],warn:[{text:'Without Facebook only half the reach is available.'}],action:{label:'Connect Facebook'}},
  sources:{summary:'70 destinations total: 48 Telegram ready for auto, 22 Facebook in manual mode. 3 need a check — refresh them before the next campaign.',
    facts:[{label:'TG ready',val:'48'},{label:'FB manual',val:'22'},{label:'To check',val:'3'}],warn:[],action:{label:'Check all'}},
  bot:{summary:'The bot is set to a friendly tone, replies in ~8 seconds, around the clock. Check the “hot” criteria — they decide who you see first.',
    facts:[{label:'Tone',val:'Friendly'},{label:'Reply',val:'8s'},{label:'Language',val:'Auto'}],warn:[],action:{label:'Test the bot'}},
  analytics:{summary:'214 enquiries and 11 hot leads this week. “Rental · Florentin” leads — 4.2% conversion. The Mazda listing barely produces leads — refresh or remove it.',
    facts:[{label:'Posts',val:'52'},{label:'Hot',val:'11'},{label:'Closed',val:'4'}],warn:[],action:{label:'Go to listings'}},
  company:{summary:'Set where to send hot leads so you don’t miss contact. Telegram is set, the backup email isn’t. The team has 2 active operators.',
    facts:[{label:'TG for leads',val:'set'},{label:'Email',val:'no'},{label:'Team',val:'2'}],warn:[{text:'Email for hot leads isn’t set — the backup channel is off.'}],action:{label:'Add a member'}},
  billing:{summary:'A Pro trial is running — 11 days left. When it ends, posting pauses. Switch to a paid plan ahead of time so you don’t lose reach.',
    facts:[{label:'Plan',val:'Pro · trial'},{label:'Left',val:'11 days'}],warn:[{text:'The trial expires in 11 days — then auto-posting pauses.'}],action:{label:'Switch to Pro'}}
 }
};

var he={
 companies:[
  {name:'Dirot TLV',type:'נדל״ן · Pro'},
  {name:'Cafe Norm',type:'גיוס · Starter'},
  {name:'AutoDeal',type:'רכב · Pro'}
 ],
 leads:{
  1:{name:'אלכס מ.',ad:'השכרה · פלורנטין',summary:'מחפש דירת 3 חדרים בפלורנטין, תקציב עד ₪6,000, מוכן להיכנס תוך שבועיים. השאיר טלפון — עדיפות גבוהה.',
     chat:['היי! מחפש דירה?','כן, 3 חדרים בפלורנטין','מה התקציב שלך?','עד ₪6,000','יש לי 3 התאמות! תשאיר מספר טלפון?','054-555-1234','תודה! העברתי לסוכן.']},
  2:{name:'אביטל ר.',ad:'השכרה · פלורנטין',summary:'זוג בלי ילדים, תקציב ₪6,000, כניסה מ‑1 לחודש. זמינה לצפייה בכל יום.',
     chat:['היי! מחפשת דירה?','כן, לשניים, כניסה מ‑1','מה התקציב?','₪6,000. טלפון 050-220-4417']},
  3:{name:'דינה ק.',ad:'השכרה · פלורנטין',summary:'בקשה דחופה: נכנסת השבוע, שניים, תקציב ₪5,500. התקבל טלפון.',
     chat:['היי! מחפשת דירה?','כן, אפשר להיכנס השבוע?','כן! מה התקציב וכמה אנשים?','₪5,500, שניים','052-880-7711']},
  4:{name:'שירה ב.',ad:'השכרה · פלורנטין',summary:'סטודנטית, מחפשת לטווח ארוך, תקציב ₪5,800. שאלה על חיות — חתול בסדר.',
     chat:['היי! מחפשת דירה?','כן, לשנה. אפשר עם חתול?','כן, בסדר. תקציב?','עד ₪5,800. 054-771-9920']},
  5:{name:'יוסי ב.',ad:'השכרה · פלורנטין',summary:'תקציב ₪6,200, חשובה חניה. מוכן לשלם פיקדון מיד אחרי צפייה.',
     chat:['היי! מחפש דירה?','כן, צריך חניה','יש אפשרויות עם חניה. תקציב?','עד ₪6,200. 053-660-1185']},
  6:{name:'רונן ג.',ad:'דרושים · ברמן קפה',summary:'3 שנות ניסיון בבית קפה, מחפש משרה מלאה. השאיר טלפון, מחכה לשיחה.',
     chat:['היי! משרת בריסטה פתוחה. יש ניסיון?','3 שנים','משרה מלאה מתאימה?','כן. 052-339-7740']},
  7:{name:'מאיה ת.',ad:'דרושים · ברמן קפה',summary:'בלי ניסיון אבל רוצה ללמוד, גרה קרוב. השאירה טלפון.',
     chat:['היי! משרת בריסטה פתוחה. יש ניסיון?','אין ניסיון, אבל לומדת מהר, גרה קרוב','מצוין, תשאירי טלפון','054-118-3302']},
  8:{name:'לנה ג.',ad:'דרושים · ברמן קפה',summary:'2 שנות ניסיון, יכולה להתחיל מחר. לא ציינה משמרת — צריך לחזור אליה.',
     chat:['היי! משרת בריסטה עדיין פתוחה. יש ניסיון?','כן, שנתיים','מתי אפשר להתחיל?','אפילו מחר. 053-401-2290']},
  9:{name:'תום ק.',ad:'השכרה · פלורנטין',summary:'מתעניין, אבל התקציב מתחת לשוק (₪4,500). עדיין לא השאיר טלפון.',
     chat:['היי! מחפש דירה?','כן, תקציב ₪4,500','זה מתחת למחירים הנוכחיים, אבל אשלח מה שיתפנה.']},
  10:{name:'איגור פ.',ad:'השכרה · פלורנטין',summary:'רק מסתכל, לא נקב תקציב, בלי טלפון. עדיפות נמוכה.',
     chat:['היי! מחפש דירה?','בינתיים רק מסתכל','כשתחליט על תקציב — תכתוב לי, אמצא אפשרויות.']},
  11:{name:'כפילות · אלכס',ad:'השכרה · פלורנטין',summary:'פנייה חוזרת מאותו משתמש על מודעה אחרת. הושתקה, אוחדה עם המקור #1.',
     chat:['זה שוב אני, על דירה אחרת','זיהיתי אותך! אוחד עם הפנייה הקודמת.']},
  12:{name:'Promo Bot',ad:'—',summary:'הודעה פרסומית, סומנה כספאם ע״י הבוט והוסתרה מהפיד.',
     chat:['💰 רווחים בקזינו אונליין הצטרפו עכשיו','ההודעה סומנה כספאם והוסתרה.']}
 },
 campaigns:[
  {name:'השכרה · פלורנטין',ad:'3 חדרים פלורנטין',channels:'TG · FB · 48 קבוצות',statusLabel:'פעיל'},
  {name:'דרושים · ברמן קפה',ad:'בריסטה, מרכז',channels:'TG · 30 קבוצות',statusLabel:'פעיל'},
  {name:'מכירת רכב · Mazda',ad:'Mazda 3, 2019',channels:'FB · 22 קבוצות',statusLabel:'מושהה'}
 ],
 attempts:[
  {group:'השכרות ת״א · מרכז',label:'פורסם'},
  {group:'דירות פלורנטין',label:'פורסם'},
  {group:'להשכיר/לשכור ת״א',label:'פעולה ידנית'},
  {group:'השכרות בלי תיווך',label:'מתוזמן'},
  {group:'דיור דרום ת״א',label:'נחסם'}
 ],
 queue:[
  {title:'להשכיר/לשכור ת״א (Facebook)',sub:'הדביקו את הטקסט המוכן בקבוצה וסמנו תוצאה'},
  {title:'דיור מרכז ת״א (Facebook)',sub:'הקבוצה דורשת אישור מנהל'}
 ],
 ads:{
  a1:{title:'דירת 3 חדרים להשכרה בפלורנטין',vertLabel:'נדל״ן',city:'תל אביב',price:'₪6,000/חודש',preview:'דירת 3 חדרים מוארת אחרי שיפוץ. בתי קפה ותחבורה בקרבת מקום. תקציב עד ₪6,000. כתבו לבוט.'},
  a2:{title:'בריסטה לבית קפה (מרכז)',vertLabel:'דרושים',city:'תל אביב',price:'₪45/שעה',preview:'מחפשים בריסטה למשרה מלאה. ניסיון יתרון, מכשירים. משמרות גמישות. כתבו לבוט.'},
  a3:{title:'Mazda 3, 2019, 78,000 ק״מ',vertLabel:'רכב',city:'תל אביב',price:'₪72,000',preview:'יד ראשונה, ספר שירות, ללא תאונות. מחיר גמיש על הרכב. כתבו לבוט — אענה על שאלות.'}
 },
 tg_groups:[
  {name:'השכרות ת״א · מרכז',folder:'השכרה'},
  {name:'דירות פלורנטין',folder:'השכרה'},
  {name:'להשכיר/לשכור ת״א',folder:'השכרה'},
  {name:'השכרות בלי תיווך',folder:'השכרה'},
  {name:'עבודה בתל אביב',folder:'עבודה'},
  {name:'דרושים בתי קפה וברים',folder:'עבודה'}
 ],
 fb_sources:[
  {name:'השכרת דירות תל אביב',mode:'ידני'},
  {name:'Florentin Apartments',mode:'ידני'}
 ],
 sources:[
  {name:'השכרות ת״א · מרכז',kind:'קבוצה',mode:'אוטומטי'},
  {name:'דירות פלורנטין',kind:'קבוצה',mode:'אוטומטי'},
  {name:'להשכיר/לשכור ת״א',kind:'קבוצה',mode:'אוטומטי'},
  {name:'השכרת דירות תל אביב',kind:'קבוצה',mode:'ידני'},
  {name:'Florentin Apartments',kind:'קבוצה',mode:'ידני'}
 ],
 funnel:[{label:'כל התגובות'},{label:'עברו את הבוט'},{label:'פושרים'},{label:'חמים'},{label:'נסגרו'}],
 onboard:[{t:'חברה'},{t:'מודעה'},{t:'Telegram'},{t:'Facebook'},{t:'קמפיין'},{t:'פרסום ראשון'}],
 bot:{
  positive:'נקב תקציב, השאיר טלפון, מוכן לצפייה או לתחילת עבודה תוך שבוע, עונה לעניין.',
  negative:'שואל רק על מחיר בלי עניין, מסרב להשאיר קשר, גס רוח, ספאם, תקציב הרבה מתחת לשוק.',
  greet:'היי! שמח שזה עניין אותך 🙂 אשאל כמה שאלות קצרות כדי למצוא את האפשרות הטובה ביותר.',
  reject:'תודה על העניין! כרגע אין משהו שמתאים לבקשה — אכתוב ברגע שיתפנה.',
  success:'מצוין, העברתי את הפרטים שלך לסוכן — הוא יחזור אליך תוך שעה. שיהיה יום טוב!'
 },
 bot_demo:[
  {kw:['תקציב','6000','5000','טלפון','054','050','052','053'],a:'תודה! העברתי את הפרטים שלך לסוכן — הוא יחזור אליך תוך שעה. 🔥'},
  {kw:['מסתכל','מחירים','רק','מתעניין'],a:'הבנתי! כשתחליט על תקציב — תכתוב לי, אמצא אפשרויות.'},
  {kw:['חדרים','דירה','השכרה','עבודה','דרושים','ניסיון'],a:'בחירה מצוינת! ספר לי על התקציב והאזור המועדף — והשאר מספר כדי שהסוכן יחזור אליך.'}
 ],
 bot_default:'היי! כדי למצוא אפשרות, ספר לי את התקציב, האזור והשאר מספר טלפון.',
 fill_hot:'מחפש 3 חדרים, תקציב ₪6,000, טלפון 054-555-1234',
 fill_cold:'רק מסתכל על מחירים',
 analytics:{
  kpi:[{label:'פרסומים',sub:'+12 השבוע'},{label:'טופלו ע״י הבוט',sub:'81% ספאם סוננו'},{label:'לידים חמים',sub:'+3 השבוע'},{label:'עסקאות נסגרו',sub:'1.9% המרה'}],
  funnel:[{label:'כל התגובות'},{label:'עברו את הבוט'},{label:'פושרים'},{label:'חמים'},{label:'נסגרו'}],
  langs:[{label:'רוסית'},{label:'עברית'},{label:'אנגלית'}],
  days:[{d:'ב׳'},{d:'ג׳'},{d:'ד׳'},{d:'ה׳'},{d:'ו׳'},{d:'ש׳'},{d:'א׳'}],
  ops:[{label:'פוסטים פורסמו'},{label:'אישורי FB ידניים'},{label:'נחסמו ע״י קבוצות'},{label:'זמן תגובה ממוצע'}],
  ads:[{title:'השכרה · פלורנטין'},{title:'בריסטה · מרכז'},{title:'Mazda 3, 2019'}]
 },
 team:[
  {name:'דמיטרי ו.',role:'בעלים'},
  {name:'אנה ק.',role:'מפעיל'},
  {name:'מיכאל ר.',role:'מפעיל'}
 ],
 plans:[
  {tagline:'מודעה אחת, פרסום ידני',feats:['מודעה פעילה אחת','10 ערוצי פרסום','בוט סינון AI','לידים ולוח בקרה בסיסי']},
  {tagline:'פרסום רב‑ערוצי פעיל',feats:['5 מודעות פעילות','50 ערוצי פרסום','מתזמן ומצב לילה','אנליטיקה ומשפך','תמיכה מועדפת']},
  {tagline:'סוכנויות ומספר חברות',feats:['מודעות ללא הגבלה','ריבוי חברות','API ו‑webhooks','קבינט White-label','מנהל אישי']}
 ],
 cp:{
  leads:{summary:'7 לידים חמים מחכים לתגובה. אביטל ר. ואלכס מ. השאירו טלפון — התקשרו אליהם ראשונים כל עוד הקשר טרי.',
    facts:[{label:'חמים',val:'7'},{label:'עם טלפון',val:'6'},{label:'ספאם סונן',val:'173'}],warn:[],action:{label:'פתיחת הראשון'}},
  dashboard:{summary:'ההגדרה כמעט מוכנה: 3 מתוך 6 שלבים. חברו את Facebook והפעילו קמפיין ראשון — והפרסום יהפוך לאוטומטי.',
    facts:[{label:'מודעה',val:'יש'},{label:'Telegram',val:'מוכן'},{label:'Facebook',val:'אין'}],warn:[{text:'Facebook לא מחובר — חצי מהערוצים אינם זמינים.'}],action:{label:'חיבור Facebook'}},
  campaigns:{summary:'2 קמפיינים פעילים. יש 2 פעולות Facebook ידניות — בצעו אותן כדי שהפוסטים יגיעו לקבוצות FB.',
    facts:[{label:'פעילים',val:'2'},{label:'ידניות',val:'2'},{label:'מצב לילה',val:'23:00'}],warn:[{text:'מצב לילה: פרסום אוטומטי מושהה 23:00–07:00.'}],action:{label:'לתור הפעולות'}},
  ads:{summary:'2 מתוך 5 מודעות פעילות במסלול Pro. „השכרה · פלורנטין” מביאה הכי הרבה לידים חמים — שמרו אותה בראש הקמפיינים.',
    facts:[{label:'פעילות',val:'2'},{label:'לידים מהן',val:'9'},{label:'מכסת Pro',val:'3 / 5'}],warn:[],action:{label:'יצירת מודעה'}},
  'channel-tg':{summary:'Telegram מחובר, 64 קבוצות סונכרנו, 48 נבחרו לפרסום. אפשר להוסיף עוד — מכסת Pro של 50 ערוצים כמעט מלאה.',
    facts:[{label:'מחובר',val:'כן'},{label:'קבוצות שנבחרו',val:'48'},{label:'מכסת Pro',val:'48 / 50'}],warn:[],action:{label:'ליעדים'}},
  'channel-fb':{summary:'Facebook עדיין לא מחובר. חברו דרך OAuth או הדביקו קישורי קבוצות — והחצי השני של הערוצים ייפתח.',
    facts:[{label:'מחובר',val:'אין'},{label:'קבוצות FB',val:'0'}],warn:[{text:'בלי Facebook זמין רק חצי מהטווח.'}],action:{label:'חיבור Facebook'}},
  sources:{summary:'70 יעדים בסך הכול: 48 Telegram מוכנים לאוטו, 22 Facebook במצב ידני. 3 דורשים בדיקה — רעננו אותם לפני הקמפיין הבא.',
    facts:[{label:'TG מוכנים',val:'48'},{label:'FB ידניים',val:'22'},{label:'לבדיקה',val:'3'}],warn:[],action:{label:'בדיקת הכול'}},
  bot:{summary:'הבוט מוגדר בטון ידידותי, עונה תוך כ‑8 שניות, מסביב לשעון. בדקו את קריטריוני „החם” — הם קובעים את מי תראו ראשון.',
    facts:[{label:'טון',val:'ידידותי'},{label:'תגובה',val:'8 שנ׳'},{label:'שפה',val:'אוטו'}],warn:[],action:{label:'בדיקת הבוט'}},
  analytics:{summary:'השבוע 214 פניות ו‑11 לידים חמים. „השכרה · פלורנטין” מובילה — המרה 4.2%. המודעה על Mazda כמעט לא מביאה לידים — רעננו או הסירו.',
    facts:[{label:'פרסומים',val:'52'},{label:'חמים',val:'11'},{label:'נסגרו',val:'4'}],warn:[],action:{label:'למודעות'}},
  company:{summary:'הגדירו לאן לשלוח לידים חמים כדי לא לפספס קשר. Telegram הוגדר, אימייל גיבוי לא. בצוות 2 מפעילים פעילים.',
    facts:[{label:'TG ללידים',val:'הוגדר'},{label:'Email',val:'אין'},{label:'צוות',val:'2'}],warn:[{text:'אימייל ללידים חמים לא הוגדר — ערוץ הגיבוי כבוי.'}],action:{label:'הוספת חבר'}},
  billing:{summary:'תקופת ניסיון Pro פעילה — נותרו 11 ימים. בסיומה הפרסום יושהה. עברו למסלול בתשלום מראש כדי לא לאבד טווח.',
    facts:[{label:'מסלול',val:'Pro · ניסיון'},{label:'נותרו',val:'11 ימים'}],warn:[{text:'הניסיון מסתיים בעוד 11 ימים — ואז הפרסום האוטומטי מושהה.'}],action:{label:'מעבר ל‑Pro'}}
 }
};

return { en:en, he:he };
})();
