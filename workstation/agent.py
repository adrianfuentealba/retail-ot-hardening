import os,time,json,subprocess,hashlib,asyncio
from pathlib import Path
import httpx,uvicorn
from fastapi import FastAPI,HTTPException
from pydantic import BaseModel
HOST=os.getenv('HOSTNAME','workstation');ROLE=os.getenv('ROLE','hmi');ROOT=Path('/home/student/lab');LOG=Path('/evidence/endpoint.jsonl')
ROOT.mkdir(parents=True,exist_ok=True);LOG.parent.mkdir(parents=True,exist_ok=True)
STATE={'os':False,'application':False,'network':False,'access':False,'supply-chain':False}
CONFIG=ROOT/'controller.conf';FIRMWARE=ROOT/'firmware.bin'
if not CONFIG.exists():CONFIG.write_text('setpoint=2\nmaintenance=true\n');CONFIG.chmod(0o666);os.chown(CONFIG,1000,1000)
if not FIRMWARE.exists():FIRMWARE.write_bytes(b'RETAIL-EDUCATIONAL-FIRMWARE-v1\n')
GOLDEN=hashlib.sha256(b'RETAIL-EDUCATIONAL-FIRMWARE-v1\n').hexdigest()
PROCS=[];app=FastAPI()
class Request(BaseModel):command:str
class Lateral(BaseModel):source:str='ws-vendor'
def event(action,outcome,message):
 row={'@timestamp':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),'host':{'name':HOST},'event':{'dataset':'lab.endpoint','action':action,'outcome':outcome},'message':message,'role':ROLE}
 with LOG.open('a') as f:f.write(json.dumps(row)+'\n')
 return row
@app.get('/health')
def health():return {'host':HOST,'role':ROLE,'policies':STATE,'mode':oct(CONFIG.stat().st_mode & 0o777),'osquery':subprocess.run(['osqueryi','--version'],capture_output=True,text=True).stdout.strip()}
@app.post('/lateral')
def lateral(r:Lateral):
 if STATE['network'] or STATE['access']:return event('lateral','blocked','Agent allowlist prevented internal training marker')
 (ROOT/'downloads'/'lateral-marker.txt').write_text('Benign training marker from '+r.source);return event('lateral','success','Marker only; no exploit or credential theft')
@app.post('/policy/{name}')
def endpoint_policy(name:str):
 if name not in ['network','access']:raise HTTPException(400)
 STATE[name]=True
 return event('harden-'+name,'success','Internal endpoint guard activated')
@app.post('/contain')
def contain():
 for p in PROCS:
  if p.poll() is None:p.terminate()
 return event('contain','success','Benign process stopped; evidence retained')
@app.post('/command')
async def command(r:Request):
 c=r.command
 if c=='status':return health()
 if c=='inventory':
  out=subprocess.run(['osqueryi','--json','SELECT hostname,cpu_type,physical_memory FROM system_info;'],capture_output=True,text=True);return {'source':'osqueryi','rows':json.loads(out.stdout or '[]')}
 if c in ['baseline','detect']:
  out=subprocess.run(['osqueryi','--json',"SELECT path,mode,uid FROM file WHERE path='/home/student/lab/controller.conf';"],capture_output=True,text=True)
  return {'event':event(c,'success','Manual osquery evidence query'),'rows':json.loads(out.stdout or '[]'),'policies':STATE}
 if c=='evidence':return {'host':HOST,'events':[json.loads(x) for x in LOG.read_text().splitlines()[-30:]],'osquery_logs':'/evidence/osquery/osqueryd.results.log'}
 if c=='simulate malware':
  async with httpx.AsyncClient() as client:
   resp=await client.get('http://panel:8000/api/training-artifact');resp.raise_for_status();p=ROOT/'downloads'/'retail-marker.txt';p.write_bytes(resp.content)
  if STATE['application'] or STATE['os']:return event('malware-emulation','blocked','Local artifact downloaded; training execution guard blocked benign process')
  PROCS.append(subprocess.Popen(['bash','-c','exec -a retail-benign-malware sleep 45'],user=1000,group=1000));return event('malware-emulation','success','BENIGN: marker download + 45 second sleep; nothing encrypted')
 if c=='simulate firmware':
  candidate=b'RETAIL-EDUCATIONAL-FIRMWARE-v1-ALTERED\n'
  if STATE['supply-chain'] and hashlib.sha256(candidate).hexdigest()!=GOLDEN:return event('firmware','blocked','SHA256 manifest mismatch; fictitious update rejected')
  FIRMWARE.write_bytes(candidate);return event('firmware','success','Fictitious firmware file altered; no executable firmware')
 if c=='simulate lateral':
  targets=['ws-engineering','ws-hmi'];out=[]
  async with httpx.AsyncClient(timeout=4) as client:
   for host in targets:
    try:
     x=await client.post(f'http://{host}:8010/lateral',json={'source':HOST});out.append(x.json())
    except Exception as e:out.append({'host':host,'result':'unreachable','detail':type(e).__name__})
  event('lateral-attempt','success','Fixed targets via training network, not production path');return {'targets':out}
 if c.startswith('harden '):
  name=c.split()[1]
  if name in STATE:
   if name in ['network','access']:
    async with httpx.AsyncClient(timeout=10) as client:
     await client.post('http://panel:8000/api/action',json={'command':c,'host':HOST,'role':ROLE})
   STATE[name]=True
   if name=='os':CONFIG.chmod(0o640);os.chown(CONFIG,0,1000)
   if name=='application':
    for p in PROCS:
     if p.poll() is None:p.terminate()
   if name=='supply-chain':FIRMWARE.write_bytes(b'RETAIL-EDUCATIONAL-FIRMWARE-v1\n')
   return event('harden-'+name,'success','Endpoint policy applied; '+('mode=0640 owner=root' if name=='os' else 'educational application policy'))
 if c=='reset':
  STATE.update({k:False for k in STATE});CONFIG.chmod(0o666);os.chown(CONFIG,1000,1000)
  for p in PROCS:
   if p.poll() is None:p.terminate()
  return event('reset','success','Endpoint policies reset; evidence retained')
 # Process controls use fixed, out-of-band training API.
 if c in ['simulate defrost','simulate opcua','harden plc','harden opcua','harden network','harden access','recover']:
  async with httpx.AsyncClient(timeout=15) as client:
   x=await client.post('http://panel:8000/api/action',json={'command':c,'host':HOST,'role':ROLE});x.raise_for_status();return x.json()
 raise HTTPException(400,'Command not allowed')
if __name__=='__main__':uvicorn.run(app,host='0.0.0.0',port=8010,log_level='warning')
