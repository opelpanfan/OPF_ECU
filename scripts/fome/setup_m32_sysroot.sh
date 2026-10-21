#!/usr/bin/env bash
# Unpack the 32-bit gcc/libc/libstdc++ dev packages into a user directory (no sudo) so build_fome.sh
# can build the FOME simulator for base-tune generation on Ubuntu/Debian without gcc-multilib.
# usage: scripts/fome/setup_m32_sysroot.sh [dir]   (default ~/.cache/opf-fome-build/m32) ; then export M32_SYSROOT=<dir>
set -euo pipefail
DIR=${1:-$HOME/.cache/opf-fome-build/m32}; GV=$(gcc -dumpversion | cut -d. -f1)
TMP=$(mktemp -d); cd "$TMP"
apt-get download "lib32gcc-$GV-dev" "lib32stdc++-$GV-dev" libc6-dev-i386 libc6-i386 lib32gcc-s1 lib32stdc++6
mkdir -p "$DIR"; for d in *.deb; do dpkg-deb -x "$d" "$DIR"; done
rm -rf "$TMP"; echo "export M32_SYSROOT=$DIR"
