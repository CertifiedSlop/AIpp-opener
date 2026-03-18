# Zsh completion for aipp-opener
# Place in /etc/zsh/completion.d/ or ~/.zsh/completion.d/

#compdef aipp-opener

local -a opts
opts=(
  '-h[Show help message]'
  '-i[Run in interactive mode]'
  '-v[Enable voice input mode]'
  '--gui[Open GUI interface]'
  '--tray[Run in system tray mode]'
  '--list-apps[List detected applications]'
  '--config[Show configuration]'
  '--help[Show detailed help]'
  '--interactive[Run in interactive mode]'
  '--voice[Enable voice input mode]'
  '--no-notifications[Disable system notifications]'
  '--no-history[Disable usage history]'
  '-s[Get app suggestions]:QUERY: '
  '--suggest[Get app suggestions]:QUERY: '
  '--provider[AI provider]:PROVIDER:(ollama gemini openai openrouter)'
)

local -a actions
actions=(
  'open:Open an application'
  'launch:Launch an application'
  'start:Start an application'
  'run:Run an application'
)

local -a common_apps
common_apps=(
  'firefox:Mozilla Firefox'
  'chrome:Google Chrome'
  'chromium:Chromium Browser'
  'code:Visual Studio Code'
  'vlc:VLC Media Player'
  'spotify:Spotify'
  'discord:Discord'
  'slack:Slack'
  'steam:Steam'
  'gimp:GIMP'
  'blender:Blender'
  'terminal:Terminal Emulator'
  'nautilus:File Manager'
  'thunderbird:Thunderbird'
)

if [[ $CURRENT -eq 2 ]]; then
  _describe 'options and actions' opts actions
  return
fi

if [[ ${words[2]} == (-s|--suggest) ]]; then
  _message 'search query'
  return
fi

if [[ ${words[2]} == --provider ]]; then
  _values 'AI provider' ollama gemini openai openrouter
  return
fi

# After action words, suggest apps
if [[ ${words[2]} == (open|launch|start|run) ]]; then
  _describe 'applications' common_apps
  return
fi

_default
