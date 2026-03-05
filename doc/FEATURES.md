# Mackup Features: Native Sync & Git Backend

This document provides comprehensive guidance on both new features added to mackup.

## Feature 1: Native Sync Filtering

### What It Is

Automatic detection and exclusion of apps that have built-in cloud sync mechanisms. By default, mackup skips these 44 applications to prevent conflicts between mackup's symlinks and vendor-provided sync.

### Why This Matters

When an app has native sync enabled (like VS Code Settings Sync or Spotify account settings), both the app and mackup can't safely manage the same files:
- Both create symlinks/file watchers
- Conflicts cause data corruption or loss
- Duplicated backup effort

### Which Apps Are Filtered

**IDEs & Editors** (Settings Sync)
- VS Code, VS Code Insiders, VS Code OSS, Codium
- Cursor, Zed, Windsurf

**JetBrains IDEs** (IDE sync)
- IntelliJ IDEA, PyCharm, WebStorm, PhpStorm, RubyMine, CLion, GoLand, DataGrip

**Vendor Account Sync**
- 1Password, Spotify, Telegram, WhatsApp, Zoom

**iCloud Sync**
- Apple Music, Messages, Xcode
- Affinity Designer/Photo/Publisher
- Fantastical, Omnifocus, Things, 2Do

**Cloud Storage & Sync**
- Lightroom, Lightroom Classic
- Photoshop, Illustrator
- Joplin, KeyBase

### Usage

#### Default Behavior (Recommended)
```bash
mackup backup
# Skips all apps with native sync - safe and simple
```

#### List All Apps with Annotations
```bash
mackup list
# Shows which apps have native sync and their mechanism
# Example output:
#  - spotify [native sync: vendor_account]
#  - vscode [native sync: settings_sync]
#  - xcode [native sync: icloud]
```

#### Show Sync Details
```bash
mackup show vscode
# Output:
# Name: Visual Studio Code
# Native sync: settings_sync
# Configuration files:
#  - Library/Application Support/Code/User/settings.json
```

#### Override Filtering via Config
```ini
# .mackup.cfg
[applications_to_sync]
# Back up these apps even though they have native sync
vscode
spotify
```

#### Override via CLI Flag
```bash
# One-time override: backup everything including native-sync apps
mackup backup --include-native-sync
```

#### Manual Enable
```ini
# .mackup.cfg - skip filtering entirely
[storage]
engine = file_system
path = .dotfiles
directory = mackup

include_native_sync = true  # back up everything
```

### Configuration Examples

See `examples/mackup-native-sync-filter.cfg` for detailed examples.

---

## Feature 2: Git Storage Backend

### What It Is

A new storage engine that uses git instead of syncing to Dropbox/iCloud/etc. Automatically commits changes before/after backup operations, providing version control and easy multi-machine sync via git.

### Why This Matters

Advantages of git-based backup:
- **Version History** - Full `git log` of config changes
- **Easy Multi-Machine** - Clone same repo, use per-machine branches
- **Transparency** - Exactly what changed via `git diff`
- **Rollback** - `git revert` individual commits if needed
- **No Vendor Lock-in** - Works with any git hosting or self-hosted
- **Control** - Push manually when ready (default)

### Setup

#### 1. Initialize Git Repository
```bash
# Create your backup directory
mkdir -p ~/.dotfiles/mackup
cd ~/.dotfiles/mackup
git init
git config user.email "you@example.com"
git config user.name "Your Name"
```

#### 2. Create Configuration
```ini
# ~/.mackup.cfg
[storage]
engine = git
path = .dotfiles
directory = mackup

[git]
auto_commit = true      # Commit after backup
auto_push = false       # Manual push (safer)
remote = origin
branch = main
commit_message_format = mackup: {action} {app_name}
```

#### 3. Link to Remote (Optional)
```bash
cd ~/.dotfiles/mackup
git remote add origin https://github.com/yourusername/dotfiles.git
git push -u origin main
```

### Basic Workflow

```bash
# 1. Make config changes in your applications
# 2. Run backup
mackup backup
# → Copies files to ~/.dotfiles/mackup/
# → Commits automatically with message like "mackup: backup vscode"

# 3. Review changes
cd ~/.dotfiles/mackup
git log --oneline -5
git show HEAD  # See what changed

# 4. Push when ready
git push origin main
```

### Multi-Machine Setup

**On Machine 1 (Laptop)**
```bash
# Create machine-specific branch
cd ~/.dotfiles/mackup
git checkout -b laptop-configs
# Make changes, backup, review
mackup backup
git push origin laptop-configs
```

**On Machine 2 (Desktop)**
```bash
# Clone and use different branch
git clone https://github.com/yourusername/dotfiles.git ~/.dotfiles
cd ~/.dotfiles/mackup
git checkout desktop-configs
mackup restore
```

Each machine has its own branch with machine-specific configs, but they share base configs from `main`.

### Git Configuration Options

```ini
[git]
# Auto-commit after backup (default: true)
auto_commit = true

# Auto-push after commit (default: false - safer)
auto_push = false

# Remote name to push/pull (default: origin)
remote = origin

# Branch name (default: main)
branch = main

# Commit message format
# Placeholders: {action}, {app_name}, {timestamp}
# Default: "mackup: {action} {app_name}"
commit_message_format = mackup: {action} {app_name} at {timestamp}
```

### All Supported Actions

These trigger automatic commits:
- `mackup backup` - commits after backup
- `mackup restore` - pulls before restore
- `mackup link install` - commits symlink creation
- `mackup link uninstall` - commits symlink removal

### Workflow Integration

```bash
# Backup workflow
$ mackup backup
[Creates/updates files]
✓ Git commit: mackup: backup vscode
✓ Git commit: mackup: backup spotify

# Restore workflow (on another machine)
$ mackup restore
✓ Git pull: origin/main
[Restores files from commits]

# Link workflow
$ mackup link install
[Creates symlinks]
✓ Git commit: mackup: link-install all apps
```

### Advanced: Selective Push

```bash
# Backup multiple times, review, then push once
mackup backup
mackup backup
mackup backup

# Review all commits
cd ~/.dotfiles/mackup
git log --oneline -3

# Push when confident
git push origin main
```

### Advanced: Per-Machine Secrets

```bash
# Keep machine-specific secrets in machine branch
git checkout -b machine-secrets
# Add sensitive files to .gitignore
echo ".aws/" >> .gitignore
echo ".ssh/" >> .gitignore
mackup backup
git commit -am "add machine-specific settings"

# Keep on machine branch, don't merge to main
git push origin machine-secrets
```

### Configuration Examples

See `examples/mackup-git-backend.cfg` and `examples/mackup-combined-features.cfg`.

---

## Combining Both Features

You can use both native sync filtering AND git backend together:

```ini
[storage]
engine = git
path = .dotfiles
directory = mackup

[git]
auto_commit = true
auto_push = false
remote = origin
branch = main

# Filter out native-sync apps by default
# include_native_sync = false (default)

[applications_to_sync]
# Override: back up these native-sync apps anyway
vscode
spotify
```

Benefits:
- ✓ Version control of all backups
- ✓ Safe filtering of conflicting apps
- ✓ Selective override when needed
- ✓ Full transparency via git

---

## Testing Your Setup

### Test Native Sync Filtering
```bash
# List shows annotations
mackup list | grep -E "\[native sync"

# Show specific app
mackup show spotify

# Verify filtering works
mackup backup --dry-run  # See what would be backed up
```

### Test Git Backend
```bash
# Check git status
cd ~/.dotfiles/mackup
git log --oneline -3
git status

# Verify commits are created
mackup backup
cd ~/.dotfiles/mackup
git log --oneline -1  # Should show new commit
```

---

## Troubleshooting

### Native Sync Filtering

**Q: App is being backed up when I don't want it to**
```bash
# Check if it has native sync
mackup show app-name

# Add to applications_to_ignore to exclude completely
# Or check if it actually needs native sync enabled
```

**Q: An app is being skipped but I want to back it up**
```ini
# Override in [applications_to_sync]
[applications_to_sync]
app-name
```

### Git Backend

**Q: Git commits not being created**
```bash
# Check git is initialized
cd ~/.dotfiles/mackup
git status  # Should show repository, not error

# Check auto_commit is enabled
# Check config file location (~/.mackup.cfg)
```

**Q: Push fails with permission denied**
```bash
# Check SSH key or git credentials
ssh -T git@github.com  # Test SSH
git push origin main  # Try manual push to see error
```

**Q: Pull failed during restore**
```bash
# Mackup will ask if you want to continue
# Choose "Yes" to proceed without latest changes
# Or fix the remote issue and try again
```

---

## Performance Notes

- **Native Sync Filtering**: No performance impact
- **Git Backend**: Adds ~100ms per backup for git operations
  - Larger repositories may take longer
  - Use `.gitignore` to exclude large files

## See Also

- Examples directory: example configurations for both features
- Tests directory: comprehensive test suite
- GitHub issues: report bugs or request features
