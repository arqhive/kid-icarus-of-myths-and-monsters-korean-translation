"""Portable project paths. ROMs, build output and extracted text stay untracked."""
from pathlib import Path
import json
import os

ROOT = Path(__file__).resolve().parent.parent
WORK = ROOT / 'work'
FONTS = ROOT / 'tools/fonts'
KO = json.loads((ROOT / 'translation/ko.json').read_text(encoding='utf-8'))
EXPECTED_SHA256 = '92c1fbf422abb8f09ca7fdbb563d1284108cc042e60e1222422986d9a59f9d97'
ROM_NAME = 'Kid Icarus - Of Myths and Monsters (USA, Europe).gb'
DEFAULT_SOURCE = ROOT / 'roms' / ROM_NAME
if not DEFAULT_SOURCE.exists():
    DEFAULT_SOURCE = ROOT / ROM_NAME
SOURCE = Path(os.environ.get('KID_ICARUS_ROM', str(DEFAULT_SOURCE))).resolve()
