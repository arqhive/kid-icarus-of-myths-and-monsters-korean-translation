"""Reproducible full Korean text patch. No gameplay or battery-save changes."""
from pathlib import Path
import hashlib,json,sys
from paths import ROOT, WORK, KO
HERE=WORK/'full'
HERE.mkdir(parents=True,exist_ok=True)
from build_demo import load_glyphs,glyph_tile,make_ips,EXPECTED_SHA256,SOURCE
import build_title
from extract_text import dialogues,TABLE
from hangul_stack import split,final_rows
DIALOGUES=KO['dialogues']
LABELS=[(int(r['offset'],16),r['source_label'],r['korean'],r.get('align','center')) for r in KO['labels']]
OUTPUT=WORK/'Kid Icarus - Korean Full (Galmuri).gb'
LETTERS=list(range(0x94,0xa0))+list(range(0xa4,0xb2))
SPRITES=[(int(r['offset'],16),r['korean']) for r in KO['sprites']]
# Bank 2 font (VRAM 8800-8FFF) is shared with stage sprites: C7-CE are the hint
# NPC, D0-EE and F0-F1 are frames/objects. Only the katakana F2-FD are unused.
KATAKANA=list(range(0xf2,0xfe))
STATUS_SLOTS=LETTERS[:8]          # loaded only while the status window is drawn
CREDIT_POOL=list(range(0xc7,0xcf))+list(range(0xe5,0xec))
STATUS_MAP=(0x164fc,0x16664)      # window map drawn from bank 5 at 7610
CREDIT_MAP=(0x167ea,0x16952)      # continue screen, loaded from 388B only
STAGE_FONT_BANK=13
CREDIT_FONT_BANK=12
DIALOGUE_BANK=10
PAGE_TABLE=0x6800                 # per page: 32 top slots, 32 final slots
DIALOGUE_CODE=0x7400

class Asm:
 def __init__(self,start):self.start=start;self.data=bytearray();self.labels={};self.fix=[];self.abs=[]
 def emit(self,s):self.data.extend(bytes.fromhex(s))
 def label(self,s):self.labels[s]=self.start+len(self.data)
 def jr(self,opcode,label):self.emit(opcode+' 00');self.fix.append((len(self.data)-1,label))
 def call(self,label):self.emit('cd 00 00');self.abs.append((len(self.data)-2,label))
 def finish(self):
  for p,l in self.fix:
   delta=self.labels[l]-(self.start+p+1);assert -128<=delta<128;self.data[p]=delta&255
  for p,l in self.abs:self.data[p:p+2]=self.labels[l].to_bytes(2,'little')
  return self.data

def ui_tile(c,glyphs):
 return bytes(b for v in glyph_tile(c,glyphs)[::2] for b in (v,0))

def dialogue_routine():
 """Bank 10. B=syllable code. Uploads top and final glyphs, writes both map cells, returns B=top tile."""
 a=Asm(DIALOGUE_CODE)
 a.emit('c5')                                   # keep caller BC
 a.emit('fa 71 c0 6f 26 00 29 29 29 29 29 29')  # HL = page*64
 a.emit(f'11 {PAGE_TABLE&255:02x} {PAGE_TABLE>>8:02x} 19')
 a.emit('78 85 6f 7c ce 00 67')                 # HL += code
 a.emit('7e e5');a.call('upload');a.emit('4f')  # top slot -> tile in C
 a.emit('fa 6e c0 6f fa 6f c0 67');a.call('waitv');a.emit('71')
 a.emit('e1 c5 11 20 00 19 7e a7');a.jr('28','done')
 a.emit('3d');a.call('upload');a.emit('4f')     # final slot -> tile in C
 a.emit('fa 6e c0 c6 20 6f fa 6f c0 ce 00 67');a.call('waitv');a.emit('71')
 a.label('done')
 a.emit('c1 79 c1 47 c9')                       # B = top tile
 a.label('upload')                              # A=slot; returns A=tile
 a.emit('5f 87 87 87 6f fa 71 c0 c6 40 67')     # HL = glyph page + slot*8
 a.emit('e5 16 00 21 c0 7f 19 7e e1 f5')        # A = LETTERS[slot]
 a.emit('cb 37 5f e6 0f f6 80 57 7b e6 f0 5f')  # DE = $8000 + tile*16
 a.emit('c5 f0 47 e6 02 d6 01 9f 4f 06 08')     # palette selects low-only / both planes
 a.label('row');a.emit('f0 41 e6 02');a.jr('20','row')
 a.emit('2a 12 13 a1 12 13 05');a.jr('20','row')
 a.emit('c1 f1 c9')
 a.label('waitv');a.emit('f0 41 e6 02');a.jr('20','waitv');a.emit('c9')
 return a.finish()

def main(base=None):
 original=SOURCE.read_bytes();assert hashlib.sha256(original).hexdigest()==EXPECTED_SHA256
 rom=bytearray(base if base is not None else build_title.main())
 assert len(rom)==0x40000 and rom[0x1db0]==9 and rom[0x1dc1]==8
 glyphs=load_glyphs();records=dialogues()
 assert len(DIALOGUES)==len(records)==39
 manifest={'dialogues':[],'labels':[]}
 bank=DIALOGUE_BANK*0x4000
 pos=0x17966
 for i,lines in enumerate(DIALOGUES):
  assert all(len(s)<=18 for s in lines) and len(lines)<=3,(i,lines)
  syllables=list(dict.fromkeys(''.join(lines).replace(' ','')))
  tops=list(dict.fromkeys(split(c)[0] for c in syllables))
  finals=list(dict.fromkeys(f for c in syllables for f in [split(c)[1]] if f))
  slots=len(tops)+len(finals)
  assert slots<=26 and len(syllables)<=31,(i,slots,len(syllables))
  code={c:n+1 for n,c in enumerate(syllables)};code[' ']=0
  table=bytearray(64)
  for c in syllables:
   top,f=split(c)
   table[code[c]]=tops.index(top)
   table[32+code[c]]=len(tops)+finals.index(f)+1 if f else 0
  rom[bank+PAGE_TABLE-0x4000+i*64:bank+PAGE_TABLE-0x4000+i*64+64]=table
  for n,t in enumerate(tops):rom[bank+i*256+n*8:bank+i*256+n*8+8]=glyph_tile(t,glyphs)[::2]
  for n,f in enumerate(finals):
   s=len(tops)+n;rom[bank+i*256+s*8:bank+i*256+s*8+8]=final_rows(f)
  encoded=bytearray()
  for j,line in enumerate(lines):
   if j:encoded.append(0xfe)
   encoded.extend([0]*((18-len(line))//2));encoded.extend(code[c] for c in line)
  encoded.append(int(records[i]['terminal'],16))
  assert pos+len(encoded)<=0x17ff0
  rom[0x17918+i*2:0x1791a+i*2]=(pos-0x10000).to_bytes(2,'little')
  rom[pos:pos+len(encoded)]=encoded
  manifest['dialogues'].append({'id':i,'english':records[i]['english'],'korean':lines,'offset':pos,'bytes':list(encoded),'syllables':syllables,'tiles':slots})
  pos+=len(encoded)
 rom[pos:0x17ff0]=bytes(0x17ff0-pos)
 rom[bank+0x3fc0:bank+0x3fc0+26]=bytes(LETTERS)
 routine=dialogue_routine()
 assert DIALOGUE_CODE+len(routine)<=0x7fc0
 rom[bank+DIALOGUE_CODE-0x4000:bank+DIALOGUE_CODE-0x4000+len(routine)]=routine
 # Dialogue lines advance two map rows (syllable row + final row), starting one row higher.
 assert rom[0x17888:0x1788d]==bytes.fromhex('fa 6e c0 c6 20');rom[0x1788c]=0x40
 assert rom[0xf2a:0xf32]==bytes.fromhex('3e 99 ea 6f c0 3e 47 ea');rom[0xf30]=0x27
 assert rom[0x178cf:0x178d4]==bytes.fromhex('21 27 99 0e 05');rom[0x178d3]=6
 # Bank 0 stubs live in the unused space after the interrupt vectors.
 assert original[0x63:0x100]==b'\xff'*(0x100-0x63)
 rom[0x63:0x100]=b'\xff'*(0x100-0x63)
 stub=Asm(0x63)
 stub.label('dialogue')
 stub.emit(f'e5 d5 3e {DIALOGUE_BANK:02x} ea ff 3f cd {DIALOGUE_CODE&255:02x} {DIALOGUE_CODE>>8:02x} 3e 05 ea ff 3f d1 e1 3e 10 c3 55 0c')
 stub.label('status')   # upload status-window glyphs into the alphabet tiles, then draw the window
 stub.emit(f'c5 d5 3e {STAGE_FONT_BANK:02x} ea ff 3f 21 00 7e 11 40 89 01 80 00 cd 0d 18 3e 05 ea ff 3f d1 c1 21 fc 64 c3 96 04')
 stub.label('credit')   # the continue/game-over screen loads its own UI font bank
 stub.emit(f'3e {CREDIT_FONT_BANK:02x} c3 b6 15')
 stub.label('ending')
 stub.emit('3e 0b ea ff 3f 21 00 7d 11 50 8e 01 30 00 c3 0d 18')
 stubs=stub.finish();assert 0x63+len(stubs)<=0x100
 rom[0x63:0x63+len(stubs)]=stubs
 assert rom[0x178a3:0x178a8]==bytes.fromhex('3e 10 cd 55 0c')
 rom[0x178a3:0x178a8]=bytes([0xcd,stub.labels['dialogue']&255,stub.labels['dialogue']>>8,0,0])
 assert rom[0x17610:0x17616]==bytes.fromhex('21 fc 64 cd 96 04')
 rom[0x17610:0x17616]=bytes([0xcd,stub.labels['status']&255,stub.labels['status']>>8,0,0,0])
 assert rom[0x388b:0x388e]==bytes.fromhex('cd b4 15')
 rom[0x388b:0x388e]=bytes([0xcd,stub.labels['credit']&255,stub.labels['credit']>>8])
 assert rom[0x15b4:0x15b6]==bytes.fromhex('3e 02');rom[0x15b5]=STAGE_FONT_BANK
 # UI fonts. Stage font keeps every original tile except the unused katakana.
 status_chars=[];kata_chars=[];credit_chars=[]
 def bucket(offset):
  if STATUS_MAP[0]<=offset<STATUS_MAP[1]:return 'status'
  if CREDIT_MAP[0]<=offset<CREDIT_MAP[1]:return 'credit'
  return 'kata'
 for offset,_,ko,_ in LABELS:
  for c in ko:
   if c in ' ?!':continue
   (status_chars if bucket(offset)=='status' else credit_chars if bucket(offset)=='credit' else kata_chars).append(c)
 credit_chars+=[c for _,s in SPRITES for c in s if c not in ' ?!']
 kata_chars=list(dict.fromkeys(kata_chars))
 status_chars=[c for c in dict.fromkeys(status_chars) if c not in kata_chars]
 credit_chars=[c for c in dict.fromkeys(credit_chars) if c not in kata_chars]
 assert len(kata_chars)<=len(KATAKANA),kata_chars
 assert len(status_chars)<=len(STATUS_SLOTS),status_chars
 assert len(credit_chars)<=len(CREDIT_POOL),credit_chars
 punct={' ':0x8a,'?':0xc1,'!':0xc5}
 kata=dict(zip(kata_chars,KATAKANA))
 tables={'kata':{**kata,**punct},
         'status':{**kata,**dict(zip(status_chars,STATUS_SLOTS)),**punct},
         'credit':{**kata,**dict(zip(credit_chars,CREDIT_POOL)),**punct}}
 for fb in (STAGE_FONT_BANK,CREDIT_FONT_BANK):
  base=fb*0x4000
  rom[base:base+0x4000]=original[0x8000:0xc000]
  for c,t in kata.items():rom[base+0x800+(t-0x80)*16:base+0x800+(t-0x80)*16+16]=ui_tile(c,glyphs)
 sb=STAGE_FONT_BANK*0x4000
 for n,c in enumerate(status_chars):rom[sb+0x3e00+n*16:sb+0x3e00+n*16+16]=ui_tile(c,glyphs)
 cb=CREDIT_FONT_BANK*0x4000
 for c,t in zip(credit_chars,CREDIT_POOL):rom[cb+0x800+(t-0x80)*16:cb+0x800+(t-0x80)*16+16]=ui_tile(c,glyphs)
 for offset,en,ko,align in LABELS:
  assert ''.join(TABLE.get(v,' ') for v in original[offset:offset+len(en)])==en,(offset,en)
  width=max(len(en),3 if en=='NO' else len(en))
  assert len(ko)<=width,('UI label too long',en,ko)
  blank=0x8a if offset<0x16664 else 0
  table=tables[bucket(offset)]
  encoded=[blank]*width;start=0 if align=='left' else (width-len(ko))//2
  encoded[start:start+len(ko)]=[table[c] if c!=' ' else blank for c in ko]
  rom[offset:offset+width]=bytes(encoded)
  manifest['labels'].append({'offset':offset,'english':en,'korean':ko,'font':bucket(offset)})
 for offset,s in SPRITES:
  assert len(s)<=10,('Sprite text too long',s)
  tiles=[tables['credit'][c] for c in s];tiles=[0x8a]*((10-len(tiles))//2)+tiles
  tiles+= [0x8a]*(10-len(tiles))
  for n,t in enumerate(tiles):rom[offset+n*4+2]=t
 # PAUSE has its own five-tile font, loaded and restored by the original code.
 assert len(KO['pause'])==5
 for n,c in enumerate(KO['pause']):
  rom[0x71a1+n*16:0x71b1+n*16]=bytes(16) if c==' ' else glyph_tile(c,glyphs)
 # Final caption has an isolated bank/loader so it cannot disturb dialogue glyphs.
 rom[0x2c000:0x30000]=original[0x1c000:0x20000]
 ending_lines=[(r['row'],r['korean']) for r in KO['ending']]
 assert [r for r,s in ending_lines]==[0,2]
 ending_chars=list(dict.fromkeys(''.join(s for r,s in ending_lines)))
 assert len(ending_chars)<=3, 'Ending font area has three reserved glyphs'
 endtable={c:0xe5+n for n,c in enumerate(ending_chars)}
 for n,c in enumerate(ending_chars):rom[0x2fd00+n*16:0x2fd10+n*16]=glyph_tile(c,glyphs)
 for row,s in ending_lines:
  assert len(s)<=12
  tiles=[0]*12;p=(12-len(s))//2;tiles[p:p+len(s)]=[endtable[c] for c in s]
  rom[0x2f0b8+row*12:0x2f0c4+row*12]=bytes(tiles)
 ending_start=stub.labels['ending']
 rom[0xce7:0xcec]=bytes([0xcd,ending_start&255,ending_start>>8,0,0])
 for bank_no in range(8,16):rom[(bank_no+1)*0x4000-1]=bank_no
 check=0
 for v in rom[0x134:0x14d]:check=(check-v-1)&255
 rom[0x14d]=check;rom[0x14e:0x150]=b'\0\0';rom[0x14e:0x150]=(sum(rom)&65535).to_bytes(2,'big')
 OUTPUT.write_bytes(rom);(HERE/'Kid_Icarus_Korean_Full.ips').write_bytes(make_ips(original,rom))
 manifest.update({'source_sha256':EXPECTED_SHA256,'output_sha256':hashlib.sha256(rom).hexdigest(),'dialogue_bytes':pos-0x17966,'dialogue_routine_bytes':len(routine),'bank0_stub_bytes':len(stubs),'ending_hook':ending_start,'ui_characters':{k:{c:hex(t) for c,t in v.items()} for k,v in tables.items()},'output':str(OUTPUT)})
 (HERE/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
 print(json.dumps({k:v for k,v in manifest.items() if k not in ('dialogues','labels','ui_characters')},ensure_ascii=False,indent=2))
if __name__=='__main__':main()
