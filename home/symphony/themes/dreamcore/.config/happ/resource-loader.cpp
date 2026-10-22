#include <QtCore/QResource>
#include <QtCore/QString>
#include <cstdio>
#include <cstdlib>

// Loaded only into Happ. Register colors before the app's built-in resources.
__attribute__((constructor)) static void registerDreamcoreTheme() {
    const char *path = std::getenv("HAPP_DREAMCORE_RESOURCE");
    if (path && !QResource::registerResource(QString::fromUtf8(path)))
        std::fprintf(stderr, "Happ Dreamcore: could not load the color resource\n");
    // Child processes (daemon, proxy cores) must not inherit this GUI overlay.
    const char *previous = std::getenv("HAPP_DREAMCORE_PREVIOUS_PRELOAD");
    if (previous && *previous)
        setenv("LD_PRELOAD", previous, 1);
    else
        unsetenv("LD_PRELOAD");
    unsetenv("HAPP_DREAMCORE_RESOURCE");
    unsetenv("HAPP_DREAMCORE_PREVIOUS_PRELOAD");
}
