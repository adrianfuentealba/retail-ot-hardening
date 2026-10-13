#!/usr/bin/env python3
"""Valida noVNC + osquery + Logstash + ES + Kibana con eventos nuevos.
Solo destinos loopback/servicios Compose fijos. Escenarios benignos de aula.
"""
import base64,hashlib,json,os,socket,subprocess,time,urllib.request
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
HOSTS=['ws-corporate','ws-vendor','ws-engineering','ws-hmi','ws-soc']
BASE='http://127.0.0.1:'+os.getenv('LAB_PORT','8090')
CHECKS=[];MEASUREMENTS=[]
def http(path,data=None):
 req=urllib.request.Request(BASE+path,data=None if data is None else json.dumps(data).encode(),headers={'Content-Type':'application/json'})
 with urllib.request.urlopen(req,timeout=30) as r:return json.load(r)
def run(*args):
 p=subprocess.run(['docker','compose',*args],cwd=ROOT,capture_output=True,text=True,timeout=45)
 if p.returncode:raise RuntimeError(p.stderr or p.stdout)
 return p.stdout

def es(query):
 return json.loads(run('exec','-T','elasticsearch','curl','-fsS','-H','Content-Type: application/json','http://localhost:9200/retail-ot-*/_search','-d',json.dumps(query)))
def check(name,ok,detail=''):
 row={'name':name,'passed':bool(ok),'detail':detail};CHECKS.append(row);print(('PASS' if ok else 'FAIL')+' '+name+' '+str(detail),flush=True)
def cmd(host,command):
 time.sleep(1.1);return http('/api/command',{'host':host,'command':command})
def outcome(x):
 if isinstance(x,dict):
  if isinstance(x.get('event'),dict) and 'outcome' in x['event']:return x['event']['outcome']
  if 'event' in x:return outcome(x['event'])
 return None

def websocket_rfb(port):
 # Verify actual noVNC WebSocket reaches the VNC server (RFB greeting), not only static HTML.
 key=base64.b64encode(os.urandom(16)).decode()
 request=(f'GET /websockify HTTP/1.1\r\nHost: 127.0.0.1:{port}\r\nOrigin: http://127.0.0.1:{port}\r\nUpgrade: websocket\r\nConnection: Upgrade\r\nSec-WebSocket-Key: {key}\r\nSec-WebSocket-Version: 13\r\nSec-WebSocket-Protocol: binary\r\n\r\n').encode()
 with socket.create_connection(('127.0.0.1',port),timeout=10) as s:
  s.settimeout(10);s.sendall(request);buf=b''
  while b'\r\n\r\n' not in buf:
   chunk=s.recv(4096)
   if not chunk:raise RuntimeError('WebSocket connection closed before headers')
   buf+=chunk
  headers,extra=buf.split(b'\r\n\r\n',1)
  if b'101' not in headers.split(b'\r\n')[0]:return False,headers.decode()
  while b'RFB ' not in extra and len(extra)<4096:
   chunk=s.recv(4096)
   if not chunk:break
   extra+=chunk
  return b'RFB ' in extra,extra.hex()

try:
 start=time.time();http('/api/reset',{});time.sleep(3)
 for i,h in enumerate(HOSTS):
  x=cmd(h,'status');check(h+' agent/osquery version',x.get('host')==h and '5.23.1' in x.get('osquery',''),x.get('osquery'))
  check(h+' osqueryd running',bool(run('exec','-T',h,'pgrep','-x','osqueryd').strip()))
  port=int(os.getenv(['CORPORATE','VENDOR','ENGINEERING','HMI','SOC'][i]+'_VNC_PORT',str(6081+i)))
  ok,detail=websocket_rfb(port);check(h+' noVNC → RFB WebSocket',ok,detail[:100])
  inv=cmd(h,'inventory');check(h+' native osquery SQL',bool(inv.get('rows')),inv.get('rows'))
  pre=time.time();a=cmd(h,'simulate malware');check(h+' benign action accepted',outcome(a)=='success')
  filters=[{'term':{'host.name':h}},{'range':{'@timestamp':{'gte':int(pre*1000),'format':'epoch_millis'}}}]
  deadline=time.time()+35;seen={}
  while time.time()<deadline:
   q=es({'size':100,'query':{'bool':{'filter':filters}},'sort':[{'@timestamp':'desc'}]})
   hits=q.get('hits',{}).get('hits',[])
   ep=next((r for r in hits if r['_source'].get('event',{}).get('dataset')=='lab.endpoint' and r['_source']['event'].get('action')=='malware-emulation'),None)
   oq=next((r for r in hits if r['_source'].get('event',{}).get('dataset')=='osquery' and r['_source'].get('osquery',{}).get('columns',{}).get('name')=='sleep' and 'retail-benign-malware' in r['_source'].get('message','')),None)
   if ep and oq:
    seen={'endpoint_id':ep['_id'],'osquery_id':oq['_id'],'seconds_to_visible':round(time.time()-pre,2)};break
   time.sleep(2)
  check(h+' fresh endpoint + osquery events indexed',bool(seen),seen)
  MEASUREMENTS.append({'host':h,**seen})
  cmd(h,'harden application');blocked_at=time.time();b=cmd(h,'simulate malware');check(h+' execution guard blocked',outcome(b)=='blocked')
  deadline=time.time()+25;blocked_id=None
  while time.time()<deadline:
   q=es({'size':1,'query':{'bool':{'filter':[{'term':{'host.name':h}},{'term':{'event.dataset':'lab.endpoint'}},{'term':{'event.outcome':'blocked'}},{'range':{'@timestamp':{'gte':int(blocked_at*1000),'format':'epoch_millis'}}}]}}})
   hits=q.get('hits',{}).get('hits',[])
   if hits:blocked_id=hits[0]['_id'];break
   time.sleep(2)
  check(h+' fresh blocked event indexed',bool(blocked_id),blocked_id)
  cmd(h,'harden os')
  p=subprocess.run(['docker','compose','exec','-T','--user','student',h,'sh','-c',"printf 'student-write-test\n' >> /home/student/lab/controller.conf"],cwd=ROOT,capture_output=True,text=True,timeout=15)
  check(h+' Linux file write denied for student',p.returncode!=0 and 'Permission denied' in p.stderr,p.stderr.strip())
 q=es({'size':0,'query':{'range':{'@timestamp':{'gte':int(start*1000),'format':'epoch_millis'}}},'aggs':{'hosts':{'terms':{'field':'host.name','size':20}},'datasets':{'terms':{'field':'event.dataset','size':10}}}})
 check('all five hosts have new indexed events',set(HOSTS)<={r['key'] for r in q['aggregations']['hosts']['buckets']},q['aggregations']['hosts']['buckets'])
 # Test pipeline health and imported objects, independent of cached historical events.
 pipeline=json.loads(run('exec','-T','logstash','curl','-fsS','http://localhost:9600/_node/stats/pipelines'))
 check('Logstash events output >0',pipeline['pipelines']['main']['events']['out']>0,pipeline['pipelines']['main']['events'])
 obj=json.loads(run('exec','-T','kibana','curl','-fsS','http://localhost:5601/api/saved_objects/dashboard/retail-overview'))
 check('overview dashboard panels imported',len(json.loads(obj['attributes']['panelsJSON']))>=6)
 for h in HOSTS:
  obj=json.loads(run('exec','-T','kibana','curl','-fsS','http://localhost:5601/api/saved_objects/search/'+h));check(h+' default saved search',h in obj['attributes']['kibanaSavedObjectMeta']['searchSourceJSON'])
  obj=json.loads(run('exec','-T','kibana','curl','-fsS','http://localhost:5601/api/saved_objects/dashboard/retail-'+h));check(h+' filtered dashboard',h in obj['attributes']['kibanaSavedObjectMeta']['searchSourceJSON'] and len(json.loads(obj['attributes']['panelsJSON']))==3)
except Exception as e:check('verification exception',False,str(e))
finally:
 try:http('/api/reset',{})
 except Exception:pass
 report={'timestamp_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),'checks':CHECKS,'measurements':MEASUREMENTS,'passed':all(c['passed'] for c in CHECKS),'scope':'fresh benign endpoint events, real osquery, RFB WebSocket, Logstash/ES/Kibana'}
 (ROOT/'docs/observability-verification-results.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
 print('TOTAL',len(CHECKS),'PASSED',sum(x['passed'] for x in CHECKS),flush=True)
 raise SystemExit(0 if report['passed'] else 1)
