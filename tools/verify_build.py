"""Emulator regression and native-renderer tests; RAM-directed scenes are identified."""
import sys,json,hashlib
from pathlib import Path
from PIL import Image,ImageChops,ImageDraw
from paths import ROOT, WORK
HERE=WORK/'full'
from emulator_utils import boot,tap,apply_ips,equal_screens
import tempfile,build_title
from build_full import OUTPUT,SOURCE,EXPECTED_SHA256,LETTERS
ROM=OUTPUT.read_bytes();MAN=json.loads((HERE/'manifest.json').read_text(encoding='utf-8'))
SCREENS=HERE/'screens';SCREENS.mkdir(exist_ok=True)
def capture(p,name):p.screen.image.resize((480,432),Image.Resampling.NEAREST).save(SCREENS/(name+'.png'))
def save(p,name):
 with (HERE/(name+'.state')).open('wb') as f:p.save_state(f)
def load(name):
 p=boot(OUTPUT)
 with (HERE/(name+'.state')).open('rb') as f:p.load_state(f)
 return p
def redirect(p,addr):
 p.memory[0xc026:0xc028]=[addr&255,addr>>8];p.memory[0xc02d]=1
def main():
 original=SOURCE.read_bytes()
 assert hashlib.sha256(original).hexdigest()==EXPECTED_SHA256
 assert len(ROM)==0x40000 and ROM[0x147:0x149]==bytes([6,3])
 c=0
 for v in ROM[0x134:0x14d]:c=(c-v-1)&255
 assert c==ROM[0x14d]
 assert (sum(ROM)-ROM[0x14e]-ROM[0x14f])&65535==int.from_bytes(ROM[0x14e:0x150],'big')
 assert apply_ips(original,(HERE/'Kid_Icarus_Korean_Full.ips').read_bytes())==ROM
 report={'output_sha256':hashlib.sha256(ROM).hexdigest(),'source_preserved':True,'checksums':'pass','ips_roundtrip':'pass','native_dialogue_pages':[],'ram_directed_scenes':True,'full_playthrough':False}
 # Baseline: the title stage without the full text patch, kept only for this run.
 title_rom=Path(tempfile.gettempdir())/'kid_icarus_title_stage.gb';title_rom.write_bytes(build_title.main())
 base=boot(title_rom);p=boot(OUTPUT)
 try:
  for frames in [760,1040]:
   for em in [base,p]:em.tick(frames,True)
   assert equal_screens(base,p),'Opening/title differs from previous Korean build'
  capture(p,'full_title')
  for em in [base,p]:tap(em,'start');em.tick(180,True)
  assert equal_screens(base,p),'Initial gameplay changed'
  save(p,'full_game_start');capture(p,'full_game')
  for em in [base,p]:
   em.button_press('right');em.button_press('a');em.tick(45,True);em.button_release('right');em.button_release('a');em.button_press('b');em.tick(30,True);em.button_release('b');em.tick(45,True)
  assert equal_screens(base,p),'Movement/attack changed'
  report['initial_gameplay_movement_attack']='pixel-identical to previous build'
 finally:base.stop(save=False);p.stop(save=False)
 p=load('full_game_start')
 try:
  tap(p,'start');p.tick(24,True);capture(p,'full_pause')
  assert bytes(p.memory[0x8800:0x8850])==ROM[0x71a1:0x71f1]
  tap(p,'start');p.tick(30,True);capture(p,'full_status')
  assert bytes(p.memory[0x8800:0x9000])==ROM[0x30800:0x31000]
  report['pause_status_fonts']='pass'
 finally:p.stop(save=False)
 # Enter an authentic first-stage shop via its unmodified room initializer.
 p=load('full_game_start')
 try:
  p.memory[0xffb3]=1;p.memory[0xffb4]=0x20;redirect(p,0x36b1);p.tick(240,True)
  p.button_press('right');p.tick(100,True);p.button_release('right');p.tick(200,True)
  capture(p,'shop');save(p,'npc')
 finally:p.stop(save=False)
 # Invoke all records through the original VBlank dialogue state machine.
 # Only scene/state RAM is directed; release ROM code and pointers are exercised.
 for palette in [0x93,0xe1]:
  p=load('npc')
  try:
   p.memory[0xc02a:0xc02c]=[0x86,2];p.memory[0xc02d]=3
   p.memory[0xff47]=palette
   for rec in MAN['dialogues']:
    i=rec['id']
    for addr,value in {0xc070:0,0xc071:i,0xc072:1,0xc073:0,0xc06e:0x47,0xc06f:0x99,0xc022:0x47,0xc023:0x0f,0xc02c:3}.items():p.memory[addr]=value
    for frames in range(300):
     p.tick(1,True)
     if p.memory[0xc073]:break
    else:raise AssertionError(('Dialogue did not finish',palette,i))
    assert p.memory[0xc071]==i,(i,p.memory[0xc071])
    row=0;col=0
    for value in rec['bytes'][:-1]:
     if value==0xfe:row+=1;col=0;continue
     expected=LETTERS[value-1] if value else 0
     assert p.memory[0x9947+row*32+col]==expected,('tilemap',i,row,col,value)
     col+=1
    for n,ch in enumerate(rec['characters']):
     mask=ROM[0x28000+i*256+n*8:0x28008+i*256+n*8]
     expected=bytes(b for v in mask for b in (v,v if palette==0xe1 else 0))
     actual=bytes(p.memory[0x8000+LETTERS[n]*16:0x8010+LETTERS[n]*16])
     assert expected==actual,('glyph',palette,i,ch,expected.hex(),actual.hex())
    if palette==0x93:
     capture(p,f'dialogue_{i:02}')
     report['native_dialogue_pages'].append({'id':i,'frames':frames+1,'tilemap_and_glyphs':'pass'})
   report[f'palette_{palette:02x}_all_39']='pass'
  finally:p.stop(save=False)
 for credits,name in [(2,'continue'),(0,'game_over')]:
  p=load('full_game_start')
  try:
   p.memory[0xc096]=credits;redirect(p,0x3857);p.tick(90,True);capture(p,name)
   p.tick(30,True);capture(p,name+'_alternate')
   report[name]='native scene initialized and rendered'
  finally:p.stop(save=False)
 p=load('full_game_start')
 try:
  redirect(p,0x3ce2);p.tick(900,True);capture(p,'stage_result');save(p,'stage_result')
  report['stage_result']='native scene initialized and rendered'
 finally:p.stop(save=False)
 p=load('stage_result')
 try:
  p.button_press('left');p.tick(70,True);p.button_release('left');p.tick(60,True)
  capture(p,'save_prompt');save(p,'save_prompt')
  tap(p,'down');capture(p,'save_no_selected')
  report['save_prompt']='native prompt; both Korean options rendered'
  tap(p,'up');tap(p,'a');p.tick(120,True)
  assert bytes(p.memory[0xdb24:0xdb28])==b'KUMI'
  assert p.memory[0xc065]==0x12
  report['save_yes']='save signature in emulator RAM and transition to stage 1-2 verified; no user save file written'
 finally:p.stop(save=False)
 p=load('full_game_start')
 try:
  redirect(p,0x2c1d)
  for n in range(7000):
   p.tick(1,True)
   if p.memory[0xc065]==0x51 and p.memory[0xc071]==25 and p.memory[0xc073]==0x7f:
    capture(p,'ending_dialogue')
   if p.memory[0xc065]==0x52 and p.memory[0xc08e]==13:break
  else:raise AssertionError('Ending did not complete')
  p.tick(4,True);capture(p,'ending_final')
  assert bytes(p.memory[0x8e50:0x8e80])==ROM[0x2fd00:0x2fd30]
  for row in range(5):
   assert bytes(p.memory[0x98c0+32*row:0x98cc+32*row])==ROM[0x2f0b8+12*row:0x2f0c4+12*row]
  report['ending']='native ending sequence completed, final Korean glyphs and tilemap verified'
  report['ending_frames']=n+1
 finally:p.stop(save=False)
 (HERE/'verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
 print(json.dumps(report,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
