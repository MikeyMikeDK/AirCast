#!/usr/bin/env bash
# Henter UxPlay (fast commit), lægger AirCasts patch på og installerer uxplay.exe i /ucrt64/bin.
# Patchen: log skrives straks (fflush) og hver ny videostørrelse meldes ("video frame size WxH").
# Køres i en MSYS2 UCRT64-shell.
set -euo pipefail

UXPLAY_COMMIT=534e2cc0e558d6c94bcc66964f8fc13ad73a6cdc
BUILD="$(cd "$(dirname "$0")" && pwd)"
SRC="$BUILD/src/UxPlay"

if [ ! -d "$SRC" ]; then
    git clone https://github.com/FDH2/UxPlay.git "$SRC"
    git -C "$SRC" checkout "$UXPLAY_COMMIT"
    git -C "$SRC" apply "$BUILD/../patches/uxplay.patch"
fi

mkdir -p "$SRC/build"
cd "$SRC/build"
cmake -G Ninja ..
ninja
cmake --install . --prefix /ucrt64
