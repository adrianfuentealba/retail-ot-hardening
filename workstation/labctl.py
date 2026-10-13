#!/opt/venv/bin/python
import sys,json,urllib.request,urllib.error
args=sys.argv[1:];allowed=['status','inventory','baseline','simulate defrost','simulate malware','simulate lateral','simulate firmware','simulate opcua','harden os','harden application','harden plc','harden network','harden access','harden opcua','harden supply-chain','detect','recover','reset','evidence']
cmd=' '.join(args)
if cmd not in allowed:print('Comandos: '+' | '.join(allowed));sys.exit(2)
req=urllib.request.Request('http://127.0.0.1:8010/command',data=json.dumps({'command':cmd}).encode(),headers={'Content-Type':'application/json'})
try:
 with urllib.request.urlopen(req,timeout=20) as r:print(json.dumps(json.load(r),ensure_ascii=False,indent=2))
except urllib.error.URLError as e:print('Error:',e);sys.exit(1)
