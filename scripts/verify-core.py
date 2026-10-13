#!/usr/bin/env python3
"""Verificación parcial: PLC/gateway/panel/sensor. No valida noVNC, osquery ni ELK."""
import json,time,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
code=r'''
import httpx,time,json
c=httpx.Client(base_url='http://127.0.0.1:8000',timeout=20);check=[]
def test(name,value):check.append({'name':name,'passed':bool(value)})
def action(command):
 r=c.post('/api/action',json={'command':command,'host':'ws-engineering'});r.raise_for_status();return r.json()
httpx.post('http://plc:8001/reset');httpx.post('http://gateway:8003/reset');time.sleep(2)
a=action('simulate defrost');test('FC06 accepted',not a['packet']['exception']);time.sleep(18)
p=httpx.get('http://plc:8001/state').json();test('thermal impact observed',p['temperature']>30);test('stock quarantined',p['spoiled'])
a=action('harden plc');time.sleep(2);a=action('simulate defrost');test('PLC FC06 exception 86/03',a['packet']['exception'] and a['packet']['hex'].endswith('86 03'))
p=httpx.get('http://plc:8001/state').json();test('nominal setpoint restored',p['setpoint']==2);test('quarantine retained',p['spoiled'])
httpx.post('http://plc:8001/reset');time.sleep(2)
a=action('simulate opcua');test('actual OPC UA Write allowed',a['security']=='None' and a['event']['event']['outcome']=='success')
a=action('harden opcua');time.sleep(2);a=action('simulate opcua');test('secure Read and denied Write',a['security']=='SignAndEncrypt' and a['event']['event']['outcome']=='blocked')
httpx.post('http://gateway:8003/policy');a=action('simulate defrost');test('gateway denies FC06',a['packet']['exception'])
time.sleep(3);packets=c.get('/api/packets').json();test('Tshark Modbus FC03 and FC06',any(x.get('function')==3 for x in packets) and any(x.get('function')==6 for x in packets));test('Tshark OPC UA payload',any(x['protocol']=='OPC UA' for x in packets));data=c.get('/api/capture').content;test('real PCAP magic',data[:4] in [b'\xd4\xc3\xb2\xa1',b'\xa1\xb2\xc3\xd4'])
httpx.post('http://plc:8001/reset');httpx.post('http://gateway:8003/reset');print(json.dumps({'checks':check,'complete_stack_validated':False}))
'''
r=subprocess.run(['docker','compose','exec','-T','panel','python','-c',code],cwd=ROOT,capture_output=True,text=True,timeout=80)
if r.returncode:print(r.stderr);raise SystemExit(r.returncode)
report=json.loads(r.stdout);report['timestamp_utc']=time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime())
cmd="import json;from collections import Counter;c=Counter();[(c.update([r['alert']['signature']])) for r in (json.loads(x) for x in open('/evidence/eve.json')) if r.get('event_type')=='alert'];print(json.dumps(dict(c)))"
r=subprocess.run(['docker','compose','exec','-T','sensor','python3','-c',cmd],cwd=ROOT,capture_output=True,text=True,timeout=10)
report['suricata_alerts']=json.loads(r.stdout)
report['checks'].append({'name':'Suricata FC06/defrost signatures','passed':all(report['suricata_alerts'].get(x,0)>0 for x in ['RETAIL LAB Modbus FC06 write request','RETAIL LAB defrost setpoint 50 register zero'])})
(ROOT/'docs/core-verification-results.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print(json.dumps(report,ensure_ascii=False,indent=2))
raise SystemExit(0 if all(x['passed'] for x in report['checks']) else 1)
