#!/usr/bin/env node
/* Logs into the seeded QA-THEME account, screenshots channel-tg + channel-fb in
   Hebrew so the theme chips + theme-grouping are visually verified. Read-only. */
const fs = require('fs'); const path = require('path');
const BASE = 'https://app.posting-autopilot.com';
const OUT = '/tmp/pa-theme'; const EMAIL = 'qa-theme@qa.invalid'; const PASS = 'QaTheme!2025';

function findChromium() {
  const root = path.join(process.env.HOME, 'Library/Caches/ms-playwright');
  let best = null, n = -1;
  for (const d of fs.readdirSync(root)) { const m = d.match(/^chromium-(\d+)$/); if (m && +m[1] > n) { n = +m[1]; best = d; } }
  return best && path.join(root, best, 'chrome-mac', 'Chromium.app', 'Contents', 'MacOS', 'Chromium');
}

(async () => {
  fs.mkdirSync(OUT, { recursive: true });
  const { chromium } = require('playwright-core');
  let browser;
  try { browser = await chromium.launch({ headless: true }); }
  catch { browser = await chromium.launch({ headless: true, executablePath: findChromium() }); }
  const ctx = await browser.newContext({ locale: 'he-IL', extraHTTPHeaders: { 'Accept-Language': 'he' }, viewport: { width: 1440, height: 900 }, deviceScaleFactor: 2 });
  const page = await ctx.newPage();
  const errs = [];
  page.on('console', m => { if (m.type() === 'error') errs.push(m.text()); });
  page.on('pageerror', e => errs.push(String(e && e.message || e)));

  await page.goto(BASE + '/login', { waitUntil: 'domcontentloaded' });
  await page.fill('input[name="login"]', EMAIL).catch(()=>{});
  await page.fill('input[name="password"]', PASS).catch(()=>{});
  await Promise.all([page.waitForLoadState('networkidle').catch(()=>{}), page.click('button[type="submit"]').catch(()=>{})]);
  await page.waitForTimeout(800);
  await page.goto(BASE + '/set-lang/he').catch(()=>{});
  await page.goto(BASE + '/cabinet', { waitUntil: 'networkidle' }).catch(()=>{});
  await page.waitForTimeout(1000);
  const loggedIn = await page.evaluate(() => !!document.querySelector('#shell') && !document.querySelector('#shell').classList.contains('hide'));
  console.log('loggedIn:', loggedIn, '| url:', page.url());

  for (const s of ['channel-tg', 'channel-fb']) {
    await page.evaluate(n => { location.hash = '#/' + n; }, s);
    await page.waitForTimeout(800);
    await page.screenshot({ path: path.join(OUT, s + '.png'), fullPage: true });
    // pull the visible theme chips
    const chips = await page.evaluate(() => Array.from(document.querySelectorAll('.grp-theme')).map(e => e.textContent));
    console.log(s, 'theme chips:', JSON.stringify(chips));
  }
  console.log('JS errors:', errs.length, errs.slice(0, 3));
  await browser.close();
})().catch(e => { console.error('FATAL', e); process.exit(1); });
