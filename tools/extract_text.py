"""Extract source dialogues locally from the user-supplied ROM."""
import json
from paths import SOURCE, WORK
OUT=WORK/'full'
OUT.mkdir(parents=True,exist_ok=True)
D=SOURCE.read_bytes()
TABLE={0x94+i+(4 if i>=12 else 0):chr(65+i) for i in range(26)}
TABLE.update({0:' ',0xb2:"'",0xb3:'"',0xc1:'?',0xc2:',',0xc3:'.',0xc5:'!',0xfe:'\n',0xfd:'<NEXT>',0xff:'<END>'})
def dialogues():
 records=[]
 for index in range(39):
  ptr=int.from_bytes(D[0x17918+index*2:0x1791a+index*2],'little');start=0x14000+ptr-0x4000
  end=start
  while D[end] not in [0xfd,0xff]:end+=1
  raw=D[start:end+1]
  records.append({'index':index,'offset':f'{start:05X}','length':len(raw),'terminal':f'{raw[-1]:02X}',
                  'english':''.join(TABLE.get(b,f'<{b:02X}>') for b in raw)})
 (OUT/'dialogues_en.json').write_text(json.dumps(records,indent=2,ensure_ascii=False),encoding='utf-8')
 return records

if __name__=='__main__':
 print(json.dumps(dialogues(),ensure_ascii=False,indent=2))
