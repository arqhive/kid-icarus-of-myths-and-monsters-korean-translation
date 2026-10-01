"""Package a verified local v0.1 release; never publish or contact a remote."""
import argparse
import hashlib
import json
import shutil
import zipfile
from pathlib import Path
from apply_patch import apply_ips
from paths import ROOT, WORK, SOURCE, EXPECTED_SHA256


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('version', nargs='?', default='v0.1', choices=['v0.1'])
    args = parser.parse_args()
    release = ROOT/'release'
    release.mkdir(exist_ok=True)
    rom = (WORK/'Kid Icarus - Korean Full (Galmuri).gb').read_bytes()
    original = SOURCE.read_bytes()
    patch = (WORK/'full/Kid_Icarus_Korean_Full.ips').read_bytes()
    digest = hashlib.sha256(rom).hexdigest()
    assert hashlib.sha256(original).hexdigest() == EXPECTED_SHA256
    assert apply_ips(original, patch) == rom
    patch_name = f'KidIcarus_KO_{args.version}.ips'
    (release/patch_name).write_bytes(patch)
    manifest = {'version': args.version, 'patch': patch_name,
                'source_sha256': EXPECTED_SHA256, 'output_sha256': digest,
                'patch_sha256': hashlib.sha256(patch).hexdigest(), 'output_size': len(rom)}
    (release/'patch_manifest.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8')
    archive = release/f'KidIcarus_KO_{args.version}.zip'
    files = {release/patch_name:patch_name, release/'patch_manifest.json':'patch_manifest.json',
             ROOT/'tools/apply_patch.py':'apply_patch.py', release/'README_한국어.txt':'README_한국어.txt',
             ROOT/'tools/fonts/OFL.txt':'OFL.txt', ROOT/'LICENSE':'LICENSE',
             ROOT/'docs/releases/v0.1.md':'RELEASE_NOTES.md'}
    with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED) as bundle:
        for path,name in files.items():
            info=zipfile.ZipInfo(name,date_time=(2026,9,29,0,0,0))
            info.compress_type=zipfile.ZIP_DEFLATED
            bundle.writestr(info,path.read_bytes())
    print(f'Local release: {archive}')
    print(f'SHA256: {hashlib.sha256(archive.read_bytes()).hexdigest()}')


if __name__ == '__main__':
    main()
