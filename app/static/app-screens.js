/* ════════════════════════════════════════════════════════════════════════════
   Posting Autopilot — Cabinet SCREEN templates (return HTML strings)
   ════════════════════════════════════════════════════════════════════════════ */
window.PAScreens = (function(){
"use strict";
var D = window.PA;
function clsBadge(c){
  var m={hot:['cls-hot','🔥 Горячий'],warm:['cls-warm','Тёплый'],cold:['cls-cold','Холодный'],dup:['cls-dup','Дубль']};
  var x=m[c]||m.cold; return '<span class="cls '+x[0]+'">'+x[1]+'</span>';
}
function scoreCls(s){return s>=80?'hi':s>=50?'mid':'';}

/* ── LEADS (hero) ─────────────────────────────────────────────────────────── */
function leads(state){
  return ''
  + '<div class="page-hero"><div><div class="eyebrow">Входящие</div><h1>Лиды</h1>'
  + '<p class="muted">Отклики от бота. Реагируйте на горячих, пока контакт «тёплый».</p></div>'
  + '<button class="pill" data-act="export"><span class="ico" data-i="download"></span> Экспорт CSV</button></div>'
  + '<div class="seg" id="leadFilter" style="margin-bottom:16px">'
  +   '<button data-f="hot" class="active">🔥 Горячие <span class="cnt">'+D.COUNTS.hot+'</span></button>'
  +   '<button data-f="warm">Тёплые <span class="cnt">'+D.COUNTS.warm+'</span></button>'
  +   '<button data-f="all">Все <span class="cnt">'+D.COUNTS.all+'</span></button>'
  +   '<button data-f="spam">Спам <span class="cnt">'+D.COUNTS.spam+'</span></button>'
  + '</div>'
  + '<div class="leads-layout"><div class="lead-list" id="leadList"></div>'
  + '<div class="card lead-detail" id="leadDetail"></div></div>';
}
function leadListHTML(data){
  if(!data.length) return '<div class="empty-state">Нет лидов в этом фильтре</div>';
  return data.map(function(L){
    return '<div class="lead-item '+(L.cls==='dup'?'dup':'')+'" data-id="'+L.id+'">'
    + '<div class="li-top"><span class="li-name">'+L.name+'</span>'+clsBadge(L.cls)+'</div>'
    + '<div class="li-snip">'+L.summary+'</div>'
    + '<div class="li-meta"><span class="score '+scoreCls(L.score)+'">'+L.score+'</span><span>'+L.ad+'</span>'
    + (L.phone&&L.phone!=='—'?'<span>· '+L.phone+'</span>':'')+'</div></div>';
  }).join('');
}
function leadDetailHTML(L){
  if(!L) return '<div class="empty-state">Выберите лида слева</div>';
  var bubbles=L.chat.map(function(c){return '<div class="msg '+(c[0]==='bot'?'me':'')+'"><div class="bubble">'+c[1]+'</div></div>';}).join('');
  var statuses=['opened','got_responses','interview_scheduled','hired','cancelled'];
  var stLabels={opened:'Открыт',got_responses:'Ответил',interview_scheduled:'Назначена встреча',hired:'Закрыт',cancelled:'Отклонён',blocked_or_suspected:'Спам'};
  var opts=statuses.map(function(s){return '<option value="'+s+'"'+(s===L.status?' selected':'')+'>'+stLabels[s]+'</option>';}).join('');
  return ''
  + '<div class="section-head"><div><h2 style="margin:0;display:flex;align-items:center;gap:9px">'+L.name+' '+clsBadge(L.cls)+'</h2>'
  +   '<p class="muted small">'+L.user+' · '+L.ad+'</p></div>'
  +   '<span class="score '+scoreCls(L.score)+'" style="font-size:14px;padding:5px 11px">'+L.score+'</span></div>'
  + (L.dupOf?'<div class="alert">Дубликат обращения. Объединён с лидом #'+L.dupOf+'. <a data-go="leads" href="#/leads">Открыть оригинал →</a></div>':'')
  + '<div class="ai-summary"><span class="ico" data-i="sparkles"></span><div><strong>AI-резюме:</strong> '+L.summary+'</div></div>'
  + '<div class="lead-info">'
  +   '<div class="li"><span class="k">Телефон</span><span class="v">'+L.phone+'</span></div>'
  +   '<div class="li"><span class="k">Статус</span><span class="v"><select data-act="lead-status">'+opts+'</select></span></div>'
  + '</div>'
  + (L.spam?'':'<div class="actions" style="margin-bottom:6px">'
  +   '<button class="btn" data-act="wa"><span class="ico" data-i="phone"></span> WhatsApp</button>'
  +   '<button class="pill" data-act="tg"><span class="ico" data-i="send"></span> Telegram</button></div>')
  + '<div class="lead-chat-wrap"><div class="small muted" style="margin-bottom:8px">Диалог бота с кандидатом</div>'
  +   '<div class="chat">'+bubbles+'</div></div>';
}

/* ── DASHBOARD ────────────────────────────────────────────────────────────── */
function dashboard(state){
  var done=D.ONBOARD.filter(function(s){return s.done;}).length;
  var pct=Math.round(done/D.ONBOARD.length*100);
  var steps=D.ONBOARD.map(function(s){
    return '<div class="ob-step '+(s.done?'done':'')+'" data-go="'+s.go+'">'
    + '<span class="ob-tick">'+(s.done?'<span class="ico" data-i="checkbare"></span>':'')+'</span>'
    + '<span><span class="ob-n">Шаг '+s.n+'</span><br><span class="ob-t">'+s.t+'</span></span></div>';
  }).join('');
  var max=D.FUNNEL[0].val;
  var funnel=D.FUNNEL.map(function(f){
    return '<div class="fn-row"><div class="fn-label">'+f.label+'</div>'
    + '<div class="fn-track"><div class="fn-fill" style="width:'+Math.max(8,f.val/max*100)+'%;background:'+f.color+'">'+f.val+'</div></div></div>';
  }).join('');
  var leadRows=D.LEADS.filter(function(L){return !L.spam&&L.cls!=='dup';}).slice(0,4).map(function(L){
    return '<tr data-go-lead="'+L.id+'" style="cursor:pointer"><td><strong>'+L.name+'</strong></td><td>'+L.ad+'</td>'
    + '<td>'+clsBadge(L.cls)+'</td><td>'+L.phone+'</td></tr>';
  }).join('');
  return ''
  + '<div class="page-hero"><div><div class="eyebrow">Обзор</div><h1>Дашборд</h1>'
  +   '<p class="muted">Сегодня бот сэкономил вам ~3 часа.</p></div>'
  +   '<button class="btn" data-go="ads"><span class="ico" data-i="plus"></span> Новое объявление</button></div>'
  + '<div class="onboard"><h3>Завершите настройку</h3><p>Готово '+done+' из 6 шагов — осталось чуть-чуть до автопостинга.</p>'
  +   '<div class="ob-bar"><i style="width:'+pct+'%"></i></div><div class="ob-steps">'+steps+'</div></div>'
  + '<div class="kpi-grid">'
  +   kpi('chart','Публикаций','52','+12 сегодня')
  +   kpi('flame','Горячих лидов','7','+3 сегодня')
  +   kpi('bot','Обработано ботом','214','81% спама отсеяно')
  +   kpi('clock','Ответ бота','8с','круглосуточно',true)
  + '</div>'
  + '<div class="grid2" style="align-items:start">'
  +   '<div class="card"><div class="section-head"><h3 style="margin:0">Воронка лидов</h3><span class="badge">7 дней</span></div><div class="funnel">'+funnel+'</div></div>'
  +   '<div class="card"><div class="section-head"><h3 style="margin:0">Последние лиды</h3><a class="pill" data-go="leads" href="#/leads">Все →</a></div>'
  +     '<div class="table-wrap"><table class="table"><thead><tr><th>Имя</th><th>Объявление</th><th>Класс</th><th>Телефон</th></tr></thead><tbody>'+leadRows+'</tbody></table></div></div>'
  + '</div>';
}
function kpi(ic,label,val,sub,flat){
  return '<div class="kpi"><div class="k-top"><span class="k-ic" data-i="'+ic+'"></span><span class="k-label">'+label+'</span></div>'
  + '<div class="k-val">'+val+'</div><div class="k-sub'+(flat?' flat':'')+'">'+sub+'</div></div>';
}

/* ── CAMPAIGNS ────────────────────────────────────────────────────────────── */
function campaigns(state){
  var queue=D.QUEUE.map(function(q){
    return '<div class="q-item"><span class="q-ic" data-i="'+q.ic+'"></span>'
    + '<div class="q-body"><div class="q-title">'+q.title+'</div><div class="q-sub">'+q.sub+'</div></div>'
    + '<select data-act="queue-result"><option>Результат…</option><option>Опубликовано</option><option>Заблокировано</option><option>Пропустить</option></select></div>';
  }).join('');
  var camps=D.CAMPAIGNS.map(function(c){
    var act=c.status==='posted'
      ? '<button class="pill" data-act="pause"><span class="ico" data-i="pause"></span></button>'
      : '<button class="pill success" data-act="run"><span class="ico" data-i="play"></span></button>';
    return '<tr><td><strong>'+c.name+'</strong><div class="small muted">'+c.ad+'</div></td><td>'+c.channels+'</td>'
    + '<td>'+c.leads+'</td><td><span class="status status-'+c.status+'">'+c.statusLabel+'</span></td><td style="text-align:right">'+act+'</td></tr>';
  }).join('');
  var log=D.ATTEMPTS.map(function(a){
    return '<tr><td>'+a.group+'</td><td>'+a.ch+'</td><td class="muted small">'+a.time+'</td>'
    + '<td><span class="status status-'+a.status+'">'+a.label+'</span></td></tr>';
  }).join('');
  return ''
  + '<div class="page-hero"><div><div class="eyebrow">Постинг</div><h1>Кампании</h1>'
  +   '<p class="muted">Планирование и запуск мультиканального постинга.</p></div>'
  +   '<button class="btn" data-act="new-campaign"><span class="ico" data-i="plus"></span> Новая кампания</button></div>'
  + '<div class="night-banner"><span class="ico" data-i="moon"></span>Ночной режим: автопостинг на паузе с 23:00 до 07:00 — посты уйдут утром.</div>'
  + '<div class="readiness">'
  +   '<div class="ready-card tg"><span class="rc-ic" data-i="send"></span><div style="flex:1"><div class="rc-name">Telegram</div><div class="rc-sub">48 групп · готов к автопостингу</div></div><span class="status status-ready">Готов</span></div>'
  +   '<div class="ready-card fb"><span class="rc-ic" data-i="fb"></span><div style="flex:1"><div class="rc-name">Facebook</div><div class="rc-sub">22 группы · ручной режим</div></div><span class="status status-manual_action_required">Ручной</span></div>'
  + '</div>'
  + '<div class="section-head"><h2>Очередь ручных действий</h2><span class="badge">2 задачи</span></div>'
  + '<div class="queue" style="margin-bottom:26px">'+queue+'</div>'
  + '<div class="section-head"><h2>Кампании</h2></div>'
  + '<div class="table-wrap" style="margin-bottom:26px"><table class="table"><thead><tr><th>Кампания</th><th>Каналы</th><th>Лиды</th><th>Статус</th><th></th></tr></thead><tbody>'+camps+'</tbody></table></div>'
  + '<div class="section-head"><h2>Лог попыток постинга</h2><a class="pill" data-act="refresh"><span class="ico" data-i="refresh"></span> Обновить</a></div>'
  + '<div class="table-wrap"><table class="table"><thead><tr><th>Группа</th><th>Канал</th><th>Время</th><th>Статус</th></tr></thead><tbody>'+log+'</tbody></table></div>';
}

/* ════════════════════════════════════════════════════════════════════════════
   ADS — list + 3-step wizard
   ════════════════════════════════════════════════════════════════════════════ */
function ads(state){
  if(state.adView==='wizard') return adWizard(state);
  if(state.adView==='detail') return adDetail(state);
  var used=D.ADS.length, limit=D.AD_LIMIT;
  var cards=D.ADS.map(function(a){
    return '<div class="card ad-card" data-ad="'+a.id+'">'
    + '<div class="ad-card-top"><span class="ad-vert" data-i="'+a.vert+'"></span>'
    +   '<span class="status '+(a.active?'status-posted':'status-pending')+'">'+(a.active?'Активно':'Пауза')+'</span></div>'
    + '<h3 class="ad-title">'+a.title+'</h3>'
    + '<div class="ad-meta">'+a.vertLabel+' · '+a.city+' · '+a.price+'</div>'
    + '<p class="ad-preview">'+a.preview+'</p>'
    + '<div class="ad-stats"><span><span class="ico" data-i="flame"></span>'+a.leads+' лидов</span>'
    +   '<span><span class="ico" data-i="eye"></span>'+a.views.toLocaleString()+'</span>'
    +   '<button class="pill" data-act="edit-ad"><span class="ico" data-i="edit"></span>Изменить</button></div>'
    + '</div>';
  }).join('');
  var atLimit=used>=limit;
  return ''
  + '<div class="page-hero"><div><div class="eyebrow">Контент</div><h1>Объявления</h1>'
  +   '<p class="muted">Одно объявление → автопостинг во все каналы. Мультивертикаль.</p></div>'
  +   '<button class="btn" data-act="new-ad"'+(atLimit?' disabled style="opacity:.5"':'')+'><span class="ico" data-i="plus"></span> Новое объявление</button></div>'
  + '<div class="limit-bar"><div class="limit-track"><i style="width:'+(used/limit*100)+'%"></i></div>'
  +   '<span class="limit-label">'+used+' из '+limit+' объявлений · тариф Pro</span>'
  +   (atLimit?'<a class="pill" data-go="billing" href="#/billing">Повысить тариф</a>':'')+'</div>'
  + '<div class="ad-grid">'+cards+'</div>';
}

/* ── AD detail — preview + conversion funnel + leads from this ad ─────────── */
function adDetail(state){
  var a=D.ADS.filter(function(x){return x.id===state.adId;})[0]||D.ADS[0];
  var fn=[
    {label:'\u041f\u043e\u043a\u0430\u0437\u044b',val:a.views,color:'#0071e3'},
    {label:'\u041d\u0430\u043f\u0438\u0441\u0430\u043b\u0438 \u0431\u043e\u0442\u0443',val:Math.round(a.views*0.12),color:'#3a8dff'},
    {label:'\u041f\u0440\u043e\u0448\u043b\u0438 \u0441\u043a\u0440\u0438\u043d\u0438\u043d\u0433',val:Math.round(a.views*0.045)+ (a.leads||0),color:'var(--warning)'},
    {label:'\u0413\u043e\u0440\u044f\u0447\u0438\u0435',val:a.leads,color:'var(--danger)'},
    {label:'\u0417\u0430\u043a\u0440\u044b\u0442\u043e',val:Math.max(0,Math.round(a.leads*0.4)),color:'var(--success)'}
  ];
  var max=fn[0].val||1;
  var funnel=fn.map(function(f){
    return '<div class="fn-row"><div class="fn-label">'+f.label+'</div>'
    + '<div class="fn-track"><div class="fn-fill" style="width:'+Math.max(8,f.val/max*100)+'%;background:'+f.color+'">'+f.val.toLocaleString()+'</div></div></div>';
  }).join('');
  var kw=a.vert==='home'?'\u0410\u0440\u0435\u043d\u0434\u0430':a.vert==='users'?'\u0412\u0430\u043a\u0430\u043d\u0441\u0438\u044f':'\u0430\u0432\u0442\u043e';
  var rel=D.LEADS.filter(function(L){return !L.spam&&L.cls!=='dup'&&L.ad&&L.ad.indexOf(kw)>=0;}).slice(0,4);
  var leadRows=rel.length?rel.map(function(L){
    return '<tr data-go-lead="'+L.id+'" style="cursor:pointer"><td><strong>'+L.name+'</strong></td><td>'+clsBadge(L.cls)+'</td><td>'+L.phone+'</td></tr>';
  }).join(''):'<tr><td colspan="3" class="muted small" style="padding:18px;text-align:center">\u041f\u043e\u043a\u0430 \u043d\u0435\u0442 \u043b\u0438\u0434\u043e\u0432 \u0441 \u044d\u0442\u043e\u0433\u043e \u043e\u0431\u044a\u044f\u0432\u043b\u0435\u043d\u0438\u044f</td></tr>';
  return ''
  + '<div class="page-hero"><div><a class="back-link" data-act="ad-back"><span class="ico" data-i="chevron" style="transform:rotate(90deg)"></span> \u041a \u043e\u0431\u044a\u044f\u0432\u043b\u0435\u043d\u0438\u044f\u043c</a>'
  +   '<h1 style="margin-top:6px">'+a.title+'</h1>'
  +   '<p class="muted">'+a.vertLabel+' \u00b7 '+a.city+' \u00b7 '+a.price+'</p></div>'
  +   '<div class="actions"><span class="status '+(a.active?'status-posted':'status-pending')+'" style="font-size:13px">'+(a.active?'\u0410\u043a\u0442\u0438\u0432\u043d\u043e':'\u041f\u0430\u0443\u0437\u0430')+'</span>'
  +     '<button class="pill" data-act="'+(a.active?'pause':'run')+'"><span class="ico" data-i="'+(a.active?'pause':'play')+'"></span>'+(a.active?'\u041d\u0430 \u043f\u0430\u0443\u0437\u0443':'\u0417\u0430\u043f\u0443\u0441\u0442\u0438\u0442\u044c')+'</button>'
  +     '<button class="btn" data-act="edit-ad"><span class="ico" data-i="edit"></span>\u0418\u0437\u043c\u0435\u043d\u0438\u0442\u044c</button></div></div>'
  + '<div class="kpi-grid k3">'
  +   kpi('eye','\u041f\u043e\u043a\u0430\u0437\u044b',a.views.toLocaleString(),'\u0437\u0430 \u0432\u0441\u0451 \u0432\u0440\u0435\u043c\u044f',true)
  +   kpi('flame','\u0413\u043e\u0440\u044f\u0447\u0438\u0445 \u043b\u0438\u0434\u043e\u0432',a.leads,a.leads?'\u0441 \u044d\u0442\u043e\u0433\u043e \u043e\u0431\u044a\u044f\u0432\u043b\u0435\u043d\u0438\u044f':'\u043f\u043e\u043a\u0430 \u043d\u0435\u0442',true)
  +   kpi('chart','\u041a\u043e\u043d\u0432\u0435\u0440\u0441\u0438\u044f',(a.views?(a.leads/a.views*100).toFixed(1):'0')+'%','\u043f\u043e\u043a\u0430\u0437 \u2192 \u0433\u043e\u0440\u044f\u0447\u0438\u0439',true)
  + '</div>'
  + '<div class="grid2" style="align-items:start">'
  +   '<div class="card"><div class="section-head"><h3 style="margin:0">\u0412\u043e\u0440\u043e\u043d\u043a\u0430 \u043e\u0431\u044a\u044f\u0432\u043b\u0435\u043d\u0438\u044f</h3><span class="badge">\u0432\u0441\u0451 \u0432\u0440\u0435\u043c\u044f</span></div><div class="funnel">'+funnel+'</div></div>'
  +   '<div class="card card-flat wz-preview"><div class="section-head"><h3 style="margin:0">\u0422\u0435\u043a\u0441\u0442 \u043f\u043e\u0441\u0442\u0430</h3><span class="badge">'+a.vertLabel+'</span></div>'
  +     '<div class="fb-preview">'+a.title+'\n\n'+a.preview+'</div>'
  +     '<div class="chip-row"><span class="mini-chip ok">'+a.city+'</span><span class="mini-chip">'+a.price+'</span><span class="mini-chip">AI-\u0431\u043e\u0442</span></div></div>'
  + '</div>'
  + '<div class="section-head" style="margin-top:24px"><h2>\u041b\u0438\u0434\u044b \u0441 \u044d\u0442\u043e\u0433\u043e \u043e\u0431\u044a\u044f\u0432\u043b\u0435\u043d\u0438\u044f</h2><a class="pill" data-go="leads" href="#/leads">\u0412\u0441\u0435 \u043b\u0438\u0434\u044b \u2192</a></div>'
  + '<div class="table-wrap"><table class="table"><thead><tr><th>\u0418\u043c\u044f</th><th>\u041a\u043b\u0430\u0441\u0441</th><th>\u0422\u0435\u043b\u0435\u0444\u043e\u043d</th></tr></thead><tbody>'+leadRows+'</tbody></table></div>';
}
function adWizard(state){
  var step=state.adStep||1;
  var verts=[['home','Недвижимость'],['users','Вакансия'],['car','Авто'],['wrench','Услуга']];
  var dots=[1,2,3].map(function(n){
    var st=n<step?'done':n===step?'active':'';
    return '<div class="wz-dot '+st+'"><span class="wz-num">'+(n<step?'<span class=\'ico\' data-i=\'checkbare\'></span>':n)+'</span>'
    + '<span class="wz-label">'+['Что','Детали','Бот'][n-1]+'</span></div>';
  }).join('<div class="wz-line"></div>');
  var body;
  if(step===1){
    body='<div class="wz-field"><label>Тип объявления</label><div class="vert-row">'
    + verts.map(function(v,i){return '<button class="vert-chip'+(i===0?' active':'')+'" data-vert="'+v[0]+'"><span class="ico" data-i="'+v[0]+'"></span>'+v[1]+'</button>';}).join('')+'</div></div>'
    + '<div class="wz-field"><label>Заголовок</label><input id="wzTitle" value="Сдаётся 3-комн. во Флорентине"></div>'
    + '<div class="wz-field"><label>Текст объявления</label><textarea id="wzBody" rows="4">Светлая 3-комнатная после ремонта. Рядом кафе и транспорт. Бюджет до 6000₪. Пишите боту — отвечу на вопросы и пришлю фото.</textarea></div>'
    + '<div class="grid2"><div class="wz-field"><label>Город</label><input value="Тель-Авив"></div>'
    + '<div class="wz-field"><label>Язык объявления</label><select><option>Русский</option><option>עברית</option><option>English</option></select></div></div>';
  } else if(step===2){
    body='<div class="grid2"><div class="wz-field"><label>Цена / бюджет</label><input value="6000₪/мес"></div>'
    + '<div class="wz-field"><label>Контакт для бота</label><input value="054-555-1234"></div></div>'
    + '<div class="wz-field"><label>Фотографии</label><div class="photo-row">'
    +   '<div class="photo-cell filled"></div><div class="photo-cell filled"></div><div class="photo-cell filled"></div>'
    +   '<div class="photo-cell add"><span class="ico" data-i="plus"></span></div></div>'
    +   '<div class="small muted" style="margin-top:7px">Карусель до 10 фото — публикуется вместе с постом.</div></div>'
    + '<div class="wz-field"><label>Ссылка (необязательно)</label><input placeholder="https://…"></div>';
  } else {
    body='<div class="wz-field"><label>Вопросы скрининга</label><div class="stack tight">'
    +   '<input value="Какой у вас бюджет?"><input value="На какой срок аренда?"><input value="Оставьте номер телефона"></div>'
    +   '<button class="pill" style="margin-top:9px"><span class="ico" data-i="plus"></span> Добавить вопрос</button></div>'
    + '<div class="grid2"><div class="wz-field"><label>Критерий «горячий»</label><input value="Назвал бюджет + оставил телефон"></div>'
    + '<div class="wz-field"><label>Критерий «холодный»</label><input value="Без бюджета и контакта"></div></div>'
    + '<div class="wz-field"><label>Шаблон приветствия</label><textarea rows="2">Здравствуйте! Рад, что заинтересовало. Задам пару вопросов, чтобы подобрать лучший вариант.</textarea></div>';
  }
  return ''
  + '<div class="page-hero"><div><div class="eyebrow">Объявление · шаг '+step+' из 3</div><h1>'+['Что публикуем','Детали','Настройка бота'][step-1]+'</h1></div>'
  +   '<button class="pill" data-act="wz-close"><span class="ico" data-i="x"></span> Отмена</button></div>'
  + '<div class="wizard-steps">'+dots+'</div>'
  + '<div class="create-grid"><div class="card">'+body+'</div>'
  +   '<div class="card card-flat wz-preview"><div class="section-head"><h3 style="margin:0">Превью</h3><span class="badge">Telegram</span></div>'
  +     '<div class="fb-preview" id="wzPreview">Сдаётся 3-комн. во Флорентине\n\nСветлая 3-комнатная после ремонта. Рядом кафе и транспорт. Бюджет до 6000₪.\n\n— Напишите боту, отвечу за секунды.</div>'
  +     '<div class="chip-row"><span class="mini-chip ok">48 TG-групп</span><span class="mini-chip">AI-бот</span></div></div></div>'
  + '<div class="wizard-nav">'
  +   (step>1?'<button class="pill" data-act="wz-back">← Назад</button>':'<span></span>')
  +   (step<3?'<button class="btn" data-act="wz-next">Далее →</button>':'<button class="btn" data-act="wz-finish"><span class="ico" data-i="check"></span> Опубликовать</button>')
  + '</div>';
}

/* ════════════════════════════════════════════════════════════════════════════
   TELEGRAM — connection (done) + synced groups
   ════════════════════════════════════════════════════════════════════════════ */
function channelTg(state){
  if(state.tgView==='wizard') return tgWizard(state);
  var groups=D.TG_GROUPS.map(function(g,i){
    return '<label class="grp-row"><input type="checkbox" data-grp="'+i+'"'+(g.on?' checked':'')+'>'
    + '<span class="grp-name">'+g.name+'</span><span class="grp-folder">'+g.folder+'</span>'
    + '<span class="grp-members">'+g.members+'</span></label>';
  }).join('');
  return ''
  + '<div class="page-hero"><div><div class="eyebrow">Канал</div><h1>Telegram</h1></div>'
  +   '<span class="status status-ready" style="font-size:13px">● Подключено</span></div>'
  + '<div class="conn-steps-done">'
  +   stepDone('Аккаунт авторизован','+972 54-555-1234')
  +   stepDone('Сессия активна','обновлена сегодня')
  +   stepDone('Группы синхронизированы','64 группы')
  + '</div>'
  + '<div class="actions" style="margin-top:14px"><button class="pill" data-act="tg-reconnect"><span class="ico" data-i="refresh"></span> Переподключить аккаунт</button>'
  +   '<span class="muted small">Сессия Telegram живёт ~30 дней — при истечении попросим войти заново.</span></div>'
  + '<div class="section-head" style="margin-top:24px"><h2>Группы для постинга</h2><span class="badge">48 из 50 · лимит Pro</span></div>'
  + '<div class="limit-bar" style="margin-bottom:16px"><div class="limit-track"><i style="width:96%"></i></div>'
  +   '<span class="limit-label">48 из 50 каналов · тариф Pro</span><a class="pill" data-go="billing" href="#/billing">Повысить лимит</a></div>'
  + '<div class="card"><div class="grp-head"><span>Группа</span><span>Папка</span><span>Участники</span></div>'
  +   '<div class="grp-list">'+groups+'</div>'
  +   '<div class="actions" style="margin-top:14px"><button class="btn" data-act="tg-add">Добавить выбранные</button>'
  +     '<button class="pill" data-act="tg-resync"><span class="ico" data-i="refresh"></span> Пересинхронизировать</button></div></div>';
}

/* ── TG connect wizard: credentials → code (+2FA) → connected ─────────────── */
function tgWizard(state){
  var step=state.tgStep||1;
  var dots=[1,2,3].map(function(n){
    var st=n<step?'done':n===step?'active':'';
    return '<div class="wz-dot '+st+'"><span class="wz-num">'+(n<step?'<span class=\'ico\' data-i=\'checkbare\'></span>':n)+'</span>'
    + '<span class="wz-label">'+['Данные','Код','2FA'][n-1]+'</span></div>';
  }).join('<div class="wz-line"></div>');
  var body;
  if(step===1){
    body='<div class="alert">Получите <strong>api_id</strong> и <strong>api_hash</strong> на my.telegram.org → API development tools. Мы храним их в зашифрованном виде.</div>'
    + '<div class="grid2"><div class="wz-field"><label>api_id</label><input value="21834756"></div>'
    + '<div class="wz-field"><label>api_hash</label><input value="••••••••••••7c1f"></div></div>'
    + '<div class="wz-field"><label>Номер телефона (с кодом страны)</label><input value="+972 54-555-1234"></div>';
  } else if(step===2){
    body='<div class="alert success">Код отправлен в Telegram на +972 54-555-1234. Введите 5 цифр из сообщения.</div>'
    + '<div class="wz-field"><label>Код подтверждения</label><input class="code-input" maxlength="9" value="4 2 9 1 7"></div>'
    + '<div class="small muted" style="margin-top:8px">Не пришёл код? <a data-act="tg-resend" style="cursor:pointer">Отправить повторно</a> · осталось 0:48</div>';
  } else {
    body='<div class="alert">На аккаунте включён облачный пароль (2FA). Введите его, чтобы завершить вход.</div>'
    + '<div class="wz-field"><label>Облачный пароль 2FA</label><input type="password" value="demo1234"></div>'
    + '<div class="small muted" style="margin-top:8px">Подсказка: «Название первого питомца»</div>';
  }
  return ''
  + '<div class="page-hero"><div><div class="eyebrow">Telegram · подключение</div><h1>'+['Данные API','Код из Telegram','Пароль 2FA'][step-1]+'</h1></div>'
  +   '<button class="pill" data-act="tg-cancel"><span class="ico" data-i="x"></span> Отмена</button></div>'
  + '<div class="wizard-steps">'+dots+'</div>'
  + '<div class="create-grid"><div class="card">'+body+'</div>'
  +   '<div class="card card-flat"><div class="section-head"><h3 style="margin:0">Что это даёт</h3></div>'
  +     '<ul class="why-list"><li><span class="ico" data-i="check"></span>Автопостинг в десятки групп</li>'
  +       '<li><span class="ico" data-i="check"></span>Синхронизация ваших групп и папок</li>'
  +       '<li><span class="ico" data-i="check"></span>Бот отвечает на отклики от вашего имени</li></ul>'
  +     '<div class="lock-note"><span class="ico" data-i="lock"></span>Данные шифруются. Мы не читаем личные сообщения.</div></div></div>'
  + '<div class="wizard-nav">'
  +   (step>1?'<button class="pill" data-act="tg-back">← Назад</button>':'<button class="pill" data-act="tg-cancel">Отмена</button>')
  +   (step<3?'<button class="btn" data-act="tg-next">'+(step===1?'Получить код':'Подтвердить')+' →</button>':'<button class="btn" data-act="tg-finish"><span class="ico" data-i="check"></span> Завершить</button>')
  + '</div>';
}
function stepDone(t,sub){
  return '<div class="cstep done"><span class="cstep-tick"><span class="ico" data-i="checkbare"></span></span>'
  + '<div><div class="cstep-t">'+t+'</div><div class="cstep-s">'+sub+'</div></div></div>';
}

/* ════════════════════════════════════════════════════════════════════════════
   FACEBOOK — connect (OAuth or bulk URL)
   ════════════════════════════════════════════════════════════════════════════ */
function channelFb(state){
  var readyMap={ready:['status-ready','READY'],check:['status-manual_action_required','CHECK NEEDED'],format:['status-pending','FORMAT ONLY']};
  var fbRows=D.FB_SOURCES.map(function(s){
    var r=readyMap[s.ready]||readyMap.format;
    return '<tr><td><strong>'+s.name+'</strong></td><td>'+s.mode+'</td>'
    + '<td><span class="status '+r[0]+'">'+r[1]+'</span></td>'
    + '<td style="text-align:right"><button class="pill" data-act="src-test"><span class="ico" data-i="send"></span> Тест</button></td></tr>';
  }).join('');
  return ''
  + '<div class="page-hero"><div><div class="eyebrow">Канал</div><h1>Facebook</h1>'
  +   '<p class="muted">FB не любит автопостинг — мы готовим текст, вы вставляете в пару кликов, с рандомными задержками.</p></div>'
  +   '<span class="status status-pending" style="font-size:13px">○ Не подключено</span></div>'
  + '<div class="alert">Режим пилота: assisted-manual — бот формирует пост и ведёт переписку, публикацию подтверждаете вы.</div>'
  + '<div class="grid2" style="align-items:start;margin-top:6px">'
  +   '<div class="card"><div class="fb-opt-ic" data-i="link"></div><h3>Вариант 1 · OAuth</h3>'
  +     '<p class="muted small">Войдите через Facebook и разрешите доступ к спискам ваших групп — подтянем автоматически.</p>'
  +     '<button class="btn" data-act="fb-oauth" style="margin-top:12px;background:#1877F2;border-color:#1877F2"><span class="ico" data-i="fb"></span> Войти через Facebook</button></div>'
  +   '<div class="card"><div class="fb-opt-ic" data-i="doc"></div><h3>Вариант 2 · Вставка ссылок</h3>'
  +     '<p class="muted small">Вставьте ссылки на группы построчно — добавим как точки ручного постинга.</p>'
  +     '<textarea rows="4" placeholder="https://facebook.com/groups/..." style="margin-top:10px"></textarea>'
  +     '<button class="btn" data-act="fb-urls" style="margin-top:10px">Добавить группы</button></div>'
  + '</div>'
  + '<div class="perm-note"><span class="ico" data-i="alert"></span><div><strong>Мало прав?</strong> Если Facebook не показал ваши группы — выдайте доступ <em>Groups</em> и <em>Pages</em> в окне входа. Без них синхронизация вернёт пустой список.</div></div>'
  + '<div class="section-head" style="margin-top:24px"><h2>Существующие источники</h2><span class="badge">режим assisted-manual</span></div>'
  + '<div class="table-wrap"><table class="table"><thead><tr><th>Источник</th><th>Режим</th><th>Готовность</th><th></th></tr></thead><tbody>'+fbRows+'</tbody></table></div>'
  + '<div class="src-hint"><span class="ico" data-i="lock"></span>Ручной режим защищает аккаунт от блокировок: бот готовит пост, вы вставляете его в пару кликов с рандомной задержкой.</div>';
}

/* ════════════════════════════════════════════════════════════════════════════
   НАЗНАЧЕНИЯ — unified posting targets
   ════════════════════════════════════════════════════════════════════════════ */
function sources(state){
  var readyMap={ready:['status-ready','READY'],check:['status-manual_action_required','CHECK NEEDED'],format:['status-pending','FORMAT ONLY']};
  var rows=D.SOURCES.map(function(s){
    var r=readyMap[s.ready];
    return '<tr><td><strong>'+s.name+'</strong></td><td>'+s.platform+'</td><td>'+s.kind+'</td>'
    + '<td>'+s.mode+'</td><td><span class="status '+r[0]+'">'+r[1]+'</span></td>'
    + '<td style="text-align:right"><button class="pill" data-act="src-test"><span class="ico" data-i="send"></span> Тест</button></td></tr>';
  }).join('');
  return ''
  + '<div class="page-hero"><div><div class="eyebrow">Каналы</div><h1>Назначения</h1>'
  +   '<p class="muted">Единое управление точками постинга — где и как публикуются объявления.</p></div>'
  +   '<button class="pill" data-act="src-check-all"><span class="ico" data-i="refresh"></span> Проверить все</button></div>'
  + '<div class="readiness">'
  +   '<div class="ready-card tg"><span class="rc-ic" data-i="send"></span><div style="flex:1"><div class="rc-name">Telegram · 48</div><div class="rc-sub">готовы к автопостингу</div></div><span class="status status-ready">Готовы</span></div>'
  +   '<div class="ready-card fb"><span class="rc-ic" data-i="fb"></span><div style="flex:1"><div class="rc-name">Facebook · 22</div><div class="rc-sub">ручной режим</div></div><span class="status status-manual_action_required">Ручные</span></div>'
  + '</div>'
  + '<div class="card" style="margin-bottom:22px"><h3 style="margin-top:0">Добавить назначение</h3>'
  +   '<div class="src-form"><select><option>Telegram</option><option>Facebook</option></select>'
  +     '<select><option>Группа</option><option>Канал</option><option>Страница</option></select>'
  +     '<input placeholder="Ярлык (напр. «Аренда центр»)"><input placeholder="URL или @username">'
  +     '<button class="btn" data-act="src-add">Добавить</button></div></div>'
  + '<div class="section-head"><h2>Все назначения</h2><span class="badge">'+D.SOURCES.length+' показано из 70</span></div>'
  + '<div class="table-wrap"><table class="table"><thead><tr><th>Название</th><th>Платформа</th><th>Вид</th><th>Режим</th><th>Готовность</th><th></th></tr></thead><tbody>'+rows+'</tbody></table></div>';
}

/* ── PHASE placeholders (honest, with planned content) ────────────────────── */
var PHASE={
 ads:{ic:'doc',desc:'CRUD объявлений с мастером в 3 шага (что → детали → бот), мультивертикаль: наём, недвижимость, авто, услуги.',
   items:['Список объявлений с превью поста и воронкой','Мастер: заголовок, текст, город, цена/зарплата, фото-карусель','Скрининг-вопросы и критерии hot/cold для бота','Шаблоны приветствия / отказа / успеха']},
 'channel-tg':{ic:'send',desc:'Подключение Telegram: визард авторизации и выбор групп для постинга.',
   items:['Визард: api_id / api_hash → телефон → код (+2FA)','Синхронизация групп с чекбоксами по папкам','Список активных источников','Состояния: ждём код / 2FA / сессия истекла / лимит']},
 'channel-fb':{ic:'fb',desc:'Подключение Facebook: OAuth-синхронизация страниц или массовая вставка URL групп.',
   items:['OAuth-синк страниц или вставка ссылок построчно','Ручной assisted-режим (защита от банов)','Список FB-источников','Состояния: не настроен / мало прав / лимит']},
 sources:{ic:'target',desc:'Единое управление точками постинга — где и как публикуются объявления.',
   items:['Сводные карточки: TG готовы / FB ручные','Форма добавления (платформа, режим, ярлык, URL)','Таблица готовности: READY / CHECK NEEDED / FORMAT ONLY','Действия: проверить, тест-сообщение, проверить все']},
 bot:{ic:'bot',desc:'Настройки AI-бота: тон, язык, промты, шаблоны и тестовый прогон.',
   items:['Тон: профессиональный / дружелюбный / строгий','Позитивный и негативный промт','Шаблоны: приветствие / отказ / успех','Тест бота: ввод «как от кандидата» → ответ']},
 analytics:{ic:'chart',desc:'Аналитика воронки, конверсии и эффективности объявлений.',
   items:['KPI: всего / прошли / отклонены / закрыто','Воронка конверсии с разбивкой по языкам','Эффективность объявлений','Активность за 7 дней']},
 company:{ic:'users',desc:'Профиль компании и управление командой.',
   items:['Поля компании: имя, тип, контакты, лого','Куда слать горячих лидов (Telegram chat id, email)','Команда: участники, роли, добавить / деактивировать','Статус подключения Telegram']},
 billing:{ic:'card',desc:'Тарифы и подписка.',
   items:['Starter 299₪ · 1 объявление, 10 каналов','Pro 899₪ · 5 объявлений, 50 каналов, планировщик, аналитика','Agency 1999₪ · безлимит, мультикомпания, API, white-label','Триал 14 дней, гейт при истечении, Stripe-checkout']}
};
function phase(id, meta){
  var p=PHASE[id]||{ic:'grid',desc:'',items:[]};
  var items=p.items.map(function(t){return '<li><span class="ico" data-i="check"></span><span>'+t+'</span></li>';}).join('');
  return '<div class="page-hero"><div><div class="eyebrow">'+(meta.phase===2?'Фаза 2':'Фаза 3')+'</div><h1>'+meta.title+'</h1></div></div>'
  + '<div class="soon"><span class="soon-ic" data-i="'+p.ic+'"></span><h3>'+meta.title+' — в разработке</h3>'
  + '<p>'+p.desc+'</p><ul>'+items+'</ul>'
  + '<span class="soon-phase">Запланировано · Фаза '+meta.phase+'</span></div>';
}

return {leads:leads,leadListHTML:leadListHTML,leadDetailHTML:leadDetailHTML,
  dashboard:dashboard,campaigns:campaigns,ads:ads,channelTg:channelTg,channelFb:channelFb,sources:sources,
  phase:phase,clsBadge:clsBadge};
})();
