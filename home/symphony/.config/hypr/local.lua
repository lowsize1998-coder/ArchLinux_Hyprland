-- Personal overrides go here; Symphony theme switching keeps this file.

-- BEGIN myvault-codex-cli
hl.bind("SUPER + G", hl.dsp.exec_cmd("/home/rozetta/.local/bin/myvault-codex-window"), {description = "Codex CLI"})
-- END myvault-codex-cli

-- BEGIN lazyvim-go-shortcuts
-- Physical N works with both US and RU keyboard layouts.
hl.unbind("ALT + N")
hl.bind("ALT + code:57", hl.dsp.exec_cmd("/home/rozetta/.local/bin/lazyvim-go-window"), {description = "LazyVim Go"})
hl.bind("ALT + SHIFT + code:57", hl.dsp.exec_cmd("/home/rozetta/.local/bin/lazyvim-go-window --lab"), {description = "LazyVim Go practice"})
-- END lazyvim-go-shortcuts

-- Keep pointer speed constant regardless of mouse movement speed.
hl.config({input = {accel_profile = "flat"}})

-- Disable Symphony's Alt+Q shortcut for Yazi.
hl.unbind("ALT + Q")
hl.unbind("SUPER + E")

-- Personal app shortcuts; physical W/T also work with the RU layout.
hl.unbind("SUPER + W")
hl.unbind("SUPER + T")
hl.bind("SUPER + code:25", hl.dsp.exec_cmd("ghostty -e yazi"), {description = "Yazi"})
hl.bind("SUPER + code:28", hl.dsp.exec_cmd("Telegram"), {description = "Telegram"})

-- BEGIN zathura-rice
-- Physical Z works with both US and RU keyboard layouts.
hl.bind("SUPER + code:52", hl.dsp.exec_cmd("/home/rozetta/.local/bin/zathura-rice"), {description = "Zathura Reader"})
hl.window_rule({name = "zathura-readable", match = {class = "^(org[.]pwmt[.]zathura|Zathura|zathura)$"}, opacity = "1 1"})

-- GTK can consume Alt in multilingual keyboard layouts. Handle these physical
-- number keys in Hyprland, and enable them only while Zathura has focus.
local reader_profile_bindings = {}
local function is_reader(window)
    if not window then return false end
    return window.class == "org.pwmt.zathura" or window.class == "Zathura" or window.class == "zathura"
end
local function update_reader_bindings(window)
    local enabled = is_reader(window)
    for _, binding in ipairs(reader_profile_bindings) do
        binding:set_enabled(enabled)
    end
end
for _, entry in ipairs({{"rice", 10}, {"paper", 11}, {"warm", 12}, {"original", 19}}) do
    local profile = entry[1]
    local binding = hl.bind("ALT + code:" .. entry[2], function()
        local window = hl.get_active_window()
        if is_reader(window) then
            hl.exec_cmd("/home/rozetta/.local/bin/zathura-rice profile " .. profile .. " org.pwmt.zathura.PID-" .. window.pid)
        end
    end, {description = "Zathura profile: " .. profile})
    binding:set_enabled(false)
    table.insert(reader_profile_bindings, binding)
end
-- Opacity controls share the same focus guard as the reading profiles.
for _, entry in ipairs({
    {"CTRL + ALT + Down", "down", "Zathura opacity: decrease"},
    {"CTRL + ALT + Up", "up", "Zathura opacity: increase"},
    {"CTRL + ALT + code:19", "reset", "Zathura opacity: reset"},
}) do
    local binding = hl.bind(entry[1], hl.dsp.exec_cmd("python3 /home/rozetta/.config/zathura/opacity.py " .. entry[2]),
        {description = entry[3], repeating = entry[2] ~= "reset"})
    binding:set_enabled(false)
    table.insert(reader_profile_bindings, binding)
end
hl.on("window.active", update_reader_bindings)
hl.on("window.class", function() update_reader_bindings(hl.get_active_window()) end)
update_reader_bindings(hl.get_active_window())
-- END zathura-rice


-- BEGIN desktop-monitor-layout
-- Main DP-2 keeps 2560x1440 at 240 Hz and position 0x0.
-- BenQ XL2411P: 1920x1080 at 144 Hz, immediately on the left.
hl.monitor({output = "desc:BNQ ZOWIE XL LCD", mode = "1920x1080@144", position = "-1920x0", scale = 1})
-- END desktop-monitor-layout


-- BEGIN dual-monitor-workflow
-- Workspaces have predictable monitor ownership; no applications are auto-launched.
local main_display = "DP-2"
local side_display = "desc:BNQ ZOWIE XL LCD"
for id = 1, 5 do
    hl.workspace_rule({workspace = tostring(id), monitor = main_display, persistent = true})
end
for id = 6, 10 do
    hl.workspace_rule({workspace = tostring(id), monitor = side_display, persistent = true, default = id == 6})
end
-- Physical comma/period keys work in US and RU layouts.
hl.bind("SUPER + code:59", hl.dsp.focus({monitor = side_display}), {description = "Focus left monitor"})
hl.bind("SUPER + code:60", hl.dsp.focus({monitor = main_display}), {description = "Focus main monitor"})
hl.bind("SUPER + SHIFT + code:59", hl.dsp.window.move({monitor = side_display, follow = false}), {description = "Send window to left monitor"})
hl.bind("SUPER + SHIFT + code:60", hl.dsp.window.move({monitor = main_display, follow = false}), {description = "Send window to main monitor"})
-- END dual-monitor-workflow

-- BEGIN spotify-mini
-- A normal floating controller on the invoking monitor, without pinning.
hl.window_rule({name = "spotify-mini", match = {class = "^dreamcore-spotify-mini$"}, float = true, size = "480 190", center = true})
-- END spotify-mini

-- BEGIN waybar-display-mode
-- Physical B works with both US and RU keyboard layouts.
hl.bind("SUPER + SHIFT + code:56", hl.dsp.exec_cmd("/home/rozetta/.local/bin/waybar-mode-menu"), {description = "Waybar: choose display mode"})
-- END waybar-display-mode

