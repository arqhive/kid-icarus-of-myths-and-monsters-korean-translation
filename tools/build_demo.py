"""Build a Korean opening/title-menu demo from the user's verified original ROM."""
from pathlib import Path
import hashlib
import json
import re
from PIL import Image, ImageDraw

from paths import ROOT, WORK, SOURCE, EXPECTED_SHA256, FONTS, KO
HERE = WORK/'opening'
HERE.mkdir(parents=True, exist_ok=True)
FONT = FONTS/'Galmuri7.bdf'
OPENING = KO['opening']
MENU = KO['menu']


def load_glyphs():
    result = {}
    for block in FONT.read_text(encoding='utf-8').split('STARTCHAR ')[1:]:
        code = int(re.search(r'^ENCODING (-?\d+)', block, re.M)[1])
        if code < 0:
            continue
        box = tuple(map(int, re.search(r'^BBX (.*)', block, re.M)[1].split()))
        rows = block.split('BITMAP\n')[1].split('ENDCHAR')[0].strip().splitlines()
        result[chr(code)] = (box, rows)
    return result


def glyph_tile(char, glyphs):
    (width, height, xoff, yoff), rows = glyphs[char]
    # The native Galmuri7 Hangul is 7x7 on an 8px advance. Baseline is row 7.
    x = xoff if '\uac00' <= char <= '\ud7a3' else (8-width)//2 + xoff
    y = 7-height-yoff
    assert x >= 0 and y >= 0 and x+width <= 8 and y+height <= 8, (char, glyphs[char])
    bits = [0]*8
    for row_index, row_hex in enumerate(rows):
        row_bits = int(row_hex, 16)
        packed_width = len(row_hex)*4
        for col in range(width):
            if (row_bits >> (packed_width-1-col)) & 1:
                bits[y+row_index] |= 1 << (7-x-col)
    return bytes(value for row in bits for value in (row, row))


def make_ips(original, patched):
    result = bytearray(b'PATCH')
    i = 0
    while i < len(patched):
        if i < len(original) and patched[i] == original[i]:
            i += 1
            continue
        start = i
        while i < len(patched) and i-start < 65535 and (i >= len(original) or patched[i] != original[i]):
            i += 1
        result += start.to_bytes(3, 'big') + (i-start).to_bytes(2, 'big') + patched[start:i]
    return bytes(result + b'EOF')


def main():
    """Return the opening-stage ROM bytes; only build_full writes a ROM."""
    original = SOURCE.read_bytes()
    assert hashlib.sha256(original).hexdigest() == EXPECTED_SHA256, 'Unexpected source ROM'
    assert len(OPENING) == 27 and all(len(line) <= 20 for line in OPENING)
    glyphs = load_glyphs()
    chars = sorted(set(''.join(OPENING)+''.join(MENU.values())) - {' '})
    # Keep the solid/blank tiles 80/81, cursor 84, and all decorations B6-DF.
    available = [0x82, 0x83] + list(range(0x85, 0xB6)) + list(range(0xE0, 0x100))
    assert len(chars) <= len(available), (len(chars), len(available))
    assert not set(chars)-set(glyphs), 'Missing font glyph'
    table = dict(zip(chars, available))
    table[' '] = 0x81
    rom = bytearray(original) + bytearray([0xFF])*len(original)
    # Bank 8 mirrors bank 5's original assets at the original CPU addresses.
    # Its otherwise-unused 4000-47FF now contains the independent font block.
    rom[0x20000:0x24000] = original[0x14000:0x18000]
    for bank in range(8, 16):
        rom[(bank+1)*0x4000-1] = bank
    atlas = bytearray(original[0x16B82:0x17382])
    for char in chars:
        tile = table[char]
        atlas[(tile-0x80)*16:(tile-0x80+1)*16] = glyph_tile(char, glyphs)
    rom[0x20000:0x20800] = atlas
    for index, line in enumerate(OPENING):
        encoded = bytes(table[c] for c in line.center(20))
        offset = 0x23196+index*20
        rom[offset:offset+20] = encoded
    rom[0x234F8:0x23500] = bytes(table[c] for c in MENU['new_game'].center(8))
    rom[0x23520:0x23528] = bytes(table[c] for c in MENU['continue'].center(8))
    # Only the opening-specific font load and row streamer select the new bank.
    assert original[0x1DC0:0x1DC8] == bytes.fromhex('3e 05 ea ff 3f 21 82 6b')
    assert original[0x1E92:0x1E97] == bytes.fromhex('3e 05 ea ff 3f')
    rom[0x1DC1] = 8
    rom[0x1DC6:0x1DC8] = bytes.fromhex('00 40')
    rom[0x1E93] = 8
    rom[0x148] = 3  # 256 KiB, still MBC2.
    checksum = 0
    for value in rom[0x134:0x14D]:
        checksum = (checksum-value-1) & 255
    rom[0x14D] = checksum
    rom[0x14E:0x150] = b'\0\0'
    rom[0x14E:0x150] = (sum(rom)&65535).to_bytes(2, 'big')
    (HERE/'translation_ko.txt').write_text('\n'.join(OPENING)+'\n\nNEW GAME → 새 게임\nCONTINUE → 이어하기\n', encoding='utf-8')
    (HERE/'korean.tbl').write_text('\n'.join(f'{tile:02X}={char}' for char, tile in table.items()), encoding='utf-8')
    manifest = {
        'stage': 'opening', 'source_sha256': EXPECTED_SHA256,
        'output_sha256': hashlib.sha256(rom).hexdigest(),
        'font_sha256': hashlib.sha256(FONT.read_bytes()).hexdigest(),
        'font': 'Galmuri7 native BDF glyphs, no scaling',
        'glyph_count': len(chars), 'size_bytes': len(rom),
        'changed_original_offsets': [f'{i:05X}' for i in range(len(original)) if original[i] != rom[i]],
        'translation_scope': ['opening story', 'NEW GAME', 'CONTINUE'],
        'new_font_offset': '20000', 'opening_offset': '23182', 'title_map_offset': '23402',
    }
    (HERE/'build_manifest.json').write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding='utf-8')
    # Accurate pixel preview of the whole opening with the original frame.
    tiles = {index: bytes(atlas[(index-128)*16:(index-127)*16]) for index in range(128,256)}
    preview = Image.new('RGB', (160,256), (160,160,160))
    for pos, tile_id in enumerate(rom[0x23182:0x23402]):
        raw = tiles[tile_id]
        for y in range(8):
            for x in range(8):
                color = ((raw[y*2]>>(7-x))&1) | (((raw[y*2+1]>>(7-x))&1)<<1)
                preview.putpixel((pos%20*8+x, pos//20*8+y), [(160,160,160),(100,100,100),(60,60,60),(0,0,0)][color])
    preview.resize((480,768), Image.Resampling.NEAREST).save(HERE/'opening_layout.png')
    return bytes(rom)
    print(json.dumps(manifest, indent=2, ensure_ascii=False))


if __name__ == '__main__':
    main()
