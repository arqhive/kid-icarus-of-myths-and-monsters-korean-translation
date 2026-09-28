"""Copy the completed build to the actual Windows Desktop, including redirection."""
from pathlib import Path
import ctypes
import hashlib
import os
import shutil


def copy_to_desktop(source):
    if os.name != 'nt':
        return None
    buf = ctypes.create_unicode_buffer(32768)
    result = ctypes.windll.shell32.SHGetFolderPathW(None, 0x10, None, 0, buf)
    if result != 0 or not buf.value:
        raise OSError(f'Cannot resolve Windows Desktop: {result}')
    source = Path(source).resolve()
    destination = Path(buf.value) / 'Kid Icarus - Korean Full (Galmuri).gb'
    source_hash = hashlib.sha256(source.read_bytes()).hexdigest()
    if not destination.exists() or hashlib.sha256(destination.read_bytes()).hexdigest() != source_hash:
        shutil.copy2(source, destination)
    if hashlib.sha256(destination.read_bytes()).hexdigest() != source_hash:
        raise OSError('Desktop copy hash mismatch')
    print(f'Desktop copy verified: {destination}')
    return destination
