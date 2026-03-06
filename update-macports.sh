#!/bin/bash
# Rebuild mackup MacPorts port: tarball → checksums → Portfile → portindex → install

set -e

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VERSION=$(grep '^version' "${REPO_DIR}/pyproject.toml" | head -1 | sed 's/.*= *"\(.*\)"/\1/')
PORTFILE_DIR="/opt/macports-ports-local/sysutils/mackup"
PORTFILE="${PORTFILE_DIR}/Portfile"
FILES_DIR="${PORTFILE_DIR}/files"
TARBALL="${FILES_DIR}/mackup-${VERSION}.tar.gz"
LOCAL_PORTS_DIR="/opt/macports-ports-local"

echo "==> mackup MacPorts port update"
echo "    Version:  $VERSION"
echo "    Portfile: $PORTFILE"

# 1. Generate tarball from git HEAD
echo "==> Creating tarball from git HEAD..."
mkdir -p "$FILES_DIR"
git -C "$REPO_DIR" archive --prefix="mackup-${VERSION}/" --format=tar.gz HEAD \
    -o "$TARBALL"
echo "    Created: $TARBALL ($(du -sh "$TARBALL" | cut -f1))"

# 2. Calculate checksums
echo "==> Calculating checksums..."
RMD160=$(openssl dgst -rmd160 "$TARBALL" | awk '{print $NF}')
SHA256=$(openssl dgst -sha256 "$TARBALL" | awk '{print $NF}')
SIZE=$(stat -f%z "$TARBALL" 2>/dev/null || stat -c%s "$TARBALL")
echo "    rmd160  $RMD160"
echo "    sha256  $SHA256"
echo "    size    $SIZE"

# 3. Update checksums in Portfile (also sync the canonical copy in packaging/)
echo "==> Updating Portfile checksums..."
for PF in "$PORTFILE" "${REPO_DIR}/packaging/macports/Portfile"; do
    if [ -f "$PF" ]; then
        perl -i -0pe \
            "s|(checksums\s+rmd160\s+)\w+(\s*\\\\\s*\n\s*sha256\s+)\w+(\s*\\\\\s*\n\s*size\s+)\d+|\${1}${RMD160}\${2}${SHA256}\${3}${SIZE}|" \
            "$PF"
    fi
done
echo "    Done"

# 4. Rebuild PortIndex
echo "==> Rebuilding PortIndex..."
/opt/local/bin/portindex "$LOCAL_PORTS_DIR" 2>&1 | grep -v "^$"

# 5. Install
echo "==> Installing port..."
sudo /opt/local/bin/port install mackup

echo ""
echo "==> mackup @${VERSION} installed successfully"
