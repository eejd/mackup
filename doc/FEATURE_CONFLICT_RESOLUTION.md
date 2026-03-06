# Feature Design: Smart Conflict Resolution

## Problem Statement

When backing up files, mackup currently shows a generic prompt if a file already exists:

```
A file named /path/to/file already exists in the Mackup folder.
Are you sure that you want to replace it? (use --force to skip this prompt) <Yes|No>
```

**Issues:**
- No information about what's different between the files
- User can't make informed decision without manually comparing
- Binary files like `.plist` are hard to inspect
- No way to see a diff before deciding

## Proposed Solution

Add **intelligent file comparison** when conflicts are detected, showing:
1. File metadata (size, modification time, checksum)
2. Smart diff for text files
3. Special handling for macOS plist files (binary → XML conversion)
4. Options to view full diff, keep both, or skip

## Design

### Phase 1: File Analysis

When conflict detected, analyze both files:

```python
class FileConflict:
    def __init__(self, home_path, mackup_path):
        self.home_path = home_path
        self.mackup_path = mackup_path
        self.home_info = self._get_file_info(home_path)
        self.mackup_info = self._get_file_info(mackup_path)
        self.file_type = self._detect_file_type(home_path)
        
    def _get_file_info(self, path):
        """Get file metadata."""
        stat = os.stat(path)
        return {
            'size': stat.st_size,
            'mtime': datetime.fromtimestamp(stat.st_mtime),
            'checksum': self._checksum(path) if stat.st_size < 10MB else None,
            'is_binary': self._is_binary(path)
        }
    
    def _detect_file_type(self, path):
        """Detect special file types."""
        ext = os.path.splitext(path)[1].lower()
        
        if ext == '.plist':
            return 'plist'
        elif ext in ['.json', '.xml', '.yaml', '.yml']:
            return 'structured'
        elif ext in ['.sh', '.py', '.rb', '.js', '.ts']:
            return 'script'
        elif self.home_info['is_binary']:
            return 'binary'
        else:
            return 'text'
```

### Phase 2: Smart Comparison

Show appropriate comparison based on file type:

#### Text Files
```python
def show_text_diff(self):
    """Show unified diff for text files."""
    with open(self.home_path) as f1, open(self.mackup_path) as f2:
        diff = difflib.unified_diff(
            f2.readlines(),
            f1.readlines(),
            fromfile=f'existing ({self.mackup_info["mtime"]})',
            tofile=f'new ({self.home_info["mtime"]})',
            lineterm='',
            n=3  # context lines
        )
        
        # Show first 50 lines of diff
        diff_lines = list(diff)[:50]
        if diff_lines:
            print("\nFile differences:")
            for line in diff_lines:
                if line.startswith('+'):
                    print(colored(line, 'green'))
                elif line.startswith('-'):
                    print(colored(line, 'red'))
                else:
                    print(line)
            
            if len(list(diff)) > 50:
                print(f"\n... ({len(list(diff)) - 50} more lines)")
```

#### macOS Plist Files
```python
def show_plist_diff(self):
    """Convert binary plist to XML and show diff."""
    import subprocess
    import tempfile
    
    # Convert both files to XML
    with tempfile.NamedTemporaryFile(suffix='.xml') as tmp1, \
         tempfile.NamedTemporaryFile(suffix='.xml') as tmp2:
        
        # Convert to XML
        subprocess.run(['plutil', '-convert', 'xml1', 
                       self.home_path, '-o', tmp1.name])
        subprocess.run(['plutil', '-convert', 'xml1', 
                       self.mackup_path, '-o', tmp2.name])
        
        # Show diff of XML
        self._show_diff(tmp1.name, tmp2.name, format='xml')
```

#### Binary Files
```python
def show_binary_info(self):
    """Show metadata for binary files."""
    print("\nBinary file comparison:")
    print(f"  Existing: {self.mackup_info['size']:,} bytes, "
          f"modified {self.mackup_info['mtime']}")
    print(f"  New:      {self.home_info['size']:,} bytes, "
          f"modified {self.home_info['mtime']}")
    
    if self.mackup_info['checksum'] and self.home_info['checksum']:
        if self.mackup_info['checksum'] == self.home_info['checksum']:
            print("  ✓ Files are identical (same checksum)")
        else:
            print("  ✗ Files differ (different checksum)")
```

### Phase 3: Enhanced Prompt

```python
def resolve_conflict(self) -> str:
    """
    Interactive conflict resolution.
    Returns: 'replace', 'keep', 'skip', 'diff'
    """
    print(f"\nConflict: {os.path.basename(self.home_path)}")
    
    # Show quick summary
    self._show_summary()
    
    # Show appropriate comparison
    if self.file_type == 'plist':
        self.show_plist_diff()
    elif self.file_type == 'text':
        self.show_text_diff()
    elif self.file_type == 'binary':
        self.show_binary_info()
    
    # Prompt with options
    print("\nOptions:")
    print("  r - Replace existing with new")
    print("  k - Keep existing, skip backup")
    print("  d - Show full diff")
    print("  b - Keep both (rename new)")
    print("  s - Skip this file")
    
    while True:
        choice = input("Your choice [r/k/d/b/s]: ").lower()
        
        if choice == 'd':
            self._show_full_diff()
            continue
        elif choice in ['r', 'k', 'b', 's']:
            return choice
        else:
            print("Invalid choice. Try again.")
```

### Phase 4: Integration

Modify `Application.backup()`:

```python
def backup(self, force=False, compare=True) -> None:
    """Backup application config files.
    
    Args:
        force: Skip all prompts
        compare: Show file comparison on conflicts (default True)
    """
    for filename in self.get_files_to_backup():
        home_filepath = os.path.join(os.environ["HOME"], filename)
        mackup_filepath = os.path.join(self.mackup_folder, filename)
        
        if os.path.lexists(mackup_filepath):
            if force:
                utils.delete(mackup_filepath)
            elif compare:
                # NEW: Smart conflict resolution
                conflict = FileConflict(home_filepath, mackup_filepath)
                resolution = conflict.resolve_conflict()
                
                if resolution == 'r':  # replace
                    utils.delete(mackup_filepath)
                elif resolution == 'k':  # keep existing
                    continue
                elif resolution == 'b':  # keep both
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    backup_name = f"{mackup_filepath}.{timestamp}"
                    os.rename(mackup_filepath, backup_name)
                    print(f"Existing file renamed to {backup_name}")
                elif resolution == 's':  # skip
                    continue
            else:
                # OLD: Simple confirmation
                if not utils.confirm(...):
                    continue
                utils.delete(mackup_filepath)
        
        utils.copy(home_filepath, mackup_filepath)
```

## Configuration

Add to `.mackup.cfg`:

```ini
[storage]
engine = git
path = .dotfiles
directory = mackup

[backup]
# Show smart comparison on conflicts (default: true)
compare_on_conflict = true

# Auto-resolve if files are identical
skip_identical = true

# Max diff lines to show (default: 50)
max_diff_lines = 50

# Convert binary plists to XML for comparison (macOS only)
convert_plists = true
```

## CLI Options

```bash
# Disable comparison (old behavior)
mackup backup --no-compare

# Always show full diff
mackup backup --full-diff

# Auto-replace if newer
mackup backup --prefer-newer

# Auto-keep if identical checksum
mackup backup --skip-identical
```

## Implementation Checklist

### Core Features
- [ ] `FileConflict` class with file analysis
- [ ] Binary vs text detection
- [ ] Checksum calculation for small files
- [ ] Unified diff generation for text files
- [ ] macOS plist → XML conversion
- [ ] Interactive conflict resolution prompt

### User Experience
- [ ] Colorized diff output (red/green)
- [ ] File metadata display (size, date, checksum)
- [ ] "Show full diff" option
- [ ] "Keep both" option with timestamp rename
- [ ] Progress indicator for large diffs

### Configuration
- [ ] `compare_on_conflict` config option
- [ ] `skip_identical` config option
- [ ] `max_diff_lines` config option
- [ ] `--no-compare` CLI flag
- [ ] `--skip-identical` CLI flag

### Testing
- [ ] Test with text files
- [ ] Test with binary files
- [ ] Test with plist files (binary and XML)
- [ ] Test with identical files
- [ ] Test with large files (> 10MB)
- [ ] Test with symlinks

### Edge Cases
- [ ] Handle permission errors
- [ ] Handle corrupt plist files
- [ ] Handle extremely large diffs
- [ ] Handle binary files that look like text
- [ ] Handle Unicode/encoding issues

## Example Output

### Text File Conflict
```
Conflict: .zshrc

File comparison:
  Existing: 2,847 bytes, modified 2025-08-09 17:13:15
  New:      2,901 bytes, modified 2026-03-05 14:22:33

File differences:
--- existing (2025-08-09 17:13:15)
+++ new (2026-03-05 14:22:33)
@@ -23,7 +23,10 @@
 # 2023          cruft cleanup
 # 2025          work on multi-OS, python (miniforge3)
+# 2026          added mackup git backend support
 
+# Mackup git backend
+export MACKUP_GIT_AUTO_COMMIT=true
+
 # environment settings for specific OSs

Options:
  r - Replace existing with new
  k - Keep existing, skip backup
  d - Show full diff
  b - Keep both (rename new)
  s - Skip this file

Your choice [r/k/d/b/s]: 
```

### Plist File Conflict
```
Conflict: com.apple.symbolichotkeys.plist

Binary plist detected, converting to XML for comparison...

File comparison:
  Existing: 12,458 bytes, modified 2025-12-15 09:23:11
  New:      12,502 bytes, modified 2026-03-05 14:22:33

File differences (XML representation):
--- existing (2025-12-15 09:23:11)
+++ new (2026-03-05 14:22:33)
@@ -234,6 +234,12 @@
         <key>enabled</key>
         <true/>
+        <key>value</key>
+        <dict>
+            <key>parameters</key>
+            <array>
+                <integer>65535</integer>
+                <integer>49</integer>

Options:
  r - Replace existing with new
  k - Keep existing, skip backup
  d - Show full diff
  b - Keep both (rename new)
  s - Skip this file

Your choice [r/k/d/b/s]: 
```

### Binary File Conflict
```
Conflict: some-binary-file.dat

Binary file comparison:
  Existing: 1,234,567 bytes, modified 2025-08-09 17:13:15
  New:      1,234,600 bytes, modified 2026-03-05 14:22:33
  ✗ Files differ (different checksum)

Options:
  r - Replace existing with new
  k - Keep existing, skip backup
  b - Keep both (rename new)
  s - Skip this file

Your choice [r/k/b/s]: 
```

## Benefits

1. **Informed Decisions** - Users see exactly what's different
2. **Safety** - Avoid accidentally overwriting important changes
3. **Transparency** - Clear what will happen before it happens
4. **Flexibility** - Multiple resolution options (replace, keep, both, skip)
5. **Special Format Support** - Handles plist and other binary formats intelligently

## Dependencies

- `difflib` (stdlib) - text diffs
- `hashlib` (stdlib) - checksums
- `plutil` (macOS) - plist conversion (graceful fallback if not available)
- `colorama` (optional) - colored output

## Future Enhancements

- Three-way merge for git backend conflicts
- External diff tool integration (`git difftool`, `vimdiff`, etc.)
- JSON/YAML semantic diff (not just text)
- Image diff for common formats (show dimensions, size)
- Audio/video metadata comparison
- SQLite database schema comparison

## Related Features

- Complements **Feature 2: Git Backend** - conflicts are common with version control
- Works with **Feature 1: Native Sync Filtering** - helps when apps write to both locations
- Future **Feature 4: Store Hygiene** - identifies duplicate or conflicting configs

---

## Related Feature: Per-Application Git Tracking

### Problem

When using git backend across multiple machines, some configs should be:
- **Common**: Synced across all machines (shell configs, git config, editor settings)
- **Machine-specific**: Kept per-machine only (SSH configs with local hosts, machine-specific paths)

Currently, mackup treats all apps the same - either backup ALL files or ignore the app entirely.

### Proposed Solution

Add `sync_scope` attribute to application configurations:

```ini
# In application .cfg file (e.g., mackup/applications/ssh.cfg)
[application]
name = SSH

# New attribute: common, machine, or prompt
sync_scope = machine

[configuration_files]
.ssh/config
.ssh/known_hosts
```

Or allow per-file granularity:

```ini
[application]
name = Git

[configuration_files]
# Syntax: filename:scope
.gitconfig:common           # Sync across all machines
.gitconfig.local:machine    # Keep per-machine only
.git-credentials:machine    # Keep per-machine only
```

### Git Backend Integration

When using git backend with branches per machine:

```ini
# .mackup.cfg
[storage]
engine = git
path = .dotfiles
directory = mackup

[git]
auto_commit = true
branch = mackup-sibeling  # Machine-specific branch
common_branch = main       # Branch for common configs

# Automatically filter what goes where
sync_common_to_main = true
```

**Behavior**:
- Apps with `sync_scope = common` → committed to `main` branch
- Apps with `sync_scope = machine` → committed to machine branch only
- Apps with `sync_scope = prompt` → ask user during backup

**Benefits**:
1. Clear separation of shared vs machine-specific configs
2. No accidental leakage of sensitive machine-specific data
3. Easy to merge common configs across machines
4. Machine branches only contain machine-specific overrides

### Implementation Complexity

- Add `sync_scope` to application parsing (~1 day)
- Git backend branching logic (~2 days)  
- Update 250+ application configs with appropriate scopes (~3-5 days)
- Testing across multiple machines (~2 days)

**Total**: ~8-10 days

### Configuration Examples

```ini
# ssh.cfg (machine-specific)
[application]
name = SSH
sync_scope = machine

# git.cfg (mixed)
[application]
name = Git
sync_scope = common

[configuration_files]
.gitconfig:common
.gitconfig.local:machine

# vscode.cfg (common - but might be filtered by native sync)
[application]
name = Visual Studio Code
sync_scope = common
has_native_sync = true
```

---

**Status**: Future feature - Design proposal
**Complexity**: Medium (3-5 days implementation)
**Priority**: High (directly addresses user pain point)
**Dependencies**: None (standalone feature)
**Related Features**: Complements Feature 2 (Git Backend) and future per-app git tracking
