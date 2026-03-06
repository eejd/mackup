# Mackup Feature Roadmap

Status as of 2026-03-05

## ✅ Completed Features

### Feature 1: Native Sync Filtering
- **Status**: ✅ Implemented, tested, merged to master
- **Commit**: `7bc5663` (merged via `310958d`)
- **What**: Automatically detects and excludes 44 apps with built-in cloud sync
- **Tests**: 11 new tests, all passing
- **Documentation**: [FEATURES.md](FEATURES.md#feature-1-native-sync-filtering)

### Feature 2: Git Backend Storage
- **Status**: ✅ Implemented, tested, merged to master
- **Commit**: `dafc0bc` (merged via `b5e35f7`)
- **What**: Git-based storage with optional auto-commit/push
- **Tests**: 11 new tests, all passing
- **Documentation**: [FEATURES.md](FEATURES.md#feature-2-git-backend)

### Documentation & Examples
- **Status**: ✅ Complete and published
- **Commit**: `774a5d1`
- **What**: 
  - Comprehensive user guide (FEATURES.md)
  - Decision guide (FEATURE_COMPARISON.md)
  - 3 example configurations
  - Testing documentation
- **Total**: 1,019 insertions

---

## 🎯 Current Priority: Multi-Machine Sync

### Goal
Get all active machines' configs into git repo and merge them intelligently while respecting machine-specific configurations.

### Machines to Sync
- ✅ **sibeling** - Current machine, up to date
- ⏳ **memphisto** - Branch exists (stale ~2022)
- ⏳ **democracy** - Branch exists (stale ~2022)
- ⏳ **krikkit** - Branch exists (stale ~2022)

### Sync Workflow

#### Phase 1: Pull and Review (Per Machine)
```bash
# On each machine
cd ~/.dotfiles
git fetch origin
git checkout mackup-<machine>
git pull origin mackup-<machine>

# Review differences from sibeling
git log mackup-sibeling..HEAD
git diff mackup-sibeling

# Document machine-specific configs
cat > MACHINE_SPECIFIC.md << EOF
- SSH config (local hosts)
- Paths specific to this machine
- Applications only on this machine
EOF
```

#### Phase 2: Identify Common vs Machine-Specific
Create a tracking file in each branch listing:
- **Common configs** (should be shared): shell configs, git settings, editor configs
- **Machine configs** (keep separate): SSH, machine-specific paths, local credentials

#### Phase 3: Merge Strategy Decision
After reviewing all machines, choose:
- **Option A**: Keep machine branches (current structure)
- **Option B**: Single master + hostname conditionals
- **Option C**: Master + per-app common/machine tracking (future feature)

#### Phase 4: Test with New Mackup Features
```bash
# On each machine after sync
mackup-3.13 list | grep "native sync"
mackup-3.13 backup
```

---

## 📋 Planned Features

### Feature 3: Smart Conflict Resolution
- **Status**: 🟡 Design complete, implementation pending
- **Priority**: High
- **Effort**: 3-5 days
- **Design**: [FEATURE_CONFLICT_RESOLUTION.md](FEATURE_CONFLICT_RESOLUTION.md)

**What**: Show intelligent diffs when backup conflicts occur
- Text file unified diff with colors
- Binary plist → XML conversion for comparison
- File metadata (size, date, checksum)
- Interactive resolution options (replace/keep/both/skip)

**Why**: Currently users see generic "replace?" prompt with no context

**Use Case**: 
```
Conflict: com.apple.symbolichotkeys.plist
Binary plist detected, converting to XML for comparison...
[shows diff of actual changes]

Options: r/k/d/b/s
```

**Blocked By**: None (can implement anytime)
**Depends On**: stdlib only, optional `plutil` for plist support

---

### Feature 4: Per-Application Common/Machine Config Tracking
- **Status**: 🟡 Design proposed
- **Priority**: High (for multi-machine workflows)
- **Effort**: 8-10 days
- **Design**: [FEATURE_CONFLICT_RESOLUTION.md](FEATURE_CONFLICT_RESOLUTION.md#related-feature-per-application-git-tracking)

**What**: Mark configs as "common" (sync everywhere) or "machine" (local only)

**Syntax Option 1 - Application Level**:
```ini
# ssh.cfg
[application]
name = SSH
sync_scope = machine  # Keep per-machine only
```

**Syntax Option 2 - Per-File**:
```ini
# git.cfg
[application]
name = Git
sync_scope = common

[configuration_files]
.gitconfig:common           # Sync everywhere
.gitconfig.local:machine    # Keep local
.git-credentials:machine    # Keep local
```

**Git Backend Integration**:
```ini
# .mackup.cfg
[git]
branch = mackup-sibeling      # Machine-specific branch
common_branch = main          # Shared configs branch
sync_common_to_main = true    # Auto-commit common → main
```

**Behavior**:
- `sync_scope = common` → committed to `main` branch
- `sync_scope = machine` → committed to machine branch only
- `sync_scope = prompt` → ask user each time

**Benefits**:
1. ✓ Clear separation of shared vs machine configs
2. ✓ No accidental sync of machine-specific data
3. ✓ Easy merge of common configs across machines
4. ✓ Machine branches only have overrides

**Tasks**:
- [ ] Add `sync_scope` parsing to appsdb
- [ ] Implement dual-branch logic in git backend
- [ ] Update 250+ app configs with appropriate scopes
- [ ] Add `common_branch` config option
- [ ] Testing with multiple machines

**Blocked By**: Multi-machine testing environment needed
**Depends On**: Feature 2 (Git Backend) already implemented ✓

---

### Feature 5: OS-Aware Configuration Layering
- **Status**: 🔴 Proposed (original plan)
- **Priority**: Medium
- **Effort**: 5-7 days

**What**: Conditional config loading based on OS/architecture
```ini
[application]
name = VS Code

[configuration_files]
# macOS only
Library/Application Support/Code/User/settings.json:darwin

# Linux only  
.config/Code/User/settings.json:linux

# All OSes
.vscode/extensions.json:*
```

**Benefits**: Single mackup repo works across macOS, Linux, Windows

**Blocked By**: Need multi-OS testing environment
**May Be Superseded By**: Feature 4 with hostname conditionals

---

### Feature 6: Store Hygiene and Security Audit
- **Status**: 🔴 Proposed (original plan)
- **Priority**: Low-Medium
- **Effort**: 3-5 days

**What**: Command to audit backup store for issues
```bash
mackup audit
```

**Checks**:
- Duplicate files (same checksum)
- Stale files (app no longer installed)
- Permission/ownership issues
- Sensitive data in plain text
- Broken symlinks
- Large files that shouldn't be synced
- Files ignored by .gitignore but in store

**Output**:
```
Audit Report:
✓ 127 apps backed up
⚠ 3 duplicate files (12KB wasted)
⚠ 5 stale configs (apps no longer installed)
✗ 2 files with sensitive data:
  - .aws/credentials (contains passwords)
  - .ssh/id_rsa (private key, should not sync)

Re-run with --fix to clean up issues
```

**Benefits**: Keep backup store clean and secure

---

## 🔄 Integration Plans

### Upstream PR Submission
- **Status**: ⏳ Ready when user decides
- **Branches Available**:
  - `origin/feature/native-sync-ignore` (Feature 1)
  - `origin/feature/git-backend` (Feature 2)
  
**Considerations**:
- Split into 2 separate PRs (easier review)
- Feature 1 (native sync) is less controversial, submit first
- Feature 2 (git backend) may need upstream discussion on architecture

**Before Submitting**:
- [ ] Ensure tests pass on upstream CI
- [ ] Update upstream README with new features
- [ ] Add migration guide for existing users
- [ ] Get user feedback on documentation clarity

---

## 📊 Feature Comparison Matrix

| Feature | Priority | Effort | Status | Blocks | Blocked By |
|---------|----------|--------|--------|--------|------------|
| Native Sync Filtering | ✅ High | 3-4 days | ✅ Complete | - | - |
| Git Backend | ✅ High | 4-5 days | ✅ Complete | - | - |
| Documentation | ✅ High | 1-2 days | ✅ Complete | - | - |
| **Multi-Machine Sync** | **🎯 Current** | **2-3 days** | **⏳ In Progress** | Feature 4 | User action needed |
| Smart Conflict Resolution | 🟡 High | 3-5 days | 🟡 Designed | - | None |
| Common/Machine Tracking | 🟡 High | 8-10 days | 🟡 Designed | - | Multi-machine testing |
| OS-Aware Configs | 🔴 Medium | 5-7 days | 🔴 Proposed | - | Multi-OS testing |
| Store Hygiene Audit | 🔴 Low | 3-5 days | 🔴 Proposed | - | None |

---

## 🎯 Recommended Implementation Order

### Phase 1: Multi-Machine Foundation (Current) ⏳
**Goal**: Get all machines synced and identify needs
1. ✅ Clean up sibeling (duplicate files removed)
2. ⏳ Pull configs from memphisto, democracy, krikkit
3. ⏳ Document machine-specific needs
4. ⏳ Test Feature 1 & 2 across all machines

**ETA**: 2-3 days of user effort

### Phase 2: Enhanced Workflow 🟡
**Goal**: Make multi-machine workflow seamless
1. Implement Feature 4 (Common/Machine tracking)
2. Update application configs with sync_scope
3. Set up dual-branch git strategy

**ETA**: 8-10 days development

### Phase 3: User Experience 🟡
**Goal**: Improve conflict handling and feedback
1. Implement Feature 3 (Smart Conflict Resolution)
2. Add audit command basics (Feature 6 partial)

**ETA**: 5-7 days development

### Phase 4: Upstream & Polish 🔵
**Goal**: Share with community
1. Prepare upstream PRs (Feature 1 & 2)
2. Gather community feedback
3. OS-aware configs if needed (Feature 5)

**ETA**: Variable, depends on upstream review

---

## 💡 Future Ideas

### Low Priority / Exploratory
- Three-way merge for git conflicts
- External diff tool integration (`vimdiff`, `meld`)
- JSON/YAML semantic diff (not just text)
- Image metadata comparison
- SQLite schema diff
- Encrypted sensitive configs
- Cloud backend encryption
- Backup scheduling / cron integration
- Web UI for config management

### Community Requests
- Windows support improvements
- Docker container configs
- Kubernetes config support
- Cloud-native app support

---

## 📝 Notes

### Decision Log
- **2026-03-05**: Features 1 & 2 completed and merged to master
- **2026-03-05**: Documentation and examples published
- **2026-03-05**: Feature 3 (Conflict Resolution) designed, marked as future
- **2026-03-05**: Feature 4 (Common/Machine tracking) proposed for multi-machine workflow
- **2026-03-05**: Focus shifted to multi-machine sync before implementing new features

### Key Insights
- Users need intelligent conflict resolution when files differ
- Machine-specific vs common configs is a major pain point
- Git backend enables more sophisticated multi-machine workflows
- Native sync filtering prevents common mistakes (already proven valuable)

### Next Review
After completing multi-machine sync, reassess priorities based on:
- Which features would have helped during sync
- Pain points encountered
- Time saved by existing features
- User feedback on Feature 1 & 2

---

**Last Updated**: 2026-03-05
**Maintainer**: @eejd
**Repository**: https://github.com/eejd/mackup
**Upstream**: https://github.com/lra/mackup
