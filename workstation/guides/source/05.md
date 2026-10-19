# 05 · Conductos y acceso del proveedor

> **Guía local del laboratorio Retail OT — borrador ampliado.** Este taller se ejecuta únicamente en la maqueta aislada. La guía es autosuficiente: no se debe volver al portal para buscar instrucciones.

## Ficha de ejecución

- **Estación principal (carril proveedor):** `ws-vendor`, abierta en noVNC.
- **Estación de verificación de protocolo (carril ingeniería):** `ws-engineering`, solo para las pruebas Modbus del paso 4. Volver después a `ws-vendor`.
- **Interfaz de instrucciones:** Firefox local en el escritorio de la estación. Abrir la guía local con `labctl guides`; no usar la consola web del portal como shell.
- **Terminal:** cada bloque se pega en **Terminal del laboratorio** de la estación indicada. En noVNC se puede usar el botón Copiar de esta guía y `Ctrl+Shift+V` en xfce4-terminal. No copiar el prompt `$`, salidas JSON ni el portapapeles del anfitrión.
- **Participantes:** operador, observador SOC y responsable de evidencia. La maqueta es compartida: no ejecutar dos escenarios a la vez.

### Qué se demostrará

1. Los marcadores laterales usan dos destinos internos fijos (`ws-engineering` y `ws-hmi`); no son una ruta de movimiento lateral OT productiva.
2. `harden access` aplica un guard global a los endpoints, pero la excepción de escritura de proceso solo permite la ruta `simulate defrost` cuando el hostname es `ws-engineering`. Es un control de rol/hostname, **no** MFA ni una prueba de identidad humana.
3. `harden network` pone un rechazo de escrituras en el gateway y guardas de marcadores en los agentes. FC06 y FC16 quedan bloqueados; FC03 de lectura permanece disponible.
4. La misma acción lateral, con los mismos objetivos, cambia de dos resultados `success` a dos resultados `blocked`.

### Alcance local frente a global

| Acción | Dónde se inicia | Alcance real | Qué no demuestra |
|---|---|---|---|
| `labctl status`, `inventory`, `baseline`, `evidence` | Estación de la terminal | Endpoint local | No inspecciona mágicamente otro contenedor |
| `labctl reset` | Estación de la terminal | Solo ese endpoint; conserva evidencia | No restablece PLC, gateway ni las otras estaciones |
| `labctl reset-all` | Terminal de la estación principal, con coordinación | Aula completa: proceso, gateway, endpoints y políticas; conserva evidencia | No debe ejecutarse durante la sesión de otro alumno |
| `labctl harden access` | `ws-vendor` en esta guía | Estado del panel y guardas de los cinco endpoints | No añade MFA ni gate universal a todos los comandos Red/Purple Team |
| `labctl harden network` | `ws-vendor` en esta guía | Política global del gateway y guardas de lateralidad de los endpoints | No elimina conectividad ni convierte el gateway en un firewall transparente |
| `labctl simulate lateral` | `ws-vendor` | Solo marcadores hacia los dos destinos fijos del laboratorio | No prueba explotación, credenciales ni una ruta productiva |
| `labctl redteam ...` | `ws-engineering` en el paso 4 | Ejercicios educativos con gateway/PLC fijos | No permite IP, puerto, payload o ráfaga elegibles por el alumno |

El control global no se debe confundir con un cambio local: volver a noVNC de `ws-hmi` y ejecutar `labctl reset` no deshace `harden access` o `harden network` en el aula.

## Preparación limpia y coordinada

### 0.1 Abrir la guía local y comprobar el carril

En noVNC de `ws-vendor`, abrir **Terminal del laboratorio** y ejecutar:

```sh
labctl guides
```

**Propósito:** abrir la copia HTML/local de la guía y trabajar desde Firefox, sin depender del portal para las instrucciones.

**Resultado esperado y significado:** Firefox muestra las guías locales del laboratorio. La salida exacta de apertura puede variar; no es una evidencia de hardening.

**Segunda evidencia:** el título de esta guía aparece en el listado local de guías. Si el comando solo imprime ayuda o no abre Firefox, no sustituirlo por la consola del portal: mantener la terminal de noVNC y avisar al responsable de aula.

### 0.2 Identidad, host y estado inicial

Ejecutar cada comando por separado en `ws-vendor`:

```sh
hostname
```

```sh
id
```

```sh
labctl status
```

```sh
labctl inventory
```

```sh
labctl baseline
```

**Propósito:** dejar registrado qué estación y usuario ejecutan la práctica, y obtener una línea base local antes de tocar políticas.

**Resultado esperado y significado:**

- `hostname` debe identificar `ws-vendor`.
- `id` debe mostrar el usuario de laboratorio `student` y sus grupos reales; no se requiere ni se debe pedir `sudo` general.
- `labctl status` devuelve un objeto del endpoint con `host`, `role`, `policies`, `mode` y la versión disponible de `osquery`. Tras un aula limpia, las políticas del endpoint (`os`, `application`, `network`, `access`, `supply-chain`) deben estar desactivadas.
- `labctl inventory` devuelve `source: osqueryi` y filas del inventario local.
- `labctl baseline` devuelve `rows` de osquery para `/home/student/lab/controller.conf`; en una línea base nueva el archivo es legible por el estudiante y tiene modo `0666`. Los UID numéricos pueden variar según la imagen; no inventarlos.

La salida de `baseline` es evidencia manual de `osqueryi`, no un certificado de seguridad. Un resultado vacío significa **no observado**, no ausencia absoluta de actividad.

**Segunda evidencia:** ejecutar el nuevo comando de solo lectura:

```sh
labctl classroom-state
```

Debe mostrar el gemelo del aula con `process`, `gateway`, `endpoints`, `policies`, `events`, `history`, `last_update` y `errors`. Tras una preparación limpia, comprobar que el proceso está nominal, que `policies.network` y `policies.access` son falsas y que los cinco endpoints están disponibles. No buscar un campo `event.outcome` en toda la respuesta: `classroom-state` es un estado agregado, no el wrapper de todos los comandos.

**Si difiere:** conservar las salidas, no comenzar el ataque emulado y no corregirlo con `labctl reset` en otra estación. Si el hostname no es `ws-vendor`, cambiar al noVNC correcto y repetir la identificación. Si hay una política global activa, un endpoint `unavailable`, un error del proceso o un gateway ya endurecido, coordinar un reset de aula antes de continuar.

### 0.3 Restablecimiento de aula

El responsable anuncia el reset a la cohorte y confirma que no hay otra sesión activa. Desde la terminal de `ws-vendor`, ejecutar el comando nuevo:

```sh
labctl reset-all
```

**Propósito:** empezar con proceso, gateway, endpoints y políticas coordinados. Este reset mantiene la evidencia existente; no borrar volúmenes ni evidencias para “limpiar”.

**Resultado esperado y significado:** respuesta de reset de aula completado. El texto exacto y los campos pueden variar según el wrapper implementado por el padre; no asumir que la respuesta es un evento de endpoint.

**Segunda evidencia:** repetir:

```sh
labctl classroom-state
```

y luego:

```sh
labctl status
```

Confirmar de nuevo el estado nominal y las políticas desactivadas en `ws-vendor` y en el estado agregado.

**Si difiere:** no llamar a `labctl reset` en cada estación como sustituto. Un `reset-all` parcial o fallido puede haber dejado políticas aplicadas en algunos destinos; conservar la respuesta y coordinar con el responsable. No ejecutar `docker`, `docker compose down -v`, `git` ni comandos de firewall desde la estación.

## Acciones paso a paso

### Paso 1 — Observar la lateralidad emulada antes de la barrera

**Host y propósito.** Permanecer en `ws-vendor`. Observar la acción de referencia antes de endurecer, sin cambiar el origen ni los objetivos.

Ejecutar:

```sh
labctl simulate lateral
```

**Resultado esperado y significado:** la salida contiene `targets` con dos resultados, uno para `ws-engineering` y otro para `ws-hmi`; en una línea base limpia cada resultado tiene `event.outcome: success` y un mensaje de marcador benigno. El agente crea solo el marcador de entrenamiento; no hay exploit ni robo de credenciales. La respuesta no es un benchmark de red.

**Segunda evidencia:**

```sh
labctl classroom-state
```

Usar el estado para confirmar que ambos endpoints están disponibles y que `endpoints.ws-engineering.policies.network` y `endpoints.ws-hmi.policies.network` siguen desactivadas. Para confirmar los resultados de cada destino en observabilidad, en la misma Firefox local se puede consultar Discover con estos filtros separados:

```kql
event.dataset : "lab.endpoint" AND event.action : "lateral" AND host.name : "ws-engineering"
```

```kql
event.dataset : "lab.endpoint" AND event.action : "lateral" AND host.name : "ws-hmi"
```

**Si difiere:**

- Si aparece `unreachable`, es indisponibilidad del destino, no un bloqueo. No marcar el control como eficaz.
- Si aparece `blocked` antes de aplicar políticas, el aula no está limpia o una política global ya estaba activa; conservar la salida y volver a `classroom-state`.
- Si solo un destino tiene resultado, no completar el criterio por inferencia: revisar disponibilidad y los dos eventos por host.

### Paso 2 — Limitar el acceso del proveedor

**Host y propósito.** Volver a comprobar que se está en `ws-vendor`. Activar el guard global que exige `ws-engineering` para la ruta educativa de escritura de deshielo.

Ejecutar:

```sh
labctl harden access
```

**Resultado esperado y significado:** la respuesta directa es un evento de control con `event.action: harden-access` y `event.outcome: success`. La salida directa **no tiene por qué contener** un campo `access: true`; no usar la ausencia de ese campo como diagnóstico. El panel marca `access` y activa el guard de los cinco agentes.

**Segunda evidencia:**

```sh
labctl classroom-state
```

Comprobar `policies.access: true`
También deben figurar `endpoints.ws-vendor.policies.access`, `endpoints.ws-engineering.policies.access`, `endpoints.ws-hmi.policies.access`, `endpoints.ws-corporate.policies.access` y `endpoints.ws-soc.policies.access` como verdaderas. La respuesta de `harden access` puede ser un evento directo y `classroom-state` puede ser un objeto agregado: son wrappers distintos.

Como comprobación local adicional, sin cambiar de host:

```sh
labctl status
```

Debe mostrar `policies.access: true` en `ws-vendor`. El estado local demuestra el agente de esta estación; el agregado demuestra el alcance global.

**Si difiere:**

- Si el evento no tiene `outcome: success`, conservar la salida y no asumir que se aplicó la política.
- Si `ws-vendor` es verdadero pero algún endpoint es `unavailable` o tiene `access: false`, el cambio global quedó incompleto o no es observable todavía. No sustituirlo por resets locales; consultar al responsable y guardar `classroom-state`.
- Si `access` sigue falso en todo el aula, comprobar que la acción se ejecutó desde el agente real de `ws-vendor` y que el panel está disponible. No atribuir todavía el futuro bloqueo a esta barrera.

**Qué controla realmente:** solo la ruta `simulate defrost` compara el hostname solicitante con `ws-engineering`. No es una identidad humana fuerte, no es MFA y no es un gate universal para nuevas órdenes Red/Purple Team.

### Paso 3 — Probar la solicitud del proveedor

**Host y propósito.** Permanecer en `ws-vendor` y repetir la acción del proveedor sin cambiar el objetivo. Probar que la solicitud se detiene en el guard de rol antes de llegar al protocolo.

Ejecutar:

```sh
labctl simulate defrost
```

**Resultado esperado y significado:** la respuesta es un evento con `event.action: defrost`, `event.outcome: blocked`, `host.name: ws-vendor` y un mensaje equivalente a `Training role gate: engineering only process write`. Al bloquearse en el panel por rol, la respuesta no debe contener un campo `packet`: no se llegó a Modbus ni se debe atribuir el resultado a Suricata.

**Segunda evidencia:**

```sh
labctl classroom-state
```

Buscar en `events`/estado el evento de `defrost` para `ws-vendor` y confirmar que `policies.access` permanece verdadera. En Discover, si se usa la observabilidad opcional de la misma Firefox:

```kql
event.dataset : "lab.control" AND event.action : "defrost" AND host.name : "ws-vendor"
```

La captura puede contener lecturas FC03 generadas por el polling del aula; por eso no usar la mera presencia de un PCAP para afirmar que esta orden alcanzó el gateway.

**Si difiere:**

- Si el resultado es `success` o aparece `packet`, detenerse: revisar `hostname`, `labctl status` y `classroom-state.policies.access`. Una ejecución en `ws-engineering` no es la prueba de proveedor.
- Si `access` es falso, repetir primero el paso 2 solo después de coordinar y conservar la salida fallida.
- Si hay `503`, endpoint no disponible o error de panel, registrar la indisponibilidad; no convertirla en `blocked`.
- Si el evento es `blocked` pero el mensaje corresponde a otra barrera, anotar la barrera efectiva. Este paso pretende demostrar el guard de rol, no una firma de red.

### Paso 4 — Filtrar escrituras en el gateway sin quitar las lecturas

Este paso separa dos hosts. La política se aplica globalmente desde `ws-vendor`; las solicitudes Modbus controladas se comprueban desde una terminal real de `ws-engineering` para conservar la procedencia declarada en la práctica. No ejecutar `labctl reset` al cambiar de noVNC.

#### 4.1 Activar la política global de red

**Host y propósito.** Volver a `ws-vendor`. Activar la denegación de escrituras en el gateway y el guard de marcadores de los agentes.

Ejecutar:

```sh
labctl harden network
```

**Resultado esperado y significado:** la respuesta es un evento con `event.action: harden-network` y `event.outcome: success`. La salida directa puede no incluir `network: true`; la política real se comprueba en el estado agregado. El gateway queda configurado para rechazar FC06 y FC16, mientras que el endpoint network guard bloquea marcadores laterales.

**Segunda evidencia:**

```sh
labctl classroom-state
```

Comprobar `policies.network: true`, `gateway.deny_writes: true` y `endpoints.*.policies.network: true` para los endpoints disponibles. El contador `blocked_writes` es acumulativo y puede incluir pruebas anteriores; registrar su valor observado, no inventar una diferencia.

**Si difiere:** si algún endpoint está `unavailable`, el gateway no tiene `deny_writes: true` o el evento no fue `success`, conservar el estado y no pasar a la prueba de protocolo. La acción puede haber alcanzado algunos componentes antes de fallar; no inferir que la aplicación fue atómica. Coordinar la corrección global.

#### 4.2 Cambiar al carril de ingeniería y comprobar identidad

Abrir el noVNC de `ws-engineering`, abrir su **Terminal del laboratorio** y ejecutar por separado:

```sh
hostname
```

```sh
id
```

```sh
labctl status
```

**Propósito:** comprobar que las pruebas de protocolo realmente salen del host de ingeniería y que el agente local está disponible.

**Resultado esperado y significado:** `hostname` identifica `ws-engineering`; `id` vuelve a mostrar el usuario local del laboratorio; `labctl status` muestra el endpoint disponible y `policies.network: true`. Los valores de versión, PID, timestamp y contadores son variables y no se deben fabricar.

**Segunda evidencia:** `labctl classroom-state` desde esta terminal debe mostrar el mismo `gateway.deny_writes: true` y el endpoint `ws-engineering` con `network: true`.

**Si difiere:** no ejecutar las pruebas como si fueran de ingeniería. Volver al noVNC correcto, repetir la comprobación y, si el endpoint está indisponible, guardar el estado como fallo de disponibilidad.

#### 4.3 Probar FC06 (Write Single Register)

**Propósito:** verificar el rechazo de una escritura FC06 en el gateway después del hardening.

Ejecutar en `ws-engineering`:

```sh
labctl redteam modbus-write
```

**Resultado esperado y significado:** la respuesta contiene un evento `lab.control` con acción equivalente a `redteam-modbus-write` y `outcome: blocked`. En `result`, la respuesta real TCP tiene `exception: true` y la fuente indica que fue una solicitud/respuesta Modbus a través del gateway fijo. No hay IP, puerto ni payload libre: es la operación educativa fija del código.

**Segunda evidencia:** en la misma terminal:

```sh
curl -sS http://panel:8000/api/packets
```

Correlacionar el paquete FC06 por la ventana UTC y la respuesta de excepción. Como fuente adicional, Discover puede filtrar:

```kql
event.dataset : "lab.control" AND event.action : "gateway-write" AND host.name : "gateway"
```

El evento del gateway debe mostrar una decisión `blocked` para FC06. La respuesta de `labctl` y el evento del gateway son fuentes distintas; `lab.endpoint` no sustituye a ninguna de ellas.

**Si difiere:**

- Si `outcome` es `success` o `result.exception` es falso, no marcar FC06 como bloqueado. Confirmar que se ejecutó `harden network`, que `gateway.deny_writes` es verdadero y que la terminal es `ws-engineering`.
- Si no hay paquete, usar el evento del gateway y el estado; una ausencia de captura no transforma un éxito en un bloqueo.
- Si hay `503`, `unreachable` o respuesta truncada, es un problema de servicio/captura, no evidencia de control eficaz.

#### 4.4 Probar FC16 (Write Multiple Registers)

**Propósito:** comprobar que el mismo guard global cubre la variante de escritura múltiple, sin confundirla con una ráfaga.

Ejecutar en `ws-engineering`:

```sh
labctl redteam modbus-fc16
```

**Resultado esperado y significado:** el evento de control equivalente a `redteam-modbus-fc16` tiene `outcome: blocked` y `result.exception: true`. La operación está fijada a una escritura educativa de un registro; no es un flood ni una prueba de denegación de servicio.

**Segunda evidencia:** volver a consultar:

```sh
curl -sS http://panel:8000/api/packets
```

y filtrar en Kibana el mismo evento `gateway-write` por la ventana UTC, identificando el mensaje FC16 y `event.outcome: blocked`.

**Si difiere:** si FC16 pasa mientras FC06 está bloqueado, guardar ambas respuestas y revisar `gateway.deny_writes` y el evento del gateway. No concluir que la red está endurecida por una sola función. Si el resultado es `unreachable`, no llamarlo `blocked`.

#### 4.5 Comprobar que FC03 Read sigue permitido

**Propósito:** demostrar la diferencia entre filtrar escrituras y eliminar la conectividad del gateway.

Ejecutar en `ws-engineering`:

```sh
labctl redteam baseline
```

**Resultado esperado y significado:** el evento equivalente a `redteam-baseline` tiene `outcome: success`; `result.function` es `3`, `result.exception` es falso y la fuente describe una respuesta TCP real. La lectura sigue permitida. Que el contador de lecturas cambie no es una alarma: el panel también genera polling.

**Segunda evidencia:**

```sh
curl -sS http://panel:8000/api/packets
```

Correlacionar la solicitud FC03 y su respuesta normal por el timestamp y el resultado hexadecimal devuelto por `labctl`. En Kibana, `event.dataset: "lab.control"` puede mostrar el evento del ejercicio; la traza de paquetes es la fuente específica del protocolo.

**Si difiere:** si FC03 se bloquea, el gateway puede estar indisponible o se aplicó una política distinta de la prevista. Revisar `gateway.deny_writes`, conservar el PCAP/paquetes y no declarar “lectura preservada”. Si FC03 pasa pero la respuesta no es del gateway fijo, detenerse: no usar destinos externos.

Al terminar las tres pruebas, cerrar la terminal de `ws-engineering` y volver al noVNC de `ws-vendor`. No restablecer el endpoint de ingeniería: la política es global y la siguiente prueba necesita los guards activos.

### Paso 5 — Repetir exactamente la lateralidad

**Host y propósito.** Volver a `ws-vendor`. Repetir el mismo comando del paso 1, con los mismos destinos fijos, después de `harden access` y `harden network`.

Ejecutar:

```sh
labctl simulate lateral
```

**Resultado esperado y significado:** `targets` contiene dos resultados, para `ws-engineering` y `ws-hmi`; cada resultado tiene `event.outcome: blocked` y un mensaje de guard de allowlist interna. La salida superior no necesariamente tiene un `outcome` global: leer cada elemento de `targets`. La acción `lateral-attempt` local puede registrarse como intento realizado, pero eso no contradice que ambos destinos hayan bloqueado el marcador.

**Segunda evidencia:**

```sh
labctl classroom-state
```

Confirmar que los dos endpoints siguen disponibles y con `policies.network: true` (y `access: true`). En Discover, separar los hosts; no filtrar todo por HMI:

```kql
event.dataset : "lab.endpoint" AND event.action : "lateral" AND host.name : "ws-engineering"
```

```kql
event.dataset : "lab.endpoint" AND event.action : "lateral" AND host.name : "ws-hmi"
```

**Si difiere:**

- Un resultado `success` indica que ese agente no tenía el guard aplicado o que se está observando otra ventana/host; no completar el criterio con el otro destino.
- `unreachable` significa indisponibilidad, no bloqueo.
- Si la salida tiene dos bloqueos pero `classroom-state` muestra una política falsa, conservar ambas fuentes y diagnosticar la discrepancia de observabilidad antes de concluir.

## Verificación local y observabilidad

### Consultas Linux/osquery en la estación observada

Estas consultas se ejecutan en la Terminal del noVNC del host observado. `osqueryi` es una consulta manual e independiente de `osqueryd`; no esperar que el valor, PID o timestamp de una consulta manual coincida con el siguiente registro programado.

Sistema del endpoint:

```sh
osqueryi --json "SELECT name,version,platform FROM os_version;"
```

**Resultado y significado:** filas de la versión local; confirma qué endpoint se consultó, no el estado del gateway. Si está vacío, registrar `no observado`.

Procesos del laboratorio:

```sh
osqueryi --json "SELECT pid,name,path,cmdline FROM processes WHERE cmdline LIKE '%retail-%';"
```

**Resultado y significado:** lista procesos locales cuyo comando contiene `retail-`. En este taller no se ejecuta malware real; una fila, si apareciera por otro ejercicio, es solo un proceso de entrenamiento. No inventar PID.

Usuarios:

```sh
osqueryi --json "SELECT uid,username,shell FROM users;"
```

**Resultado y significado:** cuentas y shells visibles en ese endpoint; no prueba autorización de proveedor en el panel.

Puertos en escucha:

```sh
osqueryi --json "SELECT pid,port,address,protocol FROM listening_ports;"
```

**Resultado y significado:** escucha local observada por osquery. No equivale a un escaneo de red.

Permisos de configuración:

```sh
osqueryi --json "SELECT path,mode,uid,gid FROM file WHERE path='/home/student/lab/controller.conf';"
```

**Resultado y significado:** evidencia local del modo/propietario del archivo. Para esta guía la línea base esperada es `0666`; el hardening de OS que convertiría el archivo en `0640 root:student` pertenece a otro control y no se debe atribuir a `harden network`.

Hash manual del firmware educativo:

```sh
osqueryi --json "SELECT path,sha256 FROM hash WHERE path='/home/student/lab/firmware.bin';"
```

**Resultado y significado:** hash observado en el endpoint consultado. No inventar el hash ni afirmar que `osqueryd` monitoriza `firmware.bin`: la consulta manual es una evidencia distinta de `config_integrity`.

Un resultado vacío en cualquiera de estas consultas es `no observado`, no una prueba de ausencia absoluta. Las consultas programadas del collector pueden tener latencia de cinco segundos más collector/Logstash y refresco de Kibana.

### Kibana opcional

La observación visual es opcional y se hace desde la misma Firefox local, usando el host interno, no `127.0.0.1`:

- Panel/estado: `http://panel:8000`.
- Kibana: `http://kibana:5601/app/dashboards#/view/retail-overview`.

En Discover seleccionar el data view `retail-ot-*`, una ventana reciente (por ejemplo, los últimos 15 minutos) y refresco de 5 segundos. Copiar KQL, no SQL. Filtros base:

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

`lab.control` puede tener como `host.name` a PLC, gateway o endpoint solicitante según la fuente; no filtrar todo por HMI. Suricata usa el host `sensor`. Los eventos osqueryd de configuración incluyen `osquery.columns` y el nombre `config_integrity`. Un bloqueo por rol del paso 3 no debe explicarse como una alerta Suricata.

## Evidencia entregable y cierre

### Guardar sin escribir en el collector

Antes de cerrar la sesión, y **antes del reset final**, desde la terminal de cada carril guardar la evidencia en el directorio del alumno:

```sh
mkdir -p ~/lab/evidencias/taller-05
```

En `ws-engineering`, después de las pruebas Modbus:

```sh
labctl evidence > ~/lab/evidencias/taller-05/ws-engineering-evidence.json
```

En `ws-vendor`, después del paso 5:

```sh
labctl evidence > ~/lab/evidencias/taller-05/ws-vendor-evidence.json
```

Desde `ws-vendor`, guardar el estado agregado y los paquetes disponibles:

```sh
labctl classroom-state > ~/lab/evidencias/taller-05/classroom-state-final.json
```

```sh
curl -sS http://panel:8000/api/packets > ~/lab/evidencias/taller-05/modbus-packets.json
```

Los comandos anteriores guardan datos generados, no hashes/PIDs inventados. Registrar junto a ellos: comando, hostname, usuario, hora UTC que aparece en los eventos, resultado permitido/bloqueado, efecto observable, fuente exacta y limitación. No redireccionar a `/evidence` del collector; la ruta `/evidence/osquery/osqueryd.results.log` que pueda aparecer en `labctl evidence` es solo una referencia de lectura del agente.

Si se necesita un PCAP real, usar únicamente el endpoint fijo del panel y solo si está listo; un `404 Capture is not yet ready` se registra como captura no disponible, no como PCAP vacío ni como prueba de bloqueo. No usar capturas de pantalla inventadas.

### Criterios de éxito

| Criterio | Evidencia mínima | Significado y límite |
|---|---|---|
| Lateralidad de referencia | Paso 1: dos destinos fijos observados | Solo marcador del training network; no lateralidad productiva |
| Guard de proveedor | Paso 2 estado global y paso 3 `defrost` de `ws-vendor` bloqueado sin `packet` | Guard de hostname en una ruta; no MFA ni identidad humana robusta |
| FC06 bloqueado | Paso 4.3: excepción TCP, evento `gateway-write` bloqueado | Política de gateway en la maqueta; no firewall transparente |
| FC16 bloqueado | Paso 4.4: excepción TCP, evento de gateway bloqueado | Cubre la otra escritura fija; no es DoS |
| FC03 preservado | Paso 4.5: función 3 y respuesta normal | Lectura de este gateway educativo, no disponibilidad universal |
| Lateralidad después | Paso 5: `ws-engineering` y `ws-hmi` bloqueados por separado | Guardas de agentes; no elimina conectividad ni acciones administrativas fuera de banda |

### Solución razonada

La resolución correcta es comprobar el estado inicial, reproducir benignamente, aplicar exactamente la barrera, repetir la misma acción sin cambiar origen/objetivo y contrastar dos fuentes. Si una salida no coincide, conservarla y diagnosticar; nunca reemplazarla por la salida esperada.

### Restablecimiento final

Después de guardar la evidencia, anunciar a la cohorte el cierre y ejecutar desde `ws-vendor`:

```sh
labctl reset-all
```

**Propósito:** dejar proceso, gateway y endpoints listos para la siguiente práctica sin borrar la evidencia. Es una operación coordinada que afecta a otros alumnos. Si no hay autorización de aula o el comando no está disponible, no sustituirlo por una cadena de resets locales: dejar constancia y pedir al responsable que coordine el reset.

No ejecutar `docker compose down -v`: elimina volúmenes y evidencia. `docker compose down` tampoco es una acción de la terminal del laboratorio para resolver este taller.

## Límites, mapeo y uso responsable

- Solo aula aislada y autorizada. No conectar a PLC, HMI, RTU, gateway o tiendas reales.
- No hay malware operativo, explotación, cifrado, escaneo, direcciones externas configurables ni credenciales de producción. Los artefactos educativos están bajo `/home/student/lab`.
- Un marcador lateral y una simulación de proceso no prueban una APT. Una ejecución temporal de 45 segundos, si aparece en otro ejercicio, tampoco lo demuestra.
- El hardening de este taller está acotado a un guard de ejecución de agente, una política de gateway de aplicación y una lista de roles/hosts para una ruta fija. No equivale a SELinux/AppArmor, GPO, firewall de red transparente, protección endpoint completa, SIS ni certificación IEC 62443.
- La red de administración pedagógica permite acciones fuera de banda y es una excepción explícita del diseño; `harden network` no elimina esa excepción.
- El modelo de proceso y el PLC son ficticios y educativos; no calcular salud alimentaria real a partir de sus ticks o temperatura simulada.
- La referencia normativa del material incluye **MITRE ATT&CK for ICS**, **IEC 62443** y el contexto chileno de la **Ley 21.663**. Este ejercicio no acredita cumplimiento, SL-T/SL-A, certificación ni obligaciones de notificación a ANCI.

### MITRE ATT&CK for ICS / IEC 62443

La lateralidad de este taller está representada mediante marcadores hacia destinos internos fijos; no hay exploit. T0836 solo sería aplicable a órdenes reales del proceso, que aquí no existen.

El diseño se relaciona pedagógicamente con FR1, FR2 y FR5 de IEC 62443. El SL-T debe definirse mediante análisis de riesgo de cada zona y activo. SL-A requiere evaluación, diseño y evidencia mucho más amplios: no se obtiene pulsando estos controles ni observando siete eventos.

### Antipatrón contextual y acción posterior

Para discusión en plantas y tiendas chilenas, no como observación atribuida a una organización: acceso compartido de proveedor sin ventana, copia de configuración sin hash y cambios del HMI sin validación del proceso. El siguiente día hábil: identificar al dueño del activo, documentar cambio y reversión, probar primero fuera de producción y acordar una ventana con operaciones. No bloquear remotamente una planta sin evaluar la seguridad física.

El tutorial complementario de observabilidad se encuentra como `docs/tutorial-observabilidad.md` dentro del laboratorio. Es material de apoyo; este taller no depende de volver al portal ni de ejecutar pruebas automáticas en paralelo.
