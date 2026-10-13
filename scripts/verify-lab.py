#!/usr/bin/env python3
"""Pruebas educativas sobre loopback; modifican/restablecen estado del aula."""
import urllib.request,urllib.error,json,time,subprocess,os,sys
from pathlib import Path
BASE='http://127.0.0.1:'+os.getenv('LAB_PORT','8090'); ROOT=Path(__file__).resolve().parents[1]
HOSTS=['ws-corporate','ws-vendor','ws-engineering','ws-hmi','ws-soc'];CHECKS=[]
def api(path,data=None):
 req=urllib.request.Request(BASE+path,data=json.dumps(data).encode() if data is not None else None,headers={'Content-Type':'application/json'})
 with urllib.request.urlopen(req,timeout=25) as r:return json.load(r)
def check(name,condition,detail=''):
 CHECKS.append({'name':name,'passed':bool(condition),'detail':detail});print(('PASS' if condition else 'FAIL')+' '+name+' '+str(detail),flush=True)
def cmd(command,host='ws-engineering'):
 time.sleep(1.1);return api('/api/command',{'host':host,'command':command})
def compose(*args):
 return subprocess.run(['docker','compose',*args],cwd=ROOT,capture_output=True,text=True,timeout=40)
def es(query):
 r=compose('exec','-T','elasticsearch','curl','-fsS','-H','Content-Type: application/json','http://localhost:9200/retail-ot-*/_search','-d',json.dumps(query));return json.loads(r.stdout)
try:
 api('/api/reset',{});time.sleep(3)
 for host in HOSTS:
  status=cmd('status',host);check(host+' osquery real','5.23.1' in status.get('osquery',''))
  r=compose('exec','-T',host,'pgrep','-x','osqueryd');check(host+' osqueryd active',r.returncode==0)
  port=6081+HOSTS.index(host)
  with urllib.request.urlopen(f'http://127.0.0.1:{port}/vnc.html',timeout=5) as response:check(host+' noVNC HTML',response.status==200)
  inv=cmd('inventory',host);check(host+' SQL inventory',bool(inv.get('rows')))
 st=api('/api/state');check('nominal process',st['process']['setpoint']==2)
 a=cmd('simulate defrost');check('Modbus FC06 accepted',a.get('packet',{}).get('exception') is False)
 time.sleep(8);st=api('/api/state');check('real process effect',st['process']['temperature']>8)
 cmd('harden plc');a=cmd('simulate defrost');check('PLC Write rejected',a.get('packet',{}).get('exception') is True)
 cmd('simulate malware','ws-hmi');r=compose('exec','-T','ws-hmi','osqueryi','--json',"SELECT pid,cmdline FROM processes WHERE name='sleep' AND cmdline LIKE '%retail-benign-malware%';");check('osquery observed benign process','retail-benign-malware' in r.stdout)
 cmd('harden os','ws-hmi');r=compose('exec','-T','ws-hmi','stat','-c','%a:%u','/home/student/lab/controller.conf');check('actual Linux mode owner',r.stdout.strip()=='640:0',r.stdout.strip())
 a=cmd('simulate malware','ws-hmi');check('endpoint guard blocked',a.get('event',{}).get('outcome',a.get('outcome'))=='blocked' or a.get('event',{}).get('dataset')=='lab.endpoint' and a['event'].get('outcome')=='blocked')
 # response row event.outcome is nested event.
 api('/api/reset',{});time.sleep(2)
 a=cmd('simulate lateral','ws-vendor');check('two markers accepted',len(a.get('targets',[]))==2 and all(x.get('event',{}).get('outcome')=='success' for x in a['targets']))
 cmd('harden network','ws-vendor');a=cmd('simulate lateral','ws-vendor');check('two markers blocked',all(x.get('event',{}).get('outcome')=='blocked' for x in a.get('targets',[])))
 a=cmd('simulate defrost');check('gateway denies FC06',a.get('packet',{}).get('exception') is True)
 api('/api/reset',{});time.sleep(2)
 a=cmd('simulate opcua');check('OPC UA Write accepted',a.get('event',{}).get('event',{}).get('outcome')=='success')
 cmd('harden opcua');time.sleep(2);a=cmd('simulate opcua');check('OPC UA secure Write denied',a.get('security')=='SignAndEncrypt' and a.get('event',{}).get('event',{}).get('outcome')=='blocked')
 a=cmd('simulate firmware');check('fictitious firmware accepted',a.get('event',{}).get('outcome')=='success')
 cmd('harden supply-chain');a=cmd('simulate firmware');check('firmware integrity guard',a.get('event',{}).get('outcome')=='blocked')
 cmd('simulate defrost');time.sleep(2);packets=api('/api/packets');check('Tshark real packets',bool(packets) and any(p.get('function')==6 for p in packets))
 with urllib.request.urlopen(BASE+'/api/capture',timeout=10) as r:pcap=r.read();check('Ethernet PCAP magic',pcap[:4] in [b'\xd4\xc3\xb2\xa1',b'\xa1\xb2\xc3\xd4'])
 q=es({'size':0,'query':{'term':{'event.dataset':'osquery'}},'aggs':{'hosts':{'terms':{'field':'host.name','size':10}}}});names={x['key'] for x in q.get('aggregations',{}).get('hosts',{}).get('buckets',[])};check('five endpoints in Elastic',set(HOSTS)<=names,str(sorted(names)))
 q=es({'size':0,'query':{'bool':{'filter':[{'term':{'event.dataset':'suricata'}},{'term':{'event.action':'alert'}}]}}});check('Suricata alert indexed',q['hits']['total']['value']>0,str(q['hits']['total']))
 r=compose('exec','-T','kibana','curl','-fsS','http://localhost:5601/api/saved_objects/dashboard/retail-overview');check('default dashboard exists',r.returncode==0 and 'retail-overview' in r.stdout)
except Exception as e:check('verification exception',False,str(e))
finally:
 try:api('/api/reset',{})
 except Exception:pass
 report={'timestamp_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),'checks':CHECKS,'passed':all(x['passed'] for x in CHECKS),'platform':'Docker local; endpoint architecture visible in inventory'}
 (ROOT/'docs'/'verification-results.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
 print('TOTAL',len(CHECKS),'PASS',sum(x['passed'] for x in CHECKS),flush=True)
 sys.exit(0 if report['passed'] else 1)
