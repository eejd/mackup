"""
The Mackup Class.

The Mackup class is keeping all the state that Mackup needs to keep during its
runtime. It also provides easy to use interface that is used by the Mackup UI.
The only UI for now is the command line.
"""

import os
import os.path
import shutil
import subprocess
import tempfile
from datetime import datetime, timezone
from typing import Optional

from . import appsdb, config, utils
from .constants import ENGINE_GIT


class Mackup:
    """Main Mackup class."""

    def __init__(self, config_file: Optional[str] = None) -> None:
        """Mackup Constructor."""
        self._config: config.Config = config.Config(config_file)

        self.mackup_folder: str = self._config.fullpath
        self.temp_folder: str = tempfile.mkdtemp(prefix="mackup_tmp_")

    def check_for_usable_environment(self) -> None:
        """Check if the current env is usable and has everything's required."""

        # Allow only explicit superuser usage
        if os.geteuid() == 0 and not utils.CAN_RUN_AS_ROOT:
            utils.error(
                "Running Mackup as superuser can be dangerous."
                " Don't do it unless you know what you're doing!"
                " Run mackup --help for guidance.",
            )

        # Do we have a folder set to save Mackup content into?
        if not os.path.isdir(self._config.path):
            utils.error(
                f"Unable to find the storage folder: {self._config.path}",
            )

        # Is Sublime Text running?
        # if is_process_running('Sublime Text'):
        #    error("Sublime Text is running. It is known to cause problems"
        #          " when Sublime Text is running while I backup or restore"
        #          " its configuration files. Please close Sublime Text and"
        #          " run me again.")

    def check_for_usable_backup_env(self) -> None:
        """Check if the current env can be used to back up files."""
        self.check_for_usable_environment()
        self.create_mackup_home()

    def check_for_usable_restore_env(self) -> None:
        """Check if the current env can be used to restore files."""
        self.check_for_usable_environment()

        if not os.path.isdir(self.mackup_folder):
            utils.error(
                f"Unable to find the Mackup folder: {self.mackup_folder}\n"
                "You might want to back up some files or get your"
                " storage directory synced first.",
            )

    def clean_temp_folder(self) -> None:
        """Delete the temp folder and files created while running."""
        shutil.rmtree(self.temp_folder)

    def create_mackup_home(self) -> None:
        """If the Mackup home folder does not exist, create it."""
        if not os.path.isdir(self.mackup_folder):
            if utils.confirm(
                "Mackup needs a directory to store your"
                " configuration files\n"
                f"Do you want to create it now? <{self.mackup_folder}>",
            ):
                os.makedirs(self.mackup_folder)
            else:
                utils.error("Mackup can't do anything without a home =(")

    def get_apps_to_backup(self) -> set[str]:
        """
        Get the list of applications that should be backed up by Mackup.

        It's the list of allowed apps minus the list of ignored apps.
        Apps with native sync are excluded by default unless the user
        explicitly includes them via [applications_to_sync] or sets
        include_native_sync = true in [storage].

        Returns:
            (set) List of application names to back up
        """
        # Instantiate the app db
        app_db: appsdb.ApplicationsDatabase = appsdb.ApplicationsDatabase()

        # If a list of apps to sync is specified, we only allow those
        # Or we allow every supported app by default
        apps_to_backup: set[str] = self._config.apps_to_sync or app_db.get_app_names()

        # Remove apps with native sync unless overridden
        if not self._config.include_native_sync:
            native_sync_apps = app_db.get_native_sync_apps()
            # Don't remove apps the user explicitly listed in [applications_to_sync]
            explicitly_requested = self._config.apps_to_sync
            for app_name in native_sync_apps:
                if app_name not in explicitly_requested:
                    apps_to_backup.discard(app_name)

        # Remove the specified apps to ignore
        for app_name in self._config.apps_to_ignore:
            apps_to_backup.discard(app_name)

        return apps_to_backup

    def is_git_backend(self) -> bool:
        """Check if using the git storage backend."""
        return self._config.engine == ENGINE_GIT

    def git_init_if_needed(self) -> None:
        """Initialize git repository in the mackup folder if not already init'd."""
        if not self.is_git_backend():
            return

        git_dir = os.path.join(self.mackup_folder, ".git")
        if not os.path.isdir(git_dir):
            try:
                subprocess.run(
                    ["git", "init"],
                    cwd=self.mackup_folder,
                    check=True,
                    capture_output=True,
                    text=True,
                )
                print(f"Initialized git repository in {self.mackup_folder}")
            except subprocess.CalledProcessError as e:
                utils.error(f"Failed to initialize git repository: {e.stderr}")
            except FileNotFoundError:
                utils.error(
                    "git command not found. Please install git to use the git backend.",
                )

    def git_commit(self, action: str, app_name: str = "multiple apps") -> None:
        """
        Commit changes to the git repository.

        Args:
            action: The action performed (backup, restore, uninstall, etc.)
            app_name: The name of the application (or "multiple apps")
        """
        if not self.is_git_backend() or not self._config.git_auto_commit:
            return

        try:
            # Add all changes
            subprocess.run(
                ["git", "add", "-A"],
                cwd=self.mackup_folder,
                check=True,
                capture_output=True,
                text=True,
            )

            # Check if there are changes to commit
            result = subprocess.run(
                ["git", "diff", "--cached", "--exit-code"],
                cwd=self.mackup_folder,
                capture_output=True,
                text=True,
                check=False,
            )

            # Exit code 0 means no changes, 1 means changes exist
            if result.returncode == 0:
                # No changes to commit
                return

            # Format commit message
            timestamp = datetime.now(tz=timezone.utc).isoformat()
            message = self._config.git_commit_message_format.format(
                action=action,
                app_name=app_name,
                timestamp=timestamp,
            )

            # Commit
            subprocess.run(
                ["git", "commit", "-m", message],
                cwd=self.mackup_folder,
                check=True,
                capture_output=True,
                text=True,
            )
            print(f"✓ Git commit: {message}")

        except subprocess.CalledProcessError as e:
            print(f"Warning: Failed to commit changes: {e.stderr}")
        except FileNotFoundError:
            print("Warning: git command not found")

    def git_push(self) -> None:
        """Push commits to the configured remote."""
        if not self.is_git_backend() or not self._config.git_auto_push:
            return

        try:
            remote = self._config.git_remote
            branch = self._config.git_branch

            subprocess.run(
                ["git", "push", remote, branch],
                cwd=self.mackup_folder,
                check=True,
                capture_output=True,
                text=True,
            )
            print(f"✓ Git push: {remote}/{branch}")

        except subprocess.CalledProcessError as e:
            print(f"Warning: Failed to push to remote: {e.stderr}")
        except FileNotFoundError:
            print("Warning: git command not found")

    def git_pull(self) -> bool:
        """
        Pull changes from the configured remote before restore.

        Returns:
            bool: True if pull was successful or not needed, False on failure
        """
        if not self.is_git_backend():
            return True

        try:
            remote = self._config.git_remote
            branch = self._config.git_branch

            # Check if remote exists
            result = subprocess.run(
                ["git", "remote", "get-url", remote],
                cwd=self.mackup_folder,
                capture_output=True,
                text=True,
                check=False,
            )

            if result.returncode != 0:
                # No remote configured, skip pull
                return True

            # Pull changes
            subprocess.run(
                ["git", "pull", remote, branch],
                cwd=self.mackup_folder,
                check=True,
                capture_output=True,
                text=True,
            )
            print(f"✓ Git pull: {remote}/{branch}")
            return True

        except subprocess.CalledProcessError as e:
            print(f"Warning: Failed to pull from remote: {e.stderr}")
            return utils.confirm(
                "Git pull failed. Do you want to continue with restore anyway?",
            )
        except FileNotFoundError:
            print("Warning: git command not found")
            return True
