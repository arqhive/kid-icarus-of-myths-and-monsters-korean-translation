"""Reproducible full Korean text patch. No gameplay or battery-save changes."""
from pathlib import Path
import hashlib,json,sys
from paths import ROOT, WORK, KO
HERE=WORK/'full'
HERE.mkdir(parents=True,exist_ok=True)
from build_demo import load_glyphs,glyph_tile,make_ips,EXPECTED_SHA256,SOURCE
from build_title import OUTPUT as TITLE_ROM
from extract_text import dialogues,TABLE
DIALOGUES=KO['dialogues']
LABELS=[(int(r['offset'],16),r['source_label'],r['korean']) for r in KO['labels']]
OUTPUT=WORK/'Kid Icarus - Korean Full (Galmuri).gb'
LETTERS=list(range(0x94,0xa0))+list(range(0xa4,0xb2))
SPRITES=[(int(r['offset'],16),r['korean']) for r in KO['sprites']]

class Asm:
 def __init__(self,start):self.start=start;self.data=bytearray();self.labels={};self.fix=[]
 def emit(self,s):self.data.extend(bytes.fromhex(s))
 def label(self,s):self.labels[s]=self.start+len(self.data)
 def jr(self,opcode,label):self.emit(opcode+' 00');self.fix.append((len(self.data)-1,label))
 def finish(self):
  for p,l in self.fix:
   delta=self.labels[l]-(self.start+p+1);assert -128<=delta<128;self.data[p]=delta&255
  return self.data

def main():
 original=SOURCE.read_bytes();assert hashlib.sha256(original).hexdigest()==EXPECTED_SHA256
 rom=bytearray(TITLE_ROM.read_bytes())
 assert len(rom)==0x40000 and rom[0x1db0]==9 and rom[0x1dc1]==8
 glyphs=load_glyphs();records=dialogues()
 assert len(DIALOGUES)==len(records)==39
 manifest={'dialogues':[],'labels':[]}
 pos=0x17966
 for i,lines in enumerate(DIALOGUES):
  chars=list(dict.fromkeys(''.join(lines).replace(' ','')))
  assert len(chars)<=26 and all(len(s)<=18 for s in lines) and len(lines)<=3,(i,chars)
  table={c:n+1 for n,c in enumerate(chars)};table[' ']=0
  encoded=bytearray()
  for j,line in enumerate(lines):
   if j:encoded.append(0xfe)
   encoded.extend([0]*((18-len(line))//2));encoded.extend(table[c] for c in line)
  encoded.append(int(records[i]['terminal'],16))
  assert pos+len(encoded)<=0x17ff0
  rom[0x17918+i*2:0x1791a+i*2]=(pos-0x10000).to_bytes(2,'little')
  rom[pos:pos+len(encoded)]=encoded
  for n,c in enumerate(chars):rom[0x28000+i*256+n*8:0x28000+i*256+n*8+8]=glyph_tile(c,glyphs)[::2]
  manifest['dialogues'].append({'id':i,'english':records[i]['english'],'korean':lines,'offset':pos,'bytes':list(encoded),'characters':chars})
  pos+=len(encoded)
 rom[pos:0x17ff0]=bytes(0x17ff0-pos)
 rom[0x2bfc0:0x2bfc0+26]=bytes(LETTERS)
 # VBlank renderer: translate one local character and upload its 8 scanlines.
 a=Asm(0x63)
 a.emit('e5 d5 c5 3e 0a ea ff 3f') # preserve registers; bank 10
 a.emit('78 3d 5f 16 00 21 c0 7f 19 7e') # local character -> tile
 a.emit('cb 37 5f e6 0f f6 80 57 7b e6 f0 5f') # DE = $8000 + tile*16
 a.emit('78 3d 87 87 87 6f fa 71 c0 c6 40 67') # HL = per-page glyph
 a.emit('f0 47 e6 02 d6 01 9f 4f 06 08') # palette selects low-only / both planes
 a.label('row');a.emit('f0 41 e6 02');a.jr('20','row')
 a.emit('2a 12 13 a1 12 13 05');a.jr('20','row')
 a.emit('c1 78 3d 5f 16 00 21 c0 7f 19 46')
 a.emit('3e 05 ea ff 3f d1 e1 3e 10 c3 55 0c')
 hook=a.finish();assert original[0x63:0x63+len(hook)]==b'\xff'*len(hook)
 rom[0x63:0x63+len(hook)]=hook
 assert rom[0x178a3:0x178a8]==bytes.fromhex('3e 10 cd 55 0c')
 rom[0x178a3:0x178a8]=bytes.fromhex('cd 63 00 00 00')
 # UI-only font bank; keep dialogue letters and numerical/icon tiles intact.
 rom[0x30000:0x34000]=original[0x8000:0xc000]
 chars=list(dict.fromkeys(''.join(s for _,_,s in LABELS)+''.join(s for _,s in SPRITES)))
 chars=[c for c in chars if c not in ' ?!']
 pool=list(range(0xe5,0xff))+list(range(0xc7,0xe0))
 assert len(chars)<=len(pool)
 table=dict(zip(chars,pool));table.update({' ':0x8a,'?':0xc1,'!':0xc5})
 for c,t in zip(chars,pool):
  mask=glyph_tile(c,glyphs)[::2]
  rom[0x30000+t*16:0x30000+t*16+16]=bytes(b for v in mask for b in (v,0))
 assert rom[0x15b5]==2;rom[0x15b5]=12
 for offset,en,ko in LABELS:
  assert ''.join(TABLE.get(v,' ') for v in original[offset:offset+len(en)])==en,(offset,en)
  width=max(len(en),3 if en=='NO' else len(en))
  assert len(ko)<=width,('UI label too long',en,ko)
  blank=0x8a if offset<0x16664 else 0
  encoded=[blank]*width;start=(width-len(ko))//2
  encoded[start:start+len(ko)]=[table[c] if c!=' ' else blank for c in ko]
  rom[offset:offset+width]=bytes(encoded)
  manifest['labels'].append({'offset':offset,'english':en,'korean':ko})
 for offset,s in SPRITES:
  assert len(s)<=10,('Sprite text too long',s)
  tiles=[table[c] for c in s];tiles=[0x8a]*((10-len(tiles))//2)+tiles
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
 ending_start=0x63+len(hook)
 b=bytes.fromhex('3e 0b ea ff 3f 21 00 7d 11 50 8e 01 30 00 c3 0d 18')
 assert ending_start+len(b)<=0x100
 rom[ending_start:ending_start+len(b)]=b
 rom[0xce7:0xcec]=bytes([0xcd,ending_start&255,ending_start>>8,0,0])
 for bank in range(8,16):rom[(bank+1)*0x4000-1]=bank
 check=0
 for v in rom[0x134:0x14d]:check=(check-v-1)&255
 rom[0x14d]=check;rom[0x14e:0x150]=b'\0\0';rom[0x14e:0x150]=(sum(rom)&65535).to_bytes(2,'big')
 OUTPUT.write_bytes(rom);(HERE/'Kid_Icarus_Korean_Full.ips').write_bytes(make_ips(original,rom))
 manifest.update({'source_sha256':EXPECTED_SHA256,'output_sha256':hashlib.sha256(rom).hexdigest(),'dialogue_bytes':pos-0x17966,'dialogue_hook_bytes':len(hook),'ending_hook':ending_start,'ui_characters':table,'output':str(OUTPUT)})
 (HERE/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
 print(json.dumps({k:v for k,v in manifest.items() if k not in ('dialogues','labels','ui_characters')},ensure_ascii=False,indent=2))
if __name__=='__main__':main()
