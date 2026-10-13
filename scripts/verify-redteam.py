#!/usr/bin/env python3
"""Prueba del aula local exclusivamente. Cambia/restablece estado, conserva evidencia."""
import urllib.request,urllib.error,json,time,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];BASE='http://127.0.0.1:8090';CHECKS=[]
def api(path,data=None):
 req=urllib.request.Request(BASE+path,data=None if data is None else json.dumps(data).encode(),headers={'Content-Type':'application/json'})
 with urllib.request.urlopen(req,timeout=30) as r:return json.load(r)
def state():return api('/api/state')['process']
def cmd(c):
 time.sleep(1.1);return api('/api/command',{'host':'ws-engineering','command':c})
def reset():
 api('/api/reset',{});time.sleep(2)
 for i in range(20):
  if state().get('opcua_ready'):return
  time.sleep(.5)
def check(name,ok,detail=''):
 CHECKS.append({'name':name,'passed':bool(ok),'detail':detail});print(('PASS ' if ok else 'FAIL ')+name+' '+str(detail),flush=True)
def wait_until(predicate,limit=12):
 end=time.time()+limit
 while time.time()<end:
  p=state()
  if predicate(p):return p
  time.sleep(.5)
 return state()
try:
 reset();check('six fixed practices',len(api('/api/redteam/catalog'))==6)
 src=api('/api/anatomy');check('Anatomy serves actual CPU code','def control_cycle' in src['source'] and src['source_path']=='plc/control_logic.py')
 a=cmd('redteam modbus-write');check('FC06 accepted',not a['result']['exception']);p=wait_until(lambda p:p['temperature']>8);check('digital twin real thermal effect',p['temperature']>8 and p['heater'])
 cmd('harden plc');a=cmd('redteam modbus-write');check('FC06 interlock exception',a['result']['exception_code']==3);check('nominal setpoint after interlock',state()['setpoint']==2)
 reset();cmd('redteam fc06-only');a=cmd('redteam modbus-write');check('incomplete FC06 denylist',a['result']['exception'])
 a=cmd('redteam modbus-fc16');check('FC16 bypasses incomplete denylist',not a['result']['exception'] and a['after']['setpoint']==50)
 cmd('harden modbus');a=cmd('redteam modbus-fc16');check('FC16 hardening rejects value',a['result']['exception_code']==3)
 a=cmd('redteam baseline');check('FC03 still available',not a['result']['exception'])
 reset();a=cmd('redteam modbus-sensor');check('sensor bias write accepted',not a['result']['exception'])
 p=wait_until(lambda p:p['sensor_bias']==-20 and not p['compressor']);check('same physics sees false cold sensor',p['sensor_bias']==-20 and p['measured_temperature']<p['temperature']-10 and not p['compressor'])
 cmd('harden inputs');a=cmd('redteam modbus-sensor');check('sensor remote write protected',a['result']['exception_code']==2 and a['after']['sensor_bias']==0)
 api('/api/anatomy/wiring',{'signal':'AI0','connected':False});p=wait_until(lambda p:p['fallback_active']);check('Anatomy disconnected signal triggers fallback alarm',p['fallback_active'] and p['alarm'])
 api('/api/anatomy/wiring',{'signal':'AI0','connected':True});p=wait_until(lambda p:not p['fallback_active']);check('Anatomy reconnection restores primary signal',p['sensor_connected'] and not p['fallback_active'])
 reset();a=cmd('redteam modbus-burst');check('finite eight writes before guard',a['result']['sent']==8 and a['result']['accepted']==8)
 cmd('harden write-rate');a=cmd('redteam modbus-burst');check('bounded burst partly rejected',a['result']['blocked']>0 and a['result']['accepted']<=2,a['result']['blocked']);a=cmd('redteam baseline');check('rate guard preserves Read',not a['result']['exception'])
 reset();a=cmd('redteam opcua-anonymous');check('anonymous None Write initially accepted',a['result']['outcome']=='success' and a['after']['setpoint']==50)
 a=cmd('redteam opcua-observer');check('encrypted observer Write initially accepted',a['result']['security']=='SignAndEncrypt' and a['result']['outcome']=='success')
 cmd('harden opcua-rbac');a=cmd('redteam opcua-observer');check('server denies observer Write',a['result']['outcome']=='blocked' and 'BadUserAccessDenied' in a['result']['status'])
 cmd('recover');a=cmd('redteam opcua-engineer');check('authorized engineer still writes 3 C',a['result']['outcome']=='success' and a['result']['readback']==3)
 cmd('harden plc');a=cmd('redteam opcua-overrange');check('server semantic guard rejects engineer bad setpoint',a['result']['outcome']=='blocked' and 'BadOutOfRange' in a['result']['status'])
 reset();cmd('harden opcua-channel');a=cmd('redteam opcua-anonymous');check('server removes None endpoint',a['result']['outcome']=='blocked')
 cmd('harden opcua-rbac');a=cmd('redteam opcua-browse');check('secure Browse and Read remain',a['result']['outcome']=='success' and a['result']['security']=='SignAndEncrypt' and all(x['mode']=='SignAndEncrypt' for x in a['result']['endpoints']))
 a=cmd('redteam opcua-engineer');check('secure engineer remains functional',a['result']['outcome']=='success' and a['result']['readback']==3)
 # Evidence from server and sensor is independent from the UI step indicator.
 cmd('redteam modbus-fc16');time.sleep(3)
 packets=api('/api/packets');check('real captured FC16',any(p.get('function')==16 for p in packets))
 q={'size':0,'query':{'bool':{'filter':[{'term':{'event.dataset':'suricata'}},{'term':{'event.action':'alert'}}],'must':[{'match_phrase':{'message':'FC16'}}]}}}
 # Collector stores Suricata signature in suricata.alert.signature, not message.
 q={'size':0,'query':{'bool':{'filter':[{'term':{'event.dataset':'suricata'}},{'term':{'event.action':'alert'}}],'must':[{'match_phrase':{'suricata.alert.signature':'FC16'}}]}}}
 end=time.time()+20;count=0
 while time.time()<end:
  p=subprocess.run(['docker','compose','exec','-T','elasticsearch','curl','-fsS','-H','Content-Type: application/json','http://localhost:9200/retail-ot-*/_search','-d',json.dumps(q)],cwd=ROOT,capture_output=True,text=True,timeout=10)
  try:count=json.loads(p.stdout)['hits']['total']['value']
  except Exception:count=0
  if count:break
  time.sleep(2)
 check('Suricata FC16 alert indexed',count>0,count)
except Exception as e:check('integration exception',False,repr(e))
finally:
 try:reset()
 except Exception:pass
 report={'checks':CHECKS,'passed':all(x['passed'] for x in CHECKS),'scope':'Fixed Modbus/OPC UA classroom scenarios, CPU source, wiring, same process physics, defenses and independent evidence'}
 (ROOT/'docs/redteam-verification-results.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
 print('TOTAL',len(CHECKS),'PASS',sum(x['passed'] for x in CHECKS),flush=True)
 raise SystemExit(0 if report['passed'] else 1)
