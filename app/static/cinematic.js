/* ════════════════════════════════════════════════════════════════════════════
   Posting Autopilot — Cinematic layer (phase 2)  ·  shared by he / en / ru
   Everything here is scroll/pointer-driven and has visibility failsafes, so it
   never leaves content stuck invisible.
   ════════════════════════════════════════════════════════════════════════════ */
(function(){
"use strict";
var REDUCED = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;
var LANG = (document.documentElement.lang || 'en').slice(0,2);
if(LANG!=='he' && LANG!=='ru') LANG='en';
var RTL = LANG==='he';
function $(s,r){return (r||document).querySelector(s);}
function clamp(v,a,b){return v<a?a:v>b?b:v;}

/* ── Per-language strings ─────────────────────────────────────────────────── */
var STR = {
 en:{
  eyebrow:'How it works', title:'One listing. Four steps. Zero effort.',
  steps:[
   {n:'STEP 01',t:'Create your ad',d:'Pick a template — job, car, apartment, service — or start from scratch. Set the FAQ and screening questions for the bot.'},
   {n:'STEP 02',t:'Post to 50+ groups',d:'Automatic on Telegram. On Facebook you paste ready-made text. Randomised delays, no bans.'},
   {n:'STEP 03',t:'The AI bot handles it',d:'Answers questions, asks screening questions, collects the phone. Spam and cold leads — filtered automatically.'},
   {n:'STEP 04',t:'Get only hot leads',d:'Instant alert: name, phone, summary, chat link. Instead of 30 chats — 3-5 ready to close.'}
  ],
  adImg:'your listing', adPrice:'6000\u20AA', groupsSuf:'+ groups',
  bot:[ {k:'spam',t:'Promo / spam message',tag:'filtered'},
        {k:'spam',t:'\u201CJust browsing\u201D, no budget',tag:'cold'},
        {k:'hot', t:'3 rooms, budget 6000\u20AA, phone shared',tag:'HOT'} ],
  lead:{badge:'\u2713 HOT LEAD', name:'User TG', meta:'3 rooms \u00B7 Florentin \u00B7 up to 6000\u20AA', phone:'054-555-1234'},
  tour:[
   {sel:'.lang-dots', t:'The site speaks your language', d:'It auto-detects your device language. Switch any time with EN / RU / HE — your choice is remembered.'},
   {sel:'.l-nav-links a[href="#how"]', t:'See how it works', d:'Scroll through the 4-step story: one ad turns into 50+ groups, the bot filters, and you get hot leads.'},
   {sel:'.l-nav-links a[href="#pricing"]', t:'Simple, transparent pricing', d:'Three clear plans, no surprises. Jump straight to them here.'},
   {sel:'.l-nav-links .btn', t:'Start in 5 minutes', d:'No credit card. Tap here and we\u2019ll get you set up over Telegram.'}
  ],
  next:'Next', done:'Got it', skip:'Skip', replay:'Quick tour'
 },
 ru:{
  eyebrow:'Как это работает', title:'Одно объявление. Четыре шага. Ноль усилий.',
  steps:[
   {n:'ШАГ 01',t:'Создай объявление',d:'Выбери шаблон — вакансия, авто, квартира, услуга — или с нуля. Задай FAQ и вопросы для скрининга боту.'},
   {n:'ШАГ 02',t:'Размести в 50+ группах',d:'Автоматически в Telegram. В Facebook — вставляешь готовый текст. Случайные задержки, без банов.'},
   {n:'ШАГ 03',t:'AI-бот всё ведёт',d:'Отвечает на вопросы, задаёт вопросы скрининга, собирает телефон. Спам и холодные лиды — фильтрует сам.'},
   {n:'ШАГ 04',t:'Получай только горячих',d:'Мгновенное уведомление: имя, телефон, итог, ссылка на чат. Вместо 30 диалогов — 3-5 готовых.'}
  ],
  adImg:'ваше объявление', adPrice:'6000\u20AA', groupsSuf:'+ групп',
  bot:[ {k:'spam',t:'Реклама / спам',tag:'отфильтровано'},
        {k:'spam',t:'«Просто смотрю», нет бюджета',tag:'холодный'},
        {k:'hot', t:'3 комнаты, бюджет 6000\u20AA, дал телефон',tag:'ГОРЯЧИЙ'} ],
  lead:{badge:'\u2713 ГОРЯЧИЙ ЛИД', name:'User TG', meta:'3 комнаты \u00B7 Флорентин \u00B7 до 6000\u20AA', phone:'054-555-1234'},
  tour:[
   {sel:'.lang-dots', t:'Сайт на вашем языке', d:'Язык определяется автоматически по устройству. Переключайте EN / RU / HE — выбор запомнится.'},
   {sel:'.l-nav-links a[href="#how"]', t:'Посмотрите, как это работает', d:'Пролистайте историю из 4 шагов: одно объявление → 50+ групп → бот фильтрует → вы получаете горячих лидов.'},
   {sel:'.l-nav-links a[href="#pricing"]', t:'Простые и прозрачные тарифы', d:'Три понятных плана, без сюрпризов. Перейти к ним можно отсюда.'},
   {sel:'.l-nav-links .btn', t:'Старт за 5 минут', d:'Без карты. Нажмите здесь — поможем подключиться через Telegram.'}
  ],
  next:'Далее', done:'Понятно', skip:'Пропустить', replay:'Тур по сайту'
 },
 he:{
  eyebrow:'איך זה עובד', title:'מודעה אחת. ארבעה צעדים. אפס מאמץ.',
  steps:[
   {n:'צעד 01',t:'צור מודעה',d:'בחר תבנית — משרה, רכב, דירה, שירות — או מאפס. הגדר FAQ ושאלות סינון לבוט.'},
   {n:'צעד 02',t:'פרסם ב-50+ קבוצות',d:'אוטומטי בטלגרם. בפייסבוק — מעתיקים טקסט מוכן. עיכובים אקראיים, בלי באנים.'},
   {n:'צעד 03',t:'בוט ה-AI מטפל',d:'עונה לשאלות, שואל שאלות סינון, אוסף טלפון. ספאם ולידים קרים — מסונן אוטומטית.'},
   {n:'צעד 04',t:'קבל רק לידים חמים',d:'התראה מיידית: שם, טלפון, סיכום, לינק לצ׳אט. במקום 30 שיחות — 3-5 מוכנים לסגירה.'}
  ],
  adImg:'המודעה שלך', adPrice:'6000\u20AA', groupsSuf:'+ קבוצות',
  bot:[ {k:'spam',t:'הודעת פרסום / ספאם',tag:'סונן'},
        {k:'spam',t:'״רק מסתכל״, בלי תקציב',tag:'קר'},
        {k:'hot', t:'3 חדרים, תקציב 6000\u20AA, השאיר טלפון',tag:'חם'} ],
  lead:{badge:'\u2713 ליד חם', name:'User TG', meta:'3 חדרים \u00B7 פלורנטין \u00B7 עד 6000\u20AA', phone:'054-555-1234'},
  tour:[
   {sel:'.lang-dots', t:'האתר בשפה שלך', d:'השפה מזוהה אוטומטית לפי המכשיר. אפשר להחליף EN / RU / HE — הבחירה נשמרת.'},
   {sel:'.l-nav-links a[href="#how"]', t:'ראה איך זה עובד', d:'גלול דרך הסיפור בן 4 הצעדים: מודעה אחת → 50+ קבוצות → הבוט מסנן → אתה מקבל לידים חמים.'},
   {sel:'.l-nav-links a[href="#pricing"]', t:'מחירים פשוטים ושקופים', d:'שלוש תוכניות ברורות, בלי הפתעות. אפשר לקפוץ אליהן מכאן.'},
   {sel:'.l-nav-links .btn', t:'התחל ב-5 דקות', d:'בלי כרטיס אשראי. הקש כאן ונחבר אותך דרך טלגרם.'}
  ],
  next:'הבא', done:'הבנתי', skip:'דלג', replay:'סיור באתר'
 }
};
var T = STR[LANG];

/* ════════════════════════════════════════════════════════════════════════════
   1) Reading progress bar
   ════════════════════════════════════════════════════════════════════════════ */
(function(){
  if(REDUCED) return;
  var bar=document.createElement('div'); bar.className='read-progress'; document.body.appendChild(bar);
  function upd(){var h=document.documentElement;var max=h.scrollHeight-h.clientHeight;
    bar.style.width=(max>0?(h.scrollTop/max*100):0)+'%';}
  window.addEventListener('scroll',upd,{passive:true}); window.addEventListener('resize',upd); upd();
})();

/* ════════════════════════════════════════════════════════════════════════════
   2) Hero — word reveal + interactive canvas field + parallax
   ════════════════════════════════════════════════════════════════════════════ */
(function(){
  var h=$('.hero-h1'); if(!h) return;
  if(!REDUCED){
    var idx=0, kids=[].slice.call(h.childNodes);
    kids.forEach(function(n){
      if(n.nodeType===3){
        var words=n.textContent.split(/(\s+)/), frag=document.createDocumentFragment();
        words.forEach(function(w){
          if(!w.trim()){frag.appendChild(document.createTextNode(w));return;}
          var o=document.createElement('span');o.className='w';
          var inr=document.createElement('span');inr.textContent=w;inr.style.animationDelay=(idx*0.06)+'s';idx++;
          o.appendChild(inr);frag.appendChild(o);
        });
        h.replaceChild(frag,n);
      } else if(n.nodeType===1 && n.tagName!=='BR'){
        var o=document.createElement('span');o.className='w';
        h.replaceChild(o,n);
        n.style.display='inline-block';n.style.transform='translateY(110%)';n.style.opacity='0';
        n.style.animation='wordRise .9s cubic-bezier(.16,1,.3,1) forwards';n.style.animationDelay=(idx*0.06)+'s';idx++;
        o.appendChild(n);
      }
    });
    // failsafe: guarantee headline ends visible even if animations are throttled
    setTimeout(function(){h.querySelectorAll('.w>span,.w> *').forEach(function(e){e.style.opacity='1';e.style.transform='none';});},1400);
  }

  // canvas particle / connection field
  if(REDUCED) return;
  var hero=$('.l-hero'); if(!hero) return;
  var cv=document.createElement('canvas'); cv.id='hero-canvas'; hero.insertBefore(cv,hero.firstChild);
  var ctx=cv.getContext('2d'), W,H,DPR=Math.min(window.devicePixelRatio||1,2), pts=[], mouse={x:-999,y:-999};
  function resize(){W=hero.clientWidth;H=hero.clientHeight;cv.width=W*DPR;cv.height=H*DPR;ctx.setTransform(DPR,0,0,DPR,0,0);
    var n=Math.min(64,Math.round(W*H/24000)); pts=[];
    for(var i=0;i<n;i++)pts.push({x:Math.random()*W,y:Math.random()*H,vx:(Math.random()-.5)*.25,vy:(Math.random()-.5)*.25});}
  hero.addEventListener('pointermove',function(e){var r=hero.getBoundingClientRect();mouse.x=e.clientX-r.left;mouse.y=e.clientY-r.top;});
  hero.addEventListener('pointerleave',function(){mouse.x=mouse.y=-999;});
  var running=true;
  function tick(){
    if(!running)return;
    ctx.clearRect(0,0,W,H);
    for(var i=0;i<pts.length;i++){var p=pts[i];
      var dx=mouse.x-p.x,dy=mouse.y-p.y,d2=dx*dx+dy*dy;
      if(d2<22000){var f=(1-d2/22000)*.6;p.vx+=dx/Math.sqrt(d2+1)*f*.05;p.vy+=dy/Math.sqrt(d2+1)*f*.05;}
      p.x+=p.vx;p.y+=p.vy;p.vx*=.985;p.vy*=.985;
      if(p.x<0||p.x>W)p.vx*=-1;if(p.y<0||p.y>H)p.vy*=-1;
      p.x=clamp(p.x,0,W);p.y=clamp(p.y,0,H);
      ctx.beginPath();ctx.arc(p.x,p.y,1.8,0,7);ctx.fillStyle='rgba(0,113,227,.45)';ctx.fill();
    }
    for(var a=0;a<pts.length;a++)for(var b=a+1;b<pts.length;b++){
      var p1=pts[a],p2=pts[b],ddx=p1.x-p2.x,ddy=p1.y-p2.y,dd=ddx*ddx+ddy*ddy;
      if(dd<13000){ctx.beginPath();ctx.moveTo(p1.x,p1.y);ctx.lineTo(p2.x,p2.y);
        ctx.strokeStyle='rgba(0,113,227,'+(.13*(1-dd/13000))+')';ctx.lineWidth=1;ctx.stroke();}
    }
    requestAnimationFrame(tick);
  }
  resize();window.addEventListener('resize',resize);requestAnimationFrame(tick);
  document.addEventListener('visibilitychange',function(){running=!document.hidden;if(running)requestAnimationFrame(tick);});

  // gentle parallax on hero content
  hero.addEventListener('pointermove',function(e){
    var r=hero.getBoundingClientRect(),cx=(e.clientX-r.left)/r.width-.5,cy=(e.clientY-r.top)/r.height-.5;
    var hh=$('.hero-h1'),hs=$('.hero-sub');
    if(hh)hh.style.transform='translate('+(cx*10)+'px,'+(cy*8)+'px)';
    if(hs)hs.style.transform='translate('+(cx*6)+'px,'+(cy*5)+'px)';
  });
  hero.addEventListener('pointerleave',function(){var hh=$('.hero-h1'),hs=$('.hero-sub');if(hh)hh.style.transform='';if(hs)hs.style.transform='';});
})();

/* ════════════════════════════════════════════════════════════════════════════
   3) Micro — magnetic buttons + 3D card tilt
   ════════════════════════════════════════════════════════════════════════════ */
(function(){
  if(REDUCED) return;
  // magnetic
  document.querySelectorAll('.hero-ctas .btn, .hero-ctas .btn-ghost, .l-nav-links .btn, .final-btn').forEach(function(el){
    el.classList.add('magnetic');
    el.addEventListener('pointermove',function(e){var r=el.getBoundingClientRect();
      el.style.transform='translate('+((e.clientX-r.left-r.width/2)*.25)+'px,'+((e.clientY-r.top-r.height/2)*.35)+'px)';});
    el.addEventListener('pointerleave',function(){el.style.transform='';});
  });
  // 3D tilt + glare
  document.querySelectorAll('.case-card,.pain-stat,.roi-card,.price-card,.bot-feature').forEach(function(el){
    el.classList.add('tilt'); var g=document.createElement('span'); g.className='tilt-glare'; el.appendChild(g);
    el.addEventListener('pointermove',function(e){var r=el.getBoundingClientRect();
      var px=(e.clientX-r.left)/r.width,py=(e.clientY-r.top)/r.height;
      el.style.transform='perspective(800px) rotateX('+((.5-py)*7)+'deg) rotateY('+((px-.5)*9)+'deg) translateY(-4px)';
      g.style.setProperty('--gx',(px*100)+'%');g.style.setProperty('--gy',(py*100)+'%');});
    el.addEventListener('pointerleave',function(){el.style.transform='';});
  });
})();

/* ════════════════════════════════════════════════════════════════════════════
   4) Sticky scroll-story
   ════════════════════════════════════════════════════════════════════════════ */
(function(){
  var sec=$('.l-story'); if(!sec) return;
  // fill text
  $('#storyEyebrow').textContent=T.eyebrow; $('#storyTitle').textContent=T.title;
  $('#adImgLabel').textContent=T.adImg; $('#adPrice').textContent=T.adPrice;
  $('#groupsSuf').textContent=T.groupsSuf;
  var grid=$('#groupsGrid'); for(var i=0;i<50;i++){grid.appendChild(document.createElement('i'));}
  var botRows=$('#botRows'); var ICR={spam:'ban',hot:'check'};
  T.bot.forEach(function(b){var row=document.createElement('div');row.className='b-row '+b.k;
    row.innerHTML='<span class="b-ic"><i class="ico" data-i="'+ICR[b.k]+'"></i></span><span>'+b.t+'</span><span class="b-tag">'+b.tag+'</span>';
    row.style.opacity='0';botRows.appendChild(row);});
  var lead=T.lead; $('#leadBadge').textContent=lead.badge; $('#leadName').textContent=lead.name;
  $('#leadMeta').textContent=lead.meta; $('#leadPhone').textContent=lead.phone;
  // fallback list (reduced motion / no anim)
  var fb=$('#storyFallback');
  T.steps.forEach(function(s){var c=document.createElement('div');c.className='step-card';
    c.innerHTML='<div class="step-num">'+s.n.replace(/\D/g,'')+'</div><h3>'+s.t+'</h3><p>'+s.d+'</p>';fb.appendChild(c);});
  // re-inject icons we just added (icon system runs in page script; do it here too)
  reinjectIcons(sec);

  if(REDUCED) return;
  sec.classList.add('story-on');

  var track=$('.story-track'), scenes=[].slice.call(sec.querySelectorAll('.scene')),
      dots=[].slice.call(sec.querySelectorAll('.story-dots span')),
      fill=$('#storyRailFill'), cells=[].slice.call(grid.children),
      countEl=$('#groupsCount'), rows=[].slice.call(botRows.children),
      capNum=$('#capNum'),capTitle=$('#capTitle'),capDesc=$('#capDesc'),cap=$('#storyCaption');
  var curStage=-1, ticking=false;
  function render(){
    ticking=false;
    var r=track.getBoundingClientRect(), total=track.offsetHeight-window.innerHeight;
    var p=clamp(-r.top/total,0,1), stageF=p*4, stage=clamp(Math.floor(stageF),0,3);
    fill.style.width=(p*100)+'%';
    dots.forEach(function(d,i){d.classList.toggle('done',i<stage);d.classList.toggle('active',i===stage);});
    scenes.forEach(function(sc,i){
      var local=stageF-i, op=clamp(1.35-Math.abs(local-0.5)*1.9,0,1);
      sc.style.opacity=op; sc.style.transform='translateY('+((local-0.5)*-26)+'px) scale('+(0.96+op*0.04)+')';
    });
    // stage 1: groups fill
    var gf=clamp(stageF-1,0,1); var on=Math.round(gf*50);
    countEl.textContent=Math.round(gf*50);
    for(var i=0;i<cells.length;i++)cells[i].classList.toggle('on',i<on);
    // stage 2: rows reveal
    var bf=clamp(stageF-2,0,1);
    rows.forEach(function(row,i){var t=clamp(bf*rows.length-i,0,1);row.style.opacity=t;row.style.transform='translateX('+((1-t)*(RTL?-16:16))+'px)';});
    // caption swap
    if(stage!==curStage){curStage=stage;var s=T.steps[stage];
      cap.classList.add('swap');
      setTimeout(function(){capNum.textContent=s.n;capTitle.textContent=s.t;capDesc.textContent=s.d;cap.classList.remove('swap');},180);
    }
  }
  function onScroll(){if(!ticking){ticking=true;requestAnimationFrame(render);}}
  window.addEventListener('scroll',onScroll,{passive:true});window.addEventListener('resize',onScroll);
  // init caption
  var s0=T.steps[0];capNum.textContent=s0.n;capTitle.textContent=s0.t;capDesc.textContent=s0.d;curStage=0;
  render();
})();

/* helper: (re)inject line icons for nodes added after the page's own injector ran */
function reinjectIcons(root){
  var I=window.__PA_ICONS; if(!I) return;
  (root||document).querySelectorAll('i.ico[data-i]').forEach(function(el){
    if(el.firstChild) return; var n=el.getAttribute('data-i');
    if(I[n])el.innerHTML='<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">'+I[n]+'</svg>';
  });
}

/* ════════════════════════════════════════════════════════════════════════════
   5) First-visit onboarding tour
   ════════════════════════════════════════════════════════════════════════════ */
(function(){
  var KEY='pa_tour_done';
  var steps=T.tour.filter(function(s){return $(s.sel);});
  if(!steps.length) return;
  var mask=document.createElement('div'); mask.className='tour-mask';
  var spot=document.createElement('div'); spot.className='tour-spot';
  var pop=document.createElement('div'); pop.className='tour-pop';
  mask.appendChild(spot); document.body.appendChild(mask); document.body.appendChild(pop);
  var idx=0;
  function place(){
    var st=steps[idx], el=$(st.sel); if(!el){next();return;}
    var r=el.getBoundingClientRect(), pad=8;
    if(r.width===0&&r.height===0){next();return;}
    // if target is off-screen (mobile collapsed nav), scroll into view by approximations
    spot.style.top=(r.top-pad)+'px'; spot.style.left=(r.left-pad)+'px';
    spot.style.width=(r.width+pad*2)+'px'; spot.style.height=(r.height+pad*2)+'px';
    var dots=steps.map(function(_,i){return '<i class="'+(i===idx?'on':'')+'"></i>';}).join('');
    pop.innerHTML='<div class="tp-step">'+(idx+1)+' / '+steps.length+'</div>'+
      '<h4>'+st.t+'</h4><p>'+st.d+'</p>'+
      '<div class="tp-row"><div class="tp-dots">'+dots+'</div>'+
      '<div class="tp-actions"><button class="tp-skip">'+T.skip+'</button>'+
      '<button class="tp-next">'+(idx===steps.length-1?T.done:T.next)+'</button></div></div>';
    pop.querySelector('.tp-skip').onclick=end;
    pop.querySelector('.tp-next').onclick=next;
    // position popover below the spot (or above if low)
    pop.classList.remove('show'); void pop.offsetWidth;
    var pw=Math.min(300,window.innerWidth*0.88), below=r.bottom+14, ph=pop.offsetHeight||180;
    var top=(below+ph>window.innerHeight-10)?(r.top-ph-14):below;
    if(top<10)top=10;
    var left=clamp(r.left+r.width/2-pw/2,10,window.innerWidth-pw-10);
    pop.style.top=top+'px'; pop.style.left=left+'px';
    requestAnimationFrame(function(){pop.classList.add('show');});
  }
  function next(){if(idx<steps.length-1){idx++;place();}else end();}
  function end(){mask.classList.remove('show');pop.classList.remove('show');
    setTimeout(function(){mask.style.display='none';pop.style.display='none';},320);
    try{localStorage.setItem(KEY,'1');}catch(e){}}
  function start(){idx=0;mask.style.display='';pop.style.display='';mask.classList.add('show');place();}
  window.addEventListener('resize',function(){if(mask.classList.contains('show'))place();});

  // launcher (always available to replay)
  var launch=document.createElement('button'); launch.className='tour-launch';
  launch.innerHTML='<span class="tl-ic"><i class="ico" data-i="lightbulb"></i></span><span>'+T.replay+'</span>';
  document.body.appendChild(launch); reinjectIcons(launch);
  launch.onclick=start;

  var seen=false; try{seen=!!localStorage.getItem(KEY);}catch(e){}
  if(!seen && !REDUCED && window.innerWidth>760){ setTimeout(start,1600); }
})();

})();
