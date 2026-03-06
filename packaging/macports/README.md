# MacPorts Packaging

This directory contains the MacPorts `Portfile` for building and installing mackup.

## Overview

The `Portfile` defines how to build mackup with MacPorts on macOS. It:
- Fetches the latest code from the `master` branch
- Installs for Python 3.13 and 3.14
- Uses the `hatch` build system
- Includes all tests in the build process
- Provides both `py313-mackup` and `py314-mackup` ports

## Current Configuration

**Port Name**: `py-mackup` (also creates `py313-mackup` and `py314-mackup` subports)  
**Version**: 0.10.2  
**Branch**: `master` (can be overridden to `feature/*` for testing)  
**License**: GPL-3+  
**Maintainer**: @eejd  
**Repository**: https://github.com/eejd/mackup

## What's Included

### Features
- ✅ Feature 1: Native Sync Filtering (detects 44+ apps with vendor sync)
- ✅ Feature 2: Git Backend Storage (optional auto-commit/push)

### Dependencies
- `py${python.version}-docopt-ng` - Command-line argument handling
- `py${python.version}-pytest` - Testing framework
- `py${python.version}-pytest-cov` - Code coverage

## Building with MacPorts

### Prerequisites
```bash
# Ensure MacPorts is installed
sudo port selfupdate
```

### Standard Build (Stable - master branch)
```bash
# Install py313-mackup
sudo port install py313-mackup

# Or for Python 3.14
sudo port install py314-mackup
```

### Development Build (Feature branch)
Edit the Portfile to use a different branch:
```tcl
set git_branch      "feature/git-backend"  # or any other branch
```

Then install:
```bash
sudo port install py313-mackup +universal
```

### Local Development (from local ports tree)
```bash
# Add to MacPorts sources.conf
file:///opt/macports-ports-local [nosync]

# Install from local tree
sudo port install py313-mackup
```

## Installation Locations

When installed via MacPorts:
- **Command**: `/opt/local/bin/mackup-3.13` or `/opt/local/bin/mackup-3.14`
- **Package**: `/opt/local/Library/Frameworks/Python.framework/Versions/3.13/...`

## Updating the Portfile

### When to Update
- **Version bump**: Update `0.10.2` version number
- **New Python release**: Add to `python.versions`
- **New dependencies**: Add to `depends_lib-append`
- **Build system change**: Update `python.pep517_backend`
- **Branch default change**: Update `set git_branch`

### How to Update

1. Edit `/Users/dep/Workspaces/UnixLike/mackup/packaging/macports/Portfile`
2. Commit to master branch with clear message:
   ```bash
   git commit -m "build: update Portfile for version X.Y.Z"
   ```
3. Copy updated version to local ports tree:
   ```bash
   cp packaging/macports/Portfile /opt/macports-ports-local/python/py-mackup/
   ```
4. Test build:
   ```bash
   sudo port clean py313-mackup
   sudo port install py313-mackup
   ```
5. Push to repo:
   ```bash
   git push origin master
   ```

## For Upstream (if submitting to official MacPorts)

The Portfile can be contributed to the official MacPorts ports tree:
- **Target**: `https://github.com/MacPorts/macports-ports/tree/master/python`
- **Note**: Use stable release tags `v0.10.2` instead of `master` branch
- **Modification needed**: Change `git_branch` from `master` to tag-based approach

Example PR modification:
```tcl
# Instead of:
github.setup        eejd mackup 0.10.2 v
fetch.type          git
git.url             https://github.com/eejd/mackup.git
git.branch          ${git_branch}

# Use standard GitHub tarball:
github.setup        eejd mackup 0.10.2 v
github.tarball_from archive
```

## Notes

### Features Available
Both new features are included when building from master:

1. **Native Sync Filtering**: Automatically skips 44 apps with vendor sync
   - Use `mackup list` to see which apps are filtered
   - Override with `mackup backup --include-native-sync`

2. **Git Backend**: Optional git-based storage
   - Configure in `.mackup.cfg`:
     ```ini
     [storage]
     engine = git
     path = .dotfiles
     directory = mackup
     ```

### Testing After Installation
```bash
# Verify installation
mackup-3.13 --version

# Check native sync filtering
mackup-3.13 list | grep "native sync"

# Test configuration
cat ~/.mackup.cfg  # or create one

# Dry run (not actually backing up)
mackup-3.13 backup --help
```

## Troubleshooting

### Port Not Found
```bash
# Ensure custom ports tree is in sources.conf
cat /opt/local/etc/macports/sources.conf | grep "macports-ports-local"

# If missing, add it:
sudo nano /opt/local/etc/macports/sources.conf
# Add: file:///opt/macports-ports-local [nosync]
```

### Build Fails
```bash
# Clean and try again
sudo port clean py313-mackup
sudo port install py313-mackup

# Check logs
tail -100 /opt/local/var/macports/logs/python/py313-mackup/main.log
```

### Dependencies Not Met
```bash
# Check what's required
port deps py313-mackup

# Install missing dependencies manually
sudo port install py313-docopt-ng py313-pytest
```

## Version Control

### Branch Strategy
- **master**: Stable Portfile for current release
- **feature/*** branches: Only code changes, Portfile usually doesn't change
- Updates to Portfile stay in master unless feature requires new dependencies

### Keeping Portfile in Sync
The Portfile in this repo should match:
- `/opt/macports-ports-local/python/py-mackup/Portfile` (local test port)

To sync after building/testing:
```bash
# Copy updated Portfile
cp /opt/macports-ports-local/python/py-mackup/Portfile packaging/macports/
git add packaging/macports/Portfile
git commit -m "build: sync Portfile with local port tree"
git push origin master
```

## Related Documentation

- [FEATURES.md](../doc/FEATURES.md) - Feature documentation
- [FEATURE_ROADMAP.md](../doc/FEATURE_ROADMAP.md) - Planned features
- [FEATURE_COMPARISON.md](../doc/FEATURE_COMPARISON.md) - Feature decisions

## Questions?

See:
- MacPorts documentation: https://guide.macports.org/
- Our issue tracker: https://github.com/eejd/mackup/issues
- Upstream mackup: https://github.com/lra/mackup
