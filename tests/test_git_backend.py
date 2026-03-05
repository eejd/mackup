"""Unit tests for git storage backend."""

import os
import tempfile
import unittest
from unittest.mock import MagicMock, mock_open, patch

from mackup.config import Config
from mackup.constants import ENGINE_GIT
from mackup.mackup import Mackup


class TestGitBackendConfig(unittest.TestCase):
    """Test git backend configuration parsing."""

    def test_git_engine_recognized(self):
        """Test that ENGINE_GIT is recognized as a valid engine."""
        config_content = """[storage]
engine = git
path = .dotfiles
directory = mackup
"""
        with patch("builtins.open", mock_open(read_data=config_content)):
            with patch("os.path.isfile", return_value=True):
                cfg = Config()
                self.assertEqual(cfg.engine, ENGINE_GIT)

    def test_git_default_settings(self):
        """Test that git has sensible default settings."""
        config_content = """[storage]
engine = git
path = .dotfiles
directory = mackup
"""
        with patch("builtins.open", mock_open(read_data=config_content)):
            with patch("os.path.isfile", return_value=True):
                cfg = Config()
                self.assertTrue(cfg.git_auto_commit)
                self.assertFalse(cfg.git_auto_push)
                self.assertEqual(cfg.git_remote, "origin")
                self.assertEqual(cfg.git_branch, "main")
                self.assertIn("{action}", cfg.git_commit_message_format)

    def test_git_custom_settings(self):
        """Test custom git configuration options."""
        config_content = """[storage]
engine = git
path = .dotfiles
directory = mackup

[git]
auto_commit = false
auto_push = true
remote = upstream
branch = develop
commit_message_format = backup: {app_name} at {timestamp}
"""
        with patch("builtins.open", mock_open(read_data=config_content)):
            with patch("os.path.isfile", return_value=True):
                cfg = Config()
                self.assertFalse(cfg.git_auto_commit)
                self.assertTrue(cfg.git_auto_push)
                self.assertEqual(cfg.git_remote, "upstream")
                self.assertEqual(cfg.git_branch, "develop")
                self.assertEqual(
                    cfg.git_commit_message_format,
                    "backup: {app_name} at {timestamp}",
                )

    def test_git_path_handling(self):
        """Test that git engine handles path like file_system."""
        config_content = """[storage]
engine = git
path = .dotfiles/mackup-store
directory = configs
"""
        with patch("builtins.open", mock_open(read_data=config_content)):
            with patch("os.path.isfile", return_value=True):
                with patch.dict(os.environ, {"HOME": "/home/user"}):
                    cfg = Config()
                    self.assertEqual(cfg.engine, ENGINE_GIT)
                    self.assertIn(".dotfiles/mackup-store", cfg.path)
                    self.assertEqual(cfg.directory, "configs")


class TestGitBackendOperations(unittest.TestCase):
    """Test git backend operations."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.config_content = f"""[storage]
engine = git
path = {self.temp_dir}
directory = mackup

[git]
auto_commit = true
auto_push = false
"""

    def test_is_git_backend(self):
        """Test is_git_backend() detection."""
        with patch("builtins.open", mock_open(read_data=self.config_content)):
            with patch("os.path.isfile", return_value=True):
                with patch("os.path.isdir", return_value=True):
                    mckp = Mackup()
                    self.assertTrue(mckp.is_git_backend())

    def test_git_init_creates_repo(self):
        """Test that git_init_if_needed() initializes a repository."""
        with patch("builtins.open", mock_open(read_data=self.config_content)):
            with patch("os.path.isfile", return_value=True):
                with patch("os.path.isdir") as mock_isdir:
                    # Mackup folder exists, but .git does not
                    mock_isdir.side_effect = lambda path: ".git" not in path

                    with patch("subprocess.run") as mock_run:
                        mock_run.return_value = MagicMock(returncode=0)

                        mckp = Mackup()
                        mckp.git_init_if_needed()

                        # Verify git init was called
                        mock_run.assert_called_once()
                        args = mock_run.call_args[0][0]
                        self.assertEqual(args[0], "git")
                        self.assertEqual(args[1], "init")

    def test_git_commit_with_changes(self):
        """Test git commit when there are changes."""
        with patch("builtins.open", mock_open(read_data=self.config_content)):
            with patch("os.path.isfile", return_value=True):
                with patch("os.path.isdir", return_value=True):
                    with patch("subprocess.run") as mock_run:
                        # git diff returns 1 (changes exist)
                        mock_run.return_value = MagicMock(returncode=1)

                        mckp = Mackup()
                        mckp.git_commit("backup", "test-app")

                        # Should have called: git add, git diff, git commit
                        self.assertEqual(mock_run.call_count, 3)

    def test_git_commit_no_changes(self):
        """Test git commit when there are no changes."""
        with patch("builtins.open", mock_open(read_data=self.config_content)):
            with patch("os.path.isfile", return_value=True):
                with patch("os.path.isdir", return_value=True):
                    with patch("subprocess.run") as mock_run:
                        # git diff returns 0 (no changes)
                        mock_run.return_value = MagicMock(returncode=0)

                        mckp = Mackup()
                        mckp.git_commit("backup", "test-app")

                        # Should have called: git add, git diff (but not commit)
                        self.assertEqual(mock_run.call_count, 2)

    def test_git_push_when_enabled(self):
        """Test git push when auto_push is enabled."""
        config_with_push = self.config_content.replace(
            "auto_push = false", "auto_push = true",
        )
        with patch("builtins.open", mock_open(read_data=config_with_push)):
            with patch("os.path.isfile", return_value=True):
                with patch("os.path.isdir", return_value=True):
                    with patch("subprocess.run") as mock_run:
                        mock_run.return_value = MagicMock(returncode=0)

                        mckp = Mackup()
                        mckp.git_push()

                        # Verify git push was called
                        mock_run.assert_called_once()
                        args = mock_run.call_args[0][0]
                        self.assertEqual(args[0], "git")
                        self.assertEqual(args[1], "push")

    def test_git_pull_with_remote(self):
        """Test git pull when remote is configured."""
        with patch("builtins.open", mock_open(read_data=self.config_content)):
            with patch("os.path.isfile", return_value=True):
                with patch("os.path.isdir", return_value=True):
                    with patch("subprocess.run") as mock_run:
                        # First call (check remote) succeeds, second call (pull) succeeds
                        mock_run.return_value = MagicMock(returncode=0)

                        mckp = Mackup()
                        result = mckp.git_pull()

                        # Should succeed
                        self.assertTrue(result)
                        # Should have called: git remote get-url, git pull
                        self.assertEqual(mock_run.call_count, 2)

    def test_git_operations_skipped_for_non_git_engine(self):
        """Test that git operations are skipped for non-git engines."""
        non_git_config = """[storage]
engine = file_system
path = .dotfiles
directory = mackup
"""
        with patch("builtins.open", mock_open(read_data=non_git_config)):
            with patch("os.path.isfile", return_value=True):
                with patch("os.path.isdir", return_value=True):
                    with patch("subprocess.run") as mock_run:
                        mckp = Mackup()

                        self.assertFalse(mckp.is_git_backend())
                        mckp.git_init_if_needed()
                        mckp.git_commit("backup", "test")
                        mckp.git_push()
                        result = mckp.git_pull()

                        # No git commands should have been called
                        mock_run.assert_not_called()
                        # git_pull should still return True (success)
                        self.assertTrue(result)


if __name__ == "__main__":
    unittest.main()
