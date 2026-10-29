# AirCast

Spejl din iPhone eller iPad til en Windows-PC via **Skærmspejling** i Kontrolcenter, ligesom AirServer.
AirCast er én portabel `AirCast.exe` (ca. 18 MB) og skal ikke installeres.

- Op til 60 fps og lav forsinkelse; videoen afkodes af grafikkortet (Direct3D 12)
- Videovinduet skifter selv mellem stående og liggende, når du drejer enheden
- Lyd, fuldskærm (Alt+Enter), valgfri PIN-kode og valgfrit navn på modtageren
- Opløsning fra 720p op til 4K (H.265)

## Brug

1. Start `AirCast.exe`. Første gang spørger Windows Firewall om netværksadgang: tryk **Tillad**.
   Windows SmartScreen kan advare, fordi exe'en ikke er signeret: **Flere oplysninger → Kør alligevel**.
2. På iPhone/iPad: Kontrolcenter → **Skærmspejling** → vælg PC'ens navn.

PC og iPhone/iPad skal være på samme netværk. Kan enheden ikke se PC'en, er det næsten altid firewallen:
sæt netværket til **Privat** (Indstillinger → Netværk og internet) og tillad AirCast i firewallen.

Indstillinger gemmes i `%APPDATA%\AirCast`. AirPlay-motoren pakkes ud til `%LOCALAPPDATA%\AirCast` første gang.

## Sådan virker det

AirCast er et lille Python/Tk-program ([aircast.pyw](aircast.pyw)) oven på
[UxPlay](https://github.com/FDH2/UxPlay), der står for AirPlay-protokollen, og GStreamer, der afkoder og viser videoen.

- [videowindow.py](videowindow.py) tilpasser videovinduet, når UxPlay melder en ny billedstørrelse.
- [portable.py](portable.py) pakker den indbyggede motor (`engine.tar.xz`) ud første gang.
- [patches/uxplay.patch](patches/uxplay.patch) er AirCasts to ændringer i UxPlay: loggen skrives straks (`fflush`),
  og hver ny videostørrelse meldes, så vinduet kan følge med, når enheden drejes.

## Byg selv

Kræver [MSYS2](https://www.msys2.org) i `C:\msys64`, Python 3 og Windows PowerShell.

1. Installer pakker i en MSYS2 UCRT64-shell:

   ```bash
   pacman -S --needed git make diffutils mingw-w64-ucrt-x86_64-{cmake,gcc,ninja,pkgconf,openssl,libplist,gstreamer,gst-plugins-base,gst-plugins-good,gst-plugins-bad,gst-libav}
   ```

2. Byg UxPlay (med patch) og en minimal FFmpeg (kun AAC/ALAC/H.264/H.265-afkodere), stadig i UCRT64-shellen:

   ```bash
   bash build/build_uxplay.sh
   bash build/build_ffmpeg_min.sh
   ```

3. Byg `AirCast.exe` i PowerShell:

   ```powershell
   python -m pip install pyinstaller pillow
   .\build\build.ps1
   ```

   Resultatet ligger i `build\dist\AirCast.exe`.

## Licens

AirCast er udgivet under GPL-3.0 (se [LICENSE](LICENSE)), ligesom UxPlay, som den bygger på og indeholder.
`AirCast.exe` indeholder også GStreamer og FFmpeg (LGPL-2.1+), OpenSSL (Apache-2.0), libplist (LGPL-2.1+) og glib (LGPL-2.1+).
Kildekoden til dem kan hentes fra deres egne projekter; build-scripts angiver de præcise versioner.
