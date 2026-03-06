#!/bin/bash
# Script to update mackup MacPorts port with latest source tarball and checksums

set -e

# Configuration
VERSION="0.10.2"
REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DIST_DIR="${REPO_DIR}/dist"
PORTFILE_DIR="/opt/macports-ports-local/devel/mackup"
PORTFILE="${PORTFILE_DIR}/Portfile"
FILES_DIR="${PORTFILE_DIR}/files"

echo "Updating mackup MacPorts port..."
echo "Repository: $REPO_DIR"
echo "Version: $VERSION"

# Create dist directory if it doesn't exist
mkdir -p "$DIST_DIR"

# Clean old tarball
if [ -f "${DIST_DIR}/mackup-${VERSION}.tar.gz" ]; then
    echo "Removing old tarball..."
    rm "${DIST_DIR}/mackup-${VERSION}.tar.gz"
fi

# Create temporary staging directory
STAGING_DIR=$(mktemp -d)
trap "rm -rf $STAGING_DIR" EXIT

echo "Creating tarball..."
mkdir -p "${STAGING_DIR}/mackup-${VERSION}"
rsync -av --exclude=.git --exclude=__pycache__ --exclude=.pytest_cache --exclude=.mypy_cache --exclude=dist "${REPO_DIR}/" "${STAGING_DIR}/mackup-${VERSION}/" > /dev/null 2>&1

cd "$STAGING_DIR"
tar czf "${DIST_DIR}/mackup-${VERSION}.tar.gz" "mackup-${VERSION}/"

# Generate checksums
echo "Generating checksums..."
cd "$DIST_DIR"
RMD160=$(openssl dgst -rmd160 "mackup-${VERSION}.tar.gz" | awk '{print $NF}')
SHA256=$(sha256sum "mackup-${VERSION}.tar.gz" | awk '{print $1}')

echo "RMD160: $RMD160"
echo "SHA256: $SHA256"

# Copy tarball to port files directory
echo "Copying tarball to port directory..."
mkdir -p "$FILES_DIR"
cp "${DIST_DIR}/mackup-${VERSION}.tar.gz" "$FILES_DIR/"

# Update Portfile checksums if it exists
if [ -f "$PORTFILE" ]; then
    echo "Updating Portfile checksums..."
    
    # Use perl for cross-platform sed compatibility
    perl -i -pe "s/checksums\s+rmd160\s+\w+.*?sha256\s+\w+/checksums           rmd160  $RMD160 \\\\\n                    sha256  $SHA256/s" "$PORTFILE"
    
    echo "Portfile updated successfully"
fi

echo ""
echo "✓ Tarball created: ${DIST_DIR}/mackup-${VERSION}.tar.gz"
echo "✓ Checksums generated and Portfile updated"
echo ""
echo "Next step: sudo port install mackup @${VERSION}"
