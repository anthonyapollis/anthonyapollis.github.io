// Render animatic.html to video.
//   node record.js [seconds] [outDir]
//
// Playwright captures frames at a variable rate but muxes them at a nominal
// 25fps, so the raw .webm plays back longer than the wall-clock capture -
// roughly 13% in practice. That makes the file useless as a timing reference,
// so the container timestamps are rescaled afterwards to match real elapsed
// time. The rescale is a remux, not a re-encode: no quality is lost.

const { chromium } = require('/opt/node22/lib/node_modules/playwright');
const { execFileSync } = require('child_process');
const path = require('path');
const fs = require('fs');

const FFMPEG = '/opt/pw-browsers/ffmpeg-1011/ffmpeg-linux';
const W = 1920, H = 1080;

const probeDuration = (file) => {
  const err = execFileSync(FFMPEG, ['-hide_banner', '-i', file],
    { stdio: ['ignore', 'ignore', 'pipe'], encoding: 'utf8' });
  return err;
};

(async () => {
  const secs = Number(process.argv[2] || 246);
  const outDir = process.argv[3] || 'out';

  const browser = await chromium.launch({
    args: ['--disable-gpu-vsync', '--force-device-scale-factor=1', '--hide-scrollbars']
  });
  const ctx = await browser.newContext({
    viewport: { width: W, height: H },
    recordVideo: { dir: outDir, size: { width: W, height: H } }
  });
  const page = await ctx.newPage();
  await page.goto('file://' + path.resolve(__dirname, 'animatic.html'));

  const t0 = Date.now();
  await page.waitForTimeout(secs * 1000);
  await ctx.close();           // flushes the webm
  await browser.close();
  const elapsed = (Date.now() - t0) / 1000;

  const raw = path.join(outDir, fs.readdirSync(outDir).find(f => f.endsWith('.webm')));

  // parse "Duration: HH:MM:SS.ss" out of ffmpeg's stderr
  let info = '';
  try { execFileSync(FFMPEG, ['-hide_banner', '-i', raw], { encoding: 'utf8' }); }
  catch (e) { info = e.stderr || ''; }
  const m = info.match(/Duration:\s*(\d+):(\d+):(\d+\.\d+)/);
  if (!m) { console.error('could not probe duration; leaving ' + raw + ' unmodified'); return; }
  const container = (+m[1]) * 3600 + (+m[2]) * 60 + parseFloat(m[3]);

  const scale = elapsed / container;
  const final = path.resolve(__dirname, 'like-i-never-left-animatic.webm');
  execFileSync(FFMPEG, ['-hide_banner', '-loglevel', 'error', '-y',
    '-itsscale', scale.toFixed(6), '-i', raw, '-c', 'copy', final]);

  console.log(`captured ${elapsed.toFixed(1)}s | container ${container.toFixed(2)}s ` +
              `| scale ${scale.toFixed(6)}`);
  console.log('wrote ' + final);
})();
