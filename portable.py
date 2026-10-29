"""Pakker AirPlay-motoren (engine.tar.xz, indbygget i AirCast.exe) ud til en fast mappe første gang."""

import shutil
import tarfile
import zlib
from pathlib import Path


def unpack_engine(archive: Path, data_dir: Path) -> Path:
    """Returnerer mappen med den udpakkede motor. Pakker kun ud, når arkivet er nyt/ændret,
    og fjerner så tidligere udgaver."""
    checksum = zlib.crc32(archive.read_bytes())
    target = data_dir / f"engine-{checksum:08x}"
    if target.exists():
        return target

    unpacking = data_dir / "engine-unpacking"
    if unpacking.exists():
        shutil.rmtree(unpacking)
    with tarfile.open(archive, "r:xz") as tar:
        tar.extractall(unpacking, filter="data")
    unpacking.rename(target)

    for old in data_dir.glob("engine-*"):
        if old != target:
            shutil.rmtree(old)
    return target
