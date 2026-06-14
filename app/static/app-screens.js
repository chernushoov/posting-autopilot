/* ════════════════════════════════════════════════════════════════════════════
   Posting Autopilot — Cabinet SCREEN templates (return HTML strings) · i18n
   Chrome via t(); content fields come localized from PA.applyLang().
   ════════════════════════════════════════════════════════════════════════════ */
window.PAScreens = (function(){
"use strict";
var D = window.PA;
function t(k,v){ return window.PA_I18N.t(k,v); }
function clsBadge(c){
  var m={hot:['cls-hot',t('cls.hot')],warm:['cls-warm',t('cls.warm')],cold:['cls-cold',t('cls.cold')],dup:['cls-dup',t('cls.dup')]};
  var x=m[c]||m.cold; return '<span class="cls '+x[0]+'">'+x[1]+'</span>';
}
function scoreCls(s){return s>=80?'hi':s>=50?'mid':'';}
function adById(id){ return D.ADS.filter(function(x){return x.id===id;})[0]||D.ADS[0]; }

/* ── LEADS ────────────────────────────────────────────────────────────────── */
function leads(state){
  return ''
  + '<div class="page-hero"><div><div class="eyebrow">'+t('lead.eyebrow')+'</div><h1>'+t('title.leads')+'</h1>'
  + '<p class="muted">'+t('lead.sub')+'</p></div>'
  + '<button class="pill" data-act="export"><span class="ico" data-i="download"></span> '+t('c.export_csv')+'</button></div>'
  + '<div class="seg" id="leadFilter" style="margin-bottom:16px">'
  +   '<button data-f="hot" class="active">'+t('lead.f.hot')+' <span class="cnt">'+D.COUNTS.hot+'</span></button>'
  +   '<button data-f="warm">'+t('lead.f.warm')+' <span class="cnt">'+D.COUNTS.warm+'</span></button>'
  +   '<button data-f="all">'+t('lead.f.all')+' <span class="cnt">'+D.COUNTS.all+'</span></button>'
  +   '<button data-f="spam">'+t('lead.f.spam')+' <span class="cnt">'+D.COUNTS.spam+'</span></button>'
  + '</div>'
  + '<div class="leads-layout"><div class="lead-list" id="leadList"></div>'
  + '<div class="card lead-detail" id="leadDetail"></div></div>';
}
function leadListHTML(data){
  if(!data.length) return '<div class="empty-state">'+t('lead.empty')+'</div>';
  return data.map(function(L){
    return '<div class="lead-item '+(L.cls==='dup'?'dup':'')+'" data-id="'+L.id+'">'
    + '<div class="li-top"><span class="li-name">'+L.name+'</span>'+clsBadge(L.cls)+'</div>'
    + '<div class="li-snip">'+L.summary+'</div>'
    + '<div class="li-meta"><span class="score '+scoreCls(L.score)+'">'+L.score+'</span><span>'+L.ad+'</span>'
    + (L.phone&&L.phone!=='—'?'<span>· '+L.phone+'</span>':'')+'</div></div>';
  }).join('');
}
function leadDetailHTML(L){
  if(!L) return '<div class="empty-state">'+t('lead.pick')+'</div>';
  var bubbles=L.chat.map(function(c){return '<div class="msg '+(c[0]==='bot'?'me':'')+'"><div class="bubble">'+c[1]+'</div></div>';}).join('');
  var statuses=['opened','got_responses','interview_scheduled','hired','cancelled'];
  var opts=statuses.map(function(s){return '<option value="'+s+'"'+(s===L.status?' selected':'')+'>'+t('ls.'+s)+'</option>';}).join('');
  return ''
  + '<div class="section-head"><div><h2 style="margin:0;display:flex;align-items:center;gap:9px">'+L.name+' '+clsBadge(L.cls)+'</h2>'
  +   '<p class="muted small">'+L.user+' · '+L.ad+'</p></div>'
  +   '<span class="score '+scoreCls(L.score)+'" style="font-size:14px;padding:5px 11px">'+L.score+'</span></div>'
  + (L.dupOf?'<div class="alert">'+t('lead.dup',{n:L.dupOf})+'<a data-go="leads" href="#/leads">'+t('lead.dup_open')+'</a></div>':'')
  + '<div class="ai-summary"><span class="ico" data-i="sparkles"></span><div><strong>'+t('lead.aisum')+'</strong> '+L.summary+'</div></div>'
  + '<div class="lead-info">'
  +   '<div class="li"><span class="k">'+t('lead.phone')+'</span><span class="v">'+L.phone+'</span></div>'
  +   '<div class="li"><span class="k">'+t('lead.status')+'</span><span class="v"><select data-act="lead-status">'+opts+'</select></span></div>'
  + '</div>'
  + (L.spam?'':'<div class="actions" style="margin-bottom:6px">'
  +   '<button class="btn" data-act="wa"><span class="ico" data-i="phone"></span> '+t('lead.wa')+'</button>'
  +   '<button class="pill" data-act="tg"><span class="ico" data-i="send"></span> '+t('lead.tg')+'</button></div>')
  + '<div class="lead-chat-wrap"><div class="small muted" style="margin-bottom:8px">'+t('lead.dialog')+'</div>'
  +   '<div class="chat">'+bubbles+'</div></div>';
}

/* ── DASHBOARD ────────────────────────────────────────────────────────────── */
function dashboard(state){
  var done=D.ONBOARD.filter(function(s){return s.done;}).length;
  var pct=Math.round(done/D.ONBOARD.length*100);
  var steps=D.ONBOARD.map(function(s){
    return '<div class="ob-step '+(s.done?'done':'')+'" data-go="'+s.go+'">'
    + '<span class="ob-tick">'+(s.done?'<span class="ico" data-i="checkbare"></span>':'')+'</span>'
    + '<span><span class="ob-n">'+t('dsh.step')+' '+s.n+'</span><br><span class="ob-t">'+s.t+'</span></span></div>';
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
  + '<div class="page-hero"><div><div class="eyebrow">'+t('dsh.eyebrow')+'</div><h1>'+t('title.dashboard')+'</h1>'
  +   '<p class="muted">'+t('dsh.sub')+'</p></div>'
  +   '<button class="btn" data-go="ads"><span class="ico" data-i="plus"></span> '+t('dsh.new_ad')+'</button></div>'
  + '<div class="onboard"><h3>'+t('dsh.setup_h')+'</h3><p>'+t('dsh.setup_p',{done:done})+'</p>'
  +   '<div class="ob-bar"><i style="width:'+pct+'%"></i></div><div class="ob-steps">'+steps+'</div></div>'
  + '<div class="kpi-grid">'
  +   kpi('chart',t('dsh.k.posts'),((D.ANALYTICS.kpi[0]&&D.ANALYTICS.kpi[0].val)||'0'),'')
  +   kpi('flame',t('dsh.k.hot'),String(D.COUNTS.hot||0),'')
  +   kpi('bot',t('dsh.k.bot'),String(D.COUNTS.processed||0),'')
  +   kpi('clock',t('dsh.k.reply'),(D.COUNTS.processed?'<1м':'—'),t('dsh.k.reply_s'),true)
  + '</div>'
  + '<div class="grid2" style="align-items:start">'
  +   '<div class="card"><div class="section-head"><h3 style="margin:0">'+t('dsh.funnel')+'</h3><span class="badge">'+t('dsh.7d')+'</span></div><div class="funnel">'+funnel+'</div></div>'
  +   '<div class="card"><div class="section-head"><h3 style="margin:0">'+t('dsh.recent')+'</h3><a class="pill" data-go="leads" href="#/leads">'+t('c.all')+'</a></div>'
  +     '<div class="table-wrap"><table class="table"><thead><tr><th>'+t('th.name')+'</th><th>'+t('th.ad')+'</th><th>'+t('th.class')+'</th><th>'+t('th.phone')+'</th></tr></thead><tbody>'+leadRows+'</tbody></table></div></div>'
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
    + '<select data-act="queue-result"><option>'+t('cmp.result')+'</option><option>'+t('cmp.r.posted')+'</option><option>'+t('cmp.r.blocked')+'</option><option>'+t('cmp.r.skip')+'</option></select></div>';
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
  + '<div class="page-hero"><div><div class="eyebrow">'+t('cmp.eyebrow')+'</div><h1>'+t('title.campaigns')+'</h1>'
  +   '<p class="muted">'+t('cmp.sub')+'</p></div>'
  +   '<button class="btn" data-act="new-campaign"><span class="ico" data-i="plus"></span> '+t('cmp.new')+'</button></div>'
  + '<div class="night-banner"><span class="ico" data-i="moon"></span>'+t('cmp.night')+'</div>'
  + '<div class="readiness">'
  +   '<div class="ready-card tg"><span class="rc-ic" data-i="send"></span><div style="flex:1"><div class="rc-name">Telegram</div><div class="rc-sub">'+D.SOURCES.filter(function(s){return s.platform==='Telegram';}).length+' · '+t('st.ready_pl')+'</div></div><span class="status status-ready">'+t('st.ready')+'</span></div>'
  +   '<div class="ready-card fb"><span class="rc-ic" data-i="fb"></span><div style="flex:1"><div class="rc-name">Facebook</div><div class="rc-sub">'+D.SOURCES.filter(function(s){return s.platform==='Facebook';}).length+' · '+t('st.manual_pl')+'</div></div><span class="status status-manual_action_required">'+t('st.manual')+'</span></div>'
  + '</div>'
  + '<div class="section-head"><h2>'+t('cmp.queue')+'</h2><span class="badge">'+t('cmp.tasks',{n:D.QUEUE.length})+'</span></div>'
  + '<div class="queue" style="margin-bottom:26px">'+queue+'</div>'
  + '<div class="section-head"><h2>'+t('cmp.list')+'</h2></div>'
  + '<div class="table-wrap" style="margin-bottom:26px"><table class="table"><thead><tr><th>'+t('th.campaign')+'</th><th>'+t('th.channels')+'</th><th>'+t('th.leads')+'</th><th>'+t('th.status')+'</th><th></th></tr></thead><tbody>'+camps+'</tbody></table></div>'
  + '<div class="section-head"><h2>'+t('cmp.log')+'</h2><a class="pill" data-act="refresh"><span class="ico" data-i="refresh"></span> '+t('c.refresh')+'</a></div>'
  + '<div class="table-wrap"><table class="table"><thead><tr><th>'+t('th.group')+'</th><th>'+t('th.channel')+'</th><th>'+t('th.time')+'</th><th>'+t('th.status')+'</th></tr></thead><tbody>'+log+'</tbody></table></div>';
}

/* ════════════════════════════════════════════════════════════════════════════
   ADS — list + detail + 3-step wizard
   ════════════════════════════════════════════════════════════════════════════ */
function ads(state){
  if(state.adView==='wizard') return adWizard(state);
  if(state.adView==='detail') return adDetail(state);
  var used=D.ADS.length, limit=D.AD_LIMIT;
  var cards=D.ADS.map(function(a){
    return '<div class="card ad-card" data-ad="'+a.id+'">'
    + '<div class="ad-card-top"><span class="ad-vert" data-i="'+a.vert+'"></span>'
    +   '<span class="status '+(a.active?'status-posted':'status-pending')+'">'+(a.active?t('st.active'):t('st.paused'))+'</span></div>'
    + '<h3 class="ad-title">'+a.title+'</h3>'
    + '<div class="ad-meta">'+a.vertLabel+' · '+a.city+' · '+a.price+'</div>'
    + '<p class="ad-preview">'+a.preview+'</p>'
    + '<div class="ad-stats"><span><span class="ico" data-i="flame"></span>'+t('ads.leads',{n:a.leads})+'</span>'
    +   '<span><span class="ico" data-i="eye"></span>'+a.views.toLocaleString()+'</span>'
    +   '<button class="pill" data-act="edit-ad"><span class="ico" data-i="edit"></span>'+t('c.edit')+'</button></div>'
    + '</div>';
  }).join('');
  var atLimit=used>=limit;
  return ''
  + '<div class="page-hero"><div><div class="eyebrow">'+t('ads.eyebrow')+'</div><h1>'+t('title.ads')+'</h1>'
  +   '<p class="muted">'+t('ads.sub')+'</p></div>'
  +   '<button class="btn" data-act="new-ad"'+(atLimit?' disabled style="opacity:.5"':'')+'><span class="ico" data-i="plus"></span> '+t('ads.new')+'</button></div>'
  + '<div class="limit-bar"><div class="limit-track"><i style="width:'+(used/limit*100)+'%"></i></div>'
  +   '<span class="limit-label">'+t('ads.limit',{used:used,limit:limit})+'</span>'
  +   (atLimit?'<a class="pill" data-go="billing" href="#/billing">'+t('c.upgrade')+'</a>':'')+'</div>'
  + '<div class="ad-grid">'+cards+'</div>';
}
function adDetail(state){
  var a=adById(state.adId);
  var fn=[
    {label:t('ads.k.views'),val:a.views,color:'#0071e3'},
    {label:t('adf.msg'),val:Math.round(a.views*0.12),color:'#3a8dff'},
    {label:t('adf.screen'),val:Math.round(a.views*0.045)+(a.leads||0),color:'var(--warning)'},
    {label:t('adf.hot'),val:a.leads,color:'var(--danger)'},
    {label:t('adf.closed'),val:Math.max(0,Math.round(a.leads*0.4)),color:'var(--success)'}
  ];
  var max=fn[0].val||1;
  var funnel=fn.map(function(f){
    return '<div class="fn-row"><div class="fn-label">'+f.label+'</div>'
    + '<div class="fn-track"><div class="fn-fill" style="width:'+Math.max(8,f.val/max*100)+'%;background:'+f.color+'">'+f.val.toLocaleString()+'</div></div></div>';
  }).join('');
  var kw=a.title; var rel=D.LEADS.filter(function(L){return !L.spam&&L.cls!=='dup'&&L.ad&&(L.ad===a.ad||false);});
  // fall back: match by vertical keyword in the leads' ad label
  if(!rel.length){
    rel=D.LEADS.filter(function(L){ if(L.spam||L.cls==='dup'||!L.ad) return false;
      return (a.vert==='home'&&/Florent|פלורנט|Флорент/i.test(L.ad)) || (a.vert==='users'&&/Barista|Бариста|\u05d1\u05e8\u05de\u05df|Job|\u05d3\u05e8\u05d5\u05e9|\u0412\u0430\u043a/i.test(L.ad)); });
  }
  rel=rel.slice(0,4);
  var leadRows=rel.length?rel.map(function(L){
    return '<tr data-go-lead="'+L.id+'" style="cursor:pointer"><td><strong>'+L.name+'</strong></td><td>'+clsBadge(L.cls)+'</td><td>'+L.phone+'</td></tr>';
  }).join(''):'<tr><td colspan="3" class="muted small" style="padding:18px;text-align:center">'+t('ads.no_leads')+'</td></tr>';
  return ''
  + '<div class="page-hero"><div><a class="back-link" data-act="ad-back"><span class="ico" data-i="chevron" style="transform:rotate(90deg)"></span> '+t('ads.back')+'</a>'
  +   '<h1 style="margin-top:6px">'+a.title+'</h1>'
  +   '<p class="muted">'+a.vertLabel+' · '+a.city+' · '+a.price+'</p></div>'
  +   '<div class="actions"><span class="status '+(a.active?'status-posted':'status-pending')+'" style="font-size:13px">'+(a.active?t('st.active'):t('st.paused'))+'</span>'
  +     '<button class="pill" data-act="'+(a.active?'pause':'run')+'"><span class="ico" data-i="'+(a.active?'pause':'play')+'"></span>'+(a.active?t('ads.pause'):t('ads.run'))+'</button>'
  +     '<button class="btn" data-act="edit-ad"><span class="ico" data-i="edit"></span>'+t('c.edit')+'</button></div></div>'
  + '<div class="kpi-grid k3">'
  +   kpi('eye',t('ads.k.views'),a.views.toLocaleString(),t('ads.k.views_s'),true)
  +   kpi('flame',t('ads.k.hot'),a.leads,a.leads?t('ads.k.hot_s'):t('ads.k.hot_s0'),true)
  +   kpi('chart',t('ads.k.conv'),(a.views?(a.leads/a.views*100).toFixed(1):'0')+'%',t('ads.k.conv_s'),true)
  + '</div>'
  + '<div class="grid2" style="align-items:start">'
  +   '<div class="card"><div class="section-head"><h3 style="margin:0">'+t('ads.funnel')+'</h3><span class="badge">'+t('ads.alltime')+'</span></div><div class="funnel">'+funnel+'</div></div>'
  +   '<div class="card card-flat wz-preview"><div class="section-head"><h3 style="margin:0">'+t('ads.posttext')+'</h3><span class="badge">'+a.vertLabel+'</span></div>'
  +     '<div class="fb-preview">'+a.title+'\n\n'+a.preview+'</div>'
  +     '<div class="chip-row"><span class="mini-chip ok">'+a.city+'</span><span class="mini-chip">'+a.price+'</span><span class="mini-chip">'+t('nav.bot')+'</span></div></div>'
  + '</div>'
  + '<div class="section-head" style="margin-top:24px"><h2>'+t('ads.from_ad')+'</h2><a class="pill" data-go="leads" href="#/leads">'+t('ads.all_leads')+'</a></div>'
  + '<div class="table-wrap"><table class="table"><thead><tr><th>'+t('th.name')+'</th><th>'+t('th.class')+'</th><th>'+t('th.phone')+'</th></tr></thead><tbody>'+leadRows+'</tbody></table></div>';
}
function adWizard(state){
  var step=state.adStep||1; var a1=adById('a1');
  var verts=[['home',t('vert.home')],['users',t('vert.users')],['car',t('vert.car')],['wrench',t('vert.wrench')]];
  var dots=[1,2,3].map(function(n){
    var st=n<step?'done':n===step?'active':'';
    return '<div class="wz-dot '+st+'"><span class="wz-num">'+(n<step?'<span class=\'ico\' data-i=\'checkbare\'></span>':n)+'</span>'
    + '<span class="wz-label">'+[t('wz.s1'),t('wz.s2'),t('wz.s3')][n-1]+'</span></div>';
  }).join('<div class="wz-line"></div>');
  var body;
  if(step===1){
    body='<div class="wz-field"><label>'+t('wz.type')+'</label><div class="vert-row">'
    + verts.map(function(v,i){return '<button class="vert-chip'+(i===0?' active':'')+'" data-vert="'+v[0]+'"><span class="ico" data-i="'+v[0]+'"></span>'+v[1]+'</button>';}).join('')+'</div></div>'
    + '<div class="wz-field"><label>'+t('wz.title')+'</label><input id="wzTitle" value="'+a1.title+'"></div>'
    + '<div class="wz-field"><label>'+t('wz.body')+'</label><textarea id="wzBody" rows="4">'+a1.preview+'</textarea></div>'
    + '<div class="grid2"><div class="wz-field"><label>'+t('wz.city')+'</label><input value="'+a1.city+'"></div>'
    + '<div class="wz-field"><label>'+t('wz.lang')+'</label><select><option>Русский</option><option>עברית</option><option>English</option></select></div></div>';
  } else if(step===2){
    body='<div class="grid2"><div class="wz-field"><label>'+t('wz.price')+'</label><input value="'+a1.price+'"></div>'
    + '<div class="wz-field"><label>'+t('wz.contact')+'</label><input value="054-555-1234"></div></div>'
    + '<div class="wz-field"><label>'+t('wz.photos')+'</label><div class="photo-row">'
    +   '<div class="photo-cell filled"></div><div class="photo-cell filled"></div><div class="photo-cell filled"></div>'
    +   '<div class="photo-cell add"><span class="ico" data-i="plus"></span></div></div>'
    +   '<div class="small muted" style="margin-top:7px">'+t('wz.photos_h')+'</div></div>'
    + '<div class="wz-field"><label>'+t('wz.link')+'</label><input placeholder="https://…"></div>';
  } else {
    body='<div class="wz-field"><label>'+t('wz.screen')+'</label><div class="stack tight">'
    +   '<input value="'+t('wz.q1')+'"><input value="'+t('wz.q2')+'"><input value="'+t('wz.q3')+'"></div>'
    +   '<button class="pill" style="margin-top:9px"><span class="ico" data-i="plus"></span> '+t('wz.addq')+'</button></div>'
    + '<div class="grid2"><div class="wz-field"><label>'+t('wz.hot_c')+'</label><input value="'+t('wz.hot_val')+'"></div>'
    + '<div class="wz-field"><label>'+t('wz.cold_c')+'</label><input value="'+t('wz.cold_val')+'"></div></div>'
    + '<div class="wz-field"><label>'+t('wz.greet')+'</label><textarea rows="2">'+t('wz.greet_val')+'</textarea></div>';
  }
  return ''
  + '<div class="page-hero"><div><div class="eyebrow">'+t('wz.eyebrow',{n:step})+'</div><h1>'+[t('wz.t1'),t('wz.t2'),t('wz.t3')][step-1]+'</h1></div>'
  +   '<button class="pill" data-act="wz-close"><span class="ico" data-i="x"></span> '+t('c.cancel')+'</button></div>'
  + '<div class="wizard-steps">'+dots+'</div>'
  + '<div class="create-grid"><div class="card">'+body+'</div>'
  +   '<div class="card card-flat wz-preview"><div class="section-head"><h3 style="margin:0">'+t('wz.preview')+'</h3><span class="badge">Telegram</span></div>'
  +     '<div class="fb-preview" id="wzPreview">'+a1.title+'\n\n'+a1.preview+'</div>'
  +     '<div class="chip-row"><span class="mini-chip ok">'+t('wz.tg48')+'</span><span class="mini-chip">'+t('nav.bot')+'</span></div></div></div>'
  + '<div class="wizard-nav">'
  +   (step>1?'<button class="pill" data-act="wz-back">← '+t('c.back')+'</button>':'<span></span>')
  +   (step<3?'<button class="btn" data-act="wz-next">'+t('c.next')+' →</button>':'<button class="btn" data-act="wz-finish"><span class="ico" data-i="check"></span> '+t('wz.publish')+'</button>')
  + '</div>';
}

/* ════════════════════════════════════════════════════════════════════════════
   TELEGRAM
   ════════════════════════════════════════════════════════════════════════════ */
function channelTg(state){
  if(state.tgView==='wizard') return tgWizard(state);
  var groups=D.TG_GROUPS.map(function(g,i){
    return '<label class="grp-row"><input type="checkbox" data-grp="'+i+'"'+(g.on?' checked':'')+'>'
    + '<span class="grp-name">'+g.name+'</span><span class="grp-folder">'+g.folder+'</span>'
    + '<span class="grp-members">'+g.members+'</span></label>';
  }).join('');
  var tgN=D.TG_GROUPS.length, tgConn=tgN>0, tgPct=Math.min(100,Math.round(tgN/50*100));
  return ''
  + '<div class="page-hero"><div><div class="eyebrow">'+t('tg.channel')+'</div><h1>Telegram</h1></div>'
  +   (tgConn?'<span class="status status-ready" style="font-size:13px">● '+t('st.connected')+'</span>':'<span class="status status-pending" style="font-size:13px">○ '+t('st.not_connected')+'</span>')+'</div>'
  + '<div class="actions" style="margin-top:14px"><button class="pill" data-act="tg-reconnect"><span class="ico" data-i="refresh"></span> '+(tgConn?t('tg.reconnect'):t('tg.get_code'))+'</button>'
  +   '<span class="muted small">'+t('tg.session_note')+'</span></div>'
  + '<div class="section-head" style="margin-top:24px"><h2>'+t('tg.groups')+'</h2><span class="badge">'+tgN+' / 50 · Pro</span></div>'
  + '<div class="limit-bar" style="margin-bottom:16px"><div class="limit-track"><i style="width:'+tgPct+'%"></i></div>'
  +   '<span class="limit-label">'+tgN+' / 50</span><a class="pill" data-go="billing" href="#/billing">'+t('c.upgrade_limit')+'</a></div>'
  + '<div class="card"><div class="grp-head"><span>'+t('tg.th.group')+'</span><span>'+t('tg.th.folder')+'</span><span>'+t('tg.th.members')+'</span></div>'
  +   '<div class="grp-list">'+groups+'</div>'
  +   '<div class="actions" style="margin-top:14px"><button class="btn" data-act="tg-add">'+t('tg.add_sel')+'</button>'
  +     '<button class="pill" data-act="tg-resync"><span class="ico" data-i="refresh"></span> '+t('tg.resync')+'</button></div></div>';
}
function tgWizard(state){
  var step=state.tgStep||1;
  var dots=[1,2,3].map(function(n){
    var st=n<step?'done':n===step?'active':'';
    return '<div class="wz-dot '+st+'"><span class="wz-num">'+(n<step?'<span class=\'ico\' data-i=\'checkbare\'></span>':n)+'</span>'
    + '<span class="wz-label">'+[t('tg.s.data'),t('tg.s.code'),t('tg.s.2fa')][n-1]+'</span></div>';
  }).join('<div class="wz-line"></div>');
  var body;
  if(step===1){
    body='<div class="alert">'+t('tg.w1_alert')+'</div>'
    + '<div class="grid2"><div class="wz-field"><label>api_id</label><input value="21834756"></div>'
    + '<div class="wz-field"><label>api_hash</label><input value="••••••••••••7c1f"></div></div>'
    + '<div class="wz-field"><label>'+t('tg.phone')+'</label><input value="+972 54-555-1234"></div>';
  } else if(step===2){
    body='<div class="alert success">'+t('tg.w2_alert')+'</div>'
    + '<div class="wz-field"><label>'+t('tg.code')+'</label><input class="code-input" maxlength="9" value="4 2 9 1 7"></div>'
    + '<div class="small muted" style="margin-top:8px">'+t('tg.no_code')+' <a data-act="tg-resend" style="cursor:pointer">'+t('tg.resend')+'</a> · '+t('tg.left')+'</div>';
  } else {
    body='<div class="alert">'+t('tg.w3_alert')+'</div>'
    + '<div class="wz-field"><label>'+t('tg.pass2fa')+'</label><input type="password" value="demo1234"></div>'
    + '<div class="small muted" style="margin-top:8px">'+t('tg.hint')+'</div>';
  }
  return ''
  + '<div class="page-hero"><div><div class="eyebrow">'+t('tg.w.eyebrow')+'</div><h1>'+[t('tg.w1'),t('tg.w2'),t('tg.w3')][step-1]+'</h1></div>'
  +   '<button class="pill" data-act="tg-cancel"><span class="ico" data-i="x"></span> '+t('c.cancel')+'</button></div>'
  + '<div class="wizard-steps">'+dots+'</div>'
  + '<div class="create-grid"><div class="card">'+body+'</div>'
  +   '<div class="card card-flat"><div class="section-head"><h3 style="margin:0">'+t('tg.why')+'</h3></div>'
  +     '<ul class="why-list"><li><span class="ico" data-i="check"></span>'+t('tg.why1')+'</li>'
  +       '<li><span class="ico" data-i="check"></span>'+t('tg.why2')+'</li>'
  +       '<li><span class="ico" data-i="check"></span>'+t('tg.why3')+'</li></ul>'
  +     '<div class="lock-note"><span class="ico" data-i="lock"></span>'+t('tg.lock')+'</div></div></div>'
  + '<div class="wizard-nav">'
  +   (step>1?'<button class="pill" data-act="tg-back">← '+t('c.back')+'</button>':'<button class="pill" data-act="tg-cancel">'+t('c.cancel')+'</button>')
  +   (step<3?'<button class="btn" data-act="tg-next">'+(step===1?t('tg.get_code'):t('tg.confirm'))+' →</button>':'<button class="btn" data-act="tg-finish"><span class="ico" data-i="check"></span> '+t('tg.finish')+'</button>')
  + '</div>';
}
function stepDone(tt,sub){
  return '<div class="cstep done"><span class="cstep-tick"><span class="ico" data-i="checkbare"></span></span>'
  + '<div><div class="cstep-t">'+tt+'</div><div class="cstep-s">'+sub+'</div></div></div>';
}

/* ════════════════════════════════════════════════════════════════════════════
   FACEBOOK
   ════════════════════════════════════════════════════════════════════════════ */
function channelFb(state){
  var readyMap={ready:['status-ready',t('rd.ready')],check:['status-manual_action_required',t('rd.check')],format:['status-pending',t('rd.format')]};
  var fbRows=D.FB_SOURCES.map(function(s){
    var r=readyMap[s.ready]||readyMap.format;
    return '<tr><td><strong>'+s.name+'</strong></td><td>'+s.mode+'</td>'
    + '<td><span class="status '+r[0]+'">'+r[1]+'</span></td>'
    + '<td style="text-align:right"><button class="pill" data-act="src-test"><span class="ico" data-i="send"></span> '+t('c.test')+'</button></td></tr>';
  }).join('');
  return ''
  + '<div class="page-hero"><div><div class="eyebrow">'+t('tg.channel')+'</div><h1>Facebook</h1>'
  +   '<p class="muted">'+t('fb.sub')+'</p></div>'
  +   (D.FB_SOURCES.length?'<span class="status status-ready" style="font-size:13px">● '+t('st.connected')+'</span>':'<span class="status status-pending" style="font-size:13px">○ '+t('st.not_connected')+'</span>')+'</div>'
  + '<div class="alert">'+t('fb.pilot')+'</div>'
  + '<div class="grid2" style="align-items:start;margin-top:6px">'
  +   '<div class="card"><div class="fb-opt-ic" data-i="link"></div><h3>'+t('fb.opt1')+'</h3>'
  +     '<p class="muted small">'+t('fb.opt1_p')+'</p>'
  +     '<button class="btn" data-act="fb-oauth" style="margin-top:12px;background:#1877F2;border-color:#1877F2"><span class="ico" data-i="fb"></span> '+t('fb.login')+'</button></div>'
  +   '<div class="card"><div class="fb-opt-ic" data-i="doc"></div><h3>'+t('fb.opt2')+'</h3>'
  +     '<p class="muted small">'+t('fb.opt2_p')+'</p>'
  +     '<textarea rows="4" placeholder="https://facebook.com/groups/..." style="margin-top:10px"></textarea>'
  +     '<button class="btn" data-act="fb-urls" style="margin-top:10px">'+t('fb.add_groups')+'</button></div>'
  + '</div>'
  + '<div class="perm-note"><span class="ico" data-i="alert"></span><div>'+t('fb.perm')+'</div></div>'
  + '<div class="section-head" style="margin-top:24px"><h2>'+t('fb.existing')+'</h2><span class="badge">'+t('fb.assisted')+'</span></div>'
  + '<div class="table-wrap"><table class="table"><thead><tr><th>'+t('fb.th.source')+'</th><th>'+t('fb.th.mode')+'</th><th>'+t('fb.th.ready')+'</th><th></th></tr></thead><tbody>'+fbRows+'</tbody></table></div>'
  + '<div class="src-hint"><span class="ico" data-i="lock"></span>'+t('fb.hint')+'</div>';
}

/* ════════════════════════════════════════════════════════════════════════════
   НАЗНАЧЕНИЯ / DESTINATIONS
   ════════════════════════════════════════════════════════════════════════════ */
function sources(state){
  var readyMap={ready:['status-ready',t('rd.ready')],check:['status-manual_action_required',t('rd.check')],format:['status-pending',t('rd.format')]};
  var rows=D.SOURCES.map(function(s){
    var r=readyMap[s.ready];
    return '<tr><td><strong>'+s.name+'</strong></td><td>'+s.platform+'</td><td>'+s.kind+'</td>'
    + '<td>'+s.mode+'</td><td><span class="status '+r[0]+'">'+r[1]+'</span></td>'
    + '<td style="text-align:right"><button class="pill" data-act="src-test"><span class="ico" data-i="send"></span> '+t('c.test')+'</button></td></tr>';
  }).join('');
  return ''
  + '<div class="page-hero"><div><div class="eyebrow">'+t('src.eyebrow')+'</div><h1>'+t('title.sources')+'</h1>'
  +   '<p class="muted">'+t('src.sub')+'</p></div>'
  +   '<button class="pill" data-act="src-check-all"><span class="ico" data-i="refresh"></span> '+t('c.check_all')+'</button></div>'
  + '<div class="readiness">'
  +   '<div class="ready-card tg"><span class="rc-ic" data-i="send"></span><div style="flex:1"><div class="rc-name">Telegram · '+D.SOURCES.filter(function(s){return s.platform==='Telegram';}).length+'</div><div class="rc-sub">'+t('src.tg_sub')+'</div></div><span class="status status-ready">'+t('st.ready_pl')+'</span></div>'
  +   '<div class="ready-card fb"><span class="rc-ic" data-i="fb"></span><div style="flex:1"><div class="rc-name">Facebook · '+D.SOURCES.filter(function(s){return s.platform==='Facebook';}).length+'</div><div class="rc-sub">'+t('src.fb_sub')+'</div></div><span class="status status-manual_action_required">'+t('st.manual_pl')+'</span></div>'
  + '</div>'
  + '<div class="card" style="margin-bottom:22px"><h3 style="margin-top:0">'+t('src.add')+'</h3>'
  +   '<div class="src-form"><select><option>Telegram</option><option>Facebook</option></select>'
  +     '<select><option>'+t('kind.group')+'</option><option>'+t('kind.channel')+'</option><option>'+t('kind.page')+'</option></select>'
  +     '<input placeholder="'+t('src.label_ph')+'"><input placeholder="'+t('src.url_ph')+'">'
  +     '<button class="btn" data-act="src-add">'+t('c.add')+'</button></div></div>'
  + '<div class="section-head"><h2>'+t('src.all')+'</h2><span class="badge">'+D.SOURCES.length+'</span></div>'
  + '<div class="table-wrap"><table class="table"><thead><tr><th>'+t('src.th.name')+'</th><th>'+t('src.th.platform')+'</th><th>'+t('src.th.kind')+'</th><th>'+t('src.th.mode')+'</th><th>'+t('src.th.ready')+'</th><th></th></tr></thead><tbody>'+rows+'</tbody></table></div>';
}

return {leads:leads,leadListHTML:leadListHTML,leadDetailHTML:leadDetailHTML,
  dashboard:dashboard,campaigns:campaigns,ads:ads,channelTg:channelTg,channelFb:channelFb,sources:sources,
  clsBadge:clsBadge};
})();
