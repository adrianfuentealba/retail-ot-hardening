"""Ejercicios controlados. Ninguna función acepta IP, puerto, payload libre o ráfaga abierta."""
import asyncio,socket,struct,time
from asyncua import Client,ua
from asyncua.crypto.security_policies import SecurityPolicyBasic256Sha256
COMMANDS={'redteam baseline','redteam modbus-write','redteam modbus-fc16','redteam modbus-sensor','redteam modbus-burst','redteam opcua-anonymous','redteam opcua-observer','redteam opcua-engineer','redteam opcua-browse','redteam opcua-overrange','harden modbus','harden inputs','harden write-rate','harden opcua-rbac','harden opcua-channel','redteam fc06-only'}
def exact(sock,n):
 b=b''
 while len(b)<n:
  x=sock.recv(n-len(b))
  if not x:raise EOFError('Truncated Modbus response')
  b+=x
 return b
def exchange(pdu,tid=41000):
 frame=struct.pack('>HHHB',tid,0,len(pdu)+1,1)+pdu
 with socket.create_connection(('gateway',502),timeout=4) as s:
  s.sendall(frame);header=exact(s,7);body=exact(s,struct.unpack('>HHHB',header)[2]-1)
 return {'protocol':'Modbus TCP','function':pdu[0],'request_hex':frame.hex(' '),'response_hex':(header+body).hex(' '),'exception':bool(body[0]&128),'exception_code':body[1] if body[0]&128 else None,'source':'real TCP request/response through fixed gateway'}
def single(address,value,tid=41000):return exchange(struct.pack('>BHH',6,address,value),tid)
def multiple(address,value):return exchange(struct.pack('>BHHBH',16,address,1,2,value),41001)
def burst():
 # Exactly eight sequential requests; not a flood or a real DoS benchmark.
 return [single(0,50,42000+i) for i in range(8)]
async def ua_operation(command,process):
 secure=command in ['redteam opcua-observer','redteam opcua-engineer','redteam opcua-overrange'] or (command=='redteam opcua-browse' and process['opcua_tls_only'])
 client=Client('opc.tcp://gateway:4840/retail/',timeout=5);client.application_uri='urn:retail:plc'
 if secure:await client.set_security(SecurityPolicyBasic256Sha256,certificate='/certs/cert.der',private_key='/certs/key.pem',server_certificate='/certs/cert.der',mode=ua.MessageSecurityMode.SignAndEncrypt)
 identity='anonymous'
 if command in ['redteam opcua-observer','redteam opcua-engineer','redteam opcua-overrange']:
  identity='observer' if command.endswith('observer') else 'engineer';client.set_user(identity);client.set_password('retail-'+identity+'-lab')
 try:
  async with client:
   node=client.get_node('ns=2;s=Setpoint');before=await node.read_value()
   if command=='redteam opcua-browse':
    obj=client.get_node('ns=2;i=1')
    # Discovery fixed to known educational object; no recursive network scanner.
    children=await client.nodes.objects.get_children()
    return {'outcome':'success','protocol':'OPC UA','operation':'Read/Browse','identity':identity,'security':'SignAndEncrypt' if secure else 'None','setpoint':before,'objects':[str(x.nodeid) for x in children],'endpoints':[{'policy':x.SecurityPolicyUri,'mode':x.SecurityMode.name} for x in await client.get_endpoints()]}
   target=3.0 if command=='redteam opcua-engineer' else 50.0
   try:
    await node.write_value(target);outcome='success';status='Good'
   except ua.UaStatusCodeError as e:outcome='blocked';status=e.__class__.__name__
   return {'outcome':outcome,'protocol':'OPC UA','operation':'Write','identity':identity,'security':'SignAndEncrypt' if secure else 'None','before':before,'requested':target,'readback':await node.read_value(),'status':status}
 except Exception as e:
  if not secure and process.get('opcua_tls_only') and ('No matching endpoints' in str(e) or type(e).__name__ in ['BadSecurityPolicyRejected','BadSecurityModeRejected']):
   return {'outcome':'blocked','protocol':'OPC UA','operation':'Connect None / Write','identity':identity,'security':'None','status':type(e).__name__,'detail':str(e),'barrier':'Server exposes only SignAndEncrypt; verify secure engineer still reads/writes'}
  raise
async def run(command,client,event,host):
 if command not in COMMANDS:raise ValueError('Fixed educational command only')
 if command in ['harden modbus','harden write-rate','redteam fc06-only']:
  name={'harden modbus':'modbus','harden write-rate':'write-rate','redteam fc06-only':'fc06-only'}[command]
  r=await client.post('http://gateway:8003/policy/'+name);r.raise_for_status();return {'event':event(command.replace(' ','-'),'success','Fixed gateway policy '+name,host),'gateway':r.json()}
 if command in ['harden inputs','harden opcua-rbac','harden opcua-channel']:
  name=command.split()[1];r=await client.post('http://plc:8001/policy/'+name);r.raise_for_status()
  if name=='opcua-channel':
   for i in range(45):
    await asyncio.sleep(.2);p=(await client.get('http://plc:8001/state')).json()
    if p['opcua_ready']:break
   else:raise RuntimeError('Secure endpoint did not become ready')
  return {'event':event(command.replace(' ','-'),'success','Server policy '+name,host),'process':r.json()}
 before=(await client.get('http://plc:8001/state')).json()
 if command=='redteam baseline':result=await asyncio.to_thread(exchange,struct.pack('>BHH',3,0,8));outcome='success'
 elif command=='redteam modbus-write':result=await asyncio.to_thread(single,0,50);outcome='blocked' if result['exception'] else 'success'
 elif command=='redteam modbus-fc16':result=await asyncio.to_thread(multiple,0,50);outcome='blocked' if result['exception'] else 'success'
 elif command=='redteam modbus-sensor':result=await asyncio.to_thread(single,4,800);outcome='blocked' if result['exception'] else 'success'
 elif command=='redteam modbus-burst':
  packets=await asyncio.to_thread(burst);allowed=sum(not x['exception'] for x in packets);result={'packets':packets,'sent':8,'accepted':allowed,'blocked':8-allowed,'notice':'Finite eight-request classroom exercise; not a DoS or open flood'};outcome='blocked' if allowed<8 else 'success'
 else:result=await ua_operation(command,before);outcome=result['outcome']
 after=(await client.get('http://plc:8001/state')).json()
 return {'event':event(command.replace(' ','-'),outcome,'SCENARIO CONTROLADO: fixed Modbus/OPC UA exercise; verify packet/server and process evidence',host),'result':result,'before':before,'after':after}
