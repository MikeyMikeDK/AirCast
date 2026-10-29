#!/usr/bin/env bash
# Bygger en minimal FFmpeg (samme version som MSYS2's, så gst-libav kan bruge den) med kun
# de afkodere AirCast har brug for: AAC/ALAC (AirPlay-lyd) og H.264/H.265 (software-reserve).
# Installeres i /opt/ffmpeg-min. Køres i en MSYS2 UCRT64-shell.
set -euo pipefail

FFMPEG=ffmpeg-9.0.2
SRC_DIR="$(cd "$(dirname "$0")" && pwd)/src"

mkdir -p "$SRC_DIR"
cd "$SRC_DIR"
if [ ! -d "$FFMPEG" ]; then
    curl -fsSLO "https://ffmpeg.org/releases/$FFMPEG.tar.xz"
    tar xf "$FFMPEG.tar.xz"
fi
cd "$FFMPEG"
./configure --prefix=/opt/ffmpeg-min \
    --enable-shared --disable-static --enable-small \
    --disable-programs --disable-doc --disable-debug --disable-network \
    --disable-everything --disable-autodetect --disable-x86asm --enable-w32threads \
    --enable-decoder=aac,alac,h264,hevc --enable-parser=aac,h264,hevc
make -j"$(nproc)"
make install
