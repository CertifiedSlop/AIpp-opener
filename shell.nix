{ pkgs ? import <nixpkgs> {} }:

pkgs.mkShell {
  name = "aipp-opener";

  buildInputs = with pkgs; [
    # Python and dependencies
    python311
    python311Packages.pip

    # Python packages from nixpkgs (for faster setup)
    python311Packages.requests
    python311Packages.pydantic
    python311Packages.pyyaml
    python311Packages.pillow
    python311Packages.fuzzywuzzy
    python311Packages.levenshtein

    # Optional: Speech recognition (for voice input)
    portaudio

    # Optional: System notifications
    libnotify

    # Development tools
    git

    # GUI support
    python311Packages.tkinter
  ];

  shellHook = ''
    echo "AIpp Opener Development Environment"
    echo "===================================="
    echo "Python: $(python --version)"
    echo ""
    echo "Nix-provided packages are available."
    echo "For additional pip packages, create a virtualenv:"
    echo "  python -m venv venv"
    echo "  source venv/bin/activate"
    echo "  pip install -r requirements.txt"
    echo ""
    echo "Or use: pip install --user <package>"
    echo ""
    echo "To run the GUI: python -m aipp_opener --gui"
    echo "To run CLI: python -m aipp_opener --help"
    echo ""
  '';
}
