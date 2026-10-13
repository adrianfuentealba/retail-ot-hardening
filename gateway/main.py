import socketserver,socket,struct,threading,json,time
from collections import defaultdict,deque
from pathlib import Path
from fastapi import FastAPI,HTTPException
import uvicorn
POLICY={'deny_writes':False,'fc06_only':False,'modbus_allowlist':False,'write_rate':False,'accepted_writes':0,'blocked_writes':0}
app=FastAPI();LOCK=threading.RLock();WINDOWS=defaultdict(deque)
logpath=Path('/evidence/gateway.jsonl');logpath.parent.mkdir(parents=True,exist_ok=True)
def log(outcome,reason,fc):
 with logpath.open('a') as f:f.write(json.dumps({'@timestamp':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),'host':{'name':'gateway'},'event':{'dataset':'lab.control','action':'gateway-write','outcome':outcome},'message':f'FC{fc:02d}: {reason}'},ensure_ascii=False)+'\n')
@app.get('/health')
def health():return dict(POLICY)
@app.post('/policy')
def policy():POLICY['deny_writes']=True;return health()
@app.post('/policy/{name}')
def profile(name:str):
 if name=='fc06-only':POLICY['fc06_only']=True
 elif name=='modbus':POLICY['modbus_allowlist']=True
 elif name=='write-rate':POLICY['write_rate']=True;WINDOWS.clear()
 else:raise HTTPException(400,'Fixed policies only')
 return health()
@app.post('/reset')
def reset():
 for k in ['deny_writes','fc06_only','modbus_allowlist','write_rate']:POLICY[k]=False
 WINDOWS.clear();return health()
def exact(sock,n):
 b=b''
 while len(b)<n:
  x=sock.recv(n-len(b))
  if not x:raise EOFError
  b+=x
 return b
def decision(p,unit,source):
 fc=p[0]
 with LOCK:
  if unit!=1:return 2,'Unit ID not allowlisted'
  if POLICY['modbus_allowlist']:
   if fc not in [3,6,16]:return 1,'Function not allowlisted'
   if fc==3:
    if len(p)!=5:return 3,'Malformed Read'
    a,n=struct.unpack('>HH',p[1:])
    if not 1<=n<=8 or a+n>8:return 2,'Read range not allowlisted'
   if fc==6:
    if len(p)!=5:return 3,'Malformed FC06'
    a,v=struct.unpack('>HH',p[1:])
    if a!=0:return 2,'Only setpoint register may be remotely written'
    if v>6:return 3,'Setpoint 0–6 allowlist'
   if fc==16:
    if len(p)<6:return 3,'Malformed FC16'
    a,n,b=struct.unpack('>HHB',p[1:6])
    if n<1 or n>123 or b!=n*2 or len(p)!=6+b:return 3,'Malformed FC16'
    if a!=0 or n!=1:return 2,'Atomic Write only to setpoint register'
    if struct.unpack('>H',p[6:8])[0]>6:return 3,'Setpoint 0–6 allowlist'
  if fc in [6,16]:
   if POLICY['deny_writes'] or (POLICY['fc06_only'] and fc==6):return 1,'Write blocked by function policy'
   if POLICY['write_rate']:
    now=time.monotonic();q=WINDOWS[source]
    while q and now-q[0]>1:q.popleft()
    if len(q)>=2:return 6,'Write rate limit: server busy; Read preserved'
    q.append(now)
  return 0,'Forwarded to PLC'
class Proxy(socketserver.BaseRequestHandler):
 def handle(self):
  self.request.settimeout(10)
  try:
   while True:
    h=exact(self.request,7);tid,pid,l,unit=struct.unpack('>HHHB',h)
    if pid or l<2 or l>254:return
    p=exact(self.request,l-1);code,reason=decision(p,unit,self.client_address[0])
    if code:
     resp=bytes([p[0]|128,code]);self.request.sendall(struct.pack('>HHHB',tid,0,len(resp)+1,unit)+resp)
     if p[0] in [6,16]:POLICY['blocked_writes']+=1;log('blocked',reason,p[0])
    else:
     with socket.create_connection(('172.30.40.10',502),timeout=4) as s:
      s.sendall(h+p);rh=exact(s,7);rp=exact(s,struct.unpack('>HHHB',rh)[2]-1);self.request.sendall(rh+rp)
     if p[0] in [6,16]:POLICY['accepted_writes']+=1;log('success',reason,p[0])
  except (OSError,EOFError,struct.error):pass
class TCP(socketserver.ThreadingTCPServer):allow_reuse_address=True;daemon_threads=True
class UATunnel(socketserver.BaseRequestHandler):
 def handle(self):
  import select
  try:
   with socket.create_connection(('172.30.40.10',4840),timeout=10) as peer:
    self.request.settimeout(None);peer.settimeout(None)
    while True:
     ready,_,_=select.select([self.request,peer],[],[],30)
     if not ready:return
     for src in ready:
      data=src.recv(65536)
      if not data:return
      (peer if src is self.request else self.request).sendall(data)
  except OSError:pass
if __name__=='__main__':
 threading.Thread(target=TCP(('0.0.0.0',4840),UATunnel).serve_forever,daemon=True).start()
 threading.Thread(target=TCP(('0.0.0.0',502),Proxy).serve_forever,daemon=True).start();uvicorn.run(app,host='0.0.0.0',port=8003,log_level='warning')
