"""Tests for async detector base module."""

import unittest
import asyncio
from unittest.mock import patch, MagicMock, AsyncMock


class TestAppInfo(unittest.TestCase):
    """Tests for AppInfo dataclass."""

    def test_app_info_minimal(self):
        """Test AppInfo with minimal required fields."""
        from aipp_opener.async_detector_base import AppInfo

        app = AppInfo(name="test-app", executable="/usr/bin/test")
        self.assertEqual(app.name, "test-app")
        self.assertEqual(app.executable, "/usr/bin/test")
        self.assertIsNone(app.display_name)
        self.assertIsNone(app.description)
        self.assertIsNone(app.categories)
        self.assertIsNone(app.icon)

    def test_app_info_full(self):
        """Test AppInfo with all fields."""
        from aipp_opener.async_detector_base import AppInfo

        app = AppInfo(
            name="firefox",
            executable="/usr/bin/firefox",
            display_name="Firefox Browser",
            description="A web browser",
            categories=["browser", "network"],
            icon="firefox-icon"
        )
        self.assertEqual(app.name, "firefox")
        self.assertEqual(app.executable, "/usr/bin/firefox")
        self.assertEqual(app.display_name, "Firefox Browser")
        self.assertEqual(app.description, "A web browser")
        self.assertEqual(app.categories, ["browser", "network"])
        self.assertEqual(app.icon, "firefox-icon")

    def test_app_info_to_dict(self):
        """Test AppInfo conversion to dict."""
        from aipp_opener.async_detector_base import AppInfo

        app = AppInfo(
            name="test",
            executable="/test",
            display_name="Test App"
        )
        # dataclass should have __dict__
        self.assertTrue(hasattr(app, '__dict__'))


class TestAsyncAppDetector(unittest.TestCase):
    """Tests for AsyncAppDetector abstract base class."""

    def test_async_detector_is_abstract(self):
        """Test that AsyncAppDetector cannot be instantiated directly."""
        from aipp_opener.async_detector_base import AsyncAppDetector

        # Should not be able to instantiate abstract class
        with self.assertRaises(TypeError):
            AsyncAppDetector()

    def test_async_detector_subclass_must_implement_abstract_methods(self):
        """Test that subclasses must implement abstract methods."""
        from aipp_opener.async_detector_base import AsyncAppDetector

        # Create incomplete subclass
        class IncompleteDetector(AsyncAppDetector):
            pass

        # Should not be able to instantiate incomplete subclass
        with self.assertRaises(TypeError):
            IncompleteDetector()

    def test_async_detector_complete_subclass(self):
        """Test a complete implementation of AsyncAppDetector."""
        from aipp_opener.async_detector_base import AsyncAppDetector, AppInfo

        class CompleteDetector(AsyncAppDetector):
            @property
            def name(self) -> str:
                return "test-detector"

            async def is_available(self) -> bool:
                return True

            async def detect(self) -> list[AppInfo]:
                return [AppInfo(name="test", executable="/test")]

            async def refresh(self) -> None:
                pass

        async def run_test():
            detector = CompleteDetector()
            self.assertEqual(detector.name, "test-detector")

            available = await detector.is_available()
            self.assertTrue(available)

            apps = await detector.detect()
            self.assertEqual(len(apps), 1)
            self.assertEqual(apps[0].name, "test")

            await detector.refresh()  # Should not raise

        asyncio.run(run_test())

    def test_async_detector_unavailable(self):
        """Test detector reporting unavailability."""
        from aipp_opener.async_detector_base import AsyncAppDetector, AppInfo

        class UnavailableDetector(AsyncAppDetector):
            @property
            def name(self) -> str:
                return "unavailable"

            async def is_available(self) -> bool:
                return False

            async def detect(self) -> list[AppInfo]:
                return []

            async def refresh(self) -> None:
                pass

        async def run_test():
            detector = UnavailableDetector()
            available = await detector.is_available()
            self.assertFalse(available)

        asyncio.run(run_test())

    def test_async_detector_detect_empty(self):
        """Test detector returning empty app list."""
        from aipp_opener.async_detector_base import AsyncAppDetector, AppInfo

        class EmptyDetector(AsyncAppDetector):
            @property
            def name(self) -> str:
                return "empty"

            async def is_available(self) -> bool:
                return True

            async def detect(self) -> list[AppInfo]:
                return []

            async def refresh(self) -> None:
                pass

        async def run_test():
            detector = EmptyDetector()
            apps = await detector.detect()
            self.assertEqual(apps, [])

        asyncio.run(run_test())


class TestAsyncAppDetectorIntegration(unittest.TestCase):
    """Integration tests for async detector pattern."""

    def test_multiple_detectors_can_coexist(self):
        """Test that multiple detector implementations can coexist."""
        from aipp_opener.async_detector_base import AsyncAppDetector, AppInfo

        class DetectorA(AsyncAppDetector):
            @property
            def name(self) -> str:
                return "detector-a"

            async def is_available(self) -> bool:
                return True

            async def detect(self) -> list[AppInfo]:
                return [AppInfo(name="app-a", executable="/a")]

            async def refresh(self) -> None:
                pass

        class DetectorB(AsyncAppDetector):
            @property
            def name(self) -> str:
                return "detector-b"

            async def is_available(self) -> bool:
                return False

            async def detect(self) -> list[AppInfo]:
                return [AppInfo(name="app-b", executable="/b")]

            async def refresh(self) -> None:
                pass

        async def run_test():
            det_a = DetectorA()
            det_b = DetectorB()

            self.assertEqual(det_a.name, "detector-a")
            self.assertEqual(det_b.name, "detector-b")

            self.assertTrue(await det_a.is_available())
            self.assertFalse(await det_b.is_available())

            apps_a = await det_a.detect()
            apps_b = await det_b.detect()

            self.assertEqual(len(apps_a), 1)
            self.assertEqual(len(apps_b), 1)
            self.assertEqual(apps_a[0].name, "app-a")
            self.assertEqual(apps_b[0].name, "app-b")

        asyncio.run(run_test())

    def test_detector_app_info_variations(self):
        """Test detector with various AppInfo configurations."""
        from aipp_opener.async_detector_base import AsyncAppDetector, AppInfo

        class VariedDetector(AsyncAppDetector):
            @property
            def name(self) -> str:
                return "varied"

            async def is_available(self) -> bool:
                return True

            async def detect(self) -> list[AppInfo]:
                return [
                    AppInfo(name="minimal", executable="/minimal"),
                    AppInfo(
                        name="full",
                        executable="/full",
                        display_name="Full App",
                        description="A full app",
                        categories=["test"],
                        icon="icon"
                    ),
                    AppInfo(name="no-icon", executable="/no-icon", categories=["test"]),
                    AppInfo(name="no-cats", executable="/no-cats", icon="icon"),
                ]

            async def refresh(self) -> None:
                pass

        async def run_test():
            detector = VariedDetector()
            apps = await detector.detect()

            self.assertEqual(len(apps), 4)

            # Check minimal app
            self.assertEqual(apps[0].name, "minimal")
            self.assertIsNone(apps[0].display_name)

            # Check full app
            self.assertEqual(apps[1].display_name, "Full App")
            self.assertEqual(apps[1].description, "A full app")
            self.assertEqual(apps[1].categories, ["test"])
            self.assertEqual(apps[1].icon, "icon")

            # Check no-icon app
            self.assertIsNone(apps[2].icon)

            # Check no-cats app
            self.assertIsNone(apps[3].categories)

        asyncio.run(run_test())


if __name__ == "__main__":
    unittest.main()
