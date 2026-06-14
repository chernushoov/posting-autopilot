/* ════════════════════════════════════════════════════════════════════════════
   Posting Autopilot — Cabinet SCREEN templates · Phase 3
   AI-бот · Аналитика · Компания и команда · Биллинг   (return HTML strings)
   ════════════════════════════════════════════════════════════════════════════ */
window.PAScreens2 = (function(){
"use strict";
var D = window.PA;

function kpi(ic,label,val,sub,flat){
  return '<div class="kpi"><div class="k-top"><span class="k-ic" data-i="'+ic+'"></span><span class="k-label">'+label+'</span></div>'
  + '<div class="k-val">'+val+'</div><div class="k-sub'+(flat?' flat':'')+'">'+sub+'</div></div>';
}

/* ════════════════════════════════════════════════════════════════════════════
   AI-БОТ — тон, язык, промты, шаблоны, тест
   ════════════════════════════════════════════════════════════════════════════ */
function bot(state){
  var B=D.BOT;
  var tones=[['professional','Профессиональный'],['friendly','Дружелюбный'],['strict','Строгий']];
  var toneBtns=tones.map(function(t){
    return '<button class="seg-opt'+(B.tone===t[0]?' active':'')+'" data-bot-tone="'+t[0]+'">'+t[1]+'</button>';
  }).join('');
  var langs=[['auto','Авто (язык клиента)'],['ru','Русский'],['he','עברית'],['en','English']];
  var langOpts=langs.map(function(l){return '<option value="'+l[0]+'"'+(B.lang===l[0]?' selected':'')+'>'+l[1]+'</option>';}).join('');
  return ''
  + '<div class="page-hero"><div><div class="eyebrow">Настройка</div><h1>AI-бот</h1>'
  +   '<p class="muted">Бот общается с откликами, отсеивает спам и помечает горячих лидов.</p></div>'
  +   '<button class="btn" data-act="bot-save"><span class="ico" data-i="check"></span> Сохранить</button></div>'
  + '<div class="bot-layout">'
  +   '<div class="stack">'
  +     '<div class="card"><h3 style="margin-top:0">Поведение</h3>'
  +       '<div class="wz-field"><label>Тон общения</label><div class="seg-pills">'+toneBtns+'</div></div>'
  +       '<div class="wz-field"><label>Язык ответов</label><select data-bot-lang>'+langOpts+'</select>'
  +         '<div class="small muted" style="margin-top:6px">В режиме «Авто» бот отвечает на языке клиента — RU / HE / EN.</div></div></div>'
  +     '<div class="card"><h3 style="margin-top:0">Критерии классификации</h3>'
  +       '<div class="wz-field"><label><span class="dot-hot"></span> Когда лид «горячий» (позитивный промт)</label>'
  +         '<textarea rows="3">'+B.positive+'</textarea></div>'
  +       '<div class="wz-field"><label><span class="dot-cold"></span> Когда лид «холодный» (негативный промт)</label>'
  +         '<textarea rows="3">'+B.negative+'</textarea></div></div>'
  +     '<div class="card"><h3 style="margin-top:0">Шаблоны сообщений</h3>'
  +       '<div class="wz-field"><label>Приветствие</label><textarea rows="2">'+B.greet+'</textarea></div>'
  +       '<div class="wz-field"><label>Отказ</label><textarea rows="2">'+B.reject+'</textarea></div>'
  +       '<div class="wz-field"><label>Успех (контакт получен)</label><textarea rows="2">'+B.success+'</textarea></div></div>'
  +   '</div>'
  +   '<div class="bot-test card">'
  +     '<div class="section-head"><h3 style="margin:0">Тест бота</h3><span class="badge">демо</span></div>'
  +     '<p class="small muted" style="margin:0 0 4px">Напишите как кандидат — бот ответит и покажет класс.</p>'
  +     '<div class="chat bot-chat" id="botChat">'
  +       '<div class="msg me"><div class="bubble">'+B.greet+'</div></div>'
  +     '</div>'
  +     '<div class="bot-input"><input id="botInput" placeholder="до 6000₪, телефон 054…"><button class="btn" data-act="bot-send"><span class="ico" data-i="send"></span></button></div>'
  +     '<div class="bot-suggest">'
  +       '<button class="mini-chip" data-bot-fill="Ищу 3-комнатную, бюджет 6000₪, телефон 054-555-1234">Горячий пример</button>'
  +       '<button class="mini-chip" data-bot-fill="Просто смотрю цены">Холодный пример</button></div>'
  +   '</div>'
  + '</div>';
}

/* ════════════════════════════════════════════════════════════════════════════
   АНАЛИТИКА — KPI, воронка, языки, операции, эффективность, 7 дней
   ════════════════════════════════════════════════════════════════════════════ */
function analytics(state){
  var A=D.ANALYTICS;
  var kpis=A.kpi.map(function(k){return kpi(k.ic,k.label,k.val,k.sub,!k.up);}).join('');
  var fmax=A.funnel[0].val;
  var funnel=A.funnel.map(function(f){
    return '<div class="fn-row"><div class="fn-label">'+f.label+'</div>'
    + '<div class="fn-track"><div class="fn-fill" style="width:'+Math.max(8,f.val/fmax*100)+'%;background:'+f.color+'">'+f.val+'</div></div></div>';
  }).join('');
  var langs=A.langs.map(function(l){
    return '<div class="lang-row"><div class="lang-top"><span>'+l.label+'</span><span class="muted small">'+l.val+' · '+l.pct+'%</span></div>'
    + '<div class="lang-track"><i style="width:'+l.pct+'%;background:'+l.color+'"></i></div></div>';
  }).join('');
  var dmax=Math.max.apply(null,A.days.map(function(d){return d.v;}));
  var bars=A.days.map(function(d){
    return '<div class="bar-col"><div class="bar-val">'+d.v+'</div><div class="bar" style="height:'+Math.max(6,d.v/dmax*100)+'%"></div><div class="bar-lbl">'+d.d+'</div></div>';
  }).join('');
  var ops=A.ops.map(function(o){
    return '<div class="op-row"><span class="op-label">'+o.label+'</span><span class="op-val">'+o.val+'</span></div>';
  }).join('');
  var adRows=A.ads.map(function(a){
    return '<tr><td><strong>'+a.title+'</strong></td><td>'+a.leads+'</td><td>'+a.conv+'</td>'
    + '<td style="width:130px"><div class="mini-track"><i style="width:'+a.pct+'%"></i></div></td></tr>';
  }).join('');
  return ''
  + '<div class="page-hero"><div><div class="eyebrow">Обзор</div><h1>Аналитика</h1>'
  +   '<p class="muted">Воронка, конверсия и эффективность объявлений за период.</p></div>'
  +   '<div class="actions"><select class="period-sel"><option>7 дней</option><option>30 дней</option><option>Всё время</option></select>'
  +     '<button class="pill" data-act="export"><span class="ico" data-i="download"></span> Экспорт</button></div></div>'
  + '<div class="kpi-grid">'+kpis+'</div>'
  + '<div class="grid2" style="align-items:start">'
  +   '<div class="card"><div class="section-head"><h3 style="margin:0">Воронка конверсии</h3><span class="badge">7 дней</span></div><div class="funnel">'+funnel+'</div></div>'
  +   '<div class="card"><div class="section-head"><h3 style="margin:0">Разбивка по языкам</h3></div><div class="lang-list">'+langs+'</div></div>'
  + '</div>'
  + '<div class="card" style="margin-top:18px"><div class="section-head"><h3 style="margin:0">Активность за 7 дней</h3><span class="badge">публикаций / день</span></div>'
  +   '<div class="bar-chart">'+bars+'</div></div>'
  + '<div class="grid2" style="align-items:start;margin-top:18px">'
  +   '<div class="card"><div class="section-head"><h3 style="margin:0">Сводка операций</h3></div><div class="op-list">'+ops+'</div></div>'
  +   '<div class="card"><div class="section-head"><h3 style="margin:0">Эффективность объявлений</h3></div>'
  +     '<div class="table-wrap"><table class="table table-flat"><thead><tr><th>Объявление</th><th>Лиды</th><th>Конв.</th><th></th></tr></thead><tbody>'+adRows+'</tbody></table></div></div>'
  + '</div>';
}

/* ════════════════════════════════════════════════════════════════════════════
   КОМПАНИЯ И КОМАНДА
   ════════════════════════════════════════════════════════════════════════════ */
function company(state){
  var c=D.COMPANIES.filter(function(x){return x.id===state.company;})[0]||D.COMPANIES[0];
  var team=D.TEAM.map(function(m){
    var canManage=!m.you;
    return '<tr'+(m.active?'':' class="row-off"')+'><td><div class="tm-cell"><span class="tm-ava">'+m.name.charAt(0)+'</span>'
    + '<div><div class="tm-name">'+m.name+(m.you?' <span class="tm-badge">вы</span>':'')+'</div><div class="small muted">'+m.email+'</div></div></div></td>'
    + '<td><span class="role-chip'+(m.role==='Владелец'?' owner':'')+'">'+m.role+'</span></td>'
    + '<td>'+(m.active?'<span class="status status-ready">Активен</span>':'<span class="status status-pending">Отключён</span>')+'</td>'
    + '<td style="text-align:right">'+(canManage
        ? '<button class="pill'+(m.active?' danger':'')+'" data-act="team-toggle">'+(m.active?'Деактивировать':'Включить')+'</button>'
        : '<span class="small muted">—</span>')+'</td></tr>';
  }).join('');
  return ''
  + '<div class="page-hero"><div><div class="eyebrow">Настройка</div><h1>Компания и команда</h1>'
  +   '<p class="muted">Профиль компании, маршрутизация горячих лидов и доступы команды.</p></div>'
  +   '<button class="btn" data-act="company-save"><span class="ico" data-i="check"></span> Сохранить</button></div>'
  + '<div class="grid2" style="align-items:start">'
  +   '<div class="card"><h3 style="margin-top:0">Профиль компании</h3>'
  +     '<div class="company-id"><span class="cmp-logo-lg">'+c.logo+'</span>'
  +       '<button class="pill" data-act="company-logo"><span class="ico" data-i="edit"></span> Логотип</button></div>'
  +     '<div class="wz-field"><label>Название</label><input value="'+c.name+'"></div>'
  +     '<div class="grid2"><div class="wz-field"><label>Вертикаль</label><select><option>Недвижимость</option><option>Наём</option><option>Авто</option><option>Услуги</option></select></div>'
  +       '<div class="wz-field"><label>Город</label><input value="Тель-Авив"></div></div>'
  +     '<div class="wz-field"><label>Телефон компании</label><input value="+972 54-555-1234"></div></div>'
  +   '<div class="card"><h3 style="margin-top:0">Куда слать горячих лидов</h3>'
  +     '<p class="small muted" style="margin:-4px 0 6px">Как только бот находит горячего лида — мгновенное уведомление сюда.</p>'
  +     '<div class="route-row ok"><span class="ico" data-i="send"></span><div style="flex:1"><div class="wz-field" style="margin:0"><label>Telegram chat id</label><input value="-1001884220117"></div></div><span class="status status-ready">Задан</span></div>'
  +     '<div class="route-row warn"><span class="ico" data-i="mail"></span><div style="flex:1"><div class="wz-field" style="margin:0"><label>Email (резерв)</label><input placeholder="hot@company.com — не указан"></div></div><span class="status status-pending">Нет</span></div>'
  +     '<div class="tg-status-row"><span class="ico" data-i="check"></span>Telegram-бот уведомлений подключён · @PostingAutopilotBot</div></div>'
  + '</div>'
  + '<div class="section-head" style="margin-top:24px"><h2>Команда</h2>'
  +   '<button class="btn" data-act="team-add"><span class="ico" data-i="plus"></span> Добавить участника</button></div>'
  + '<div class="owner-note"><span class="ico" data-i="lock"></span>Управлять участниками и ролями может только владелец аккаунта.</div>'
  + '<div class="table-wrap"><table class="table"><thead><tr><th>Участник</th><th>Роль</th><th>Статус</th><th></th></tr></thead><tbody>'+team+'</tbody></table></div>'
  + '<div class="section-head" style="margin-top:24px"><h2>Компании</h2></div>'
  + '<div class="cmp-switch-note"><div><strong>Активна:</strong> '+c.name+' · '+c.type+'</div>'
  +   '<button class="pill" data-act="open-switcher"><span class="ico" data-i="building"></span> Переключить компанию</button></div>';
}

/* ════════════════════════════════════════════════════════════════════════════
   БИЛЛИНГ — тарифы, триал, апгрейд, истёкший триал
   ════════════════════════════════════════════════════════════════════════════ */
function billing(state){
  var T=D.TRIAL, expired=!!state.trialExpired;
  var plans=D.PLANS.map(function(p){
    var feats=p.feats.map(function(f){return '<li><span class="ico" data-i="checkbare"></span>'+f+'</li>';}).join('');
    var cta=p.current
      ? '<button class="btn-outline plan-cta" data-act="plan-manage">Текущий тариф</button>'
      : '<button class="btn plan-cta" data-act="plan-upgrade" data-plan="'+p.id+'">Перейти на '+p.name+'</button>';
    return '<div class="plan-card'+(p.featured?' featured':'')+(p.current?' current':'')+'">'
    + (p.featured?'<div class="plan-tag">Популярный</div>':'')
    + '<div class="plan-name">'+p.name+'</div>'
    + '<div class="plan-price">'+p.price+'<span>/мес</span></div>'
    + '<div class="plan-tagline">'+p.tagline+'</div>'
    + '<ul class="plan-feats">'+feats+'</ul>'
    + cta+'</div>';
  }).join('');
  var banner = expired
    ? '<div class="trial-banner expired"><div class="tb-ic" data-i="lock"></div>'
      + '<div class="tb-body"><div class="tb-title">Пробный период истёк</div>'
      + '<div class="tb-sub">Автопостинг на паузе, лиды и аналитика только для чтения. Выберите тариф, чтобы возобновить работу.</div></div>'
      + '<button class="btn" data-act="plan-upgrade" data-plan="pro">Возобновить · Pro</button></div>'
    : '<div class="trial-banner"><div class="tb-ic" data-i="clock"></div>'
      + '<div class="tb-body"><div class="tb-title">Пробный период '+T.plan+' · осталось '+T.days+' дней</div>'
      + '<div class="tb-sub">После окончания автопостинг встанет на паузу. Перейдите на платный тариф заранее.</div></div>'
      + '<button class="btn" data-act="plan-upgrade" data-plan="pro">Активировать сейчас</button></div>';
  return ''
  + '<div class="page-hero"><div><div class="eyebrow">Настройка</div><h1>Биллинг и тарифы</h1>'
  +   '<p class="muted">Тариф определяет лимиты объявлений, каналов и доступ к аналитике.</p></div>'
  +   '<button class="pill" data-act="trial-toggle">'+(expired?'← Вернуть триал':'Показать «триал истёк»')+'</button></div>'
  + banner
  + '<div class="plans-grid">'+plans+'</div>'
  + '<div class="billing-foot">'
  +   '<div class="bf-item"><span class="ico" data-i="card"></span><div><div class="bf-t">Способ оплаты</div><div class="small muted">Visa •••• 4242 · через Stripe</div></div><button class="pill" data-act="pay-method">Изменить</button></div>'
  +   '<div class="bf-item"><span class="ico" data-i="doc"></span><div><div class="bf-t">Счета и история</div><div class="small muted">Чеки приходят на email после оплаты</div></div><button class="pill" data-act="invoices">Открыть</button></div>'
  + '</div>';
}

return {bot:bot,analytics:analytics,company:company,billing:billing};
})();
