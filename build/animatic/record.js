const { chromium } = require('/opt/node22/lib/node_modules/playwright');
const path = require('path');

(async () => {
  const secs = Number(process.argv[2] || 10);
  const out  = process.argv[3] || 'out';
  const W = 1920, H = 1080;

  const browser = await chromium.launch({
    args: ['--autoplay-policy=no-user-gesture-required','--disable-gpu-vsync',
           '--force-device-scale-factor=1','--hide-scrollbars']
  });
  const ctx = await browser.newContext({
    viewport: { width: W, height: H },
    recordVideo: { dir: out, size: { width: W, height: H } }
  });
  const page = await ctx.newPage();
  await page.goto('file://' + path.resolve('animatic.html'));
  await page.waitForTimeout(secs * 1000);
  await ctx.close();
  await browser.close();
  console.log('recorded ' + secs + 's -> ' + out);
})();
