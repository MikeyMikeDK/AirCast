#!/usr/bin/env bash
# Samler uxplay.exe + de GStreamer-plugins og DLL'er den bruger i AirCast/engine,
# med samme mappestruktur som MSYS2 (bin, lib/gstreamer-1.0, libexec/gstreamer-1.0).
# FFmpeg-DLL'erne tages fra den minimale build i /opt/ffmpeg-min (se build_ffmpeg_min.sh).
# Køres i en MSYS2 UCRT64-shell.
set -euo pipefail

SRC=/ucrt64
FFMPEG_MIN=/opt/ffmpeg-min
ENGINE="$(cd "$(dirname "$0")/.." && pwd)/engine"
PLUGINS="app audioconvert audioparsers audioresample autodetect coreelements d3d12 level libav
         playback typefindfunctions videoconvertscale videofilter videoparsersbad volume wasapi2"

test -f "$FFMPEG_MIN/bin/avcodec-63.dll" || { echo "mangler $FFMPEG_MIN: kør build_ffmpeg_min.sh først"; exit 1; }

rm -rf "$ENGINE"
mkdir -p "$ENGINE/bin" "$ENGINE/lib/gstreamer-1.0" "$ENGINE/libexec/gstreamer-1.0"

cp "$SRC/bin/uxplay.exe" "$ENGINE/bin/"
cp "$SRC/libexec/gstreamer-1.0/gst-plugin-scanner.exe" "$ENGINE/libexec/gstreamer-1.0/"
for p in $PLUGINS; do
    cp "$SRC/lib/gstreamer-1.0/libgst$p.dll" "$ENGINE/lib/gstreamer-1.0/"
done

# Alle DLL'er som exe'erne og plugins afhænger af (ldd er rekursiv); den minimale FFmpeg
# står først i PATH, så dens DLL'er vælges frem for MSYS2's fulde FFmpeg
export PATH="$FFMPEG_MIN/bin:$PATH"
find "$ENGINE" -name '*.exe' -o -name '*.dll' | while read -r f; do
    ldd "$f" | awk '{print $3}' | grep -iE "^($SRC|$FFMPEG_MIN)/bin/" || true
done | sort -u | while read -r dll; do
    cp -n "$dll" "$ENGINE/bin/"
done

echo "engine: $(du -sh "$ENGINE" | cut -f1)"
