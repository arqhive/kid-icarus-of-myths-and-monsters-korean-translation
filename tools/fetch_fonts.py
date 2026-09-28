"""Download the exact upstream Galmuri BDFs used for v0.1, with SHA-256 checks."""
from pathlib import Path
import hashlib
import urllib.request

COMMIT = '71e1cacf1437a11220307120e63e30bc275312d4'
HASHES = {'Galmuri7.bdf': '0ec6b8707e8c47d85995b5b2b507180aed7bcc724792fe5477e998d41f8b075f', 'Galmuri11.bdf': '98716d08aa5762e6ce440d5a757d107cb5d3f32a53861878be06c00aacc23304'}

def main():
    folder = Path(__file__).resolve().parent/'fonts'
    folder.mkdir(exist_ok=True)
    for name, expected in HASHES.items():
        target = folder/name
        if target.exists() and hashlib.sha256(target.read_bytes()).hexdigest() == expected:
            print(f'Verified: {name}')
            continue
        url = f'https://raw.githubusercontent.com/quiple/galmuri/{COMMIT}/dist/{name}'
        with urllib.request.urlopen(url, timeout=60) as response:
            data = response.read()
        if hashlib.sha256(data).hexdigest() != expected:
            raise ValueError(f'Font checksum mismatch: {name}')
        target.write_bytes(data)
        print(f'Downloaded and verified: {name}')

if __name__ == '__main__':
    main()
