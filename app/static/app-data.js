/* ════════════════════════════════════════════════════════════════════════════
   Posting Autopilot — Cabinet DATA + icon system (mock, no backend)
   ════════════════════════════════════════════════════════════════════════════ */
window.PA = (function(){
"use strict";

/* ── Icons (Lucide-style line set) ───────────────────────────────────────── */
var ICONS={
 send:'<path d="M22 2 11 13"/><path d="M22 2 15 22l-4-9-9-4z"/>',
 chevron:'<path d="m6 9 6 6 6-6"/>',
 flame:'<path d="M8.5 14.5A2.5 2.5 0 0 0 11 12c0-1.4-.5-2-1-3-1.1-2.1-.2-4 2-6 .5 2.5 2 4.9 4 6.5 2 1.6 3 3.5 3 5.5a7 7 0 1 1-14 0c0-1.2.4-2.3 1-3a2.5 2.5 0 0 0 2.5 2.5z"/>',
 grid:'<rect x="3" y="3" width="7" height="7" rx="1.5"/><rect x="14" y="3" width="7" height="7" rx="1.5"/><rect x="14" y="14" width="7" height="7" rx="1.5"/><rect x="3" y="14" width="7" height="7" rx="1.5"/>',
 rocket:'<path d="M4.5 16.5c-1.5 1.3-2 5-2 5s3.7-.5 5-2c.7-.8.7-2.1-.1-2.9a2.1 2.1 0 0 0-2.9-.1z"/><path d="M12 15l-3-3a22 22 0 0 1 2-3.9A12.9 12.9 0 0 1 22 2c0 2.7-.8 7.5-6 11a22 22 0 0 1-4 2z"/><path d="M9 12H4s.6-3 2-4c1.6-1.1 5 0 5 0"/><path d="M12 15v5s3-.6 4-2c1.1-1.6 0-5 0-5"/>',
 doc:'<path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><path d="M14 2v6h6"/><path d="M8 13h8M8 17h8M8 9h2"/>',
 fb:'<path d="M18 2h-3a5 5 0 0 0-5 5v3H7v4h3v8h4v-8h3l1-4h-4V7a1 1 0 0 1 1-1h3z"/>',
 target:'<circle cx="12" cy="12" r="9"/><circle cx="12" cy="12" r="5"/><circle cx="12" cy="12" r="1.4" fill="currentColor"/>',
 bot:'<rect x="4" y="9" width="16" height="11" rx="2.5"/><path d="M12 5.5V9"/><circle cx="12" cy="4" r="1.5"/><circle cx="9" cy="14" r="1.1"/><circle cx="15" cy="14" r="1.1"/>',
 chart:'<path d="M3 3v18h18"/><path d="M7 14l3-3 3 2 5-5"/>',
 users:'<path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M22 21v-2a4 4 0 0 0-3-3.9"/><path d="M16 3.1a4 4 0 0 1 0 7.8"/>',
 card:'<rect x="2" y="5" width="20" height="14" rx="2.5"/><path d="M2 10h20"/>',
 clock:'<circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/>',
 logout:'<path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/><path d="M16 17l5-5-5-5"/><path d="M21 12H9"/>',
 menu:'<path d="M3 6h18M3 12h18M3 18h18"/>',
 plus:'<path d="M12 5v14"/><path d="M5 12h14"/>',
 check:'<circle cx="12" cy="12" r="9"/><path d="m8 12 3 3 5-6"/>',
 checkbare:'<path d="m5 12 5 5L20 7"/>',
 phone:'<path d="M22 16.9v3a2 2 0 0 1-2.2 2 19.8 19.8 0 0 1-8.6-3.1 19.5 19.5 0 0 1-6-6A19.8 19.8 0 0 1 2.1 4.2 2 2 0 0 1 4.1 2h3a2 2 0 0 1 2 1.7c.1 1 .4 1.9.7 2.8a2 2 0 0 1-.5 2.1L8.1 9.9a16 16 0 0 0 6 6l1.3-1.3a2 2 0 0 1 2.1-.4c.9.3 1.8.6 2.8.7a2 2 0 0 1 1.7 2z"/>',
 bell:'<path d="M6 8a6 6 0 0 1 12 0c0 7 3 9 3 9H3s3-2 3-9"/><path d="M10.3 21a1.9 1.9 0 0 0 3.4 0"/>',
 spark:'<path d="M12 3v4M12 17v4M3 12h4M17 12h4M6 6l2.5 2.5M15.5 15.5 18 18M18 6l-2.5 2.5M8.5 15.5 6 18"/>',
 sparkles:'<path d="M12 3l1.8 4.8L18.5 9.6 13.8 11.4 12 16.2l-1.8-4.8L5.5 9.6l4.7-1.8z"/><path d="M19 14l.8 2.2L22 17l-2.2.8L19 20l-.8-2.2L16 17l2.2-.8z"/>',
 moon:'<path d="M21 12.8A9 9 0 1 1 11.2 3 7 7 0 0 0 21 12.8z"/>',
 alert:'<path d="M10.3 3.9 1.8 18a2 2 0 0 0 1.7 3h17a2 2 0 0 0 1.7-3L13.7 3.9a2 2 0 0 0-3.4 0z"/><path d="M12 9v4M12 17h.01"/>',
 download:'<path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><path d="M7 10l5 5 5-5"/><path d="M12 15V3"/>',
 link:'<path d="M10 13a5 5 0 0 0 7 0l3-3a5 5 0 0 0-7-7l-1.5 1.5"/><path d="M14 11a5 5 0 0 0-7 0l-3 3a5 5 0 0 0 7 7l1.5-1.5"/>',
 building:'<rect x="4" y="2" width="16" height="20" rx="2"/><path d="M9 7h.01M15 7h.01M9 11h.01M15 11h.01M9 15h.01M15 15h.01"/>',
 home:'<path d="M3 10.5 12 3l9 7.5"/><path d="M5 9v11h14V9"/>',
 car:'<path d="M5 13l1.5-4.5A2 2 0 0 1 8.4 7h7.2a2 2 0 0 1 1.9 1.5L19 13"/><path d="M4 13h16v5H4z"/><circle cx="8" cy="18" r="1.6"/><circle cx="16" cy="18" r="1.6"/>',
 wrench:'<path d="M14.7 6.3a4 4 0 0 0-5.4 5.4L3 18l3 3 6.3-6.3a4 4 0 0 0 5.4-5.4l-2.1 2.1-2.3-.6-.6-2.3z"/>',
 mail:'<rect x="2" y="4" width="20" height="16" rx="2.5"/><path d="m3 6 9 7 9-7"/>',
 pause:'<rect x="7" y="5" width="3.5" height="14" rx="1"/><rect x="13.5" y="5" width="3.5" height="14" rx="1"/>',
 play:'<path d="M7 4.5l12 7.5-12 7.5z"/>',
 refresh:'<path d="M3 12a9 9 0 0 1 15-6.7L21 8"/><path d="M21 3v5h-5"/><path d="M21 12a9 9 0 0 1-15 6.7L3 16"/><path d="M3 21v-5h5"/>',
 edit:'<path d="M12 20h9"/><path d="M16.5 3.5a2.1 2.1 0 0 1 3 3L7 19l-4 1 1-4z"/>',
 eye:'<path d="M2 12s4-7 10-7 10 7 10 7-4 7-10 7-10-7-10-7z"/><circle cx="12" cy="12" r="3"/>',
 x:'<path d="M18 6 6 18M6 6l12 12"/>',
 lock:'<rect x="4" y="11" width="16" height="9" rx="2"/><path d="M8 11V8a4 4 0 0 1 8 0v3"/>',
 zap:'<path d="M13 2 3 14h9l-1 8 10-12h-9z"/>'
};
function svg(n,cls){return ICONS[n]?'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">'+ICONS[n]+'</svg>':'';}
function injectIcons(root){
  (root||document).querySelectorAll('[data-i]').forEach(function(e){e.innerHTML=svg(e.getAttribute('data-i'));});
  (root||document).querySelectorAll('[data-ic]').forEach(function(e){e.innerHTML=svg(e.getAttribute('data-ic'));});
}

/* ── Companies ───────────────────────────────────────────────────────────── */
var COMPANIES=[
  {id:'dirot',name:'Dirot TLV',type:'Недвижимость · Pro',logo:'Д',active:true},
  {id:'cafe',name:'Cafe Norm',type:'Наём · Starter',logo:'C'},
  {id:'auto',name:'AutoDeal',type:'Авто · Pro',logo:'A'}
];

/* ── Leads ───────────────────────────────────────────────────────────────── */
var LEADS=[
 {id:1,name:'Алекс М.',user:'@alex_m',cls:'hot',score:92,status:'got_responses',phone:'054-555-1234',ad:'Аренда · Флорентин',
  summary:'Ищет 3-комнатную во Флорентине, бюджет до 6000₪, готов заехать в течение 2 недель. Оставил телефон — высокий приоритет.',
  chat:[['bot','Здравствуйте! Ищете квартиру?'],['lead','Да, 3 комнаты во Флорентине'],['bot','Какой у вас бюджет?'],['lead','до 6000₪'],['bot','Есть 3 подходящих! Оставите номер телефона?'],['lead','054-555-1234'],['bot','Спасибо! Передал агенту.']]},
 {id:2,name:'Авиталь Р.',user:'@avital_r',cls:'hot',score:90,status:'got_responses',phone:'050-220-4417',ad:'Аренда · Флорентин',
  summary:'Пара без детей, бюджет 6000₪, заезд с 1-го числа. Готова на просмотр в любой день.',
  chat:[['bot','Здравствуйте! Ищете квартиру?'],['lead','Да, для двоих, заезд с 1-го'],['bot','Какой бюджет?'],['lead','6000₪. Телефон 050-220-4417']]},
 {id:3,name:'Дина К.',user:'@dina_k',cls:'hot',score:88,status:'got_responses',phone:'052-880-7711',ad:'Аренда · Флорентин',
  summary:'Срочный запрос: заедет на этой неделе, двое, бюджет 5500₪. Телефон получен.',
  chat:[['bot','Здравствуйте! Ищете квартиру?'],['lead','Да, можно заехать на этой неделе?'],['bot','Да! Какой бюджет и сколько человек?'],['lead','5500₪, двое'],['lead','052-880-7711']]},
 {id:4,name:'Шира Б.',user:'@shira_b',cls:'hot',score:86,status:'got_responses',phone:'054-771-9920',ad:'Аренда · Флорентин',
  summary:'Студентка, ищет на длительный срок, бюджет 5800₪. Уточнила про питомцев — можно с котом.',
  chat:[['bot','Здравствуйте! Ищете квартиру?'],['lead','Да, на год. Можно с котом?'],['bot','Да, можно. Бюджет?'],['lead','до 5800₪. 054-771-9920']]},
 {id:5,name:'Йоси Б.',user:'@yossi_b',cls:'hot',score:84,status:'got_responses',phone:'053-660-1185',ad:'Аренда · Флорентин',
  summary:'Бюджет 6200₪, важна парковка. Готов внести депозит сразу после просмотра.',
  chat:[['bot','Здравствуйте! Ищете квартиру?'],['lead','Да, нужна парковка'],['bot','Есть варианты с парковкой. Бюджет?'],['lead','до 6200₪. 053-660-1185']]},
 {id:6,name:'Ронен Г.',user:'@ronen_g',cls:'hot',score:80,status:'opened',phone:'052-339-7740',ad:'Вакансия · Бариста',
  summary:'Опыт 3 года в кофейне, ищет полную ставку. Оставил телефон, ждёт звонка.',
  chat:[['bot','Привет! Вакансия бариста открыта. Есть опыт?'],['lead','3 года'],['bot','Полная ставка подойдёт?'],['lead','Да. 052-339-7740']]},
 {id:7,name:'Майя Т.',user:'@maya_t',cls:'hot',score:78,status:'opened',phone:'054-118-3302',ad:'Вакансия · Бариста',
  summary:'Без опыта, но готова учиться, живёт рядом. Оставила телефон.',
  chat:[['bot','Привет! Вакансия бариста открыта. Есть опыт?'],['lead','Опыта нет, но быстро учусь, живу рядом'],['bot','Отлично, оставьте телефон'],['lead','054-118-3302']]},
 {id:8,name:'Лена Г.',user:'@lena_g',cls:'warm',score:64,status:'opened',phone:'053-401-2290',ad:'Вакансия · Бариста',
  summary:'Опыт 2 года, готова выйти завтра. Не уточнила график — нужен дозвон.',
  chat:[['bot','Привет! Вакансия бариста ещё открыта. Есть опыт?'],['lead','Да, 2 года'],['bot','Когда можете выйти?'],['lead','Хоть завтра. 053-401-2290']]},
 {id:9,name:'Том К.',user:'@tom_k',cls:'warm',score:55,status:'opened',phone:'—',ad:'Аренда · Флорентин',
  summary:'Интересуется, но бюджет ниже рынка (4500₪). Телефон пока не оставил.',
  chat:[['bot','Здравствуйте! Ищете квартиру?'],['lead','Да, бюджет 4500₪'],['bot','Это ниже текущих цен, но пришлю что появится.']]},
 {id:10,name:'Игорь П.',user:'@igor_p',cls:'cold',score:28,status:'opened',phone:'—',ad:'Аренда · Флорентин',
  summary:'Просто смотрит, бюджет не назвал, телефон не оставил. Низкий приоритет.',
  chat:[['bot','Здравствуйте! Ищете квартиру?'],['lead','Пока просто смотрю'],['bot','Когда определитесь с бюджетом — напишите, подберу варианты.']]},
 {id:11,name:'Дубликат · Алекс',user:'@alex_m',cls:'dup',score:0,status:'cancelled',phone:'054-555-1234',ad:'Аренда · Флорентин',dupOf:1,
  summary:'Повтор обращения того же пользователя по другому объявлению. Приглушён, объединён с оригиналом #1.',
  chat:[['lead','Это снова я, по другой квартире'],['bot','Узнал вас! Объединил с предыдущим обращением.']]},
 {id:12,name:'Promo Bot',user:'@promo99',cls:'cold',score:3,status:'blocked_or_suspected',phone:'—',ad:'—',spam:true,
  summary:'Рекламное сообщение, помечено ботом как спам и скрыто из ленты.',
  chat:[['lead','💰 ЗАРАБОТОК ОНЛАЙН КАЗИНО ПЕРЕХОДИ'],['bot','Сообщение помечено как спам и скрыто.']]}
];
/* derived counts (single source of truth for badges/labels) */
var COUNTS={
  hot:LEADS.filter(function(L){return L.cls==='hot';}).length,
  warm:LEADS.filter(function(L){return L.cls==='warm';}).length,
  withPhone:LEADS.filter(function(L){return L.cls==='hot'&&L.phone&&L.phone!=='—';}).length,
  all:LEADS.filter(function(L){return !L.spam;}).length,
  spam:LEADS.filter(function(L){return L.spam;}).length,
  processed:214
};

/* ── Campaigns + posting ─────────────────────────────────────────────────── */
var CAMPAIGNS=[
 {name:'Аренда · Флорентин',ad:'3-комн. Флорентин',channels:'TG · FB · 48 групп',leads:5,status:'posted',statusLabel:'Активна'},
 {name:'Вакансия · Бариста',ad:'Бариста, центр',channels:'TG · 30 групп',leads:2,status:'posted',statusLabel:'Активна'},
 {name:'Продажа авто · Mazda',ad:'Mazda 3, 2019',channels:'FB · 22 группы',leads:0,status:'pending',statusLabel:'На паузе'}
];
var ATTEMPTS=[
 {group:'Аренда ТЛВ · центр',ch:'Telegram',time:'14:32',status:'posted',label:'Опубликовано'},
 {group:'Квартиры Флорентин',ch:'Telegram',time:'14:30',status:'posted',label:'Опубликовано'},
 {group:'Сдам/сниму ТЛВ',ch:'Facebook',time:'14:28',status:'manual_action_required',label:'Ручное действие'},
 {group:'Аренда без посредников',ch:'Telegram',time:'14:25',status:'scheduled',label:'Запланировано'},
 {group:'Жильё юг ТЛВ',ch:'Facebook',time:'14:20',status:'blocked_or_suspected',label:'Заблокировано'}
];
var QUEUE=[
 {title:'Сдам/сниму ТЛВ (Facebook)',sub:'Вставьте готовый текст в группу и отметьте результат',ic:'fb'},
 {title:'Жильё центр ТЛВ (Facebook)',sub:'Группа требует подтверждения модератора',ic:'fb'}
];

/* ── Ads ─────────────────────────────────────────────────────────────────── */
var ADS=[
 {id:'a1',title:'Сдаётся 3-комн. во Флорентине',vert:'home',vertLabel:'Недвижимость',city:'Тель-Авив',price:'6000₪/мес',
  active:true,leads:5,views:1240,preview:'Светлая 3-комнатная после ремонта. Рядом кафе и транспорт. Бюджет до 6000₪. Пишите боту.'},
 {id:'a2',title:'Бариста в кофейню (центр)',vert:'users',vertLabel:'Вакансия',city:'Тель-Авив',price:'45₪/час',
  active:true,leads:4,views:980,preview:'Ищем бариста на полную ставку. Опыт приветствуется, обучаем. График гибкий. Пишите боту.'},
 {id:'a3',title:'Mazda 3, 2019, 78 000 км',vert:'car',vertLabel:'Авто',city:'Тель-Авив',price:'72 000₪',
  active:false,leads:0,views:310,preview:'Один владелец, сервисная книжка, без ДТП. Торг у капота. Пишите боту — отвечу на вопросы.'}
];
var AD_LIMIT=5; // Pro plan

/* ── Telegram groups (synced) ────────────────────────────────────────────── */
var TG_GROUPS=[
 {name:'Аренда ТЛВ · центр',members:'12.4k',folder:'Аренда',on:true},
 {name:'Квартиры Флорентин',members:'8.1k',folder:'Аренда',on:true},
 {name:'Сдам/сниму ТЛВ',members:'21.7k',folder:'Аренда',on:true},
 {name:'Аренда без посредников',members:'15.2k',folder:'Аренда',on:true},
 {name:'Работа в Тель-Авиве',members:'33.0k',folder:'Работа',on:false},
 {name:'Вакансии кафе и бары',members:'6.5k',folder:'Работа',on:false}
];

/* ── Facebook sources ────────────────────────────────────────────────────── */
var FB_SOURCES=[
 {name:'Аренда квартир Тель-Авив',mode:'Ручной',ready:'format'},
 {name:'Florentin Apartments',mode:'Ручной',ready:'check'}
];

/* ── Назначения (unified posting targets) ────────────────────────────────── */
var SOURCES=[
 {name:'Аренда ТЛВ · центр',platform:'Telegram',kind:'Группа',mode:'Авто',ready:'ready'},
 {name:'Квартиры Флорентин',platform:'Telegram',kind:'Группа',mode:'Авто',ready:'ready'},
 {name:'Сдам/сниму ТЛВ',platform:'Telegram',kind:'Группа',mode:'Авто',ready:'ready'},
 {name:'Аренда квартир Тель-Авив',platform:'Facebook',kind:'Группа',mode:'Ручной',ready:'format'},
 {name:'Florentin Apartments',platform:'Facebook',kind:'Группа',mode:'Ручной',ready:'check'}
];

/* ── Dashboard data ──────────────────────────────────────────────────────── */
var FUNNEL=[
 {label:'Все отклики',val:214,color:'#0071e3'},
 {label:'Прошли бота',val:96,color:'#3a8dff'},
 {label:'Тёплые',val:34,color:'var(--warning)'},
 {label:'Горячие',val:11,color:'var(--danger)'},
 {label:'Закрыто',val:4,color:'var(--success)'}
];
var ONBOARD=[
 {n:'01',t:'Компания',done:true,go:'company'},
 {n:'02',t:'Объявление',done:true,go:'ads'},
 {n:'03',t:'Telegram',done:true,go:'channel-tg'},
 {n:'04',t:'Facebook',done:false,go:'channel-fb'},
 {n:'05',t:'Кампания',done:false,go:'campaigns'},
 {n:'06',t:'Первый постинг',done:false,go:'campaigns'}
];

/* ── AI-бот config ───────────────────────────────────────────────────────── */
var BOT={
  tone:'friendly',        // professional | friendly | strict
  lang:'auto',            // ru | he | en | auto
  positive:'Назвал бюджет, оставил телефон, готов на просмотр или выход на работу в течение недели, отвечает по делу.',
  negative:'Спрашивает только цену без интереса, отказывается оставлять контакт, грубит, спам, бюджет сильно ниже рынка.',
  greet:'Здравствуйте! Рад, что заинтересовало 🙂 Задам пару коротких вопросов, чтобы подобрать лучший вариант.',
  reject:'Спасибо за интерес! Сейчас нет подходящих вариантов под ваш запрос — напишу, как только появятся.',
  success:'Отлично, передал ваши контакты агенту — он свяжется в течение часа. Хорошего дня!'
};
/* canned test-bot replies: keyword → response + resulting classification */
var BOT_DEMO=[
  {kw:['бюджет','6000','5000','телефон','054','050','052','053'],a:'Спасибо! Передал ваши контакты агенту — он свяжется в течение часа. 🔥',cls:'hot'},
  {kw:['смотрю','цены','просто','интересуюсь'],a:'Понял! Когда определитесь с бюджетом — напишите, подберу варианты.',cls:'cold'},
  {kw:['3-комн','квартир','аренда','работа','вакансия','опыт'],a:'Отличный выбор! Подскажите ваш бюджет и желаемый район — и оставьте номер, чтобы агент связался.',cls:null}
];
var BOT_DEFAULT_REPLY='Здравствуйте! Чтобы подобрать вариант, подскажите бюджет, район и оставьте номер телефона.';

/* ── Аналитика ───────────────────────────────────────────────────────────── */
var ANALYTICS={
  kpi:[
    {ic:'send', label:'Публикаций',        val:'52',  sub:'+12 за неделю', up:true},
    {ic:'bot',  label:'Обработано ботом',   val:'214', sub:'81% спама отсеяно'},
    {ic:'flame',label:'Горячих лидов',      val:'11',  sub:'+3 за неделю', up:true},
    {ic:'check',label:'Закрыто сделок',     val:'4',   sub:'конверсия 1.9%'}
  ],
  funnel:[
    {label:'Все отклики',val:214,color:'#0071e3'},
    {label:'Прошли бота',val:96, color:'#3a8dff'},
    {label:'Тёплые',     val:34, color:'var(--warning)'},
    {label:'Горячие',    val:11, color:'var(--danger)'},
    {label:'Закрыто',    val:4,  color:'var(--success)'}
  ],
  langs:[
    {label:'Русский',val:148,pct:69,color:'#0071e3'},
    {label:'עברית',  val:52, pct:24,color:'var(--warning)'},
    {label:'English', val:14, pct:7, color:'var(--success)'}
  ],
  days:[{d:'Пн',v:6},{d:'Вт',v:9},{d:'Ср',v:7},{d:'Чт',v:12},{d:'Пт',v:14},{d:'Сб',v:4},{d:'Вс',v:8}],
  ops:[
    {label:'Постов опубликовано',          val:'52'},
    {label:'Ручных подтверждений FB',       val:'18'},
    {label:'Заблокировано группами',        val:'3'},
    {label:'Среднее время ответа бота',     val:'8 с'}
  ],
  ads:[
    {title:'Аренда · Флорентин', leads:9, conv:'4.2%', pct:90},
    {title:'Бариста · центр',     leads:4, conv:'2.1%', pct:45},
    {title:'Mazda 3, 2019',       leads:0, conv:'0%',   pct:5}
  ]
};

/* ── Команда ─────────────────────────────────────────────────────────────── */
var TEAM=[
  {name:'Дмитрий В.', email:'demo@posting-autopilot.com', role:'Владелец',  you:true, active:true},
  {name:'Анна К.',     email:'anna@dirot.co.il',          role:'Оператор',           active:true},
  {name:'Михаил Р.',   email:'misha@dirot.co.il',         role:'Оператор',           active:false}
];

/* ── Тарифы / биллинг ────────────────────────────────────────────────────── */
var PLANS=[
  {id:'starter',name:'Starter',price:'299₪',  tagline:'Одно объявление, ручной постинг',
   feats:['1 активное объявление','10 каналов постинга','AI-бот скрининга','Лиды и базовый дашборд']},
  {id:'pro',name:'Pro',price:'899₪', tagline:'Активный мультиканальный постинг', featured:true, current:true,
   feats:['5 активных объявлений','50 каналов постинга','Планировщик и ночной режим','Аналитика и воронка','Приоритетная поддержка']},
  {id:'agency',name:'Agency',price:'1999₪', tagline:'Агентствам и нескольким компаниям',
   feats:['Безлимит объявлений','Мультикомпания','API и вебхуки','White-label кабинет','Персональный менеджер']}
];
var TRIAL={days:11, plan:'Pro', expired:false};

/* ── Screen meta: title + Operator Copilot content ───────────────────────── */
var SCREENS={
 leads:{title:'Лиды', cp:{tone:'running',
   summary:'7 горячих лидов ждут ответа. Авиталь Р. и Алекс М. оставили телефон — позвоните им первыми, пока контакт «тёплый».',
   facts:[{ic:'flame',tone:'bad',label:'Горячих',val:'7'},{ic:'phone',tone:'ok',label:'С телефоном',val:'6'},{ic:'bot',tone:'ok',label:'Спам отсеян',val:'173'}],
   warn:[],action:{label:'Открыть первого',go:'leads',ico:'flame'}}},
 dashboard:{title:'Дашборд', cp:{tone:'setup',
   summary:'Настройка почти готова: 3 из 6 шагов. Подключите Facebook и запустите первую кампанию — и постинг пойдёт автоматически.',
   facts:[{ic:'check',tone:'ok',label:'Объявление',val:'есть'},{ic:'send',tone:'ok',label:'Telegram',val:'готов'},{ic:'fb',tone:'warn',label:'Facebook',val:'нет'}],
   warn:[{tone:'warn',text:'Facebook не подключён — половина каналов недоступна.'}],action:{label:'Подключить Facebook',go:'channel-fb',ico:'fb'}}},
 campaigns:{title:'Кампании', cp:{tone:'manual',
   summary:'2 кампании активны. Есть 2 ручных действия по Facebook — выполните их, чтобы посты ушли в FB-группы.',
   facts:[{ic:'rocket',tone:'ok',label:'Активны',val:'2'},{ic:'alert',tone:'warn',label:'Ручных',val:'2'},{ic:'moon',tone:'warn',label:'Ночной режим',val:'23:00'}],
   warn:[{tone:'warn',text:'Ночной режим: автопостинг на паузе 23:00–07:00.'}],action:{label:'К очереди действий',go:'campaigns',ico:'alert'}}},
 ads:{title:'Объявления', cp:{tone:'running',
   summary:'Активны 2 объявления из 5 по тарифу Pro. «Аренда · Флорентин» приносит больше всего горячих лидов — держите его в топе кампаний.',
   facts:[{ic:'doc',tone:'ok',label:'Активных',val:'2'},{ic:'flame',tone:'bad',label:'Лидов с них',val:'9'},{ic:'lock',tone:'warn',label:'Лимит Pro',val:'3 / 5'}],
   warn:[],action:{label:'Создать объявление',go:'ads',ico:'plus'}}},
 'channel-tg':{title:'Telegram', cp:{tone:'running',
   summary:'Telegram подключён, синхронизировано 64 группы, 48 выбраны для постинга. Можно добавить ещё — лимит Pro 50 каналов почти достигнут.',
   facts:[{ic:'check',tone:'ok',label:'Подключено',val:'да'},{ic:'send',tone:'ok',label:'Групп выбрано',val:'48'},{ic:'lock',tone:'warn',label:'Лимит Pro',val:'48 / 50'}],
   warn:[],action:{label:'К назначениям',go:'sources',ico:'target'}}},
 'channel-fb':{title:'Facebook', cp:{tone:'setup',
   summary:'Facebook ещё не подключён. Подключите через OAuth или вставьте ссылки на группы — и вторая половина каналов станет доступна.',
   facts:[{ic:'fb',tone:'bad',label:'Подключено',val:'нет'},{ic:'target',tone:'warn',label:'FB-групп',val:'0'}],
   warn:[{tone:'warn',text:'Без Facebook доступна только половина охвата.'}],action:{label:'Подключить Facebook',go:'channel-fb',ico:'fb'}}},
 sources:{title:'Назначения', cp:{tone:'manual',
   summary:'70 назначений всего: 48 Telegram готовы к авто, 22 Facebook в ручном режиме. 3 требуют проверки — обновите их перед следующей кампанией.',
   facts:[{ic:'send',tone:'ok',label:'TG готовы',val:'48'},{ic:'fb',tone:'warn',label:'FB ручные',val:'22'},{ic:'alert',tone:'warn',label:'Проверить',val:'3'}],
   warn:[],action:{label:'Проверить все',go:'sources',ico:'refresh'}}},
 bot:{title:'AI-бот', cp:{tone:'running',
   summary:'Бот настроен в дружелюбном тоне, отвечает в среднем за 8 секунд и круглосуточно. Проверьте критерии «горячий» — от них зависит, кого вы увидите первым.',
   facts:[{ic:'bot',tone:'ok',label:'Тон',val:'Дружелюбный'},{ic:'clock',tone:'ok',label:'Ответ',val:'8 с'},{ic:'spark',tone:'ok',label:'Язык',val:'Авто'}],
   warn:[],action:{label:'Протестировать бота',go:'bot',ico:'bot'}}},
 analytics:{title:'Аналитика', cp:{tone:'running',
   summary:'За неделю 214 обращений и 11 горячих лидов. Лучше всех «Аренда · Флорентин» — конверсия 4.2%. Объявление про Mazda почти не даёт лидов — обновите или снимите.',
   facts:[{ic:'send',tone:'ok',label:'Публикаций',val:'52'},{ic:'flame',tone:'bad',label:'Горячих',val:'11'},{ic:'check',tone:'ok',label:'Закрыто',val:'4'}],
   warn:[],action:{label:'К объявлениям',go:'ads',ico:'doc'}}},
 company:{title:'Компания и команда', cp:{tone:'setup',
   summary:'Укажите, куда слать горячих лидов, чтобы не упустить контакт. Telegram задан, резервный email — нет. В команде 2 активных оператора.',
   facts:[{ic:'send',tone:'ok',label:'TG для лидов',val:'задан'},{ic:'mail',tone:'warn',label:'Email',val:'нет'},{ic:'users',tone:'ok',label:'Команда',val:'2'}],
   warn:[{tone:'warn',text:'Email для горячих лидов не указан — резервный канал отключён.'}],action:{label:'Добавить участника',go:'company',ico:'plus'}}},
 billing:{title:'Биллинг и тарифы', cp:{tone:'setup',
   summary:'Идёт пробный период тарифа Pro — осталось 11 дней. После окончания автопостинг встанет на паузу. Перейдите на платный тариф заранее, чтобы не потерять охват.',
   facts:[{ic:'card',tone:'ok',label:'Тариф',val:'Pro · триал'},{ic:'clock',tone:'warn',label:'Осталось',val:'11 дней'}],
   warn:[{tone:'warn',text:'Триал истекает через 11 дней — затем автопостинг на паузе.'}],action:{label:'Перейти на Pro',go:'billing',ico:'card'}}}
};

return {ICONS:ICONS,svg:svg,injectIcons:injectIcons,COMPANIES:COMPANIES,LEADS:LEADS,COUNTS:COUNTS,
  CAMPAIGNS:CAMPAIGNS,ATTEMPTS:ATTEMPTS,QUEUE:QUEUE,FUNNEL:FUNNEL,ONBOARD:ONBOARD,SCREENS:SCREENS,
  ADS:ADS,AD_LIMIT:AD_LIMIT,TG_GROUPS:TG_GROUPS,FB_SOURCES:FB_SOURCES,SOURCES:SOURCES,
  BOT:BOT,BOT_DEMO:BOT_DEMO,BOT_DEFAULT_REPLY:BOT_DEFAULT_REPLY,ANALYTICS:ANALYTICS,TEAM:TEAM,PLANS:PLANS,TRIAL:TRIAL};
})();
