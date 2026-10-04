"""Static verification of the built ROM. No emulator, no input automation.

Screen checks are done by a person in a real emulator; this script checks that
the ROM bytes match what the build intends and that original graphics survive.
"""
import hashlib,json
from PIL import Image,ImageDraw
from paths import WORK, KO
from apply_patch import apply_ips
from build_demo import load_glyphs,glyph_tile
from hangul_stack import split,final_rows
from build_full import (OUTPUT,SOURCE,EXPECTED_SHA256,LETTERS,KATAKANA,STATUS_SLOTS,CREDIT_POOL,
                        STATUS_MAP,CREDIT_MAP,STAGE_FONT_BANK,CREDIT_FONT_BANK,DIALOGUE_BANK,
                        PAGE_TABLE,DIALOGUE_CODE,LAST_PAGE,dialogue_routine,ui_tile)
HERE=WORK/'full'

def check(condition,message):
 if not condition:raise AssertionError(message)

def call_target(rom,at):
 check(rom[at]==0xcd,f'{at:05X}: expected CALL');return int.from_bytes(rom[at+1:at+3],'little')

def main():
 original=SOURCE.read_bytes();rom=OUTPUT.read_bytes()
 report={'output_sha256':hashlib.sha256(rom).hexdigest(),'method':'static ROM data checks; screens checked by hand in mGBA'}
 # 1. Source, header, checksums, IPS, bank markers.
 check(hashlib.sha256(original).hexdigest()==EXPECTED_SHA256,'Unexpected source ROM')
 check(len(rom)==0x40000 and rom[0x147:0x149]==bytes([6,3]),'ROM size/type')
 c=0
 for v in rom[0x134:0x14d]:c=(c-v-1)&255
 check(c==rom[0x14d],'Header checksum')
 check((sum(rom)-rom[0x14e]-rom[0x14f])&65535==int.from_bytes(rom[0x14e:0x150],'big'),'Global checksum')
 check(apply_ips(original,(HERE/'Kid_Icarus_Korean_Full.ips').read_bytes())==rom,'IPS does not reproduce ROM')
 check(all(rom[(b+1)*0x4000-1]==b for b in range(8,16)),'Bank number at 7FFF')
 report['header_checksums_ips_banks']='pass'
 # 2. Original banks 0-7 change only at known patch sites.
 allowed=[(0x63,0x100),(0x147,0x150),(0xce7,0xcec),(0xf30,0xf31),(0x15b5,0x15b6),(0x15cb,0x15ce),(0x1db0,0x1db1),
          (0x1dc1,0x1dc8),(0x1e93,0x1e94),(0x388b,0x388e),(0x7042,0x7092),(0x71a1,0x71f1),
          (0x17610,0x17616),(0x1788c,0x1788d),(0x178a3,0x178a8),(0x178d3,0x178d4),(0x17918,0x17ff0)]
 for r in KO['labels']:
  o=int(r['offset'],16);allowed.append((o,o+max(len(r['source_label']),3)))
 stray=[i for i in range(0x20000) if rom[i]!=original[i] and not any(s<=i<e for s,e in allowed)]
 check(not stray,('Unexpected changes in original banks',[hex(i) for i in stray[:16]]))
 report['original_banks_only_patch_sites']='pass'
 # 3. Code patches and the bank 10 dialogue routine.
 dialogue=call_target(rom,0x178a3);status=call_target(rom,0x17610)
 credit=call_target(rom,0x388b);ending=call_target(rom,0xce7)
 check(rom[0x15cb]==0xc3,'Stage font reload hook');reload=int.from_bytes(rom[0x15cc:0x15ce],'little')
 check(0x63<=reload<0x100 and rom[reload:reload+3]==bytes.fromhex('cd b6 03') and rom[reload+3:reload+5]==bytes([0xf0,LAST_PAGE]) and rom[reload+8:reload+10]==bytes([0x3e,DIALOGUE_BANK]),'Reload stub')
 check(all(0x63<=t<0x100 for t in (dialogue,status,credit,ending)),'Stub outside 0063-00FF')
 check(rom[dialogue:dialogue+4]==bytes([0xe5,0xd5,0x3e,DIALOGUE_BANK]),'Dialogue stub bank')
 check(rom[status+2:status+4]==bytes([0x3e,STAGE_FONT_BANK]),'Status stub bank')
 check(rom[credit:credit+2]==bytes([0x3e,CREDIT_FONT_BANK]),'Credit stub bank')
 check(rom[0x15b5]==STAGE_FONT_BANK and rom[0x1788c]==0x40 and rom[0xf30]==0x27 and rom[0x178d3]==6,'Layout patches')
 bank=DIALOGUE_BANK*0x4000
 routine=dialogue_routine()
 check(rom[bank+DIALOGUE_CODE-0x4000:bank+DIALOGUE_CODE-0x4000+len(routine)]==routine,'Dialogue routine')
 check(rom[bank+0x3fc0:bank+0x3fc0+26]==bytes(LETTERS),'Letter tile table')
 report['code_patches']='pass'
 # 4. Rebuild every dialogue page from ROM data and compare with the translation.
 glyphs=load_glyphs();pages=[]
 for i,lines in enumerate(KO['dialogues']):
  ptr=int.from_bytes(rom[0x17918+i*2:0x1791a+i*2],'little');p=0x10000+ptr
  table=rom[bank+PAGE_TABLE-0x4000+i*64:bank+PAGE_TABLE-0x4000+i*64+64]
  glyph=lambda slot:rom[bank+i*256+slot*8:bank+i*256+slot*8+8]
  row=col=0;text=['']
  cells={}
  while rom[p] not in (0xfd,0xff):
   b=rom[p];p+=1
   if b==0xfe:row+=2;col=0;text.append('');continue
   if b==0:text[-1]+=' ';col+=1;continue
   check(b<32,('Code out of range',i,b))
   top,fin=table[b],table[32+b]
   check(top<26 and fin<=26,('Slot out of range',i,b))
   cells[(row,col)]=glyph(top)
   if fin:cells[(row+1,col)]=glyph(fin-1)
   text[-1]+=chr(b);col+=1
   check(col<=18,('Line too long',i))
  check(row+1<6,('Dialogue taller than the six cleared rows',i))
  # Map codes back to the intended syllables and compare glyph bitmaps.
  check(len(text)==len(lines),('Line count',i))
  for line,(encoded) in zip(lines,text):
   pad=(18-len(line))//2
   check(encoded[:pad]==' '*pad and len(encoded)==pad+len(line),('Centering',i,line))
   for ch,code in zip(line,encoded[pad:]):
    if ch==' ':check(code==' ',('Space',i));continue
    top,f=split(ch)
    check(glyph(table[ord(code)])==glyph_tile(top,glyphs)[::2],('Top glyph',i,ch))
    fin=table[32+ord(code)]
    check((fin==0)==(f==0),('Final presence',i,ch))
    if f:check(glyph(fin-1)==final_rows(f),('Final glyph',i,ch))
  pages.append(cells)
 report['dialogue_pages']=f'{len(pages)} pages: text, glyphs, finals and box height pass'
 Z=2;sheet=Image.new('L',(2*(18*8+8)*Z,20*(6*8+10)*Z),40);dr=ImageDraw.Draw(sheet)
 for i,cells in enumerate(pages):
  ox=(i%2)*(18*8+8)*Z;oy=(i//2)*(6*8+10)*Z
  dr.rectangle([ox,oy,ox+18*8*Z,oy+6*8*Z],fill=0)
  for (r,cl),g in cells.items():
   for y in range(8):
    for x in range(8):
     if g[y]>>(7-x)&1:dr.rectangle([ox+(cl*8+x)*Z,oy+(r*8+y)*Z,ox+(cl*8+x)*Z+Z-1,oy+(r*8+y)*Z+Z-1],fill=255)
  dr.text((ox+2,oy+6*8*Z+2),str(i),fill=200)
 sheet.save(HERE/'dialogue_pages.png')
 # 5. UI fonts: stage font keeps every original tile except the katakana.
 font=lambda b,t:rom[b*0x4000+0x800+(t-0x80)*16:b*0x4000+0x800+(t-0x80)*16+16]
 orig=lambda t:original[0x8800+(t-0x80)*16:0x8800+(t-0x80)*16+16]
 stage=STAGE_FONT_BANK*0x4000;cred=CREDIT_FONT_BANK*0x4000
 check(rom[stage:stage+0x800]==original[0x8000:0x8800] and rom[stage+0x1000:stage+0x2000]==original[0x9000:0xa000],'Stage font outside 8800 block')
 changed=[t for t in range(0x80,0x100) if font(STAGE_FONT_BANK,t)!=orig(t)]
 check(set(changed)<=set(KATAKANA),('Stage font changed original graphics',[hex(t) for t in changed]))
 changed=[t for t in range(0x80,0x100) if font(CREDIT_FONT_BANK,t)!=orig(t)]
 check(set(changed)<=set(KATAKANA)|set(CREDIT_POOL),('Credit font changed unexpected tiles',[hex(t) for t in changed]))
 def ui_glyph(context,t):
  if context=='status' and t in STATUS_SLOTS:
   return rom[stage+0x3e00+(t-0x94)*16:stage+0x3e00+(t-0x94)*16+16]
  return font(CREDIT_FONT_BANK if context=='credit' else STAGE_FONT_BANK,t)
 blank={0x8a,0}
 for r in KO['labels']:
  o=int(r['offset'],16);ko=r['korean'];width=max(len(r['source_label']),3 if r['source_label']=='NO' else 0)
  context='status' if STATUS_MAP[0]<=o<STATUS_MAP[1] else 'credit' if CREDIT_MAP[0]<=o<CREDIT_MAP[1] else 'kata'
  tiles=[t for t in rom[o:o+width] if t not in blank]
  chars=[c for c in ko if c!=' ']
  check(len(tiles)==len(chars),('Label tile count',r['source_label']))
  for c,t in zip(chars,tiles):
   if c=='?':check(t==0xc1,'?');continue
   check(ui_glyph(context,t)==ui_tile(c,glyphs),('Label glyph',r['source_label'],c,hex(t)))
   if context=='kata':check(font(CREDIT_FONT_BANK,t)==font(STAGE_FONT_BANK,t),('Shared label differs between fonts',c))
 for r in KO['sprites']:
  o=int(r['offset'],16);tiles=[rom[o+n*4+2] for n in range(10)]
  tiles=[t for t in tiles if t!=0x8a];chars=[c for c in r['korean'] if c!=' ']
  check(len(tiles)==len(chars),('Sprite tile count',r['source_label']))
  for c,t in zip(chars,tiles):
   if c=='!':check(t==0xc5,'!');continue
   check(font(CREDIT_FONT_BANK,t)==ui_tile(c,glyphs),('Sprite glyph',r['source_label'],c))
 report['ui_fonts']='pass: stage font keeps original graphics; labels and sprites point at matching glyphs'
 # 6. Title trademark, pause and ending glyphs.
 tm=rom[0x23402+3*20+19]
 check(tm<0x80 and rom[0x24000+tm*16:0x24010+tm*16]==original[0x1c000+0x47*16:0x1c010+0x47*16],'Title trademark tile')
 for n,c in enumerate(KO['pause']):
  check(rom[0x71a1+n*16:0x71b1+n*16]==(bytes(16) if c==' ' else glyph_tile(c,glyphs)),('Pause glyph',c))
 chars=list(dict.fromkeys(''.join(r['korean'] for r in KO['ending'])))
 for n,c in enumerate(chars):check(rom[0x2fd00+n*16:0x2fd10+n*16]==glyph_tile(c,glyphs),('Ending glyph',c))
 report['title_pause_ending']='pass'
 (HERE/'verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
 print(json.dumps(report,ensure_ascii=False,indent=2))

if __name__=='__main__':main()
