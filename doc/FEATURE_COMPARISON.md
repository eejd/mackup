# Feature Comparison & Decision Guide

Quick reference to help you decide which features to use and how.

## Decision Tree

```
       Start
         |
         v
Do you have apps with
vendor sync (VS Code, Spotify, 1Password)?
    YES           NO
     |             |
     v             v
  USE           USE
NATIVE SYNC   GIT BACKEND
FILTERING       ONLY
     |             |
     |             v
     |        (auto-commit
     |         all backups)
     |
     v
Do you want version control
and easy git-based sync?
    YES           NO
     |             |
     v             v
  USE           NATIVE SYNC
 BOTH         FILTERING
            + file_system
```

## Feature Comparison Table

| Aspect | Native Sync Filtering | Git Backend | Both Combined |
|--------|----------------------|-------------|-----------------|
| **Storage** | Dropbox, iCloud, Drive, file_system | Git | Git |
| **Conflict Prevention** | ✓ Blocks conflicting apps | - | ✓ Blocks + Version Control |
| **Version History** | - | ✓ Full git log | ✓ Full git log |
| **Multi-Machine Sync** | Via cloud service | Via git (manual push) | Via git + filtering |
| **Setup Complexity** | Simple (no changes) | Moderate (git init) | Moderate (both) |
| **Auto-Commit** | - | ✓ Optional | ✓ Optional |
| **Rollback Support** | - | ✓ git revert | ✓ git revert |
| **Transparency** | - | ✓ git diff | ✓ git diff |
| **Cost** | Free (or cloud cost) | Free (if self-hosted) | Free (if self-hosted) |

## Use Cases

### Case 1: Someone Using Cloud Storage (Dropbox/iCloud)
**Situation**: Business laptop synced via Dropbox, needs to avoid VS Code sync conflicts

**Recommendation**: Native Sync Filtering Only
```ini
[storage]
engine = file_system
path = .dotfiles
directory = mackup
# include_native_sync = false (default)

[applications_to_sync]
# Apps you explicitly want despite native sync
custom-app
```

**Why**: 
- Cloud service handles multi-machine sync
- Native filtering prevents conflicts
- Simple, zero git overhead

---

### Case 2: Someone Using Git Already
**Situation**: Dotfiles already in GitHub, want version control and multiple machines

**Recommendation**: Git Backend Only or Combined
```ini
[storage]
engine = git
path = .dotfiles
directory = mackup

[git]
auto_commit = true
auto_push = false
```

**Why**:
- Git already part of workflow
- Full transparency and rollback
- Per-machine branches for configuration variance

---

### Case 3: Power User / Multi-Machine
**Situation**: Laptop, desktop, remote server; different configs per machine; wants safety

**Recommendation**: Both Features Combined
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

[applications_to_sync]
# Override specific apps despite native sync
vscode  # Prefer mackup version control

[applications_to_ignore]
xcode   # Completely ignore this
```

**Multi-machine setup**:
```bash
# Machine 1: Laptop
git checkout -b laptop
mackup backup
git push origin laptop

# Machine 2: Desktop  
git checkout -b desktop
mackup backup
git push origin desktop

# Main branch: shared configs between machines
```

**Why**:
- Full version control per-machine
- Native sync safety built-in
- Can selectively override native sync when desired
- Easy to see differences between machines

---

### Case 4: Minimal Setup / Team Environment
**Situation**: Just need basics, maybe on a team laptop

**Recommendation**: Native Sync Filtering Only
```bash
# No changes needed! Native filtering is default
mackup backup
```

**Why**:
- Zero configuration required
- Just works out of the box
- Prevents common conflicts

---

## Feature Details Comparison

### Native Sync Filtering

#### Pros
- ✓ Zero configuration needed
- ✓ Prevents symlink conflicts
- ✓ Works with all storage backends
- ✓ No performance impact
- ✓ Safe for beginners

#### Cons
- ✗ Can't override individual apps easily
- ✗ No version history

#### When to Use
- You have apps with vendor sync (mostly everyone!)
- You want safe defaults without conflicts
- You use Dropbox, iCloud, Google Drive
- You want simplicity

#### When to Skip
- You want version control (use git backend)
- All your apps sync manually (rare)

---

### Git Backend

#### Pros
- ✓ Full version control
- ✓ Easy multi-machine via branches
- ✓ Transparent (git diff shows changes)
- ✓ Rollback support
- ✓ No vendor lock-in
- ✓ Works with any git server

#### Cons
- ✗ Requires git knowledge
- ✗ Requires initial setup
- ✗ Slightly more overhead (~100ms per backup)
- ✗ Manual push by default (safer but more steps)

#### When to Use
- You use git for dotfiles already
- You want version history of configs
- You need multi-machine setups
- You want full transparency and rollback

#### When to Skip
- You prefer cloud-based sync (Dropbox/iCloud)
- You don't want git complexity
- You have low bandwidth - repo can grow

---

## Migration Guide

### From Existing Setup to Native Sync Filtering

**If using file_system backend**:
```bash
# No migration needed! 
# Filtering is automatic with master branch update
mackup backup
```

Check what changes:
```bash
mackup list  # See [native sync] annotations
```

### From Existing Setup to Git Backend

**If using Dropbox/iCloud**:
```bash
# Step 1: Initialize git repo
mkdir -p ~/.dotfiles/mackup
cd ~/.dotfiles/mackup
git init
git config user.email "you@example.com"
git config user.name "Your Name"

# Step 2: Copy existing backups
# (if you have them in Dropbox/etc)
cp -r ~/Dropbox/Mackup/* .

# Step 3: Update config
# [from README]

# Step 4: Initial commit
git add .
git commit -m "initial: imported existing backups"

# Step 5: (Optional) Push to GitHub
git remote add origin https://github.com/user/repo.git
git push -u origin main
```

---

## Common Questions

**Q: Should I use both features?**
A: Yes, if you want the best of both worlds:
- Safety from native sync conflicts
- Full version control
- Explicit configuration overrides
The overhead is minimal.

**Q: Do native sync apps get completely skipped?**
A: Yes, by default. But you can:
- Override via `[applications_to_sync]` in config
- Use `--include-native-sync` flag for one-time
- Set `include_native_sync = true` to disable filtering

**Q: Can I use git backend without native sync filtering?**
A: Yes! Set `include_native_sync = true` in config to back up everything.

**Q: What if I have a different cloud sync I like?**
A: Use native sync filtering. You're already being safe - this just formalizes it.

**Q: How much slower is git backend?**
A: ~100ms per backup operation for git add/commit.
Negligible unless you have thousands of files.

**Q: Can I change storage backend later?**
A: Yes, but you'll need to migrate files manually.
- file_system → git: copy files, init git repo
- git → file_system: keep `.git` folder or reclone
- cloud → anything: download first

---

## Recommendations by Use Case

| Scenario | Recommended | Config |
|----------|-------------|--------|
| Cloud sync (Dropbox) | Native filtering | Default |
| GitHub dotfiles | Git + Filtering | Combined |
| Multi-machine setup | Git + Filtering | Combined |
| Team/shared machine | Native filtering | Default |
| Minimal/beginner | Native filtering | Default |
| Power user | Git + Filtering | Combined |
| Self-hosted git | Git backend | Git only |
| iCloud/OneDrive sync | Native filtering | Default |

---

## Testing Your Configuration

### Test Native Sync Filtering Works
```bash
mackup list | grep "native sync"  # Should show apps
mackup show vscode                 # Should show sync mechanism
```

### Test Git Backend Works
```bash
cd ~/.dotfiles/mackup
git status
git log --oneline -5
```

### Test Both Together
```bash
# Verify filtering is active with git
mackup backup
cd ~/.dotfiles/mackup
git show HEAD  # See what was committed
mackup list    # Verify native sync apps marked
```

---

See also:
- [FEATURES.md](FEATURES.md) - Detailed feature documentation
- [examples/](../examples/) - Configuration examples
- [README.md](README.md) - Main documentation
