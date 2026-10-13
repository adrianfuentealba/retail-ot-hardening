import asyncio,time,json,socket,struct,hashlib,os
from pathlib import Path
import httpx,uvicorn
from fastapi import FastAPI,HTTPException
from fastapi.responses import FileResponse,Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from app.redteam import COMMANDS as REDTEAM_COMMANDS,run as run_redteam
from asyncua import Client,ua
from asyncua.crypto.security_policies import SecurityPolicyBasic256Sha256
HOSTS=['ws-corporate','ws-vendor','ws-engineering','ws-hmi','ws-soc']
app=FastAPI();LOG=Path('/evidence/panel.jsonl');LOG.parent.mkdir(parents=True,exist_ok=True)
STATE={'network':False,'access':False};CACHE={};EVENTS=[];HISTORY=[];LAST={}
class Action(BaseModel):command:str;host:str='ws-engineering';role:str='engineering'
class Command(BaseModel):command:str;host:str='ws-hmi'
def event(action,outcome,message,host='panel'):
 row={'@timestamp':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),'host':{'name':host},'event':{'dataset':'lab.control','action':action,'outcome':outcome},'message':message}
 EVENTS.append(row);EVENTS[:]=EVENTS[-300:]
 with LOG.open('a') as f:f.write(json.dumps(row)+'\n')
 return row
def modbus(fc=3,value=2):
 tid=int(time.time()*100)%65536;p=struct.pack('>BHH',fc,0,4 if fc==3 else value)
 with socket.create_connection(('gateway',502),timeout=4) as s:
  s.sendall(struct.pack('>HHHB',tid,0,len(p)+1,1)+p);b=s.recv(260)
  if len(b)<9:raise ValueError('incomplete Modbus response')
  return {'protocol':'Modbus TCP','function':fc,'hex':b.hex(' '),'exception':b[7]&128!=0,'source':'actual TCP response'}
@app.get('/api/health')
def health():return {'status':'ok'}
@app.get('/api/state')
def state():return {'process':CACHE.get('process'),'gateway':CACHE.get('gateway'),'endpoints':CACHE.get('endpoints',{}),'policies':STATE,'events':EVENTS[-30:],'history':HISTORY[-90:],'last_update':CACHE.get('last_update'),'errors':CACHE.get('errors',[])}
@app.get('/api/redteam/catalog')
def redteam_catalog():return __import__('json').loads(Path('/lab/app/redteam-catalog.json').read_text())
@app.get('/api/anatomy')
def anatomy():
 return {'source':Path('/lab/plc/control_logic.py').read_text(),'source_path':'plc/control_logic.py','process':CACHE.get('process'),'gateway':CACHE.get('gateway'),'notice':'Actual classroom Python source; not firmware or safety-certified PLC code'}
class WiringRequest(BaseModel):signal:str;connected:bool
@app.post('/api/anatomy/wiring')
async def anatomy_wiring(r:WiringRequest):
 if r.signal not in ['AI0','DI0']:raise HTTPException(400,'Fixed educational inputs only')
 async with httpx.AsyncClient(timeout=5) as c:
  x=await c.post('http://plc:8001/wiring',json=r.model_dump());x.raise_for_status();return x.json()
@app.get('/api/training-artifact')
def artifact():return Response('RETAIL OT TRAINING MARKER — BENIGN, NON EXECUTABLE\n',media_type='text/plain')
@app.post('/api/command')
async def cmd(r:Command):
 if r.host not in HOSTS:raise HTTPException(400,'Internal endpoints only')
 key=r.host
 if time.time()-LAST.get(key,0)<1:raise HTTPException(429,'Espere 1 segundo entre comandos')
 LAST[key]=time.time()
 async with httpx.AsyncClient(timeout=20) as client:
  try:
   x=await client.post(f'http://{r.host}:8010/command',json={'command':r.command})
  except httpx.RequestError:
   if r.command in ['simulate defrost','harden plc','simulate opcua','harden opcua','recover']:
    result=await action(Action(command=r.command,host=r.host))
    return {'mode':'DEMONSTRACION DEL NUCLEO — endpoint no disponible; no ejecutado en Linux/noVNC','result':result}
   raise HTTPException(503,'Endpoint Linux no disponible. El núcleo puede estar activo, pero noVNC/ELK requieren completar el build.')
  if x.status_code!=200:raise HTTPException(x.status_code,x.text)
  return x.json()
@app.post('/api/action')
async def action(r:Action):
 if r.host not in HOSTS:raise HTTPException(400,'Fixed hosts only')
 async with httpx.AsyncClient(timeout=10) as client:
  c=r.command
  if c in REDTEAM_COMMANDS:return await run_redteam(c,client,event,r.host)
  if c=='simulate defrost':
   if STATE['access'] and r.host!='ws-engineering':return event('defrost','blocked','Training role gate: engineering only',r.host)
   try:res=await asyncio.to_thread(modbus,6,50)
   except Exception as e:raise HTTPException(503,str(e))
   return {'event':event('defrost','blocked' if res['exception'] else 'success','FC06 setpoint=50 on fictitious refrigeration PLC',r.host),'packet':res}
  if c=='harden plc':await client.post('http://plc:8001/policy/plc');return event('harden-plc','success','PLC validates setpoint <=6; reset nominal value',r.host)
  if c=='harden network':
   STATE['network']=True;await client.post('http://gateway:8003/policy')
   for h in HOSTS:await client.post(f'http://{h}:8010/policy/network')
   return event('harden-network','success','Application gateway rejects FC06; endpoint lateral guard separate',r.host)
  if c=='harden access':
   STATE['access']=True
   for h in HOSTS:await client.post(f'http://{h}:8010/policy/access')
   return event('harden-access','success','Training role gate: engineering-only process write',r.host)
  if c=='harden opcua':await client.post('http://plc:8001/policy/opcua');return event('harden-opcua','success','OPC UA variable is read-only; secure Read uses pinned server certificate',r.host)
  if c=='simulate opcua':
   p=(await client.get('http://plc:8001/state')).json()
   u=Client('opc.tcp://gateway:4840/retail/',timeout=5);u.application_uri='urn:retail:plc'
   secure=p.get('opcua_secure',False)
   try:
    if secure:
     await u.set_security(SecurityPolicyBasic256Sha256,certificate='/certs/cert.der',private_key='/certs/key.pem',server_certificate='/certs/cert.der',mode=ua.MessageSecurityMode.SignAndEncrypt)
    async with u:
     node=u.get_node('ns=2;s=Setpoint');before=await node.read_value()
     try:await node.write_value(50.0);result='success'
     except ua.UaStatusCodeError:result='blocked'
     after=await node.read_value()
    return {'event':event('opcua-write',result,'Actual OPC UA Write; '+('SignAndEncrypt, read-only variable' if secure else 'None, writable variable'),r.host),'security':'SignAndEncrypt' if secure else 'None','before':before,'readback':after}
   except Exception as e:raise HTTPException(503,f'OPC UA error: {type(e).__name__}: {e}')
  if c=='recover':
   await client.post('http://plc:8001/recover')
   for h in HOSTS:
    try:await client.post(f'http://{h}:8010/contain')
    except httpx.RequestError:pass
   return event('recover','success','Cooling resumed and benign processes stopped. Spoiled stock remains quarantined.',r.host)
  if c=='reset':
   STATE.update(network=False,access=False);await client.post('http://plc:8001/reset');await client.post('http://gateway:8003/reset')
   for h in HOSTS:
    try:await client.post(f'http://{h}:8010/command',json={'command':'reset'})
    except httpx.RequestError:pass
   return event('reset','success','Process reset; available endpoints reset. Check endpoint availability; evidence retained')
 raise HTTPException(400,'Action not allowed')
@app.post('/api/reset')
async def reset():return await action(Action(command='reset'))
@app.get('/api/evidence')
async def evidence():return {'state':state(),'notice':'Application events are independent from osquery, Suricata and PCAP; reset does not delete evidence.'}
@app.get('/api/packets')
def packets():
 p=Path('/captures/packets.jsonl')
 if not p.exists():return []
 try:return [json.loads(x) for x in p.read_text().splitlines()[-60:]]
 except Exception:return []
@app.get('/api/capture')
def capture():
 files=list(Path('/captures').glob('live.pcap*'));p=max(files,key=lambda x:x.stat().st_mtime) if files else Path('/captures/live.pcap')
 if not p.exists():raise HTTPException(404,'Capture is not yet ready')
 return FileResponse(p,media_type='application/vnd.tcpdump.pcap',filename='retail-ot-live.pcap')
@app.get('/api/tutorial-observability')
def observability_tutorial():return Response(Path('/lab/docs/tutorial-observabilidad.md').read_text(),media_type='text/plain')
@app.get('/api/guides')
def guides():return [{'name':p.name,'title':p.read_text().splitlines()[0].lstrip('# ')} for p in sorted(Path('/lab/exercises').glob('*.md'))]
@app.get('/api/guides/{name}')
def guide(name:str):
 if '/' in name or not name.endswith('.md'):raise HTTPException(400)
 p=Path('/lab/exercises')/name
 if not p.exists():raise HTTPException(404)
 return Response(p.read_text(),media_type='text/plain')
async def poll():
 async with httpx.AsyncClient(timeout=2) as client:
  while True:
   errors=[]
   try:
    x=await client.get('http://plc:8001/state');x.raise_for_status();CACHE['process']=x.json();HISTORY.append({'t':time.time(),'temperature':x.json()['temperature']});HISTORY[:]=HISTORY[-240:];CACHE['last_update']=time.time()
   except Exception:errors.append('plc unavailable');CACHE['process']=None
   try:CACHE['gateway']=(await client.get('http://gateway:8003/health')).json()
   except Exception:errors.append('gateway unavailable')
   ep={}
   for h in HOSTS:
    try:ep[h]=(await client.get(f'http://{h}:8010/health')).json()
    except Exception:ep[h]={'error':'unavailable'}
   CACHE['endpoints']=ep;CACHE['errors']=errors
   try:await asyncio.to_thread(modbus)
   except Exception:pass
   await asyncio.sleep(2)
@app.on_event('startup')
async def startup():asyncio.create_task(poll())
app.mount('/static',StaticFiles(directory='/lab/app/static'),name='static')
@app.get('/')
@app.get('/labs/{number}')
def index(number:str='01'):return FileResponse('/lab/app/static/index.html')
if __name__=='__main__':uvicorn.run(app,host='0.0.0.0',port=8000,log_level='warning')
