'use strict';
const {app, BrowserWindow, Notification, powerMonitor, nativeTheme} = require('electron');
const fs = require('node:fs');
const path = require('node:path');
const installRice = require('./renderer.cjs');
const root = __dirname;
let elapsed = 0;
let previousTick = Date.now();
let busy = false;

function configuration() {
  const settings = JSON.parse(fs.readFileSync(path.join(root, 'settings.json'), 'utf8'));
  const palette = JSON.parse(fs.readFileSync(path.join(root, 'palette.json'), 'utf8'));
  const validColor = value => /^#[0-9a-f]{6}$/i.test(value);
  for (const object of [palette, ...Object.values(settings.profiles)]) {
    for (const key of ['background', 'foreground']) {
      if (!validColor(object[key])) throw new Error(`Invalid ${key} color`);
    }
  }
  for (const key of ['panel', 'accent', 'border']) {
    if (!validColor(palette[key])) throw new Error(`Invalid ${key} color`);
  }
  const ranges = {fontSize:[12,64],lineHeight:[1,3],paragraphSpacing:[0,3],
    breakMinutes:[0,180],breakSeconds:[1,120],idleSeconds:[10,3600]};
  for (const [key, [minimum, maximum]] of Object.entries(ranges)) {
    if (!Number.isFinite(settings[key]) || settings[key] < minimum || settings[key] > maximum) {
      throw new Error(`Invalid setting: ${key}`);
    }
  }
  return {settings, palette, customCSS:fs.readFileSync(path.join(root,'custom.css'),'utf8')};
}

function localReader(wc) {
  try {
    const url = new URL(wc.getURL());
    return url.protocol === 'file:' && decodeURIComponent(url.pathname) === path.join(app.getAppPath(),'build/index.html');
  } catch (_) { return false; }
}

async function apply(wc) {
  if (wc.isDestroyed() || !localReader(wc)) return;
  try {
    const payload = configuration();
    nativeTheme.themeSource = parseInt(payload.palette.background.slice(1,3),16) < 128 ? 'dark' : 'light';
    await wc.executeJavaScript(`(${installRice.toString()})(${JSON.stringify(payload)})`);
  } catch (error) { console.error('[Koodo rice]', error.message); }
}

app.on('web-contents-created', (_, wc) => {
  wc.on('did-finish-load', () => apply(wc));
});
for (const file of ['palette.json','settings.json','custom.css']) {
  fs.watchFile(path.join(root, file), {persistent:false,interval:1500}, () => {
    for (const window of BrowserWindow.getAllWindows()) apply(window.webContents);
  });
}

app.whenReady().then(() => {
  const timer = setInterval(async () => {
    const now = Date.now();
    const seconds = Math.min((now - previousTick)/1000, 12);
    previousTick = now;
    if (busy) return;
    busy = true;
    try {
      const {settings} = configuration();
      if (!settings.breakMinutes) { elapsed = 0; return; }
      const window = BrowserWindow.getFocusedWindow();
      if (!window || !localReader(window.webContents)) return;
      const idle = powerMonitor.getSystemIdleTime();
      if (idle >= settings.idleSeconds) { elapsed = 0; return; }
      const reading = await window.webContents.executeJavaScript(String.raw`Boolean(
        document.querySelector('.background-box1,foliate-view,.pdfViewer') ||
        /\/(epub|pdf|mobi|azw3|fb2|txt|html|md|cbr|cbz|cbt|cb7|reader)(\/|$|\?)/i.test(location.hash)
      )`);
      if (!reading) return;
      elapsed += seconds;
      if (elapsed >= settings.breakMinutes * 60) {
        elapsed = 0;
        if (Notification.isSupported()) {
          new Notification({title:'Перерыв от чтения',
            body:`Посмотрите вдаль примерно на 6 метров в течение ${settings.breakSeconds} секунд. Поморгайте и расслабьте глаза.`,
            silent:true}).show();
        }
      }
    } catch (error) { console.error('[Koodo breaks]', error.message); }
    finally { busy = false; }
  }, 10000);
  timer.unref();
});
