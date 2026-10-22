#
# ~/.bashrc
#

# If not running interactively, don't do anything
[[ $- != *i* ]] && return

alias ls='ls --color=auto'
alias grep='grep --color=auto'
PS1='[\u@\h \W]\$ '

# >>> Codex installer >>>
export PATH="/home/rozetta/.local/bin:$PATH"
# <<< Codex installer <<<

# Symphony paths
export PATH="$HOME/.local/bin:$HOME/dotfiles/scripts:$HOME/dotfiles/install/themes:$HOME/.config/hypr/scripts:$PATH"
export MPD_HOST="$XDG_RUNTIME_DIR/mpd/socket"
