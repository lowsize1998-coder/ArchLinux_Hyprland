#
# ~/.bash_profile
#

[[ -f ~/.bashrc ]] && . ~/.bashrc

# Symphony paths
export PATH="$HOME/.local/bin:$HOME/dotfiles/scripts:$HOME/dotfiles/install/themes:$HOME/.config/hypr/scripts:$PATH"
export MPD_HOST="$XDG_RUNTIME_DIR/mpd/socket"
