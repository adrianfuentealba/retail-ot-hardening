import socketserver,socket,struct,threading,json,time
from pathlib import Path
from fastapi import FastAPI
import uvicorn
POLICY={'deny_writes':False};app=FastAPI();logpath=Path('/evidence/gateway.jsonl');logpath.parent.mkdir(parents=True,exist_ok=True)
@app.get('/health')
def health():return POLICY
@app.post('/policy')
def policy():POLICY['deny_writes']=True;return POLICY
@app.post('/reset')
def reset():POLICY['deny_writes']=False;return POLICY
def exact(sock,n):
 b=b''
 while len(b)<n:
  x=sock.recv(n-len(b))
  if not x:raise EOFError
  b+=x
 return b
class Proxy(socketserver.BaseRequestHandler):
 def handle(self):
  self.request.settimeout(10)
  try:
   while True:
    h=exact(self.request,7);tid,pid,l,unit=struct.unpack('>HHHB',h)
    if pid or l<2 or l>254:return
    p=exact(self.request,l-1)
    if p[0]==6 and POLICY['deny_writes']:
     resp=bytes([134,1]);self.request.sendall(struct.pack('>HHHB',tid,0,len(resp)+1,unit)+resp)
     with logpath.open('a') as f:f.write(json.dumps({'@timestamp':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),'host':{'name':'gateway'},'event':{'dataset':'lab.control','action':'gateway-write','outcome':'blocked'},'message':'FC06 denied by application gateway'})+'\n')
    else:
     with socket.create_connection(('172.30.40.10',502),timeout=4) as s:
      s.sendall(h+p);rh=exact(s,7);rp=exact(s,struct.unpack('>HHHB',rh)[2]-1);self.request.sendall(rh+rp)
  except (OSError,EOFError):pass
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
