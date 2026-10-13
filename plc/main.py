import asyncio,json,time,threading,socketserver,struct,os
from pathlib import Path
from fastapi import FastAPI
import uvicorn
from asyncua import Server,ua
from asyncua.crypto.cert_gen import setup_self_signed_certificate
from cryptography.x509.oid import ExtendedKeyUsageOID
LOCK=threading.RLock()
STATE={'temperature':2.0,'setpoint':2,'heater':False,'exposure':0.0,'spoiled':False,'thermal_risk':False,'plc_guard':False,'opcua_secure':False,'modbus_reads':0,'modbus_writes':0}
EVENTS=Path('/evidence/control.jsonl'); EVENTS.parent.mkdir(parents=True,exist_ok=True)
def log(action,outcome,detail):
 with EVENTS.open('a') as f:f.write(json.dumps({'@timestamp':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),'event':{'dataset':'lab.control','action':action,'outcome':outcome},'host':{'name':'plc'},'message':detail})+'\n')
def write(v,protocol):
 with LOCK:
  if v>50 or (STATE['plc_guard'] and v>6):
   log('setpoint','blocked',f'{protocol}: setpoint {v} rejected');return False
  STATE['setpoint']=v;STATE['heater']=v>6
  log('setpoint','success',f'{protocol}: setpoint {v} accepted');return True
class Modbus(socketserver.BaseRequestHandler):
 def handle(self):
  self.request.settimeout(15)
  def recv(n):
   b=b''
   while len(b)<n:
    x=self.request.recv(n-len(b))
    if not x:raise EOFError
    b+=x
   return b
  try:
   while True:
    h=recv(7);tid,pid,length,unit=struct.unpack('>HHHB',h)
    if pid!=0 or length<2 or length>254:return
    p=recv(length-1);fc=p[0]
    with LOCK:
     regs=[STATE['setpoint'],int(STATE['temperature']*10)+1000,int(STATE['heater']),int(STATE['spoiled'])]
     if fc==3 and len(p)==5:
      addr,count=struct.unpack('>HH',p[1:]);STATE['modbus_reads']+=1
      if count<1 or count>4 or addr+count>4:resp=bytes([131,2])
      else:resp=bytes([3,count*2])+struct.pack('>'+'H'*count,*regs[addr:addr+count])
     elif fc==6 and len(p)==5:
      addr,v=struct.unpack('>HH',p[1:]);STATE['modbus_writes']+=1
      resp=p if addr==0 and write(v,'Modbus FC06') else bytes([134,3])
     else:resp=bytes([fc|128,1])
    self.request.sendall(struct.pack('>HHHB',tid,0,len(resp)+1,unit)+resp)
  except (EOFError,OSError):pass
class TCP(socketserver.ThreadingTCPServer):allow_reuse_address=True;daemon_threads=True
api=FastAPI()
@api.get('/state')
def state():
 with LOCK:return dict(STATE)
@api.post('/policy/{name}')
def policy(name:str):
 if name=='plc':STATE['plc_guard']=True;write(2,'local interlock')
 elif name=='opcua':STATE['opcua_secure']=True
 else:return {'error':'unknown'}
 log('policy','success',name);return state()
@api.post('/reset')
def reset():
 with LOCK:
  STATE.update(temperature=2.0,setpoint=2,heater=False,exposure=0.0,spoiled=False,thermal_risk=False,plc_guard=False,opcua_secure=False)
 log('reset','success','Process and policy reset; evidence preserved');return state()
@api.post('/recover')
def recover():
 with LOCK:STATE.update(setpoint=2,heater=False)
 log('recover','success','Cooling resumed; spoiled stock remains quarantined');return state()
async def ua_server():
 p=Path('/certs');p.mkdir(exist_ok=True); uri='urn:retail:plc'
 await setup_self_signed_certificate(p/'key.pem',p/'cert.der',uri,'plc',[ExtendedKeyUsageOID.SERVER_AUTH,ExtendedKeyUsageOID.CLIENT_AUTH],{'organizationName':'Retail education'})
 srv=Server();await srv.init();srv.set_endpoint('opc.tcp://0.0.0.0:4840/retail/');await srv.set_application_uri(uri)
 await srv.load_certificate(str(p/'cert.der'));await srv.load_private_key(str(p/'key.pem'))
 srv.set_security_policy([ua.SecurityPolicyType.NoSecurity,ua.SecurityPolicyType.Basic256Sha256_SignAndEncrypt])
 idx=await srv.register_namespace('urn:retail:model');obj=await srv.nodes.objects.add_object(idx,'Refrigeration')
 node=await obj.add_variable(ua.NodeId('Setpoint',idx),'Setpoint',2.0);await node.set_writable()
 temp=await obj.add_variable(ua.NodeId('Temperature',idx),'Temperature',2.0)
 previous=2.0
 async with srv:
  log('opcua-start','success','OPC UA 4840 with None and SignAndEncrypt endpoints; secure mode rejects unencrypted Write at application layer')
  while True:
   v=await node.read_value()
   if v!=previous:
    if STATE['opcua_secure']:
     # Training Write guard is enforced by the exercise client; after activation make node read-only for all writes.
     await node.set_writable(False)
    if not write(int(v),'OPC UA Write'):v=float(STATE['setpoint']);await node.write_value(v)
   if STATE['opcua_secure']:await node.set_writable(False)
   else:await node.set_writable(True)
   if float(STATE['setpoint'])!=v:v=float(STATE['setpoint']);await node.write_value(v)
   previous=v;await temp.write_value(STATE['temperature']);await asyncio.sleep(.3)
async def physics():
 while True:
  with LOCK:
   target=float(STATE['setpoint']);STATE['temperature']+=(target-STATE['temperature'])*.08
   if STATE['temperature']>8:STATE['exposure']+=1
   STATE['spoiled']=STATE['spoiled'] or STATE['exposure']>=12
   STATE['thermal_risk']=STATE['heater'] and STATE['temperature']>35
  await asyncio.sleep(1)
async def run():
 threading.Thread(target=TCP(('0.0.0.0',502),Modbus).serve_forever,daemon=True).start()
 await asyncio.gather(physics(),ua_server(),uvicorn.Server(uvicorn.Config(api,host='0.0.0.0',port=8001,log_level='warning')).serve())
if __name__=='__main__':asyncio.run(run())
