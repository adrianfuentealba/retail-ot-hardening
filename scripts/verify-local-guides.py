#!/usr/bin/env python3
"""Solo lectura: guías y comandos de consulta de las cinco estaciones. No reset ni escenarios."""
import subprocess,json,sys,argparse
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];CHECKS=[]
parser=argparse.ArgumentParser();parser.add_argument('--compose',default=str(ROOT/'docker-compose.yml'));parser.add_argument('--qa',action='store_true');options=parser.parse_args()
def check(name,ok,detail=''):
 CHECKS.append({'name':name,'passed':bool(ok),'detail':detail});print(('PASS ' if ok else 'FAIL ')+name,detail)
for host in ['ws-corporate','ws-vendor','ws-engineering','ws-hmi','ws-soc']:
 code="""import urllib.request,json,time,subprocess
base='http://127.0.0.1:8010'
for attempt in range(30):
 try:
  with urllib.request.urlopen(base+'/health',timeout=2) as r:health=json.load(r)
  break
 except Exception:
  if attempt==29:raise
  time.sleep(1)
with urllib.request.urlopen(base+'/guides/manifest.json') as r:m=json.load(r)
assert {f'{i:02d}' for i in range(11)}.issubset({x['id'] for x in m})
for row in m:
 with urllib.request.urlopen(base+'/guides/'+row['file']) as r:assert len(r.read())>500
with urllib.request.urlopen(base+'/health') as r:health=json.load(r)
req=urllib.request.Request(base+'/command',data=json.dumps({'command':'classroom-state'}).encode(),headers={'Content-Type':'application/json'})
with urllib.request.urlopen(req) as r:state=json.load(r)
assert 'process' in state and 'endpoints' in state
from pathlib import Path
assert Path('/home/student/Desktop/Guias.desktop').exists()
student=json.loads(subprocess.check_output(['su','student','-c','labctl status'],text=True))
assert student['host']==health['host']
print(json.dumps({'host':health['host'],'guides':len(m),'process_available':state['process'] is not None}))
"""
 p=subprocess.run(['docker','compose','-f',options.compose,'exec','-T',host.replace('ws-','qa-') if options.qa else host,'python','-c',code],capture_output=True,text=True)
 check(host+' local bundle/identity/CLI',p.returncode==0,p.stdout.strip() or p.stderr[-600:])
result={'passed':all(x['passed'] for x in CHECKS),'checks':CHECKS,'notice':'Solo lectura; no demuestra nuevo ensayo de escenarios ni portapapeles GUI.','environment':'QA aislada de documentación' if options.qa else 'aula configurada'}
(ROOT/'docs/local-guides-runtime-results.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
sys.exit(0 if result['passed'] else 1)
