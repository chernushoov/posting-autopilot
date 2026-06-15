#!/usr/bin/env node
/* Hebrew cabinet QA — registers a throwaway account on PROD, forces HE/RTL,
   screenshots every SPA screen, captures JS console errors, flags any Cyrillic
   leakage (untranslated RU), then hard-deletes the account. Read-only to other
   tenants (its own fresh company only). */
const fs = require('fs');
const path = require('path');

const BASE = process.env.QA_BASE || 'https://app.posting-autopilot.com';
const OUT = process.env.QA_OUT || '/tmp/pa-he-qa';
const STAMP = process.env.QA_TS || 'run';
const EMAIL = `hebqa-${STAMP}@qa.invalid`;
const PASS = 'QaCheck!2025';
const COMPANY = `QA HE ${STAMP}`;

const SCREENS = ['dashboard','leads','campaigns','ads','channel-tg','channel-fb','sources','bot','analytics','company','billing'];

function findChromium() {
  const root = path.join(process.env.HOME, 'Library/Caches/ms-playwright');
  let best = null, bestN = -1;
  for (const d of fs.readdirSync(root)) {
    const m = d.match(/^chromium-(\d+)$/);
    if (m && +m[1] > bestN) { bestN = +m[1]; best = d; }
  }
  if (!best) return null;
  return path.join(root, best, 'chrome-mac', 'Chromium.app', 'Contents', 'MacOS', 'Chromium');
}

(async () => {
  fs.mkdirSync(OUT, { recursive: true });
  const { chromium } = require('playwright-core');
  let browser;
  try { browser = await chromium.launch({ headless: true }); }
  catch (e) {
    const exe = findChromium();
    console.log('default launch failed, retrying with', exe);
    browser = await chromium.launch({ headless: true, executablePath: exe });
  }
  const ctx = await browser.newContext({
    locale: 'he-IL',
    extraHTTPHeaders: { 'Accept-Language': 'he,he-IL;q=0.9' },
    viewport: { width: 1440, height: 900 },
    deviceScaleFactor: 2,
  });
  const page = await ctx.newPage();
  const errors = [];
  page.on('console', m => { if (m.type() === 'error') errors.push('[console] ' + m.text()); });
  page.on('pageerror', e => errors.push('[pageerror] ' + (e && e.message || e)));

  const report = { base: BASE, email: EMAIL, screens: {}, errors_global: [], cyrillic: {}, html_attrs: {} };

  // ── 1. Register (open signup — no invite code set on prod) ────────────────
  await page.goto(BASE + '/register', { waitUntil: 'domcontentloaded' });
  await page.fill('input[name="email"]', EMAIL).catch(()=>{});
  await page.fill('input[name="password"]', PASS).catch(()=>{});
  await page.fill('input[name="company_name"]', COMPANY).catch(()=>{});
  // invite field, if present and required, we cannot guess — log it
  const hasInvite = await page.$('input[name="invite_code"]');
  if (hasInvite) report.invite_field_present = true;
  await Promise.all([
    page.waitForLoadState('networkidle').catch(()=>{}),
    page.click('button[type="submit"], button:has-text("Регист"), button:has-text("הרשמה"), button:has-text("Sign")').catch(()=>{}),
  ]);
  await page.waitForTimeout(1500);
  report.after_register_url = page.url();

  // ── 2. Force Hebrew + open cabinet ────────────────────────────────────────
  await page.goto(BASE + '/set-lang/he', { waitUntil: 'domcontentloaded' }).catch(()=>{});
  await page.goto(BASE + '/cabinet', { waitUntil: 'networkidle' }).catch(()=>{});
  await page.waitForTimeout(1200);
  report.cabinet_url = page.url();
  report.html_attrs = await page.evaluate(() => ({
    lang: document.documentElement.lang,
    dir: document.documentElement.dir,
    bodyClass: document.body.className,
    shellVisible: !!document.querySelector('#shell') && !document.querySelector('#shell').classList.contains('hide'),
  }));

  // sidebar text snapshot (translation sanity)
  report.sidebar_text = (await page.evaluate(() => {
    const n = document.querySelector('#sbnav'); return n ? n.innerText.replace(/\n+/g,' | ') : '(no nav)';
  })) || '';

  // ── 3. Walk every screen ─────────────────────────────────────────────────
  for (const s of SCREENS) {
    const before = errors.length;
    await page.evaluate(name => { location.hash = '#/' + name; }, s);
    await page.waitForTimeout(700);
    const file = path.join(OUT, `${String(SCREENS.indexOf(s)+1).padStart(2,'0')}-${s}.png`);
    await page.screenshot({ path: file, fullPage: true }).catch(e => report.screens[s] = 'SHOT FAIL ' + e.message);
    const viewText = await page.evaluate(() => {
      const v = document.querySelector('#view'); return v ? v.innerText : '';
    });
    const cyr = (viewText.match(/[А-Яа-яЁё]+/g) || []);
    report.screens[s] = { shot: path.basename(file), title: await page.evaluate(()=>{const t=document.querySelector('#wbTitle');return t?t.innerText:'';}), errors: errors.slice(before), cyrillic_hits: cyr.slice(0, 12) };
  }

  // ── 4. Wizards (RTL forms) ───────────────────────────────────────────────
  await page.evaluate(() => { location.hash = '#/ads'; });
  await page.waitForTimeout(500);
  await page.evaluate(() => { const b=document.querySelector('[data-act="new-ad"],[data-go="new-ad"]'); if(b) b.click(); });
  await page.waitForTimeout(700);
  await page.screenshot({ path: path.join(OUT, '12-ad-wizard.png'), fullPage: true }).catch(()=>{});

  report.errors_global = errors;

  // ── 5. Delete the throwaway account ──────────────────────────────────────
  await page.goto(BASE + '/account/delete', { waitUntil: 'domcontentloaded' }).catch(()=>{});
  await page.fill('input[name="confirm"]', COMPANY).catch(()=>{});
  await Promise.all([
    page.waitForLoadState('networkidle').catch(()=>{}),
    page.click('button[type="submit"]').catch(()=>{}),
  ]);
  await page.waitForTimeout(800);
  report.after_delete_url = page.url();

  fs.writeFileSync(path.join(OUT, 'report.json'), JSON.stringify(report, null, 2));
  console.log(JSON.stringify(report, null, 2));
  await browser.close();
})().catch(e => { console.error('FATAL', e); process.exit(1); });
