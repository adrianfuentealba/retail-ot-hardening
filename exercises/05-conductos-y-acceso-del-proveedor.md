# 05 · Conductos y acceso del proveedor

Objetivo: laboratorio, no PPTX.

## Objetivos medibles

- Distinguir segmentos reales y excepción administrativa
- Mantener Read mientras se bloquea Write y rol proveedor

## Preparación común

1. En el anfitrión, iniciar `docker compose up -d` desde este repositorio. Esperar la inicialización de ELK y verificar `docker compose ps`.
2. Abrir [portal](http://127.0.0.1:8090) y [Kibana](http://127.0.0.1:5601/app/dashboards#/view/retail-overview).
3. En el portal, **Restablecer aula** antes del taller. Este botón restablece proceso y políticas de las cinco estaciones; no borra eventos ni PCAP. `labctl reset` desde una estación solo restablece ese endpoint, no todo el proceso.
4. Abrir la estación indicada abajo con noVNC → escritorio → doble clic **Terminal del laboratorio**. La consola web es una alternativa de lista blanca, no una shell. Copiar cada bloque por separado; esperar respuesta antes del siguiente.
5. Asignar operador/ingeniería, observador SOC y responsable de evidencia. La maqueta es compartida por la cohorte; no ejecutar dos escenarios simultáneos sin coordinación.

```sh
labctl status
labctl inventory
labctl baseline
```

**Por qué:** el estado inicial, host y hora hacen posible una comparación reproducible. Un baseline no es un certificado de seguridad.

**Estación de ejecución:** `ws-vendor`. Abrir desde pestaña Estaciones del portal.

## Acciones paso a paso

### Paso 1. Observar lateralidad emulada

Dos targets internos fijos via APIs de aula: engineering y hmi. Esto NO prueba ruta de movimiento lateral OT productiva.

```sh
labctl simulate lateral
```

**Resultado esperado:** Marcadores benignos llegan a dos endpoints; respuestas identifican sus hosts.

**Observar:** escena fija a la izquierda; respuesta del comando; dataset correcto en Kibana. Comparar antes/después sin cambiar host ni objetivo.

### Paso 2. Limitar el acceso de proveedor

Política de aula exige hostname ws-engineering para el Write de deshielo. Es guard de rol, no MFA ni identidad humana robusta.

```sh
labctl harden access
```

**Resultado esperado:** access=true en todos los endpoints.

**Observar:** escena fija a la izquierda; respuesta del comando; dataset correcto en Kibana. Comparar antes/después sin cambiar host ni objetivo.

### Paso 3. Probar desde proveedor

La solicitud se rechaza antes del protocolo por rol.

```sh
labctl simulate defrost
```

**Resultado esperado:** blocked por rol; no atribuirlo a Suricata.

**Observar:** escena fija a la izquierda; respuesta del comando; dataset correcto en Kibana. Comparar antes/después sin cambiar host ni objetivo.

### Paso 4. Filtrar gateway

Deny FC06 en proxy de aplicación; mantener FC03. Guard network se aplica en agentes.

```sh
labctl harden network
```

**Resultado esperado:** network=true; rechazos de gateway observables.

**Observar:** escena fija a la izquierda; respuesta del comando; dataset correcto en Kibana. Comparar antes/después sin cambiar host ni objetivo.

### Paso 5. Repetir lateralidad

Los dos agentes objetivo rechazan los marcadores.

```sh
labctl simulate lateral
```

**Resultado esperado:** Dos resultados blocked.

**Observar:** escena fija a la izquierda; respuesta del comando; dataset correcto en Kibana. Comparar antes/después sin cambiar host ni objetivo.

## Consultas Linux/osquery de verificación

Estas consultas se ejecutan en la terminal de **la estación observada**, no en SOC para inspeccionar mágicamente otro contenedor. `osqueryi` consulta el endpoint local. `osqueryd` de los cinco endpoints envía sus propias consultas programadas a ELK.

```sh
osqueryi --json "SELECT name,version,platform FROM os_version;"
osqueryi --json "SELECT pid,name,path,cmdline FROM processes WHERE cmdline LIKE '%retail-%';"
osqueryi --json "SELECT uid,username,shell FROM users;"
osqueryi --json "SELECT pid,port,address,protocol FROM listening_ports;"
osqueryi --json "SELECT path,mode,uid,gid FROM file WHERE path='/home/student/lab/controller.conf';"
osqueryi --json "SELECT path,sha256 FROM hash WHERE path='/home/student/lab/firmware.bin';"
```

Consultas manuales osqueryi son independientes de las consultas osqueryd de `processes`, `downloads`, `config_integrity`, `inventory` y `listeners`. El intervalo programado es 5 s para cambios de proceso/archivo; sumar latencia de collector/Logstash y refresco de Kibana. Registrar resultado vacío como **no observado**, no como ausencia absoluta de actividad.

## Verificación Kibana

En Discover elegir data view `retail-ot-*`, últimos 15 minutos y refresco 5 segundos. Copiar KQL, no SQL:

```kql
event.dataset : "osquery" AND host.name : "ws-vendor"
```

```kql
event.dataset : "lab.endpoint" AND host.name : "ws-vendor"
```

```kql
event.dataset : "lab.control"
```

```kql
event.dataset : "suricata" AND event.action : "alert"
```

`lab.control` usa host PLC, gateway o endpoint solicitante según fuente; no filtrar todo por HMI. Suricata usa host `sensor`. Los eventos osqueryd de configuración contienen `osquery.columns` y nombre `config_integrity`.

## Evidencia y cierre

En la estación:

```sh
labctl evidence
```

En portal: **Exportar evidencia** y **Paquetes → Descargar segmento PCAP real**. En Kibana guardar resultados filtrados por host y ventana de tiempo. Registrar: comando, endpoint, hora UTC, resultado permitido/bloqueado, efecto térmico, fuente de evidencia y limitación. Verificar criterios antes de marcar éxito; ejecutar un botón no equivale a aprobar.

Después de guardar la evidencia, usar **Restablecer aula** para la siguiente práctica. No ejecutar `docker compose down -v`: elimina volúmenes y evidencia. `docker compose down` detiene sin eliminar esos volúmenes.

## Límites y uso responsable

Solo aula aislada y autorizada. No conectar a PLC, HMI, RTU o tiendas reales. No hay malware operativo, explotación, cifrado, escaneo ni direcciones externas configurables. Los artefactos de entrenamiento están bajo `/home/student/lab`. Una simulación de 45 segundos no demuestra una APT.

El hardening implementado es acotado: permisos reales de un archivo Linux, guard de ejecución del agente, validación de consigna en PLC ficticio, gateway de aplicación y variable OPC UA de solo lectura. No equivale a SELinux/AppArmor, firewall transparente, GPO, protección endpoint completa, SIS ni certificación IEC 62443. La red de administración pedagógica permite acciones fuera de banda y está declarada como excepción.

## Solución razonada

La resolución completa es la secuencia de **Acciones paso a paso**, seguida de los criterios abajo: comprobar estado inicial, reproducir de manera benigna, aplicar exactamente la barrera descrita, repetir la misma acción sin cambiar el objetivo y comparar resultados. Si una salida no coincide, conservar el error y consultar `docs/operacion-y-diagnostico.md`; no sustituir evidencia por el resultado esperado.

La validez requiere dos fuentes cuando corresponda: respuesta de protocolo/PCAP para control; permisos o SQL osquery para endpoint; EVE Suricata para firmas. `lab.endpoint` y `lab.control` son logs de aplicación, no detecciones independientes de osquery o Suricata.

## Criterios de éxito

- Guard de rol bloquea vendor
- Gateway bloquea FC06 desde engineering
- FC03 sigue capturándose
- Targets laterales blocked

## MITRE / IEC 62443

**MITRE ATT&CK for ICS:** Lateralidad representada mediante marcadores; no exploit. T0836 solo en órdenes reales del proceso.

**IEC 62443:** FR1, FR2 y FR5, a nivel de requisitos fundacionales y diseño pedagógico. Definir SL-T por análisis de riesgo de cada zona. SL-A exige evaluación y evidencia más amplias; no se obtiene por siete botones.

## Antipatrón contextual y qué hacer el lunes

Ejemplo para discutir en plantas y tiendas chilenas, no observación atribuida a una organización: acceso compartido del proveedor sin ventana, copia de configuración sin hash y cambios del HMI sin validación del proceso. El lunes: inventariar dueño del activo, documentar cambio y reversión, probar primero fuera de producción y asignar una ventana con operaciones. No bloquear remotamente una planta sin evaluación de seguridad física.

## Tutorial complementario validado de observabilidad

Ver [cinco estaciones, osquery y Elastic paso a paso](../docs/tutorial-observabilidad.md) para conexión, búsquedas KQL, evidencia independiente, prueba de escritura como estudiante y dashboards por endpoint. No ejecutar pruebas automáticas en paralelo con un taller activo.
