# 04 · PLC: límites y protección del proceso

> **Borrador local del laboratorio Retail OT.** Esta guía es autosuficiente: se trabaja desde la **Terminal del laboratorio** de la estación noVNC indicada y se consulta esta copia local en Firefox. No es una presentación ni una receta para equipos reales.

## Portada y alcance

**Estación recomendada:** `ws-engineering` (rol `engineering`). Abra esa estación en noVNC, entre al escritorio y haga doble clic en **Terminal del laboratorio**. Mantenga esta guía abierta en Firefox local; el botón **Copiar** de la guía se pega en `xfce4-terminal` con `Ctrl+Shift+V`. Copie un bloque cada vez, sin copiar el prompt `$` ni una salida JSON a la shell.

Todos los comandos de las secciones operativas se ejecutan en esa terminal. No se debe cambiar de estación para que una orden parezca funcionar: el host desde el que se ejecuta forma parte de la evidencia. La maqueta es compartida; coordine con el operador de aula antes de cualquier acción global.

### Objetivos medibles

Al finalizar, el estudiante podrá:

1. identificar en una respuesta Modbus TCP el MBAP, la unidad, FC06, dirección `0` y valor solicitado `50`, sin inventar el identificador de transacción;
2. observar una primera escritura FC06 aceptada y su efecto térmico en el gemelo;
3. activar el interlock del PLC ficticio y repetir **la misma** escritura, obteniendo una excepción de protocolo `0x86/0x03` y consigna nominal `2`;
4. distinguir una barrera del PLC de un bloqueo del gateway, y una evidencia de aplicación de una captura/alerta independiente;
5. recopilar evidencia reproducible en `~/lab/evidencias/taller-04/` sin inventar PIDs, hashes, capturas ni resultados de Kibana.

### Límites de alcance

- `labctl simulate defrost` es una operación fija contra el proceso ficticio y el gateway interno; no acepta IP, puerto, payload ni destino libre.
- `labctl harden plc` aplica una política al proceso del aula, no un permiso Linux del endpoint. El interlock del modelo comparte la semántica con FC06, FC16 y Write OPC UA, pero este taller verifica FC06.
- `labctl reset` solo restablece las políticas del **endpoint actual**; no restablece PLC, gateway ni otras estaciones. `labctl reset-all` es una operación global de aula y conserva evidencia: solo se ejecuta con coordinación explícita.
- El PLC, la termodinámica y la cuarentena son un modelo educativo. No permiten concluir inocuidad alimentaria, seguridad de un SIS, cumplimiento normativo ni estado de un PLC/HMI real.

## Preparación común, host y fuentes

### 1. Abrir la guía local y fijar el contexto

**Propósito.** Confirmar que se está usando la guía local de esta estación y dejar explícito el host/usuario antes de tocar el proceso.

**Acción exacta — Terminal de `ws-engineering`:**

```sh
labctl guides
```

El comando `guides` es una comodidad local incluida en esta actualización: abre la guía HTML local, no el portal ni una shell web. Si no abre Firefox, continúe con la copia local ya abierta y no vuelva al portal para obtener instrucciones.

**Resultado esperado y significado.** Firefox muestra la guía local del taller 04 y la Terminal sigue siendo el lugar de ejecución. Que Firefox cargue la guía no prueba que el endpoint, PLC o gateway estén disponibles.

**Segunda evidencia.** En Firefox, la dirección debe ser la ruta local de la guía, no una página del portal. En la Terminal, compruebe el contexto en el paso siguiente.

**Si difiere.** No pegue comandos en una consola web del portal. Abra la Terminal del escritorio noVNC y use la copia local indicada por el coordinador; si `labctl guides` no existe todavía, es una dependencia del padre y no una razón para cambiar la ruta del laboratorio.

### 2. Preparar el aula con coordinación global

**Propósito.** Distinguir el host local de la estación y dejar el gemelo en una línea base compartida, sin borrar evidencia de otros alumnos.

**Antes de ejecutar.** Anuncie que se hará un reinicio global. Si otra práctica está activa, no ejecute `reset-all`; espere a una ventana coordinada. Esta guía no autoriza a afectar una sesión ajena.

**Acción exacta — primero contexto local:**

```sh
hostname
id
labctl status
```

**Resultado esperado y significado.** `hostname` identifica la estación (debe ser `ws-engineering`), `id` muestra el usuario de laboratorio (normalmente `student`, sin asumir UID), y `labctl status` devuelve JSON del endpoint actual: políticas locales, modo del archivo y estado del agente. El JSON puede ser un evento directo o un objeto de salud; no presuponga que siempre existe `.event.outcome`.

**Acción exacta — solo después de coordinar:**

```sh
labctl reset-all
```

`reset-all` está incluido en esta actualización. Restablece de forma coordinada el proceso, gateway, políticas y endpoints del aula; conserva la evidencia. No lo sustituya por `labctl reset` cuando se necesita limpiar el PLC.

**Segunda evidencia:**

```sh
labctl classroom-state
```

`classroom-state` está incluido en esta actualización; hace un GET de solo lectura a `/api/state` y conserva en JSON `process`, `gateway`, `endpoints`, `policies`, eventos e historial. La línea base debe mostrar, como mínimo, proceso nominal (`setpoint` `2`), `plc_guard=false` y políticas globales del gateway sin activar. La temperatura puede variar mientras el poll del modelo actualiza el estado; no convierta una lectura puntual en una captura inventada.

**Si difiere.**

- Si `hostname` no es `ws-engineering`, vuelva a la estación recomendada; no compense cambiando el host en el comando.
- Si `id` no corresponde al usuario de laboratorio, registre el resultado y no use `sudo`.
- Si el estado ya tiene `plc_guard`, gateway bloqueado o una consigna distinta, el aula no está limpia: coordine otro `reset-all`. No ejecute una secuencia encima de otra.
- Si `reset-all` todavía no existe, deténgase y comunique la dependencia al coordinador; `labctl reset` no es un sustituto global.

### 3. Verificar inventario y línea base local

**Propósito.** Comprobar que las consultas se hacen en el endpoint observado y conservar el punto de comparación antes del ataque benigno.

**Acción exacta — un comando por bloque:**

```sh
labctl inventory
```

```sh
labctl baseline
```

**Resultado esperado y significado.** `inventory` devuelve un JSON con `source` `osqueryi` y filas de `system_info`. `baseline` devuelve el resultado de una consulta manual al `controller.conf`, normalmente con un `event` de `lab.endpoint`, `rows` y `policies`. Son consultas del agente local, no una inspección mágica de otro contenedor.

La línea base vulnerable del archivo es modo `0666`, con propietario UID del usuario de laboratorio, si el endpoint acaba de ser restablecido. No sustituya el UID real por un valor supuesto: conserve las columnas que devuelva el comando.

**Segunda evidencia.** Ejecute en la misma Terminal:

```sh
labctl status
```

Compare el host y las políticas del estado con `baseline`. El intervalo programado de `osqueryd` y la consulta manual de `osqueryi` son fuentes distintas; un resultado vacío significa **no observado**, no ausencia absoluta.

**Si difiere.** Una lista `rows` vacía o un error de `osqueryi` indica problema del endpoint o consulta, no que el archivo no exista. Compruebe `hostname`, `id` y `labctl status`; no use `docker`, `sudo` ni una consulta contra `/evidence` para reemplazar la evidencia local.

## Acciones paso a paso

### 4. Reproducir el deshielo simulado y decodificar FC06

**Propósito.** Obtener el control previo a la barrera: una escritura Modbus TCP real a través del gateway interno y el efecto sobre el proceso.

**Acción exacta:**

```sh
labctl simulate defrost
```

**Resultado esperado y significado.** La salida es JSON con dos niveles relevantes:

- `event`: evento de aplicación `lab.control`, host solicitante `ws-engineering`, acción de deshielo y `outcome` `success` si la escritura fue aceptada;
- `packet`: `protocol` `Modbus TCP`, `function` `6`, `exception` `false`, `source` `actual TCP response` y un `hex` capturado. El identificador de transacción está en los bytes MBAP y es variable: no se debe escribir un TID predeterminado.

La PDU esperada contiene `06 00 00 00 32`: FC06, registro `0`, valor decimal `50` (`0x0032`). En la respuesta normal, el gateway reenvía la respuesta real del PLC. El calentador/deshielo se activa, el compresor deja de enfriar y la temperatura del gemelo empieza a subir al avanzar sus ciclos. La posible cuarentena depende de que la exposición cruce el umbral del modelo; no se afirma a partir de una única línea de salida.

**Segunda evidencia — estado de proceso, solo lectura:**

```sh
labctl classroom-state
```

Busque en `.process` `setpoint`, `heater`, `compressor`, `temperature`, `exposure` y `spoiled`. La respuesta del paquete prueba el intercambio; el estado del gemelo prueba el efecto modelado. Ninguna de las dos fuentes calcula seguridad alimentaria real.

**Segunda evidencia opcional — registro de paquetes del panel interno:**

```sh
curl -fsS http://panel:8000/api/packets
```

Este endpoint fijo devuelve los últimos paquetes registrados. Guarde la salida si contiene la escritura FC06; no cambie `panel:8000` por un destino externo.

**Si difiere.**

- Si `packet.exception` ya es `true`, revise `classroom-state`: puede existir una política global previa. No repita intentos a ciegas; coordine `reset-all` y vuelva a la línea base.
- Si el evento dice `blocked` pero el proceso no cambia, la escritura no fue aceptada; no describa un deshielo.
- Si falta `packet` o el `source` no es `actual TCP response`, la orden no produjo la respuesta de protocolo esperada. Conserve la salida y consulte `/api/packets`; no fabrique un hex ni una captura.
- Si la temperatura no cambia de inmediato, compare el estado después de que el poll del gemelo se actualice. El modelo está acelerado y no es un termómetro ni una predicción termodinámica.

### 5. Activar el interlock central del PLC ficticio

**Propósito.** Aplicar la contramedida semántica al valor de proceso, no solo ocultar o bloquear una función en el gateway.

**Acción exacta:**

```sh
labctl harden plc
```

**Resultado esperado y significado.** La salida es un evento directo con `event.action` `harden-plc` y `event.outcome` `success` (campos de evento en la forma que devuelva la CLI). El controlador activa `plc_guard` y devuelve la consigna nominal a `2`. El interlock implementado permite `0–6 °C`; el mapa del aula usa consignas enteras no negativas. Esta secuencia prueba el rechazo de `50 °C`, no una curva de aceptación completa ni valores negativos.

Esto es una barrera del proceso del aula: valida el valor en la lógica central y no deshace automáticamente una exposición ni libera stock ya puesto en cuarentena. No es SELinux/AppArmor, un SIS, un firewall transparente ni una certificación.

**Segunda evidencia:**

```sh
labctl classroom-state
```

Confirme en `.process` `plc_guard=true` y `setpoint=2`. Observe también `spoiled`, `exposure`, `heater` y `compressor`; conservar `spoiled=true` es correcto si ya se alcanzó el umbral del modelo.

**Si difiere.** Si el evento no es `success`, no avance al reintento: conserve la respuesta y revise conectividad del endpoint/PLC con `labctl status` y `classroom-state`. Si `plc_guard` sigue en `false`, la barrera no quedó aplicada. Si la temperatura o la cuarentena no vuelven atrás, no es un fallo del guard: el contrato del modelo indica que la cuarentena no se revierte con hardening.

### 6. Repetir exactamente la misma escritura

**Propósito.** Probar que la barrera rechaza el mismo valor y la misma ruta, sin cambiar atacante, host, función, registro ni destino.

**Acción exacta:**

```sh
labctl simulate defrost
```

**Resultado esperado y significado.** El JSON vuelve a tener `packet`, pero ahora `exception=true`; el `hex` de la respuesta termina en `86 03` cuando se muestra la trama completa: FC06 con el bit de excepción y código `0x03` de valor no aceptable. El evento de aplicación informa `outcome` `blocked`. El `setpoint` permanece en `2` y no se inicia un nuevo deshielo. Este rechazo lo origina el guard del PLC; si el gateway estuviera bloqueando globalmente, la causa sería distinta.

**Segunda evidencia:**

```sh
labctl classroom-state
```

Confirme `process.setpoint=2`, `process.plc_guard=true` y que `heater` no se activó por esta segunda orden. Para una segunda fuente de protocolo, ejecute:

```sh
curl -fsS http://panel:8000/api/packets
```

Busque un registro de función `6` con excepción. La captura debe provenir del endpoint fijo; no invente el TID ni el contenido de `hex`.

**Si difiere.**

- `exception=false`: compruebe primero que el paso 5 dejó `plc_guard=true`. Si no, vuelva a coordinar la línea base; no encadene más escrituras.
- `exception=true` pero no `86 03`: podría ser una política anterior del gateway, otra función o una trama incompleta. Compare `packet.source`, `function` y `/api/packets`; el objetivo de esta repetición es la excepción real del PLC.
- `outcome=blocked` con causa de gateway: la escritura fue detenida antes del PLC. Registre esa diferencia; no la presente como validación del interlock.
- El proceso muestra `spoiled=false`: no concluya que el ataque fue inocuo; la exposición puede no haber alcanzado el umbral o el aula pudo haberse reiniciado. Revise el historial y la secuencia registrada.

### 7. Confirmar la retención de cuarentena y recuperar el proceso

**Propósito.** Separar recuperación operativa de remediación de producto: recuperar el frío no rehabilita stock que el modelo ya marcó.

**Acción exacta — consultar antes de recuperar:**

```sh
labctl classroom-state
```

**Resultado esperado y significado.** El estado conserva `plc_guard=true`, consigna `2` y el indicador `spoiled` según la exposición alcanzada. Si la cuarentena ya es `true`, debe seguir siéndolo después de la recuperación; si aún es `false`, significa solamente que el umbral no fue observado.

**Acción exacta — después de guardar el estado:**

```sh
labctl recover
```

`recover` detiene marcadores benignos de los endpoints, pide al PLC ficticio volver al enfriamiento y conserva la cuarentena. No endurece por sí solo ni libera stock.

**Segunda evidencia:**

```sh
labctl classroom-state
```

Confirme evento de recuperación, compresor/enfriamiento en retorno y `spoiled` sin una transición implícita a `false`. La respuesta de `recover` es una fuente de aplicación; el estado de proceso es la comprobación del efecto.

**Si difiere.** Si `recover` informa éxito pero el PLC sigue sin actualizarse, conserve ambas salidas y revise `errors`/`last_update` de `classroom-state`. Si la cuarentena cambia a `false`, trátelo como discrepancia del aula y no como liberación válida; el modelo documentado no la revierte con `recover`.

## Verificación independiente en la estación

Estas consultas se ejecutan en la Terminal de **la estación observada**, no en SOC. `osqueryi` consulta el endpoint local; `osqueryd` de los cinco endpoints envía sus consultas programadas al collector. No hay que esperar que una consulta manual tenga el mismo instante o conjunto de filas que el evento programado.

### 8. Sistema, procesos y usuarios

**Propósito.** Registrar qué endpoint y qué procesos/usuarios eran observables, sin presentar un PID o una marca de tiempo como valor fijo.

**Acciones exactas, por separado:**

```sh
osqueryi --json "SELECT name,version,platform FROM os_version;"
```

```sh
osqueryi --json "SELECT pid,name,path,cmdline FROM processes WHERE cmdline LIKE '%retail-%';"
```

```sh
osqueryi --json "SELECT uid,username,shell FROM users;"
```

**Resultado esperado y significado.** `os_version` devuelve la versión del endpoint; `processes` puede mostrar un proceso benigno `retail-*` si existe en el momento de la consulta, o `[]` si no se observó; `users` devuelve las cuentas visibles. Los PIDs, filas y tiempos son variables y deben conservarse tal como salgan.

**Segunda evidencia:**

```sh
labctl status
```

Compare el host del estado y la disponibilidad de osquery con las consultas. Para procesos, una fila de `osqueryi` es una observación local, no prueba de que `osqueryd` la haya indexado ya.

**Si difiere.** Un conjunto vacío significa **no observado**. Si la consulta falla, registre el error y no lo reemplace con un PID inventado. No use `sudo` ni `docker` desde la estación.

### 9. Puertos locales y permisos de configuración

**Propósito.** Corroborar que la línea base del archivo y los listeners pertenecen al endpoint correcto.

**Acciones exactas:**

```sh
osqueryi --json "SELECT pid,port,address,protocol FROM listening_ports;"
```

```sh
osqueryi --json "SELECT path,mode,uid,gid FROM file WHERE path='/home/student/lab/controller.conf';"
```

**Resultado esperado y significado.** La primera consulta devuelve listeners visibles con sus campos reales. La segunda devuelve el archivo educativo y sus permisos/propietario actuales. Tras un reset de endpoint, el material conocido parte de `0666`; esta guía no sustituye la salida real por un modo o UID inventado.

**Segunda evidencia:**

```sh
stat -c '%a:%u:%g' /home/student/lab/controller.conf
```

La salida de `stat` debe coincidir con los campos de `osqueryi` interpretados como modo, UID y GID. Esta verificación no demuestra que el PLC haya validado la consigna: son barreras y fuentes distintas.

**Si difiere.** Si el archivo no existe o los valores no coinciden, confirme `hostname` y `id`, conserve ambas salidas y revise si una práctica de hardening del endpoint está activa. No ejecute `sudo chmod`.

### 10. Integridad de firmware educativo y diferencia de fuentes

**Propósito.** Registrar el hash actual del artefacto educativo sin afirmar un digest predeterminado ni atribuirlo a una detección de osqueryd.

**Acción exacta:**

```sh
osqueryi --json "SELECT path,sha256 FROM hash WHERE path='/home/student/lab/firmware.bin';"
```

**Resultado esperado y significado.** Debe aparecer, si la tabla puede observarlo, la ruta y el `sha256` que tenga **en ese instante**. Este taller no ejecuta `simulate firmware`; por ello no se espera una alteración producida por esta secuencia. Un hash manual es evidencia manual, no una prueba de que el schedule de `osqueryd` monitorice `firmware.bin`.

**Segunda evidencia:**

```sh
sha256sum /home/student/lab/firmware.bin
```

Compare el digest devuelto por ambos comandos, sin escribir el valor en la guía ni inventarlo. La igualdad solo muestra que las dos lecturas locales coinciden.

**Si difiere.** Si una consulta está vacía, registre `no observado`. Si los hashes difieren, repita la lectura una vez después de comprobar que el archivo no está cambiando y conserve el diagnóstico; no lo corrija editando el artefacto.

## Evidencia entregable

### 11. Guardar las fuentes sin tocar el collector

**Propósito.** Entregar una trazabilidad mínima: contexto, estado, eventos, paquetes y captura real, si está disponible. Los archivos se guardan en la ruta del alumno, no en `/evidence`.

**Acción exacta:**

```sh
mkdir -p ~/lab/evidencias/taller-04
```

```sh
hostname > ~/lab/evidencias/taller-04/hostname.txt
```

```sh
id > ~/lab/evidencias/taller-04/id.txt
```

```sh
labctl classroom-state > ~/lab/evidencias/taller-04/classroom-state.json
```

```sh
labctl evidence > ~/lab/evidencias/taller-04/labctl-evidence.json
```

```sh
curl -fsS http://panel:8000/api/packets > ~/lab/evidencias/taller-04/packets.json
```

Para intentar conservar la PCAP real del panel, sin crear una sustituta:

```sh
curl -fsS -o ~/lab/evidencias/taller-04/retail-ot-live.pcap http://panel:8000/api/capture
```

**Resultado esperado y significado.** La carpeta contiene los JSON/textos locales y, si `/api/capture` estaba listo, una PCAP servida por el panel. `labctl evidence` devuelve eventos recientes del endpoint y la referencia del log de `osqueryd`; no convierte esos eventos en detecciones independientes. No se debe escribir a `/evidence` ni copiar desde allí como si fuera la evidencia del alumno.

**Segunda evidencia.** En Firefox local, si se requiere inspección visual, abra el Kibana interno y use el data view `retail-ot-*`, ventana que incluya la ejecución y refresco manual. También se puede leer `/api/state` con `labctl classroom-state`; no es necesario volver al portal para saber qué comando sigue.

**Si difiere.** Si `/api/capture` devuelve `404` o `Capture is not yet ready`, conserve `packets.json` y la respuesta de protocolo; no fabrique una cabecera PCAP. Si `curl` no resuelve `panel`, compruebe que se usó la Terminal del laboratorio y el host fijo interno, no una terminal del anfitrión.

### 12. Consultas KQL y criterios de segunda fuente

**Propósito.** Separar las fuentes de aplicación, endpoint, PCAP y Suricata en vez de marcar éxito solo por haber pulsado un botón.

En Discover copie KQL, no SQL. Las consultas mínimas son:

```kql
event.dataset : "osquery" AND host.name : "ws-engineering"
```

```kql
event.dataset : "lab.endpoint" AND host.name : "ws-engineering"
```

```kql
event.dataset : "lab.control"
```

```kql
event.dataset : "suricata" AND event.action : "alert"
```

**Resultado esperado y significado.**

- `osquery` muestra telemetría programada del endpoint y puede llegar después de la consulta manual.
- `lab.endpoint` muestra eventos del agente local; no es una detección independiente de osquery.
- `lab.control` puede tener `host.name` de PLC, gateway o endpoint solicitante; no se debe filtrar todo por HMI.
- Suricata usa el host `sensor` y, para este escenario, debe poder correlacionarse con las firmas de escritura FC06 del laboratorio (SID `1000001`/`1000002` si aparecen en el evento).

**Segunda evidencia.** Para la decisión de protocolo use primero `packet`/`/api/packets` o la PCAP real; para el efecto use `classroom-state`; para firmas use el documento EVE de Suricata indexado. `lab.control` por sí solo no sustituye esas fuentes.

**Si difiere.** Una ausencia en Kibana puede ser latencia de collector/Logstash o ventana KQL incorrecta, no prueba de que el comando no ocurrió. Conserve hora UTC, host, consulta y respuesta local. No invente un evento, SID, hash o captura.

## Solución razonada y criterios de éxito

La solución completa es esta secuencia, con el aula coordinada: (1) fijar host y línea base; (2) ejecutar FC06 benigno y guardar su respuesta; (3) comprobar el efecto térmico del modelo; (4) aplicar `harden plc`; (5) repetir exactamente FC06; (6) verificar excepción `0x86/0x03`, consigna `2` y estado de cuarentena; (7) recuperar sin liberar stock; y (8) conservar dos fuentes de evidencia.

La práctica se considera técnicamente demostrada cuando se observan, en los datos reales de la sesión:

- una primera FC06 a registro `0` con valor `50` aceptada y una respuesta Modbus TCP no excepcional;
- una segunda FC06 equivalente rechazada por el PLC con función de excepción `0x86` y código `0x03`;
- `plc_guard=true` y consigna nominal `2` tras el hardening;
- PCAP/paquetes reales y, cuando estén indexadas, las alertas Suricata sid `1000001`/`1000002`;
- una explicación explícita de que una cuarentena ya activada permanece y no se calcula inocuidad a partir de ticks del simulador.

Si una salida difiere, el criterio correcto es conservarla y diagnosticarla; no sustituirla por el resultado esperado. `lab.endpoint` y `lab.control` son logs de aplicación, no fuentes independientes de osquery o Suricata.

## Alcance local frente a global

| Acción | Dónde se inicia | Alcance real | Qué no demuestra |
|---|---|---|---|
| `labctl status`, `inventory`, `baseline`, `detect`, consultas `osqueryi` | Terminal del endpoint actual | Ese endpoint/usuario | Estado de otras estaciones o del PLC |
| `labctl simulate defrost` | `ws-engineering` | Ruta fija al gateway y PLC ficticios | Acceso a un PLC real o una red configurable |
| `labctl harden plc` | `ws-engineering` | Lógica del proceso del aula | Permisos Linux, firewall o SIS |
| `labctl classroom-state` | Cualquier Terminal autorizada | Lectura global de `/api/state` | Independencia frente al log de aplicación |
| `labctl reset` | Endpoint actual | Políticas de ese endpoint; conserva evidencia | PLC, gateway y otras estaciones |
| `labctl reset-all` | Terminal coordinada | Proceso, gateway y endpoints del aula; conserva evidencia | Recuperación real de producto o autorización para afectar otra cohorte |

## Diagnóstico compacto

1. **Host equivocado:** `hostname` no es `ws-engineering`. Detenga el paso y vuelva a la estación recomendada.
2. **Aula sucia:** `plc_guard`, políticas de gateway o consigna no están en línea base. Coordine `reset-all`; no use varios `reset` locales como atajo.
3. **Bloqueo en lugar incorrecto:** si la segunda orden se rechaza antes de llegar al PLC, compare la política gateway y el `packet`; no lo llame excepción del interlock.
4. **Sin efecto térmico:** lea `packet.exception` y luego `classroom-state`; una lectura de temperatura sin actualización no justifica repetir órdenes.
5. **Cuarentena inesperada:** `spoiled` es pegajoso una vez alcanzado el umbral del modelo; `recover` y `harden plc` no lo liberan. `false` solo significa que no fue observado, si la exposición no cruzó el umbral.
6. **Sin proceso en `osqueryi`:** significa no observado en esa consulta. No invente PID ni suponga que la ausencia local invalida los logs programados.
7. **Sin Kibana/PCAP:** preserve las fuentes locales, revise la ventana/collector y pruebe los endpoints fijos `/api/packets` y `/api/capture`; un `404` no se reemplaza por una captura ficticia.

## Cierre coordinado

Después de guardar evidencia, anuncie el estado al responsable de aula. Para dejar la maqueta lista para otra práctica, use solo después de coordinar:

```sh
labctl reset-all
```

No ejecute `docker compose down -v`: elimina volúmenes y evidencia. `docker compose` no se ejecuta desde la Terminal de estudiante. Si solo necesita limpiar una política del endpoint en una prueba separada, `labctl reset` es local y no equivale a este cierre global.

## Mapeo normativo y uso responsable

- **MITRE ATT&CK for ICS:** T0836 *Modify Parameter* y T0831 *Manipulation of Control*, tal como se representan en la maqueta.
- **IEC 62443:** FR3 (integridad) y FR7 (disponibilidad/recursos), a nivel de requisitos fundacionales y diseño pedagógico. El SL-T debe definirse por análisis de riesgo de cada zona; una secuencia de botones no obtiene SL-A.
- **Ley 21.663:** esta práctica no constituye evaluación de cumplimiento, notificación ni comunicación real a ANCI. No se envían notificaciones fuera del aula.

Solo aula aislada y autorizada: no conectar a PLC, HMI, RTU, tiendas ni redes externas. No hay malware operativo, explotación, cifrado, escaneo ni destinos configurables. Un marcador benigno o una emulación finita no demuestra una APT. El ejemplo contextual de proveedor sin ventana, copia sin hash y cambios HMI sin validación es una discusión de riesgo, no una observación atribuida a una organización; la respuesta responsable es inventariar dueño, documentar cambio/reversión, probar fuera de producción y acordar ventana con operaciones.

### Nota de coordinación con otros talleres

Este documento cubre el taller 04 y no sustituye el diseño de **Módulo 10** ni del **desafío 09**. En el material combinado, Módulo 10 debe conservar sus seis prácticas como unidades separadas (`mb-write`, `mb-fc16`, `mb-sensor`, `mb-burst`, `ua-roles`, `ua-channel`), y desafío 09 debe indicar explícitamente el host de cada etapa y sus siete controles, sin asumir que una orden local mueve el rol a otra estación. Aquí solo se usa `ws-engineering` y el control FC06 del proceso.
