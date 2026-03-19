"""App detection modules for AIpp Opener."""

from aipp_opener.detectors.base import AppDetector, AppInfo
from aipp_opener.detectors.debian import DebianAppDetector
from aipp_opener.detectors.nixos import NixOSAppDetector
from aipp_opener.detectors.fedora import FedoraAppDetector
from aipp_opener.detectors.arch import ArchAppDetector

__all__ = [
    "AppDetector",
    "AppInfo",
    "NixOSAppDetector",
    "DebianAppDetector",
    "FedoraAppDetector",
    "ArchAppDetector",
]
