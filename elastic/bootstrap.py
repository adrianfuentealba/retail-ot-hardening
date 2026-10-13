import httpx,time,json
from pathlib import Path
HOSTS=['ws-corporate','ws-vendor','ws-engineering','ws-hmi','ws-soc']
ES='http://elasticsearch:9200';KB='http://kibana:5601'
SEARCHES=[('endpoint','Acciones Linux y contramedidas','event.dataset : "lab.endpoint"'),('osquery','osquery — procesos y archivos reales','event.dataset : "osquery"'),('control','Proceso, PLC y conductos','event.dataset : "lab.control"'),('suricata','Suricata — firmas de red','event.dataset : "suricata" AND event.action : "alert"')]
INDEX_REF={'type':'index-pattern','id':'retail-ot','name':'kibanaSavedObjectMeta.searchSourceJSON.index'}
def search(sid,title,kql,columns=None):
 return {'type':'search','id':sid,'attributes':{'title':title,'columns':columns or ['host.name','event.action','event.outcome','message'],'sort':[['@timestamp','desc']],'kibanaSavedObjectMeta':{'searchSourceJSON':json.dumps({'indexRefName':INDEX_REF['name'],'query':{'language':'kuery','query':kql},'filter':[]})}},'references':[INDEX_REF]}
def dashboard(sid,title,items,query=''):
 panels=[];refs=[]
 for i,item in enumerate(items):
  typ,oid,x,y,w,h=item;ref='panel_'+str(i)
  panels.append({'panelIndex':str(i+1),'type':typ,'panelRefName':ref,'gridData':{'x':x,'y':y,'w':w,'h':h,'i':str(i+1)},'embeddableConfig':{}})
  refs.append({'name':ref,'type':typ,'id':oid})
 return {'type':'dashboard','id':sid,'attributes':{'title':title,'description':'Evidencia de aula local. Marcadores benignos, no malware operativo. Logs del agente separados de osquery y Suricata.','panelsJSON':json.dumps(panels),'optionsJSON':json.dumps({'useMargins':True,'syncColors':False,'hidePanelTitles':False}),'timeRestore':True,'timeFrom':'now-15m','timeTo':'now','refreshInterval':{'pause':False,'value':5000},'kibanaSavedObjectMeta':{'searchSourceJSON':json.dumps({'query':{'language':'kuery','query':query},'filter':[]})}},'references':refs}
def histogram(sid,title,field):
 vis={'title':title,'type':'histogram','params':{'addTooltip':True,'addLegend':False,'type':'histogram','grid':{'categoryLines':False},'categoryAxes':[{'id':'CategoryAxis-1','type':'category','position':'bottom','show':True,'style':{},'scale':{'type':'linear'},'labels':{'show':True,'truncate':100},'title':{}}],'valueAxes':[{'id':'ValueAxis-1','type':'value','position':'left','show':True,'style':{},'scale':{'type':'linear','mode':'normal'},'labels':{'show':True,'rotate':0,'filter':False,'truncate':100},'title':{'text':'Eventos'}}],'seriesParams':[{'show':True,'type':'histogram','mode':'stacked','data':{'label':'Count','id':'1'},'valueAxis':'ValueAxis-1','drawLinesBetweenPoints':True,'showCircles':True}],'times':[],'thresholdLine':{'show':False}},'aggs':[{'id':'1','enabled':True,'type':'count','schema':'metric','params':{}},{'id':'2','enabled':True,'type':'terms','schema':'segment','params':{'field':field,'orderBy':'1','order':'desc','size':12,'otherBucket':False,'missingBucket':False}}]}
 return {'type':'visualization','id':sid,'attributes':{'title':title,'visState':json.dumps(vis),'uiStateJSON':'{}','description':'Conteo de documentos en la ventana seleccionada, no conteo de incidentes únicos.','version':1,'kibanaSavedObjectMeta':{'searchSourceJSON':json.dumps({'indexRefName':INDEX_REF['name'],'query':{'language':'kuery','query':''},'filter':[]})}},'references':[INDEX_REF]}
def objects():
 out=[{'type':'index-pattern','id':'retail-ot','attributes':{'title':'retail-ot-*','timeFieldName':'@timestamp'}}]
 for sid,title,kql in SEARCHES:out.append(search('retail-'+sid,title,kql))
 out.extend([histogram('retail-host-count','Eventos por activo','host.name'),histogram('retail-source-count','Eventos por fuente independiente','event.dataset')])
 items=[('visualization','retail-host-count',0,0,24,12),('visualization','retail-source-count',24,0,24,12)]
 items.extend(('search','retail-'+s[0],(i%2)*24,12+(i//2)*16,24,16) for i,s in enumerate(SEARCHES))
 out.append(dashboard('retail-overview','RETAIL OT | Centro de operaciones',items))
 for h in HOSTS:
  out.append(search(h,'Endpoint '+h,'host.name : "'+h+'"',['event.dataset','event.action','event.outcome','message']))
  out.append(dashboard('retail-'+h,'RETAIL OT | '+h,[('search','retail-endpoint',0,0,24,16),('search','retail-osquery',24,0,24,16),('search',h,0,16,48,16)],'host.name : "'+h+'"'))
 return out

def main():
 c=httpx.Client(timeout=20)
 for i in range(180):
  try:
   if c.get(KB+'/api/status').status_code==200 and c.get(ES+'/_cluster/health').status_code==200:break
  except httpx.HTTPError:pass
  time.sleep(3)
 else:raise SystemExit('Elastic/Kibana readiness timeout')
 template={'index_patterns':['retail-ot-*'],'template':{'settings':{'number_of_shards':1,'number_of_replicas':0},'mappings':{'properties':{'@timestamp':{'type':'date'},'host':{'properties':{'name':{'type':'keyword'}}},'event':{'properties':{'dataset':{'type':'keyword'},'action':{'type':'keyword'},'outcome':{'type':'keyword'}}},'message':{'type':'text'}}}}}
 c.put(ES+'/_index_template/retail-ot',json=template).raise_for_status()
 blob='\n'.join(json.dumps(x,ensure_ascii=False) for x in objects())+'\n'
 r=c.post(KB+'/api/saved_objects/_import?overwrite=true',headers={'kbn-xsrf':'true'},files={'file':('retail-dashboards.ndjson',blob,'application/ndjson')});r.raise_for_status()
 result=r.json();print(json.dumps({'success':result.get('success'),'successCount':result.get('successCount'),'errors':result.get('errors',[])},indent=2))
 if not result.get('success'):raise SystemExit('Dashboard import failed')
 c.post(KB+'/api/kibana/settings',headers={'kbn-xsrf':'true'},json={'changes':{'defaultIndex':'retail-ot','defaultRoute':'/app/dashboards#/view/retail-overview'}}).raise_for_status()
 print('Default overview and five endpoint dashboards imported successfully')
if __name__=='__main__':main()
