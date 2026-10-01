"""Compile a Korean pixel title into native GB tiles in an isolated ROM bank."""
from pathlib import Path
import hashlib
import json
import re
from PIL import Image
from build_demo import SOURCE, OUTPUT as OPENING_ROM, make_ips

from paths import ROOT, WORK, FONTS, KO
HERE = FONTS.parent
OUT = WORK/'title'
OUT.mkdir(parents=True, exist_ok=True)
OUTPUT = WORK/'Kid Icarus - Korean Title and Opening (Galmuri).gb'
TITLE = KO['title']
SUBTITLE = KO['subtitle']


def font(path):
    result = {}
    for block in path.read_text(encoding='utf-8').split('STARTCHAR ')[1:]:
        code = int(re.search(r'^ENCODING (-?\d+)', block, re.M)[1])
        if code < 0:
            continue
        width, height, xoff, yoff = map(int, re.search(r'^BBX (.*)', block, re.M)[1].split())
        rows = block.split('BITMAP\n')[1].split('ENDCHAR')[0].strip().splitlines()
        points = set()
        for y, row in enumerate(rows):
            number = int(row, 16)
            for x in range(width):
                if number >> (len(row)*4-1-x) & 1:
                    points.add((x+xoff, y))
        result[chr(code)] = (width, height, xoff, yoff, points)
    return result


def decode_tile(raw):
    return [[((raw[y*2]>>(7-x))&1) | (((raw[y*2+1]>>(7-x))&1)<<1)
             for x in range(8)] for y in range(8)]


def encode_tile(pixels):
    result = bytearray()
    for row in pixels:
        lo = hi = 0
        for value in row:
            lo = (lo<<1) | (value&1)
            hi = (hi<<1) | ((value>>1)&1)
        result.extend((lo,hi))
    return bytes(result)


def main():
    original = SOURCE.read_bytes()
    base = OPENING_ROM.read_bytes()
    rom = bytearray(base)
    small = font(FONTS/'Galmuri7.bdf')
    large = font(FONTS/'Galmuri11.bdf')
    tilemap = bytearray(base[0x23402:0x2356A])
    low = [base[0x1C000+i*16:0x1C000+(i+1)*16] for i in range(128)]
    high = [base[0x20000+i*16:0x20000+(i+1)*16] for i in range(128)]
    pixels = [[0]*160 for _ in range(144)]
    for pos, tile_id in enumerate(tilemap):
        tile = decode_tile((low+high)[tile_id])
        for y in range(8):
            for x in range(8):
                pixels[pos//20*8+y][pos%20*8+x] = tile[y][x]
    # Native title area: rows 3-8. Mountains, clouds, menu and copyright stay intact.
    for y in range(24,72):
        pixels[y] = [0]*160
    face = set()
    cursor = 0
    for char in TITLE:
        if char == ' ':
            cursor += 4
            continue
        width, height, xoff, yoff, points = large[char]
        for x, y in points:
            # Integer pixel scaling: tall lettering, with a small rightward slant.
            yy = (11-height-yoff+y)*3
            for sy in range(3):
                shift = (32-(yy+sy))//8
                for sx in range(3):
                    face.add((cursor+x*2+sx+shift, yy+sy))
        cursor += 24
    minx = min(x for x,y in face)
    maxx = max(x for x,y in face)
    xorigin = (160-(maxx-minx+1+4))//2-minx+1
    face = {(x+xorigin,y+26) for x,y in face}
    outline = {(x+dx,y+dy) for x,y in face for dx in [-1,0,1] for dy in [-1,0,1]}
    shadow = {(x+step,y+step) for x,y in outline for step in [1,2,3]}
    assert all(0<=x<160 and 24<=y<64 for x,y in outline|shadow)
    for x,y in shadow:
        pixels[y][x] = 3
    for x,y in outline:
        pixels[y][x] = 3
    for x,y in face:
        # 1 is white and 2 is dark gray under the game's E1 palette.
        pixels[y][x] = 2 if (x+1,y+1) not in face else 1
    # Restore the original trademark tile at its original place (row 3, column 19).
    trademark = decode_tile(low[0x47])
    for y in range(8):
        for x in range(8):
            if trademark[y][x]:
                assert pixels[24+y][152+x] == 0, 'Logo overlaps trademark'
                pixels[24+y][152+x] = trademark[y][x]
    # Galmuri9 Hangul (9x9) keeps the final consonant of 물 legible; rows 63-71.
    sub = font(FONTS/'Galmuri9.bdf')
    advance = lambda c: 4 if c==' ' else sub[c][0]+1
    subtitle_width = sum(advance(c) for c in SUBTITLE)-1
    cursor = (160-subtitle_width)//2
    for char in SUBTITLE:
        if char == ' ':
            cursor += 4
            continue
        width,height,xoff,yoff,points = sub[char]
        for x,y in points:
            yy = 72-height-yoff+y
            assert pixels[yy][cursor+x] == 0, 'Subtitle overlaps title shadow'
            pixels[yy][cursor+x] = 3
        cursor += width+1
    left = (160-subtitle_width)//2
    for x in range(22,left-7):
        pixels[67][x] = 3
        pixels[68][x] = 1
        pixels[67][159-x] = 3
        pixels[68][159-x] = 1

    # Keep all low-bank tiles used outside the replaced area at their old IDs.
    kept_ids = {value for pos,value in enumerate(tilemap) if not 60<=pos<180 and value<128}
    # The scroller reads one additional blank row after the title map (tile 4E).
    kept_ids.update(value for value in base[0x2356A:0x2357E] if value<128)
    compiled = {index: low[index] for index in kept_ids}
    lookup = {value:index for index,value in compiled.items()}
    lookup[bytes(16)] = 0x81  # Existing high-bank blank tile.
    free_ids = iter(index for index in range(128) if index not in kept_ids)
    for tile_y in range(3,9):
        for tile_x in range(20):
            raw = encode_tile([pixels[tile_y*8+y][tile_x*8:tile_x*8+8] for y in range(8)])
            if raw not in lookup:
                index = next(free_ids)
                compiled[index] = raw
                lookup[raw] = index
            tilemap[tile_y*20+tile_x] = lookup[raw]
    # Separate bank 9: no gameplay assets in original bank 7 are overwritten.
    rom[0x24000:0x28000] = original[0x1C000:0x20000]
    rom[0x27FFF] = 9
    for index,raw in compiled.items():
        rom[0x24000+index*16:0x24000+(index+1)*16] = raw
    rom[0x23402:0x2356A] = tilemap
    assert base[0x1DAF:0x1DB4] == bytes.fromhex('3e 07 ea ff 3f')
    rom[0x1DB0] = 9
    rom[0x14E:0x150] = b'\0\0'
    rom[0x14E:0x150] = (sum(rom)&65535).to_bytes(2,'big')
    OUTPUT.write_bytes(rom)
    (OUT/'Korean_Title_and_Opening.ips').write_bytes(make_ips(original,rom))
    # Palette E1 maps native pixel IDs to [gray, white, dark gray, black].
    colors = [(153,153,153),(255,255,255),(85,85,85),(0,0,0)]
    preview = Image.new('RGB',(160,144))
    for y in range(144):
        for x in range(160):
            preview.putpixel((x,y),colors[pixels[y][x]])
    preview.resize((640,576),Image.Resampling.NEAREST).save(OUT/'title_design.png')
    manifest = {'rom':OUTPUT.name,'title':TITLE,'subtitle':SUBTITLE,
                'font':'Galmuri11 title / Galmuri7 subtitle and opening',
                'title_low_bank_tiles':len(compiled),'preserved_low_tile_ids':sorted(kept_ids),
                'new_graphics_bank':9,'input_sha256':hashlib.sha256(base).hexdigest(),
                'output_sha256':hashlib.sha256(rom).hexdigest(),
                'font_sha256':hashlib.sha256((FONTS/'Galmuri11.bdf').read_bytes()).hexdigest()}
    (OUT/'build_manifest.json').write_text(json.dumps(manifest,indent=2,ensure_ascii=False),encoding='utf-8')
    print(json.dumps(manifest,indent=2,ensure_ascii=False))


if __name__=='__main__':
    main()
