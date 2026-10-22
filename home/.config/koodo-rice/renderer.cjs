/* Local UI and reflowable-book styles. PDF canvases and fixed layouts keep
   their layout; use Koodo's own PDF appearance controls for those documents. */
module.exports = function installRice(payload) {
  const previous = window.__symphonyRice;
  if (previous) {
    previous.update(payload);
    return;
  }
  let config = payload;
  let chosen = localStorage.getItem('symphony-reading-profile');
  let scheduled = false;
  const observers = new WeakSet();
  const frames = new WeakSet();
  const styleCache = new WeakMap();

  function putStyle(root, id, css) {
    let style = root.querySelector(`style#${id}`);
    if (!style) {
      style = (root.ownerDocument || root).createElement('style');
      style.id = id;
      (root.head || root).appendChild(style);
    }
    if (styleCache.get(style) !== css) {
      style.textContent = css;
      styleCache.set(style, css);
    }
  }

  function colors() {
    const profile = chosen || config.settings.profile;
    return config.settings.profiles[profile] || config.palette;
  }

  function render() {
    scheduled = false;
    const p = config.palette;
    const c = colors();
    const s = config.settings;
    const scheme = parseInt(p.background.slice(1, 3), 16) < 128 ? 'dark' : 'light';
    const ui = `
      :root { --rice-bg:${p.background}; --rice-fg:${p.foreground};
        --rice-panel:${p.panel}; --rice-accent:${p.accent}; --rice-border:${p.border};
        color-scheme:${scheme}; }
      html, body, #root { background:var(--rice-bg)!important; color:var(--rice-fg)!important; }
      :is(.sidebar,.sidebar-box,.header,.header-box,.nav-panel,.setting-panel,
        .navigation-panel,.book-list-container,.book-list,.manager,.manager-page,
        .background-box2,.background-box3) {
        background-color:var(--rice-panel)!important; color:var(--rice-fg)!important; }
      :is(input,textarea,select) { background-color:var(--rice-panel)!important;
        color:var(--rice-fg)!important; border-color:var(--rice-border)!important; }
      :is(.background-box1,.reader-page) { background-color:${c.background}!important; }
      :focus-visible { outline:2px solid var(--rice-accent)!important; outline-offset:2px; }
      #symphony-reader-tools { position:fixed; right:12px; bottom:12px; z-index:2147483646;
        display:flex; gap:4px; padding:5px; border:1px solid var(--rice-border);
        border-radius:9px; background:var(--rice-panel); color:var(--rice-fg); }
      #symphony-reader-tools button { cursor:pointer; color:inherit; background:transparent;
        border:0; border-radius:5px; padding:4px 8px; font:12px sans-serif; }
      #symphony-reader-tools button[aria-pressed=true] { background:var(--rice-accent);
        color:var(--rice-bg); }
      @media (prefers-reduced-motion:reduce) { #symphony-reader-tools { transition:none; } }
    ` + config.customCSS;
    putStyle(document, 'symphony-ui-style', ui);
    const bookCSS = `
      html,body { background-color:${c.background}!important; color:${c.foreground}!important; }
      body { font-family:${JSON.stringify(s.fontFamily)},serif!important; font-size:${s.fontSize}px!important;
        line-height:${s.lineHeight}!important; }
      :is(p,li,blockquote,dd,dt) { color:${c.foreground}!important;
        font-family:${JSON.stringify(s.fontFamily)},serif!important;
        font-size:${s.fontSize}px!important; line-height:${s.lineHeight}!important; }
      p { margin-block-end:${s.paragraphSpacing}em!important; }
      a { color:${p.accent}!important; text-decoration:underline; }
      :is(pre,code) { font-family:monospace!important; }
    `;

    function visit(root, isBook = false) {
      if (!observers.has(root)) {
        observers.add(root);
        const observer = new MutationObserver(schedule);
        observer.observe(root, {childList:true, subtree:true});
      }
      if (isBook && root.querySelector('p,li,blockquote') &&
          !root.querySelector('canvas,.pdfViewer,meta[name="viewport"]')) {
        putStyle(root, 'symphony-book-style', bookCSS);
      }
      for (const frame of root.querySelectorAll('iframe')) {
        if (!frames.has(frame)) {
          frames.add(frame);
          frame.addEventListener('load', schedule);
        }
        try {
          if (frame.contentDocument) visit(frame.contentDocument, true);
        } catch (_) { /* Cross-origin resources keep their upstream presentation. */ }
      }
      for (const element of root.querySelectorAll('*')) {
        if (element.shadowRoot) visit(element.shadowRoot, isBook);
      }
    }
    visit(document);
    let tools = document.getElementById('symphony-reader-tools');
    if (!tools && document.body) {
      tools = document.createElement('nav');
      tools.id = 'symphony-reader-tools';
      tools.setAttribute('aria-label', 'Оформление чтения');
      for (const [profile, label, key] of [['rice','Rice','1'], ['paper','Бумага','2'], ['warm','Тёплый','3']]) {
        const button = document.createElement('button');
        button.textContent = label;
        button.dataset.profile = profile;
        button.title = `Ctrl+Alt+${key}`;
        button.onclick = () => choose(profile);
        tools.appendChild(button);
      }
      document.body.appendChild(tools);
    }
    if (tools) {
      for (const button of tools.querySelectorAll('button')) {
        const active = button.dataset.profile === (chosen || s.profile);
        const value = String(active);
        if (button.getAttribute('aria-pressed') !== value) button.setAttribute('aria-pressed', value);
      }
    }
  }

  function schedule() {
    if (!scheduled) {
      scheduled = true;
      requestAnimationFrame(render);
    }
  }

  function choose(profile) {
    chosen = profile;
    localStorage.setItem('symphony-reading-profile', profile);
    schedule();
  }

  document.addEventListener('keydown', event => {
    if (!event.ctrlKey || !event.altKey) return;
    const profile = {'Digit1':'rice','Digit2':'paper','Digit3':'warm'}[event.code];
    if (profile) { event.preventDefault(); choose(profile); }
  });
  window.addEventListener('storage', event => {
    if (event.key === 'symphony-reading-profile') { chosen = event.newValue; schedule(); }
  });
  window.__symphonyRice = {update(value) {
    if (value.settings.profile !== config.settings.profile) {
      chosen = null;
      localStorage.removeItem('symphony-reading-profile');
    }
    config = value;
    schedule();
  }};
  render();
};
