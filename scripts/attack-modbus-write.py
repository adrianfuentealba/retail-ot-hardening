#!/usr/bin/env python3
"""ESCENARIO CONTROLADO DE LABORATORIO. Solo objetivo interno fijo de la maqueta."""
import json,urllib.request
req=urllib.request.Request('http://127.0.0.1:8090/api/command',data=json.dumps({'host':'ws-engineering','command':'simulate defrost'}).encode(),headers={'Content-Type':'application/json'})
with urllib.request.urlopen(req,timeout=20) as r:print(r.read().decode())
