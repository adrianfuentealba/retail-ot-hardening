#!/usr/bin/env python3
"""FC03 legítimo mediante consola de aula fija; no admite destinos externos."""
import json,urllib.request,time
for _ in range(5):
 req=urllib.request.Request('http://127.0.0.1:8090/api/command',data=json.dumps({'host':'ws-hmi','command':'baseline'}).encode(),headers={'Content-Type':'application/json'})
 with urllib.request.urlopen(req) as r:print(r.read().decode())
 time.sleep(3)
print('El panel genera FC03 cada ciclo de supervisión automáticamente.')
