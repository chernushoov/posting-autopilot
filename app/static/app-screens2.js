/* ════════════════════════════════════════════════════════════════════════════
   Posting Autopilot — SCREEN templates · Phase 3 · i18n
   AI-бот · Аналитика · Компания и команда · Биллинг
   ════════════════════════════════════════════════════════════════════════════ */
window.PAScreens2 = (function(){
"use strict";
var D = window.PA;
function t(k,v){ return window.PA_I18N.t(k,v); }

function kpi(ic,label,val,sub,flat){
  return '<div class="kpi"><div class="k-top"><span class="k-ic" data-i="'+ic+'"></span><span class="k-label">'+label+'</span></div>'
  + '<div class="k-val">'+val+'</div><div class="k-sub'+(flat?' flat':'')+'">'+sub+'</div></div>';
}

/* ── AI-БОТ ───────────────────────────────────────────────────────────────── */
function bot(state){
  var B=D.BOT;
  var tones=[['professional',t('bot.t.pro')],['friendly',t('bot.t.friendly')],['strict',t('bot.t.strict')]];
  var toneBtns=tones.map(function(x){
    return '<button class="seg-opt'+(B.tone===x[0]?' active':'')+'" data-bot-tone="'+x[0]+'">'+x[1]+'</button>';
  }).join('');
  var langs=[['auto',t('bot.la.auto')],['ru',t('bot.la.ru')],['he',t('bot.la.he')],['en',t('bot.la.en')]];
  var langOpts=langs.map(function(l){return '<option value="'+l[0]+'"'+(B.lang===l[0]?' selected':'')+'>'+l[1]+'</option>';}).join('');
  return ''
  + '<div class="page-hero"><div><div class="eyebrow">'+t('bot.eyebrow')+'</div><h1>'+t('title.bot')+'</h1>'
  +   '<p class="muted">'+t('bot.sub')+'</p></div>'
  +   '<button class="btn" data-act="bot-save"><span class="ico" data-i="check"></span> '+t('c.save')+'</button></div>'
  + '<div class="bot-layout">'
  +   '<div class="stack">'
  +     '<div class="card"><h3 style="margin-top:0">'+t('bot.behavior')+'</h3>'
  +       '<div class="wz-field"><label>'+t('bot.tone')+'</label><div class="seg-pills">'+toneBtns+'</div></div>'
  +       '<div class="wz-field"><label>'+t('bot.lang')+'</label><select data-bot-lang>'+langOpts+'</select>'
  +         '<div class="small muted" style="margin-top:6px">'+t('bot.lang_h')+'</div></div></div>'
  +     '<div class="card"><h3 style="margin-top:0">'+t('bot.crit')+'</h3>'
  +       '<div class="wz-field"><label><span class="dot-hot"></span> '+t('bot.pos')+'</label>'
  +         '<textarea rows="3">'+B.positive+'</textarea></div>'
  +       '<div class="wz-field"><label><span class="dot-cold"></span> '+t('bot.neg')+'</label>'
  +         '<textarea rows="3">'+B.negative+'</textarea></div></div>'
  +     '<div class="card"><h3 style="margin-top:0">'+t('bot.tpl')+'</h3>'
  +       '<div class="wz-field"><label>'+t('bot.greet')+'</label><textarea rows="2">'+B.greet+'</textarea></div>'
  +       '<div class="wz-field"><label>'+t('bot.reject')+'</label><textarea rows="2">'+B.reject+'</textarea></div>'
  +       '<div class="wz-field"><label>'+t('bot.success')+'</label><textarea rows="2">'+B.success+'</textarea></div></div>'
  +   '</div>'
  +   '<div class="bot-test card">'
  +     '<div class="section-head"><h3 style="margin:0">'+t('bot.test')+'</h3><span class="badge">'+t('c.demo')+'</span></div>'
  +     '<p class="small muted" style="margin:0 0 4px">'+t('bot.test_h')+'</p>'
  +     '<div class="chat bot-chat" id="botChat">'
  +       '<div class="msg me"><div class="bubble">'+B.greet+'</div></div>'
  +     '</div>'
  +     '<div class="bot-input"><input id="botInput" placeholder="'+t('bot.input_ph')+'"><button class="btn" data-act="bot-send"><span class="ico" data-i="send"></span></button></div>'
  +     '<div class="bot-suggest">'
  +       '<button class="mini-chip" data-bot-fill="'+t('bot.fill_hot')+'">'+t('bot.ex_hot')+'</button>'
  +       '<button class="mini-chip" data-bot-fill="'+t('bot.fill_cold')+'">'+t('bot.ex_cold')+'</button></div>'
  +   '</div>'
  + '</div>';
}

/* ── АНАЛИТИКА ────────────────────────────────────────────────────────────── */
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
  + '<div class="page-hero"><div><div class="eyebrow">'+t('an.eyebrow')+'</div><h1>'+t('title.analytics')+'</h1>'
  +   '<p class="muted">'+t('an.sub')+'</p></div>'
  +   '<div class="actions"><select class="period-sel"><option>'+t('an.p.7')+'</option><option>'+t('an.p.30')+'</option><option>'+t('an.p.all')+'</option></select>'
  +     '<button class="pill" data-act="export"><span class="ico" data-i="download"></span> '+t('c.export')+'</button></div></div>'
  + '<div class="kpi-grid">'+kpis+'</div>'
  + '<div class="grid2" style="align-items:start">'
  +   '<div class="card"><div class="section-head"><h3 style="margin:0">'+t('an.funnel')+'</h3><span class="badge">'+t('an.p.7')+'</span></div><div class="funnel">'+funnel+'</div></div>'
  +   '<div class="card"><div class="section-head"><h3 style="margin:0">'+t('an.langs')+'</h3></div><div class="lang-list">'+langs+'</div></div>'
  + '</div>'
  + '<div class="card" style="margin-top:18px"><div class="section-head"><h3 style="margin:0">'+t('an.activity')+'</h3><span class="badge">'+t('an.per_day')+'</span></div>'
  +   '<div class="bar-chart">'+bars+'</div></div>'
  + '<div class="grid2" style="align-items:start;margin-top:18px">'
  +   '<div class="card"><div class="section-head"><h3 style="margin:0">'+t('an.ops')+'</h3></div><div class="op-list">'+ops+'</div></div>'
  +   '<div class="card"><div class="section-head"><h3 style="margin:0">'+t('an.ad_eff')+'</h3></div>'
  +     '<div class="table-wrap"><table class="table table-flat"><thead><tr><th>'+t('an.th.ad')+'</th><th>'+t('an.th.leads')+'</th><th>'+t('an.th.conv')+'</th><th></th></tr></thead><tbody>'+adRows+'</tbody></table></div></div>'
  + '</div>';
}

/* ── КОМПАНИЯ И КОМАНДА ───────────────────────────────────────────────────── */
function company(state){
  var c=D.COMPANIES.filter(function(x){return x.id===state.company;})[0]||D.COMPANIES[0];
  var team=D.TEAM.map(function(m){
    var canManage=!m.you;
    return '<tr'+(m.active?'':' class="row-off"')+'><td><div class="tm-cell"><span class="tm-ava">'+m.name.charAt(0)+'</span>'
    + '<div><div class="tm-name">'+m.name+(m.you?' <span class="tm-badge">'+t('co.you')+'</span>':'')+'</div><div class="small muted">'+m.email+'</div></div></div></td>'
    + '<td><span class="role-chip'+(m.you?' owner':'')+'">'+m.role+'</span></td>'
    + '<td>'+(m.active?'<span class="status status-ready">'+t('st.active_m')+'</span>':'<span class="status status-pending">'+t('st.off')+'</span>')+'</td>'
    + '<td style="text-align:right">'+(canManage
        ? '<button class="pill'+(m.active?' danger':'')+'" data-act="team-toggle">'+(m.active?t('co.deactivate'):t('co.activate'))+'</button>'
        : '<span class="small muted">—</span>')+'</td></tr>';
  }).join('');
  return ''
  + '<div class="page-hero"><div><div class="eyebrow">'+t('co.eyebrow')+'</div><h1>'+t('title.company')+'</h1>'
  +   '<p class="muted">'+t('co.sub')+'</p></div>'
  +   '<button class="btn" data-act="company-save"><span class="ico" data-i="check"></span> '+t('c.save')+'</button></div>'
  + '<div class="grid2" style="align-items:start">'
  +   '<div class="card"><h3 style="margin-top:0">'+t('co.profile')+'</h3>'
  +     '<div class="company-id"><span class="cmp-logo-lg">'+c.logo+'</span>'
  +       '<button class="pill" data-act="company-logo"><span class="ico" data-i="edit"></span> '+t('co.logo')+'</button></div>'
  +     '<div class="wz-field"><label>'+t('co.name')+'</label><input value="'+c.name+'"></div>'
  +     '<div class="grid2"><div class="wz-field"><label>'+t('co.vertical')+'</label><select><option>'+t('vert.home')+'</option><option>'+t('vert.users')+'</option><option>'+t('vert.car')+'</option><option>'+t('vert.wrench')+'</option></select></div>'
  +       '<div class="wz-field"><label>'+t('co.city')+'</label><input value="'+(D.ADS[0]?D.ADS[0].city:'')+'"></div></div>'
  +     '<div class="wz-field"><label>'+t('co.phone')+'</label><input value="+972 54-555-1234"></div></div>'
  +   '<div class="card"><h3 style="margin-top:0">'+t('co.route')+'</h3>'
  +     '<p class="small muted" style="margin:-4px 0 6px">'+t('co.route_p')+'</p>'
  +     '<div class="route-row ok"><span class="ico" data-i="send"></span><div style="flex:1"><div class="wz-field" style="margin:0"><label>'+t('co.tg_id')+'</label><input value="-1001884220117"></div></div><span class="status status-ready">'+t('co.set')+'</span></div>'
  +     '<div class="route-row warn"><span class="ico" data-i="mail"></span><div style="flex:1"><div class="wz-field" style="margin:0"><label>'+t('co.email')+'</label><input placeholder="'+t('co.email_ph')+'"></div></div><span class="status status-pending">'+t('co.none')+'</span></div>'
  +     '<div class="tg-status-row"><span class="ico" data-i="check"></span>'+t('co.tg_status')+'</div></div>'
  + '</div>'
  + '<div class="section-head" style="margin-top:24px"><h2>'+t('co.team')+'</h2>'
  +   '<button class="btn" data-act="team-add"><span class="ico" data-i="plus"></span> '+t('co.add_member')+'</button></div>'
  + '<div class="owner-note"><span class="ico" data-i="lock"></span>'+t('co.owner_note')+'</div>'
  + '<div class="table-wrap"><table class="table"><thead><tr><th>'+t('co.th.member')+'</th><th>'+t('co.th.role')+'</th><th>'+t('co.th.status')+'</th><th></th></tr></thead><tbody>'+team+'</tbody></table></div>'
  + '<div class="section-head" style="margin-top:24px"><h2>'+t('co.companies')+'</h2></div>'
  + '<div class="cmp-switch-note"><div><strong>'+t('co.active')+'</strong> '+c.name+' · '+c.type+'</div>'
  +   '<button class="pill" data-act="open-switcher"><span class="ico" data-i="building"></span> '+t('co.switch')+'</button></div>';
}

/* ── БИЛЛИНГ ──────────────────────────────────────────────────────────────── */
function billing(state){
  var T=D.TRIAL, expired=!!(T && T.expired);
  var plans=D.PLANS.map(function(p){
    var feats=p.feats.map(function(f){return '<li><span class="ico" data-i="checkbare"></span>'+f+'</li>';}).join('');
    var cta=p.current
      ? '<button class="btn-outline plan-cta" data-act="plan-manage">'+t('bl.current')+'</button>'
      : '<button class="btn plan-cta" data-act="plan-upgrade" data-plan="'+p.id+'">'+t('bl.go_to',{plan:p.name})+'</button>';
    return '<div class="plan-card'+(p.featured?' featured':'')+(p.current?' current':'')+'">'
    + (p.featured?'<div class="plan-tag">'+t('bl.popular')+'</div>':'')
    + '<div class="plan-name">'+p.name+'</div>'
    + '<div class="plan-price">'+p.price+'<span>'+t('bl.per')+'</span></div>'
    + '<div class="plan-tagline">'+p.tagline+'</div>'
    + '<ul class="plan-feats">'+feats+'</ul>'
    + cta+'</div>';
  }).join('');
  var banner = expired
    ? '<div class="trial-banner expired"><div class="tb-ic" data-i="lock"></div>'
      + '<div class="tb-body"><div class="tb-title">'+t('bl.exp_title')+'</div>'
      + '<div class="tb-sub">'+t('bl.exp_sub')+'</div></div>'
      + '<button class="btn" data-act="plan-upgrade" data-plan="pro">'+t('bl.resume')+'</button></div>'
    : '<div class="trial-banner"><div class="tb-ic" data-i="clock"></div>'
      + '<div class="tb-body"><div class="tb-title">'+t('bl.trial_title',{plan:T.plan,n:T.days})+'</div>'
      + '<div class="tb-sub">'+t('bl.trial_sub')+'</div></div>'
      + '<button class="btn" data-act="plan-upgrade" data-plan="pro">'+t('bl.activate')+'</button></div>';
  return ''
  + '<div class="page-hero"><div><div class="eyebrow">'+t('bl.eyebrow')+'</div><h1>'+t('title.billing')+'</h1>'
  +   '<p class="muted">'+t('bl.sub')+'</p></div>'
  +   '</div>'
  + banner
  + '<div class="plans-grid">'+plans+'</div>'
  + '<div class="billing-foot">'
  +   '<div class="bf-item"><span class="ico" data-i="card"></span><div><div class="bf-t">'+t('bl.pay')+'</div><div class="small muted">'+t('bl.pay_s')+'</div></div><button class="pill" data-act="pay-method">'+t('c.edit')+'</button></div>'
  +   '<div class="bf-item"><span class="ico" data-i="doc"></span><div><div class="bf-t">'+t('bl.invoices')+'</div><div class="small muted">'+t('bl.invoices_s')+'</div></div><button class="pill" data-act="invoices">'+t('bl.open')+'</button></div>'
  + '</div>';
}

return {bot:bot,analytics:analytics,company:company,billing:billing};
})();
