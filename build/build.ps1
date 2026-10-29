# Bygger AirCast som én portabel fil: build\dist\AirCast.exe (motoren ligger indbygget som engine.tar.xz).
# Kræver: MSYS2 (C:\msys64) med uxplay.exe i ucrt64 (build_uxplay.sh), minimal FFmpeg i /opt/ffmpeg-min
# (build_ffmpeg_min.sh) og Python med PyInstaller + Pillow. Se README.md.
$ErrorActionPreference = 'Stop'
$Build = $PSScriptRoot
$App = Split-Path $Build -Parent

# 1. Motor: uxplay.exe + plugins + DLL'er -> AirCast\engine -> build\engine.zip
$env:MSYSTEM = 'UCRT64'
& C:\msys64\usr\bin\bash.exe -lc "bash '$(($Build -replace '\\','/') -replace '^C:','/c')/bundle_engine.sh'"
if ($LASTEXITCODE) { throw "bundle_engine.sh fejlede" }
python -c "import lzma, sys, tarfile; t = tarfile.open(sys.argv[1], 'w:xz', preset=9 | lzma.PRESET_EXTREME); t.add(sys.argv[2], arcname='.'); t.close()" "$Build\engine.tar.xz" "$App\engine"
if ($LASTEXITCODE) { throw "pakning af motoren fejlede" }

# 2. Ikon
python "$Build\make_icon.py"

# 3. AirCast.exe (én fil)
python -m PyInstaller --noconfirm --windowed --onefile --name AirCast --icon "$App\aircast.ico" `
    --add-data "$Build\engine.tar.xz;." --add-data "$App\aircast.ico;." `
    --exclude-module _hashlib --exclude-module _ssl --exclude-module _bz2 --exclude-module _decimal `
    --distpath "$Build\dist" --workpath "$Build\work" --specpath $Build "$App\aircast.pyw"
if ($LASTEXITCODE) { throw "PyInstaller fejlede" }
Get-Item "$Build\dist\AirCast.exe"
