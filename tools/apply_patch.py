"""Apply a release IPS with input/output hash checks; preserve the source ROM."""
import argparse
import hashlib
import json
from pathlib import Path


def apply_ips(original, patch):
    if not patch.startswith(b'PATCH'):
        raise ValueError('Invalid IPS header')
    result = bytearray(original)
    pos = 5
    while True:
        if patch[pos:pos+3] == b'EOF':
            if pos+3 != len(patch):
                raise ValueError('Unexpected IPS trailing bytes')
            return bytes(result)
        if pos+5 > len(patch):
            raise ValueError('Truncated IPS record')
        offset = int.from_bytes(patch[pos:pos+3], 'big')
        size = int.from_bytes(patch[pos+3:pos+5], 'big')
        pos += 5
        if size == 0:
            if pos+3 > len(patch):
                raise ValueError('Truncated IPS RLE record')
            size = int.from_bytes(patch[pos:pos+2], 'big')
            data = bytes([patch[pos+2]]) * size
            pos += 3
        else:
            if pos+size > len(patch):
                raise ValueError('Truncated IPS payload')
            data = patch[pos:pos+size]
            pos += size
        if offset+size > 0x40000:
            raise ValueError('Patch exceeds supported ROM size')
        if offset+size > len(result):
            result.extend(bytes(offset+size-len(result)))
        result[offset:offset+size] = data


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('rom', type=Path)
    parser.add_argument('--output', type=Path)
    default = Path(__file__).resolve().parent
    if not (default/'patch_manifest.json').exists():
        default = default.parent/'release'
    parser.add_argument('--manifest', type=Path, default=default/'patch_manifest.json')
    args = parser.parse_args()
    manifest = json.loads(args.manifest.read_text(encoding='utf-8'))
    original = args.rom.read_bytes()
    if hashlib.sha256(original).hexdigest() != manifest['source_sha256']:
        raise SystemExit('Wrong source ROM. Use the unmodified USA/Europe version listed in README.')
    patch = (args.manifest.parent/manifest['patch']).read_bytes()
    if hashlib.sha256(patch).hexdigest() != manifest['patch_sha256']:
        raise SystemExit('Patch checksum mismatch.')
    result = apply_ips(original, patch)
    if hashlib.sha256(result).hexdigest() != manifest['output_sha256']:
        raise SystemExit('Output checksum mismatch.')
    output = args.output or args.rom.with_name('Kid Icarus - Korean Full (Galmuri).gb')
    if output.resolve() == args.rom.resolve():
        raise SystemExit('The original ROM cannot be overwritten.')
    if output.exists() and output.read_bytes() != result:
        raise SystemExit(f'Output already exists with different contents: {output}')
    output.write_bytes(result)
    print(f'Created and verified: {output.resolve()}')


if __name__ == '__main__':
    main()
