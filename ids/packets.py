import sys,json,time
from pathlib import Path
p=Path('/captures/packets.jsonl')
for line in sys.stdin:
 a=line.rstrip().split('|')
 if len(a)<6 or not a[5]:continue
 try:
  raw=bytes.fromhex(a[5]);row={'time':float(a[0]),'src':a[1],'sport':a[2],'dst':a[3],'dport':a[4],'hex':raw[:160].hex(' '),'length':len(raw),'source':'tshark passive capture','protocol':'Modbus TCP' if '502' in [a[2],a[4]] else 'OPC UA','function':raw[7] if len(raw)>7 and '502' in [a[2],a[4]] else None}
  with p.open('a') as f:f.write(json.dumps(row)+'\n')
  if p.stat().st_size>2000000:
   lines=p.read_text().splitlines()[-2000:];p.write_text('\n'.join(lines)+'\n')
 except (ValueError,OSError):pass
