"""Tests for native sync detection and filtering."""

import os
import unittest

from mackup.appsdb import ApplicationsDatabase
from mackup.config import Config


class TestNativeSyncAppsDB(unittest.TestCase):
    """Test ApplicationsDatabase native sync metadata parsing."""

    def setUp(self):
        realpath = os.path.dirname(os.path.realpath(__file__))
        os.environ["HOME"] = os.path.join(realpath, "fixtures")
        os.environ.pop("XDG_CONFIG_HOME", None)

    def test_spotify_has_native_sync(self):
        """Spotify should be flagged as having native sync."""
        app_db = ApplicationsDatabase()
        assert app_db.has_native_sync("spotify")

    def test_spotify_sync_mechanism(self):
        """Spotify should report vendor_account as sync mechanism."""
        app_db = ApplicationsDatabase()
        assert app_db.get_sync_mechanism("spotify") == "vendor_account"

    def test_vscode_has_native_sync(self):
        """VS Code should be flagged as having native sync."""
        app_db = ApplicationsDatabase()
        assert app_db.has_native_sync("vscode")

    def test_vscode_sync_mechanism(self):
        """VS Code should report settings_sync as sync mechanism."""
        app_db = ApplicationsDatabase()
        assert app_db.get_sync_mechanism("vscode") == "settings_sync"

    def test_bash_no_native_sync(self):
        """Bash should not have native sync."""
        app_db = ApplicationsDatabase()
        # Bash is a standard app without native sync
        if "bash" in app_db.apps:
            assert not app_db.has_native_sync("bash")

    def test_get_native_sync_apps_returns_set(self):
        """get_native_sync_apps should return a non-empty set."""
        app_db = ApplicationsDatabase()
        native_apps = app_db.get_native_sync_apps()
        assert isinstance(native_apps, set)
        assert len(native_apps) > 0

    def test_native_sync_apps_include_known_apps(self):
        """Known native-sync apps should appear in the set."""
        app_db = ApplicationsDatabase()
        native_apps = app_db.get_native_sync_apps()
        assert "spotify" in native_apps
        assert "vscode" in native_apps
        assert "pycharm" in native_apps

    def test_sync_mechanism_empty_for_untagged_app(self):
        """Apps without sync_info should return empty mechanism."""
        app_db = ApplicationsDatabase()
        if "bash" in app_db.apps:
            assert app_db.get_sync_mechanism("bash") == ""


class TestNativeSyncConfig(unittest.TestCase):
    """Test Config parsing for include_native_sync option."""

    def setUp(self):
        realpath = os.path.dirname(os.path.realpath(__file__))
        os.environ["HOME"] = os.path.join(realpath, "fixtures")
        os.environ.pop("XDG_CONFIG_HOME", None)
        os.environ.pop("MACKUP_CONFIG", None)

    def test_default_excludes_native_sync(self):
        """By default, include_native_sync should be False."""
        cfg = Config()
        assert cfg.include_native_sync is False

    def test_include_native_sync_true(self):
        """Config with include_native_sync = true should parse correctly."""
        cfg = Config("mackup-include-native-sync.cfg")
        assert cfg.include_native_sync is True

    def test_explicit_app_override(self):
        """Apps explicitly listed in [applications_to_sync] should be kept."""
        cfg = Config("mackup-explicit-native-sync-app.cfg")
        assert "spotify" in cfg.apps_to_sync
