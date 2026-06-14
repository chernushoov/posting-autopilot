/* ════════════════════════════════════════════════════════════════════════════
   Posting Autopilot — Cabinet controller (router, state, copilot, wiring)
   ════════════════════════════════════════════════════════════════════════════ */
(function(){
"use strict";
var D=window.PA, S=window.PAScreens, S2=window.PAScreens2, I=window.PA_I18N;
var $=function(s,r){return (r||document).querySelector(s);};
var $$=function(s,r){return [].slice.call((r||document).querySelectorAll(s));};

/* ── State ───────────────────────────────────────────────────────────────── */
var KEY={auth:'pa_app_auth',company:'pa_app_company'};
function get(k){try{return localStorage.getItem(k);}catch(e){return null;}}
function set(k,v){try{localStorage.setItem(k,v);}catch(e){}}
var state={filter:'hot', lead:1, company:(window.PA_BOOT&&window.PA_BOOT.current_company)||get(KEY.company)||'dirot', screen:'leads',
  adView:'list', adStep:1, adId:'a1', tgView:'connected', tgStep:1, trialExpired:false};

var ALL=Object.keys(D.SCREENS);

/* ── Render a screen ─────────────────────────────────────────────────────── */
function renderView(name){
  var meta=D.SCREENS[name]; var view=$('#view'); if(!view) return;
  if(name==='leads'){ view.innerHTML=S.leads(state); mountLeads(); }
  else if(name==='dashboard'){ view.innerHTML=S.dashboard(state); }
  else if(name==='campaigns'){ view.innerHTML=S.campaigns(state); }
  else if(name==='ads'){ view.innerHTML=S.ads(state); }
  else if(name==='channel-tg'){ view.innerHTML=S.channelTg(state); }
  else if(name==='channel-fb'){ view.innerHTML=S.channelFb(state); }
  else if(name==='sources'){ view.innerHTML=S.sources(state); }
  else if(name==='bot'){ view.innerHTML=S2.bot(state); mountBot(); }
  else if(name==='analytics'){ view.innerHTML=S2.analytics(state); }
  else if(name==='company'){ view.innerHTML=S2.company(state); }
  else if(name==='billing'){ view.innerHTML=S2.billing(state); }
  D.injectIcons(view);
  renderCopilot(name, meta);
}
function rerender(){ renderView(state.screen); }

/* ── Operator Copilot ────────────────────────────────────────────────────── */
function renderCopilot(name, meta){
  var cp=$('#copilot');
  var c = meta.cp || {tone:'setup',summary:'',facts:[],warn:[],action:null};
  var facts=(c.facts||[]).map(function(f){
    return '<div class="cp-fact '+(f.tone||'')+'"><span class="ico" data-i="'+f.ic+'"></span>'+f.label+'<span class="cf-val">'+f.val+'</span></div>';
  }).join('');
  var warns=(c.warn||[]).map(function(w){
    return '<div class="cp-warn '+(w.tone==='bad'?'bad':'')+'"><span class="ico" data-i="alert"></span><span>'+w.text+'</span></div>';
  }).join('');
  cp.className='copilot tone-'+(c.tone||'setup');
  cp.innerHTML=''
   + '<div class="cp-head"><span class="cp-spark" data-i="spark"></span>'
   +   '<div class="cp-title">'+I.t('cp.title')+'<span class="cp-sub">'+meta.title+'</span></div></div>'
   + '<div class="cp-summary">'+c.summary+'</div>'
   + (facts?'<div class="cp-divider"></div><div class="cp-section-label">'+I.t('cp.now')+'</div><div class="cp-facts">'+facts+'</div>':'')
   + (warns?warns:'')
   + (c.action?'<button class="btn cp-action" data-go="'+c.action.go+'"><span class="ico" data-i="'+c.action.ico+'"></span>'+c.action.label+'</button>':'');
  D.injectIcons(cp);
}

/* ── Routing ─────────────────────────────────────────────────────────────── */
function show(name){
  if(ALL.indexOf(name)<0) name='leads';
  if(!get(KEY.auth)&&!window.PA_BOOT){ showLogin(); return; }
  $('#screen-login').classList.remove('active');
  $('#shell').classList.remove('hide');
  $$('#sbnav .sb-link').forEach(function(a){a.classList.toggle('active',a.getAttribute('data-go')===name);});
  $('#wbTitle').textContent=D.SCREENS[name].title;
  state.screen=name;
  state.adView='list';
  state.tgView='connected';
  closeSidebar();
  renderView(name);
  window.scrollTo(0,0);
}
function showLogin(){
  $('#shell').classList.add('hide');
  $('#screen-login').classList.add('active');
}
function go(name){ if(location.hash!=='#/'+name) location.hash='#/'+name; else show(name); }
window.addEventListener('hashchange',function(){route();});
function route(){
  var h=(location.hash||'').replace('#/','');
  if(!get(KEY.auth)&&!window.PA_BOOT){ showLogin(); return; }
  show(h||'leads');
}

/* ── Leads interactions ──────────────────────────────────────────────────── */
function filteredLeads(){
  var f=state.filter;
  return D.LEADS.filter(function(L){
    if(f==='spam') return L.spam;
    if(L.spam) return false;
    if(f==='all') return true;
    if(f==='hot') return L.cls==='hot';
    if(f==='warm') return L.cls==='warm';
    return true;
  });
}
function mountLeads(){
  var data=filteredLeads();
  $('#leadList').innerHTML=S.leadListHTML(data);
  if(!data.some(function(L){return L.id===state.lead;})) state.lead=data[0]?data[0].id:null;
  paintDetail();
  $$('#leadFilter button').forEach(function(b){
    b.addEventListener('click',function(){
      $$('#leadFilter button').forEach(function(x){x.classList.remove('active');});
      b.classList.add('active'); state.filter=b.getAttribute('data-f');
      var d=filteredLeads(); $('#leadList').innerHTML=S.leadListHTML(d);
      state.lead=d[0]?d[0].id:null; paintDetail(); bindItems();
    });
  });
  bindItems();
}
function bindItems(){
  $$('#leadList .lead-item').forEach(function(it){
    it.addEventListener('click',function(){state.lead=+it.getAttribute('data-id');paintDetail();});
  });
}
function paintDetail(){
  var L=D.LEADS.filter(function(x){return x.id===state.lead;})[0];
  var el=$('#leadDetail'); if(!el) return;
  el.innerHTML=S.leadDetailHTML(L); D.injectIcons(el);
  $$('#leadList .lead-item').forEach(function(it){it.classList.toggle('active',+it.getAttribute('data-id')===state.lead);});
}

/* ── Auth ────────────────────────────────────────────────────────────────── */
function login(){ set(KEY.auth,'1'); go('leads'); show('leads'); }
var _tgL=$('#tgLogin'); if(_tgL) _tgL.addEventListener('click',login);
var _emF=$('#emailForm'); if(_emF) _emF.addEventListener('submit',function(e){e.preventDefault();login();});
$('#logoutBtn').addEventListener('click',function(){
  if(confirm(I.t('auth.logout_q'))){ try{localStorage.removeItem(KEY.auth);}catch(e){}
    if(window.PA_BOOT){ window.location='/logout'; return; }
    location.hash=''; showLogin(); }
});
$('#avatar').addEventListener('click',function(){go('company');});

/* ── Company switcher ────────────────────────────────────────────────────── */
function paintCompany(){
  var c=D.COMPANIES.filter(function(x){return x.id===state.company;})[0]||D.COMPANIES[0];
  $('#cmpLogo').textContent=c.logo; $('#cmpName').textContent=c.name;
  $('.sb-company .cmp-sub').textContent=c.type;
}
$('#cmpBtn').addEventListener('click',function(e){
  e.stopPropagation();
  var pop=$('#cmpPop');
  pop.innerHTML=D.COMPANIES.map(function(c){
    return '<div class="cmp-opt '+(c.id===state.company?'active':'')+'" data-cmp="'+c.id+'">'
    + '<span class="cmp-logo">'+c.logo+'</span><div style="flex:1"><div style="font-weight:600;font-size:13px">'+c.name+'</div><div class="small muted">'+c.type+'</div></div>'
    + (c.id===state.company?'<span class="ico" data-i="check" style="color:var(--accent);font-size:16px"></span>':'')+'</div>';
  }).join('')+'<div class="cmp-opt cmp-add" data-cmp="__new"><span class="ico" data-i="plus"></span> '+I.t('add.company')+'</div>';
  var r=$('#cmpBtn').getBoundingClientRect();
  pop.style.left=r.left+'px'; pop.style.top=(r.bottom+6)+'px';
  pop.classList.add('show'); $('#scrim').classList.add('show'); D.injectIcons(pop);
  $$('#cmpPop .cmp-opt').forEach(function(o){
    o.addEventListener('click',function(){
      var id=o.getAttribute('data-cmp');
      if(window.PA_BOOT){ window.location = (id==='__new') ? '/profile/' : '/companies/'; closePop(); return; }
      if(id==='__new'){ toast(I.t('t.new_company')); }
      else { state.company=id; set(KEY.company,id); paintCompany(); route(); }
      closePop();
    });
  });
});
function closePop(){ $('#cmpPop').classList.remove('show'); $('#scrim').classList.remove('show'); }

/* ── Mobile sidebar ──────────────────────────────────────────────────────── */
function openSidebar(){ $('#sidebar').classList.add('open'); $('#scrim').classList.add('show'); }
function closeSidebar(){ $('#sidebar').classList.remove('open'); if(!$('#cmpPop').classList.contains('show')) $('#scrim').classList.remove('show'); }
$('#burger').addEventListener('click',openSidebar);
$('#scrim').addEventListener('click',function(){closeSidebar();closePop();});

/* ── Language switch (RU · EN · HE + RTL) ────────────────────────────────── */
$$('#langSwitch button').forEach(function(b){
  b.addEventListener('click',function(){ setLanguage(b.getAttribute('data-lang')); });
});

/* ── Global delegated clicks ─────────────────────────────────────────────── */
document.addEventListener('click',function(e){
  var g=e.target.closest('[data-go]'); if(g){ e.preventDefault(); go(g.getAttribute('data-go')); return; }
  var gl=e.target.closest('[data-go-lead]'); if(gl){ state.lead=+gl.getAttribute('data-go-lead'); go('leads'); return; }
  var bt=e.target.closest('[data-bot-tone]'); if(bt){ setBotTone(bt); return; }
  var bf=e.target.closest('[data-bot-fill]'); if(bf){ var i=$('#botInput'); if(i){ i.value=bf.getAttribute('data-bot-fill'); i.focus(); } return; }
  var act=e.target.closest('[data-act]'); if(act){ handleAct(act.getAttribute('data-act'), act); return; }
  var ad=e.target.closest('[data-ad]'); if(ad){ state.adView='detail'; state.adId=ad.getAttribute('data-ad'); rerender(); window.scrollTo(0,0); return; }
});
function handleAct(a, el){
  /* REAL BACKEND: when running on the live cabinet, route actions to the working,
     tenant-secured Flask pages instead of mock toasts. The pretty SPA stays the
     hub; the real create/connect/run/billing flows live on their own pages. */
  if(window.PA_BOOT){
    var NAV={ 'export':'/candidates/', 'new-campaign':'/campaigns/', 'run':'/campaigns/', 'pause':'/campaigns/',
      'new-ad':'/vacancies/', 'edit-ad':'/vacancies/', 'tg-reconnect':'/connect/telegram', 'tg-add':'/connect/telegram',
      'tg-resync':'/connect/telegram', 'fb-oauth':'/connect/facebook', 'fb-urls':'/connect/facebook',
      'src-add':'/sources/', 'src-check-all':'/sources/', 'src-test':'/sources/',
      'bot-save':'/profile/', 'company-save':'/profile/', 'company-logo':'/profile/', 'team-add':'/profile/',
      'plan-upgrade':'/pricing', 'plan-manage':'/pricing', 'pay-method':'/pricing', 'invoices':'/pricing' };
    if(a==='wa'||a==='tg'){
      var L=D.LEADS.filter(function(x){return x.id===state.lead;})[0];
      if(a==='wa'){ var ph=L&&L.phone?L.phone.replace(/[^0-9]/g,''):''; if(ph){ window.open('https://wa.me/'+(ph.charAt(0)==='0'?'972'+ph.slice(1):ph),'_blank'); } return; }
      var un=L&&L.user?L.user.replace(/^@/,''):''; if(un){ window.open('https://t.me/'+un,'_blank'); } return;
    }
    if(NAV[a]){ window.location=NAV[a]; return; }
  }
  switch(a){
    /* leads */
    case 'export': toast('Экспортирую в CSV…'); break;
    case 'wa': toast('Открываю WhatsApp с номером лида…'); break;
    case 'tg': toast('Открываю переписку в Telegram…'); break;
    /* campaigns */
    case 'new-campaign': toast('Мастер кампании — следующая итерация.'); break;
    case 'pause': toast('Кампания на паузе.'); break;
    case 'run': toast('Кампания запущена.'); break;
    case 'refresh': toast('Обновлено.'); break;
    case 'lead-status': break;
    /* ads — wizard + detail */
    case 'new-ad': state.adView='wizard'; state.adStep=1; rerender(); window.scrollTo(0,0); break;
    case 'edit-ad': state.adView='wizard'; state.adStep=1; rerender(); window.scrollTo(0,0); break;
    case 'ad-back': state.adView='list'; rerender(); window.scrollTo(0,0); break;
    case 'wz-next': state.adStep=Math.min(3,(state.adStep||1)+1); rerender(); break;
    case 'wz-back': state.adStep=Math.max(1,(state.adStep||1)-1); rerender(); break;
    case 'wz-close': state.adView='list'; rerender(); window.scrollTo(0,0); break;
    case 'wz-finish': state.adView='list'; rerender(); window.scrollTo(0,0); toast('Объявление опубликовано во все каналы.'); break;
    /* telegram */
    case 'tg-reconnect': state.tgView='wizard'; state.tgStep=1; rerender(); window.scrollTo(0,0); break;
    case 'tg-next': state.tgStep=Math.min(3,(state.tgStep||1)+1); rerender(); break;
    case 'tg-back': state.tgStep=Math.max(1,(state.tgStep||1)-1); rerender(); break;
    case 'tg-cancel': state.tgView='connected'; rerender(); window.scrollTo(0,0); break;
    case 'tg-finish': state.tgView='connected'; rerender(); window.scrollTo(0,0); toast('Telegram подключён.'); break;
    case 'tg-resend': toast('Код отправлен повторно.'); break;
    case 'tg-add': toast('Группы добавлены в постинг.'); break;
    case 'tg-resync': toast('Синхронизирую группы…'); break;
    /* facebook */
    case 'fb-oauth': toast('Открываю вход через Facebook…'); break;
    case 'fb-urls': toast('Группы добавлены в ручном режиме.'); break;
    /* sources */
    case 'src-test': if(confirm('Отправить тест-сообщение в это назначение?')) toast('Тест-сообщение отправлено.'); break;
    case 'src-check-all': toast('Проверяю все назначения…'); break;
    case 'src-add': toast('Назначение добавлено.'); break;
    /* bot */
    case 'bot-save': toast('Настройки бота сохранены.'); break;
    case 'bot-send': botSend(); break;
    /* company */
    case 'company-save': toast('Изменения сохранены.'); break;
    case 'company-logo': toast('Загрузка логотипа…'); break;
    case 'team-toggle': toggleTeam(el); break;
    case 'team-add': toast('Приглашение отправлено по email.'); break;
    case 'open-switcher': $('#cmpBtn').click(); break;
    /* billing */
    case 'plan-upgrade': toast('Переход на тариф '+((el.getAttribute('data-plan')||'').toUpperCase())+' — Stripe checkout…'); break;
    case 'plan-manage': toast('Управление подпиской…'); break;
    case 'trial-toggle': state.trialExpired=!state.trialExpired; rerender(); window.scrollTo(0,0); break;
    case 'pay-method': toast('Изменение способа оплаты…'); break;
    case 'invoices': toast('Открываю историю счетов…'); break;
  }
}

/* ── Bot test + team helpers ─────────────────────────────────────────────── */
function esc(s){ return (s||'').replace(/[&<>]/g,function(c){return {'&':'&amp;','<':'&lt;','>':'&gt;'}[c];}); }
function botReply(txt){
  var low=txt.toLowerCase();
  for(var i=0;i<D.BOT_DEMO.length;i++){ var d=D.BOT_DEMO[i];
    for(var j=0;j<d.kw.length;j++){ if(low.indexOf(d.kw[j].toLowerCase())>=0) return {reply:d.a,cls:d.cls}; } }
  return {reply:D.BOT_DEFAULT_REPLY,cls:null};
}
function botSend(){
  var inp=$('#botInput'); if(!inp) return; var txt=(inp.value||'').trim(); if(!txt) return;
  var chat=$('#botChat'); if(!chat) return;
  chat.insertAdjacentHTML('beforeend','<div class="msg"><div class="bubble">'+esc(txt)+'</div></div>');
  var r=botReply(txt);
  var meta=r.cls?'<span class="bubble-meta">'+(r.cls==='hot'?'🔥 Лид помечен горячим':'Лид помечен холодным')+'</span>':'';
  chat.insertAdjacentHTML('beforeend','<div class="msg me"><div class="bubble">'+esc(r.reply)+meta+'</div></div>');
  inp.value=''; chat.scrollTop=chat.scrollHeight;
}
function setBotTone(btn){
  $$('[data-bot-tone]').forEach(function(b){b.classList.remove('active');});
  btn.classList.add('active'); D.BOT.tone=btn.getAttribute('data-bot-tone');
}
function mountBot(){
  var inp=$('#botInput');
  if(inp) inp.addEventListener('keydown',function(e){ if(e.key==='Enter'){ e.preventDefault(); botSend(); } });
}
function toggleTeam(el){
  var tr=el.closest('tr'); if(!tr) return;
  var off=tr.classList.toggle('row-off');
  var st=tr.querySelector('.status');
  if(st){ st.className='status '+(off?'status-pending':'status-ready'); st.textContent=off?'Отключён':'Активен'; }
  el.classList.toggle('danger',!off);
  el.textContent=off?'Включить':'Деактивировать';
  toast(off?'Участник деактивирован.':'Участник снова активен.');
}

document.addEventListener('change',function(e){
  var sel=e.target.closest('[data-act="lead-status"]');
  if(sel){
    if(window.PA_BOOT){ if(state.lead) window.location='/candidates/'+state.lead; return; }
    var L=D.LEADS.filter(function(x){return x.id===state.lead;})[0];
    toast('Статус лида'+(L?' «'+L.name+'»':'')+' обновлён: '+sel.options[sel.selectedIndex].text); }
});

/* ── Toast ───────────────────────────────────────────────────────────────── */
var toastEl;
function toast(msg){
  if(!toastEl){ toastEl=document.createElement('div'); toastEl.style.cssText='position:fixed;left:50%;bottom:26px;transform:translateX(-50%) translateY(20px);background:#1d1d1f;color:#fff;padding:11px 20px;border-radius:999px;font-size:13.5px;font-weight:500;z-index:200;opacity:0;transition:all .3s;box-shadow:0 8px 30px rgba(0,0,0,.25)'; document.body.appendChild(toastEl); }
  toastEl.textContent=msg; requestAnimationFrame(function(){toastEl.style.opacity='1';toastEl.style.transform='translateX(-50%) translateY(0)';});
  clearTimeout(toastEl._t); toastEl._t=setTimeout(function(){toastEl.style.opacity='0';toastEl.style.transform='translateX(-50%) translateY(20px)';},2200);
}

/* ── i18n glue (server-driven default + static chrome labels) ─────────────── */
function applyStaticI18n(){
  $$('[data-t]').forEach(function(el){ el.textContent=I.t(el.getAttribute('data-t')); });
  var tc=$('#trialChipText'); if(tc){ var dd=(D.TRIAL&&D.TRIAL.days); tc.textContent=(dd!=null)?I.t('foot.trial',{n:dd}):((D.TRIAL&&D.TRIAL.plan)||'Pro'); }
}
function setLanguage(l){
  I.setLang(l); D.applyLang(l);
  $$('#langSwitch button').forEach(function(b){ b.classList.toggle('active', b.getAttribute('data-lang')===l); });
  applyStaticI18n(); paintCompany();
  var _n=document.getElementById('navLeadCount'); if(_n) _n.textContent=D.COUNTS.hot;
  if(get(KEY.auth)) show(state.screen);
}

/* ── Boot ────────────────────────────────────────────────────────────────── */
D.injectIcons(document);
var _bootLang=(window.PA_LANG&&['ru','en','he'].indexOf(window.PA_LANG)>=0)?window.PA_LANG:I.detect();
setLanguage(_bootLang);
route();
})();
