import asyncio,json,time,threading,socketserver,struct,copy
from pathlib import Path
from fastapi import FastAPI,HTTPException
from pydantic import BaseModel
import uvicorn
from asyncua import Server,ua
from asyncua.crypto.cert_gen import setup_self_signed_certificate
from asyncua.server.address_space import AttributeService
from asyncua.crypto.permission_rules import PermissionRuleset,READ_TYPES
from asyncua.server.user_managers import UserManager,User,UserRole
from cryptography.x509.oid import ExtendedKeyUsageOID
from plc.control_logic import initial_state,apply_changes,control_cycle,registers
LOCK=threading.RLock();STATE=initial_state()
EVENTS=Path('/evidence/control.jsonl');EVENTS.parent.mkdir(parents=True,exist_ok=True)
def log(action,outcome,detail):
 with EVENTS.open('a') as f:f.write(json.dumps({'@timestamp':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),'event':{'dataset':'lab.control','action':action,'outcome':outcome},'host':{'name':'plc'},'message':detail},ensure_ascii=False)+'\n')
def writes(changes,protocol):
 with LOCK:
  ok,reason,code=apply_changes(STATE,changes)
  log('setpoint' if any(a==0 for a,v in changes) else 'input-write','success' if ok else 'blocked',f'{protocol}: {changes}: {reason}')
  return ok,reason,code
def write(v,protocol):return writes([(0,v)],protocol)[0]
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
     if unit!=1:resp=bytes([fc|128,2])
     elif fc==3 and len(p)==5:
      addr,count=struct.unpack('>HH',p[1:]);STATE['modbus_reads']+=1;regs=registers(STATE)
      if count<1 or count>len(regs) or addr+count>len(regs):resp=bytes([131,2])
      else:resp=bytes([3,count*2])+struct.pack('>'+'H'*count,*regs[addr:addr+count])
     elif fc==6 and len(p)==5:
      addr,v=struct.unpack('>HH',p[1:]);STATE['modbus_writes']+=1;ok,reason,code=writes([(addr,v)],'Modbus FC06');resp=p if ok else bytes([134,code])
     elif fc==16 and len(p)>=6:
      addr,count,n=struct.unpack('>HHB',p[1:6]);STATE['modbus_writes']+=1
      if count<1 or count>123 or n!=count*2 or len(p)!=6+n:resp=bytes([144,3])
      else:
       values=struct.unpack('>'+'H'*count,p[6:]);ok,reason,code=writes(list(enumerate(values,addr)),'Modbus FC16');resp=struct.pack('>BHH',16,addr,count) if ok else bytes([144,code])
     else:resp=bytes([fc|128,1])
    self.request.sendall(struct.pack('>HHHB',tid,0,len(resp)+1,unit)+resp)
  except (EOFError,OSError,struct.error):pass
class TCP(socketserver.ThreadingTCPServer):allow_reuse_address=True;daemon_threads=True
api=FastAPI()
@api.get('/state')
def state():
 with LOCK:return dict(STATE)
@api.post('/policy/{name}')
def policy(name:str):
 with LOCK:
  if name=='plc':STATE['plc_guard']=True;write(2,'local interlock')
  elif name=='opcua':STATE['opcua_secure']=True
  elif name=='opcua-rbac':STATE['opcua_rbac']=True
  elif name=='opcua-channel':STATE['opcua_tls_only']=True;STATE['opcua_ready']=False
  elif name=='inputs':
   STATE.update(input_guard=True,sensor_bias=0.0,sensor_connected=True,measured_temperature=STATE['temperature'],sensor_valid=True,compressor=True)
  else:raise HTTPException(400,'Policy not allowed')
 log('policy','success',name);return state()
class Wiring(BaseModel):signal:str;connected:bool
@api.post('/wiring')
def wiring(r:Wiring):
 with LOCK:
  if r.signal=='AI0':STATE['sensor_connected']=r.connected
  elif r.signal=='DI0':STATE['door_open']=not r.connected
  else:raise HTTPException(400,'Only training AI0/DI0 inputs')
 log('anatomy-wiring','success',f'{r.signal} connected={r.connected}; pedagogical out-of-band input');return state()
@api.post('/reset')
def reset():
 with LOCK:
  reads=STATE['modbus_reads'];writes_count=STATE['modbus_writes'];tls=STATE['opcua_tls_only'];ready=STATE['opcua_ready'];STATE.clear();STATE.update(initial_state());STATE.update(modbus_reads=reads,modbus_writes=writes_count,opcua_ready=ready and not tls)
 log('reset','success','Process and policy reset; evidence preserved');return state()
@api.post('/recover')
def recover():
 with LOCK:STATE.update(setpoint=2,heater=False,compressor=True,sensor_bias=0.0,sensor_connected=True)
 log('recover','success','Cooling resumed; spoiled stock remains quarantined');return state()
# Public classroom identities. Credentials are training examples, not production secrets.
CLASSROOM_USERS={'engineer':'retail-engineer-lab','observer':'retail-observer-lab'}
class ClassroomUsers(UserManager):
 def get_user(self,iserver,username=None,password=None,certificate=None):
  if username is None:return User(role=UserRole.Anonymous,name='anonymous')
  if CLASSROOM_USERS.get(username)!=password:
   log('opcua-identity','blocked','Unknown classroom identity');return None
  return User(role=UserRole.User,name=username)
class ClassroomServiceRules(PermissionRuleset):
 def check_validity(self,user,action_type_id,body):
  # Let Read/Browse and Write reach fine-grained server guards; deny remote node management.
  return action_type_id in {ua.NodeId(x) for x in READ_TYPES+[ua.ObjectIds.WriteRequest_Encoding_DefaultBinary]}
class GuardedAttributeService(AttributeService):
 async def write(self,params,user=User(role=UserRole.Admin)):
  # Internal server updates have Admin role. External classroom identities never do.
  if user.role==UserRole.Admin:return await super().write(params,user)
  result=[]
  for w in params.NodesToWrite:
   nid=w.NodeId.Identifier;address={'Setpoint':0,'SensorBias':4,'SensorConnected':5}.get(nid)
   if w.AttributeId!=ua.AttributeIds.Value or address is None:
    result.append(ua.StatusCode(ua.StatusCodes.BadUserAccessDenied));continue
   if STATE['opcua_secure'] or (STATE['opcua_rbac'] and user.name!='engineer'):
    log('opcua-authorization','blocked',f'{user.name}: Write {nid} denied by server node policy')
    result.append(ua.StatusCode(ua.StatusCodes.BadUserAccessDenied));continue
   try:
    value=w.Value.Value.Value
    if address==4:value=float(value)*10+1000
    elif address==5:value=int(value)
    with LOCK:
     test=dict(STATE);ok,reason,code=apply_changes(test,[(address,value)])
    if not ok:
     log('opcua-semantic','blocked',f'{user.name}: {nid}: {reason}');result.append(ua.StatusCode(ua.StatusCodes.BadOutOfRange));continue
    one=copy.copy(params);one.NodesToWrite=[w];codes=await super().write(one,user)
    if codes[0].is_good():writes([(address,value)],f'OPC UA Write by {user.name}')
    result.extend(codes)
   except (ValueError,TypeError,AttributeError):result.append(ua.StatusCode(ua.StatusCodes.BadTypeMismatch))
  return result
async def ua_server():
 p=Path('/certs');p.mkdir(exist_ok=True);uri='urn:retail:plc'
 await setup_self_signed_certificate(p/'key.pem',p/'cert.der',uri,'plc',[ExtendedKeyUsageOID.SERVER_AUTH,ExtendedKeyUsageOID.CLIENT_AUTH],{'organizationName':'Retail education'})
 while True:
  strict=STATE['opcua_tls_only'];STATE['opcua_ready']=False
  srv=Server(user_manager=ClassroomUsers());await srv.init();srv.set_endpoint('opc.tcp://0.0.0.0:4840/retail/');await srv.set_application_uri(uri)
  await srv.load_certificate(str(p/'cert.der'));await srv.load_private_key(str(p/'key.pem'))
  policies=[ua.SecurityPolicyType.Basic256Sha256_SignAndEncrypt]
  if not strict:policies.insert(0,ua.SecurityPolicyType.NoSecurity)
  srv.set_security_policy(policies,permission_ruleset=ClassroomServiceRules());srv.iserver.attribute_service=GuardedAttributeService(srv.iserver.aspace)
  idx=await srv.register_namespace('urn:retail:model');obj=await srv.nodes.objects.add_object(idx,'Refrigeration')
  nodes={}
  for name,value,writable in [('Setpoint',2.0,True),('Temperature',2.0,False),('SensorBias',0.0,True),('SensorConnected',True,True),('Compressor',True,False)]:
   n=await obj.add_variable(ua.NodeId(name,idx),name,value);nodes[name]=n
   if writable:await n.set_writable()
  async with srv:
   log('opcua-start','success','SignAndEncrypt only' if strict else 'None and SignAndEncrypt; server-side semantic and optional authorization guards')
   STATE['opcua_ready']=True
   while strict==STATE['opcua_tls_only']:
    values={'Setpoint':float(STATE['setpoint']),'Temperature':STATE['temperature'],'SensorBias':STATE['sensor_bias'],'SensorConnected':STATE['sensor_connected'],'Compressor':STATE['compressor']}
    for name,n in nodes.items():
     if name in ['Setpoint','SensorBias','SensorConnected']:await n.set_writable(not STATE['opcua_secure'])
     await n.write_value(values[name])
    await asyncio.sleep(.3)
  STATE['opcua_ready']=False
  await asyncio.sleep(.15)
async def physics():
 while True:
  with LOCK:control_cycle(STATE)
  await asyncio.sleep(1)
async def run():
 threading.Thread(target=TCP(('0.0.0.0',502),Modbus).serve_forever,daemon=True).start()
 await asyncio.gather(physics(),ua_server(),uvicorn.Server(uvicorn.Config(api,host='0.0.0.0',port=8001,log_level='warning')).serve())
if __name__=='__main__':asyncio.run(run())
