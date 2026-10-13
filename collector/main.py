import os,time,json,socket,sqlite3
from datetime import datetime,timezone
from pathlib import Path
DB=sqlite3.connect('/state/cursors.db');DB.execute('create table if not exists cursors(path text primary key, inode integer, offset integer)')
def send(row):
 payload=(json.dumps(row)+'\n').encode()
 with socket.create_connection(('logstash',5044),timeout=5) as s:s.sendall(payload)
def normalize(row,host,source):
 if source=='osquery':
  if 'snapshot' in row:row['snapshot_count']=len(row['snapshot'])
  row['osquery']=dict(row);row={'host':{'name':host},'event':{'dataset':'osquery','action':row.get('name','query'),'outcome':row.get('action','observed')},'message':json.dumps(row,ensure_ascii=False),'osquery':row['osquery'],'@timestamp':datetime.fromtimestamp(int(row.get('unixTime',time.time())),timezone.utc).isoformat()}
 elif source=='suricata':
  raw=row;row={'host':{'name':'sensor'},'event':{'dataset':'suricata','action':raw.get('event_type','event'),'outcome':'observed'},'message':raw.get('alert',{}).get('signature',raw.get('event_type','network')),'suricata':raw,'@timestamp':raw.get('timestamp')}
 return row
while True:
 for base in Path('/sources').iterdir():
  for p in base.rglob('*'):
   if p.name not in ['osqueryd.results.log','osqueryd.snapshots.log','endpoint.jsonl','control.jsonl','gateway.jsonl','panel.jsonl','eve.json']:continue
   try:
    st=p.stat();cur=DB.execute('select inode,offset from cursors where path=?',(str(p),)).fetchone();offset=cur[1] if cur and cur[0]==st.st_ino and cur[1]<=st.st_size else 0
    with p.open() as f:
     f.seek(offset)
     for i in range(300):
      begin=f.tell();line=f.readline()
      if not line or not line.endswith('\n'):break
      try:
       row=json.loads(line);src='osquery' if p.name.startswith('osqueryd') else 'suricata' if p.name=='eve.json' else 'application';send(normalize(row,base.name,src))
      except json.JSONDecodeError:pass
      except OSError:break
      offset=f.tell()
    DB.execute('insert or replace into cursors values(?,?,?)',(str(p),st.st_ino,offset));DB.commit()
   except (OSError,UnicodeError):pass
 time.sleep(2)
