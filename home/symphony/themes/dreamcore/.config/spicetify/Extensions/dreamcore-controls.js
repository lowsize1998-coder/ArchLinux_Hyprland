// Local Dreamcore controls. No external requests, keyboard bindings or polling.
(function dreamcoreControls(attempt = 0) {
    if (!Spicetify.Player?.setVolume || !document.querySelector('.Root__main-view')) {
        if (attempt < 50) setTimeout(() => dreamcoreControls(attempt + 1), 200);
        return;
    }
    const volumeSelector = '.main-nowPlayingBar-volumeBar, .volume-bar, #fad-volume';
    function wheelVolume(event) {
        if (!event.target.closest?.(volumeSelector) || event.altKey || event.metaKey || !event.deltaY) return;
        event.preventDefault();
        event.stopImmediatePropagation();
        const step = event.ctrlKey ? .01 : event.shiftKey ? .05 : .02;
        const value = Math.max(0, Math.min(1, Spicetify.Player.getVolume() + (event.deltaY < 0 ? step : -step)));
        Spicetify.Player.setVolume(value);
    }
    document.addEventListener('wheel', wheelVolume, {capture:true, passive:false});

    // The music filter removes podcast shelves without hiding unrelated music.
    function musicOnlyHome() {
        if (!['/', '/home'].includes(Spicetify.Platform.History.location.pathname)) return;
        for (const video of document.querySelectorAll('[data-testid="home-ads-container"] video')) {
            video.autoplay = false;
            video.loop = false;
            if (!video.paused) video.pause();
        }
        const music = document.querySelector('.Root__main-view button[role="checkbox"][aria-label="Music"]');
        if (music?.getAttribute('aria-checked') === 'false') music.click();
    }
    let scheduled = false;
    const observer = new MutationObserver(() => {
        if (scheduled) return;
        scheduled = true;
        setTimeout(() => { scheduled = false; musicOnlyHome(); }, 100);
    });
    observer.observe(document.querySelector('.Root__main-view'), {childList:true, subtree:true});
    musicOnlyHome();
    window.DreamcoreSpotifyControls = {wheelVolume};
})();
