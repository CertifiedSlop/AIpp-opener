# Bash completion for aipp-opener
# Place in /etc/bash_completion.d/ or ~/.bash_completion.d/

_aipp_opener() {
    local cur prev opts
    COMPREPLY=()
    cur="${COMP_WORDS[COMP_CWORD]}"
    prev="${COMP_WORDS[COMP_CWORD-1]}"
    
    opts="-h --help -i --interactive -v --voice --gui --tray --list-apps --config --suggest --no-notifications --no-history"
    actions="open launch start run"
    common_apps="firefox chrome chromium code vlc spotify discord slack steam gimp blender"
    
    if [[ ${cur} == -* ]]; then
        COMPREPLY=( $(compgen -W "${opts}" -- ${cur}) )
        return 0
    fi
    
    # If previous word is an option that takes an argument
    case "${prev}" in
        --suggest|-s)
            COMPREPLY=( $(compgen -W "browser editor terminal media game" -- ${cur}) )
            return 0
            ;;
        --provider)
            COMPREPLY=( $(compgen -W "ollama gemini openai openrouter" -- ${cur}) )
            return 0
            ;;
    esac
    
    # Check if we're at the first argument (command position)
    if [[ ${COMP_CWORD} -eq 1 ]]; then
        COMPREPLY=( $(compgen -W "${opts} ${actions}" -- ${cur}) )
        return 0
    fi
    
    # Default: suggest common apps
    COMPREPLY=( $(compgen -W "${common_apps}" -- ${cur}) )
}

complete -F _aipp_opener python3
complete -F _aipp_opener python
complete -F _aipp_opener aipp-opener
