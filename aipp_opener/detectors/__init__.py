"""App detection modules for AIpp Opener."""

from aipp_opener.detectors.base import AppDetector, AppInfo
from aipp_opener.detectors.debian import DebianAppDetector
from aipp_opener.detectors.nixos import NixOSAppDetector

__all__ = ["AppDetector", "AppInfo", "NixOSAppDetector", "DebianAppDetector"]
