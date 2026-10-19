#!/opt/venv/bin/python
import sys,json,urllib.request,urllib.error,subprocess
args=sys.argv[1:]
if args and args[0]=='guides':
 guide=args[1] if len(args)==2 else '00'
 if len(args)>2 or guide not in [f'{i:02d}' for i in range(11)]+['solucion']:
  print('Uso: labctl guides [00–10 | solucion]');sys.exit(2)
 url='http://127.0.0.1:8010/guides/index.html?guide='+guide
 try:subprocess.Popen(['firefox-esr',url],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
 except OSError as e:print('No se pudo abrir Firefox:',e);sys.exit(1)
 print('Guía local:',url);sys.exit(0)
allowed=['status','inventory','baseline','simulate defrost','simulate malware','simulate lateral','simulate firmware','simulate opcua','harden os','harden application','harden plc','harden network','harden access','harden opcua','harden supply-chain','detect','recover','reset','evidence','classroom-state','reset-all']
allowed += ['redteam baseline', 'redteam modbus-write', 'redteam modbus-fc16', 'redteam modbus-sensor', 'redteam modbus-burst', 'redteam opcua-anonymous', 'redteam opcua-observer', 'redteam opcua-engineer', 'redteam opcua-overrange', 'redteam opcua-browse', 'harden modbus', 'harden inputs', 'harden write-rate', 'harden opcua-rbac', 'harden opcua-channel', 'redteam fc06-only']
cmd=' '.join(args)
if cmd not in allowed:print('Comandos: '+' | '.join(allowed)+' | guides [00–10]');sys.exit(2)
if cmd=='reset-all':print('AVISO: reset de TODA el aula; requiere coordinación con el grupo. Conserva evidencia.',file=sys.stderr)
req=urllib.request.Request('http://127.0.0.1:8010/command',data=json.dumps({'command':cmd}).encode(),headers={'Content-Type':'application/json'})
try:
 with urllib.request.urlopen(req,timeout=35 if cmd=='reset-all' else 25) as r:print(json.dumps(json.load(r),ensure_ascii=False,indent=2))
except urllib.error.URLError as e:print('Error:',e);sys.exit(1)
