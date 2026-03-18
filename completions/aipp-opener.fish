# Fish completion for aipp-opener
# Place in ~/.config/fish/completions/

complete -c aipp-opener -s h -l help -d "Show help message"
complete -c aipp-opener -s i -l interactive -d "Run in interactive mode"
complete -c aipp-opener -s v -l voice -d "Enable voice input mode"
complete -c aipp-opener -l gui -d "Open GUI interface"
complete -c aipp-opener -l tray -d "Run in system tray mode"
complete -c aipp-opener -l list-apps -d "List detected applications"
complete -c aipp-opener -l config -d "Show configuration"
complete -c aipp-opener -l no-notifications -d "Disable system notifications"
complete -c aipp-opener -l no-history -d "Disable usage history"

complete -c aipp-opener -s s -l suggest -d "Get app suggestions" -r

complete -c aipp-opener -l provider -d "AI provider" -f -a "
    ollama\t'Local Ollama inference'
    gemini\t'Google Gemini AI'
    openai\t'OpenAI GPT models'
    openrouter\t'Multi-model via OpenRouter'
"

# Action completions
complete -c aipp-opener -n "__fish_use_subcommand" -a "open" -d "Open an application"
complete -c aipp-opener -n "__fish_use_subcommand" -a "launch" -d "Launch an application"
complete -c aipp-opener -n "__fish_use_subcommand" -a "start" -d "Start an application"
complete -c aipp-opener -n "__fish_use_subcommand" -a "run" -d "Run an application"

# Common applications
complete -c aipp-opener -n "__fish_seen_subcommand_from open launch start run" -a "
    firefox\t'Mozilla Firefox'
    chrome\t'Google Chrome'
    chromium\t'Chromium Browser'
    code\t'Visual Studio Code'
    vlc\t'VLC Media Player'
    spotify\t'Spotify'
    discord\t'Discord'
    slack\t'Slack'
    steam\t'Steam'
    gimp\t'GIMP Image Editor'
    blender\t'Blender 3D'
    terminal\t'Terminal Emulator'
    nautilus\t'File Manager'
    thunderbird\t'Mozilla Thunderbird'
"
