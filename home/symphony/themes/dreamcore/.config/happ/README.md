# Happ Dreamcore

The official Happ 4.3.0 build 318 uses a local Qt resource overlay for its two
QML color singletons. All 123 original color properties are covered. The packaged
binary, subscription database, routing, connection preferences, daemon and system
Qt settings are unchanged.

Colors are read from the shared palette.json and derived.json. color-roles.json
maps Happ's properties to palette roles. build-theme.py generates the two QML
singletons and theme.rcc under ~/.local/share/happ-dreamcore. It uses the already
installed Qt resource compiler. resource-loader.cpp registers that resource before
Happ's embedded resources. No polling, extra animation or disk-cache disabling
is added. Proxy child processes do not inherit the loader.

Launch **Happ** from Rofi, or run ~/.local/bin/happ-dreamcore. The user desktop
entry overrides the system entry. The loader applies only while Dreamcore is the
active Symphony theme; subsequent launches under another theme use native colors.
Restart Happ's GUI after switching themes. An already running instance keeps its
loaded palette. The ordinary /usr/bin/happ still launches the original app.

The tested binary hash is checked at launch. After an app update, native colors
are used until the new theme properties have been checked. Palette edits rebuild
the resource on the next launch; there is no background watcher.

Rebuild the GUI loader if needed:

```sh
./build-loader.sh
```

It links only stable Qt 6 Core APIs and uses Happ's bundled Qt at runtime. The
version-tag macro is disabled because the installed development headers are newer
than the bundled runtime; no newer Qt API is used.

To return to native colors, quit Happ's GUI and launch /usr/bin/happ. To restore
Rofi's original entry permanently, remove the user Happ.desktop override (or
restore its backup if one existed). The launcher can remain unused.

Backups and verification are stored privately under ~/.local/state/happ-dreamcore.
No subscription links, passwords, keys or account data belong in this directory
of reusable theme sources.
