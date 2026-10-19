# 07 · Firmware y detección con osquery

**Tipo:** laboratorio práctico de Retail OT; no es una presentación.

## Estación, interfaz y reglas de ejecución

- **Estación recomendada:** `ws-engineering`, abierta desde su escritorio noVNC.
- **Dónde ejecutar:** todos los bloques de esta guía se ejecutan en la **Terminal del laboratorio** de `ws-engineering`. La guía se lee en el Firefox local del mismo escritorio; no se usa la consola del portal como shell y no se cambia el origen de tráfico a otra estación.
- **Copiado en noVNC:** en Firefox, usar el botón Copiar de la guía y en `xfce4-terminal` pegar con `Ctrl+Shift+V`. No pegar el prompt `$`, ni una salida JSON como si fuera un comando, ni usar el portapapeles del anfitrión.
- **Observación opcional:** el estado del gemelo puede verse en `http://panel:8000` y los eventos en `http://kibana:5601`. Esas vistas son comprobación visual, no instrucciones necesarias para resolver el taller. La fuente primaria de los pasos es la terminal y sus archivos de evidencia.
- **Alcance autorizado:** el firmware es un archivo de texto ficticio en `/home/student/lab/firmware.bin`; no se toca firmware real, PLC real ni una tienda.

## Objetivos medibles

Al terminar, la evidencia debe demostrar, sin inventar hashes ni PID:

1. Que el hash SHA-256 nominal de `firmware.bin` fue capturado antes de la simulación.
2. Que una actualización ficticia altera el archivo cuando la validación de cadena de suministro está desactivada.
3. Que la barrera `supply-chain` restaura la referencia nominal y rechaza el mismo candidato alterado, sin reemplazar el archivo.
4. Que `labctl detect` y las consultas manuales `osqueryi` son evidencias locales distintas de los eventos de aplicación y de la consulta programada de `osqueryd`.
5. Que la protección de permisos del archivo de configuración pasa de la línea base vulnerable a `0640`, con propietario `root` y grupo `student`, y que un intento de escritura como `student` recibe `Permission denied`.
6. Que se documentan las limitaciones: esto no es una firma PKI de firmware, un antivirus global ni una certificación IEC 62443.

## Preparación limpia, alcance y coordinación

La maqueta es compartida. `labctl reset` solo restablece políticas y procesos del **endpoint actual**; no restablece PLC, gateway ni otras estaciones y **no restaura** el contenido original de `firmware.bin`. `labctl reset-all` es una operación global de aula: afecta a otros alumnos, conserva la evidencia y solo debe ejecutarla la persona coordinadora después de avisar y confirmar que no hay otra sesión activa.

El procedimiento de inicio deja el archivo nominal, pero deja las políticas del endpoint en estado vulnerable para poder reproducir el taller:

1. En el escritorio de `ws-engineering`, abrir la guía local en Firefox con el comando nuevo. No es el portal:

```sh
labctl guides
```

**Resultado esperado y significado:** Firefox abre las guías locales disponibles. No se espera un JSON de laboratorio ni se usa este comando para cambiar políticas. Si no abre nada, continuar con este archivo local y registrar el error; no sustituir la guía por instrucciones del portal.

2. **Solo la coordinación del aula**, tras avisar a la cohorte, ejecuta el restablecimiento global:

```sh
labctl reset-all
```

**Resultado esperado y significado:** respuesta JSON de restablecimiento de aula; el proceso, endpoints y políticas vuelven a una base coordinada y la evidencia histórica se conserva. No asumir que esto restauró `firmware.bin`.

**Segunda comprobación:**

```sh
labctl classroom-state
```

La salida conserva el gemelo con `process`, `gateway`, `endpoints`, `policies` y eventos. Los valores son variables y no se deben copiar como resultados esperados.

**Si difiere:** si no se coordinó el `reset-all`, no repetirlo durante la sesión de otra persona. Si el comando nuevo aún no existe, registrar el error y continuar únicamente con un `labctl reset` local después de coordinar la base; el padre implementa este comando.

3. Ahora, en la terminal de `ws-engineering`, preparar este endpoint. La primera acción restaura el archivo nominal; la segunda quita la política para que el primer intento sea reproducible.

```sh
labctl harden supply-chain
```

**Resultado esperado y significado:** evento directo con `event.dataset` `lab.endpoint`, acción `harden-supply-chain` y resultado `success`. La barrera escribe la referencia nominal de entrenamiento; no demuestra una firma PKI.

```sh
labctl reset
```

**Resultado esperado y significado:** evento directo de `reset` con resultado `success`; las políticas del endpoint actual se limpian, la evidencia se conserva y el firmware queda nominal porque se restauró en el comando anterior. Este `reset` no toca otras estaciones ni el PLC/gateway.

**Segunda comprobación:**

```sh
hostname
```

Debe identificar la estación `ws-engineering`.

```sh
id
```

Debe mostrar el usuario de laboratorio `student` sin requerir `sudo`.

```sh
labctl status
```

La respuesta de salud incluye `host`, `role`, `policies`, `mode` y `osquery`. En esta guía, los valores de política deben quedar desactivados tras el `reset`; no se fija un PID, timestamp ni hash en el texto.

**Si difiere:** si `hostname` no es `ws-engineering`, volver en noVNC a esa estación antes de ejecutar acciones. Si el usuario no es `student`, detener el taller y corregir la estación; no usar `sudo`. Si una política quedó activa, conservar la salida, coordinar y repetir la preparación local.

4. Crear la carpeta de evidencia dentro del home del alumno. Nunca redirigir la evidencia del taller al collector `/evidence`.

```sh
mkdir -p ~/lab/evidencias/taller-07
```

**Resultado esperado y significado:** se crea o conserva `~/lab/evidencias/taller-07/`, que será el entregable local. No se espera una salida.

**Segunda comprobación:**

```sh
pwd
```

La terminal sigue en la estación actual; la ruta de evidencia se usa mediante `tee` en cada paso.

**Si difiere:** si no se puede crear el directorio, registrar el mensaje exacto y no guardar en `/evidence`; revisar que la sesión sea `student` y que se esté usando `/home/student`.

## Acciones paso a paso

### 1. Capturar la línea base y el hash nominal

**Propósito.** Establecer la comparación antes de aceptar cualquier actualización. El hash que se entregue debe ser el capturado en esta ejecución, no un valor de ejemplo.

**Acción exacta:**

```sh
labctl baseline | tee ~/lab/evidencias/taller-07/01-baseline.json
```

**Resultado esperado y significado.** La salida es un objeto que contiene `event`, `rows` y `policies`. `rows` consulta localmente `/home/student/lab/controller.conf`; el evento es evidencia de que se ejecutó la consulta manual. No interpretar este comando como una consulta del hash de firmware: el código de `baseline` solo consulta el archivo de configuración.

**Segunda evidencia:**

```sh
sha256sum /home/student/lab/firmware.bin | tee ~/lab/evidencias/taller-07/01-firmware-sha256-nominal.txt
```

```sh
osqueryi --json "SELECT path,sha256 FROM hash WHERE path='/home/student/lab/firmware.bin';" | tee ~/lab/evidencias/taller-07/01-osquery-hash-nominal.json
```

Las dos salidas deben conservar el hash producido en tiempo de ejecución. La segunda consulta es `osqueryi` directo sobre el endpoint; no se afirma ningún valor literal.

**Si difiere.** Si no existe el archivo o ambas fuentes no entregan la misma referencia, no continuar con la actualización. Ejecutar `labctl status`, conservar sus salidas y volver a la preparación: `labctl harden supply-chain` y luego `labctl reset`. Si solo `osqueryi` queda vacío, significa **no observado** o un problema de la tabla/endpoint, no prueba de que el archivo no exista.

### 2. Reproducir la alteración ficticia sin protección

**Propósito.** Mostrar el antes/después de una actualización de texto no validada. Es una simulación local; no es firmware ejecutable.

**Acción exacta:**

```sh
labctl simulate firmware | tee ~/lab/evidencias/taller-07/02-firmware-alterado-evento.json
```

**Resultado esperado y significado.** El JSON directo contiene `event.dataset` `lab.endpoint`, acción `firmware`, resultado `success` y un mensaje que indica que el archivo ficticio fue alterado y no es firmware ejecutable. No asumir una envoltura `{result:...}` para este comando.

**Segunda evidencia:**

```sh
cat /home/student/lab/firmware.bin | tee ~/lab/evidencias/taller-07/02-firmware-alterado-contenido.txt
```

Debe leerse exactamente `RETAIL-EDUCATIONAL-FIRMWARE-v1-ALTERED` seguido por salto de línea. Capturar el hash posterior, sin inventarlo:

```sh
sha256sum /home/student/lab/firmware.bin | tee ~/lab/evidencias/taller-07/02-firmware-sha256-alterado.txt
```

El hash posterior debe ser distinto del hash nominal registrado en el paso 1. La diferencia prueba cambio de contenido, no autenticidad del candidato.

**Si difiere.** Si el resultado es `blocked`, la política `supply-chain` ya estaba activa o se ejecutó en otro endpoint. Revisar `labctl status` y `hostname`; no borrar la evidencia ni declarar éxito. Si el contenido no contiene `ALTERED`, repetir solo después de verificar la preparación. Si el hash no cambia pero el evento dice `success`, guardar ambas fuentes y marcar una discrepancia para diagnóstico.

### 3. Confirmar el cambio por una fuente independiente de la aplicación

**Propósito.** Separar el evento que emitió el agente de la lectura manual de osquery. `lab.endpoint` no es una detección independiente de osquery ni de Suricata.

**Acción exacta:**

```sh
osqueryi --json "SELECT path,sha256 FROM hash WHERE path='/home/student/lab/firmware.bin';" | tee ~/lab/evidencias/taller-07/03-osquery-hash-alterado.json
```

**Resultado esperado y significado.** Debe aparecer la ruta del archivo y el hash actual de la versión alterada. El valor es variable; se compara con `01-osquery-hash-nominal.json`, no se reemplaza por un hash escrito en la guía.

**Segunda evidencia:**

```sh
labctl evidence | tee ~/lab/evidencias/taller-07/03-evidence-pre-hardening.json
```

El resultado contiene `host`, los últimos `events` del endpoint y la ruta de lectura `osquery_logs`. Esta respuesta conserva eventos; no significa que `labctl evidence` haya ejecutado la consulta hash.

**Si difiere.** Si el hash manual sigue nominal, revisar el contenido con `cat` y el host con `hostname`. Si el evento de aplicación existe pero la consulta manual está vacía, registrar **no observado** y revisar disponibilidad/tabla de `osqueryi`; no concluir que no hubo alteración.

### 4. Activar la validación de cadena de suministro y restaurar la referencia

**Propósito.** Aplicar la barrera que compara el candidato con la referencia SHA-256 incorporada en el agente y deja el archivo en estado nominal. La barrera protege este artefacto del laboratorio; no valida una cadena de firma empresarial.

**Acción exacta:**

```sh
labctl harden supply-chain | tee ~/lab/evidencias/taller-07/04-supply-chain-evento.json
```

**Resultado esperado y significado.** Evento directo `lab.endpoint` con acción `harden-supply-chain` y resultado `success`. El agente vuelve a escribir `RETAIL-EDUCATIONAL-FIRMWARE-v1` seguido por salto de línea.

**Segunda evidencia:**

```sh
cat /home/student/lab/firmware.bin | tee ~/lab/evidencias/taller-07/04-firmware-restaurado.txt
```

```sh
sha256sum /home/student/lab/firmware.bin | tee ~/lab/evidencias/taller-07/04-firmware-sha256-restaurado.txt
```

El contenido debe coincidir con la referencia nominal del paso 1 y el hash debe ser igual al hash nominal **capturado allí**, sin escribir el valor en la guía.

**Si difiere.** Si el evento es correcto pero el archivo sigue alterado, conservar el JSON, `cat` y `sha256sum`; verificar `hostname` y `labctl status`. No llamar `reset` antes de investigar: `reset` no restaura firmware. Si el archivo se restauró pero la política no figura activa, el resultado sigue siendo válido para esta restauración, pero se debe volver a ejecutar el hardening antes del paso siguiente.

### 5. Reintentar exactamente el mismo candidato y demostrar el bloqueo

**Propósito.** Repetir la misma acción, con el mismo objetivo, después de la contramedida. La comparación antes/después evita confundir un cambio de estación con un control efectivo.

**Acción exacta:**

```sh
labctl simulate firmware | tee ~/lab/evidencias/taller-07/05-firmware-rechazado-evento.json
```

**Resultado esperado y significado.** El evento directo contiene acción `firmware`, resultado `blocked` y un mensaje de discrepancia SHA-256 del manifiesto. El candidato no reemplaza el archivo.

**Segunda evidencia:**

```sh
cat /home/student/lab/firmware.bin | tee ~/lab/evidencias/taller-07/05-firmware-tras-rechazo.txt
```

```sh
sha256sum /home/student/lab/firmware.bin | tee ~/lab/evidencias/taller-07/05-firmware-sha256-tras-rechazo.txt
```

El contenido y el hash deben seguir siendo los nominales capturados en el paso 1. También puede conservarse el historial del agente:

```sh
labctl evidence | tee ~/lab/evidencias/taller-07/05-evidence-final-firmware.json
```

**Si difiere.** Si vuelve a salir `success`, revisar `labctl status` y confirmar que `policies.supply-chain` está activa. Si el archivo cambia a `ALTERED`, no marcar el control como aprobado: guardar la evidencia, no ejecutar otra acción que la oculte y volver a preparar el endpoint. Si la salida contiene una excepción de conexión, verificar que la terminal es la de `ws-engineering`; no suponer que el panel ejecutó el comando.

### 6. Ejecutar `detect` y leer su envoltura real

**Propósito.** Verificar la detección local de configuración sin atribuirle capacidades que no tiene. `detect` consulta `controller.conf`, no calcula el hash de `firmware.bin`.

**Acción exacta:**

```sh
labctl detect | tee ~/lab/evidencias/taller-07/06-detect.json
```

**Resultado esperado y significado.** La respuesta contiene `event`, `rows` y `policies`. En `rows` aparece la ruta `/home/student/lab/controller.conf` y sus campos de archivo. El evento anidado dentro de `event` es la evidencia de consulta manual. No usar una ruta fija como `.event.outcome` para todos los comandos del taller: `simulate firmware` y `harden supply-chain` devuelven el evento directo, mientras `detect` agrega `rows`.

**Segunda evidencia:**

```sh
osqueryi --json "SELECT path,mode,uid,gid FROM file WHERE path='/home/student/lab/controller.conf';" | tee ~/lab/evidencias/taller-07/06-osquery-controller.json
```

Ambas fuentes deben describir la misma ruta y estado observado. La salida vacía significa **no observado** y se diagnostica; no se traduce en “archivo seguro”.

**Si difiere.** Si `detect` muestra `rows` vacías o falla `osqueryi`, conservar el JSON y ejecutar `labctl status`; comprobar usuario/host y que la ruta existe. Si solo difieren los formatos de `mode` o `uid` (texto frente a número), comparar el significado del modo y propietario con `stat` en el paso 8, no inventar una conversión.

### 7. Consultar inventario y versión del endpoint con osquery local

**Propósito.** Identificar qué endpoint respondió y dejar claro que `osqueryi` manual no equivale a `osqueryd` programado en los cinco endpoints.

**Acción exacta:**

```sh
labctl inventory | tee ~/lab/evidencias/taller-07/07-inventory.json
```

**Resultado esperado y significado.** Respuesta con `source` `osqueryi` y `rows` de `system_info` (`hostname`, `cpu_type`, `physical_memory`). Son datos del endpoint local.

**Segunda evidencia:**

```sh
osqueryi --json "SELECT name,version,platform FROM os_version;" | tee ~/lab/evidencias/taller-07/07-os-version.json
```

Debe producir filas con versión/plataforma del sistema o un resultado vacío que se marca como **no observado**. No fijar valores de versión en la solución.

**Si difiere.** Si `inventory` devuelve otro host, detener y volver a `ws-engineering`. Si una consulta falla, guardar el error y ejecutar `id` y `labctl status`; no usar `sudo` ni instalar herramientas. La consulta manual no debe atribuirse al intervalo de `osqueryd`.

### 8. Consultar procesos sin inventar PID

**Propósito.** Comprobar qué procesos están observables en el instante de la consulta y distinguir “no observado” de ausencia absoluta. Este paso no lanza malware real.

**Acción exacta:**

```sh
osqueryi --json "SELECT pid,name,path,cmdline FROM processes WHERE cmdline LIKE '%retail-%';" | tee ~/lab/evidencias/taller-07/08-osquery-processes.json
```

**Resultado esperado y significado.** Puede haber cero o más filas. Cualquier PID, ruta o timestamp es variable y se conserva exactamente como lo entregue el endpoint; la guía no inventa ninguno. Cero filas significa que no se observó un proceso cuyo `cmdline` contenga `retail-` en esa consulta.

**Segunda evidencia:**

```sh
pgrep -a -f 'retail-' | tee ~/lab/evidencias/taller-07/08-pgrep-processes.txt
```

La salida sirve para comparar la observación del kernel con la fila de osquery. También puede consultarse en Kibana con el filtro de `event.dataset : "osquery"` indicado más abajo.

**Si difiere.** Si una fuente tiene filas y otra no, registrar ambas con su hora y marcar una diferencia de instantánea/consulta; no eliminarla ni afirmar una detección total. Un proceso temporal puede terminar antes de la segunda fuente. El guard de una simulación benigna tampoco es antivirus global.

### 9. Consultar usuarios y puertos escuchando

**Propósito.** Completar la fotografía local de identidad y exposición observada, sin convertirla en un escaneo ni en una afirmación sobre otras estaciones.

**Acción exacta 1:**

```sh
osqueryi --json "SELECT uid,username,shell FROM users;" | tee ~/lab/evidencias/taller-07/09-osquery-users.json
```

**Resultado esperado y significado.** Filas de usuarios visibles para el endpoint, con valores reales de la sesión. No se usa como prueba de autorización de firmware.

**Segunda evidencia 1:**

```sh
id | tee ~/lab/evidencias/taller-07/09-id-evidence.txt
```

Sirve para corroborar el usuario efectivo que ejecutó la práctica, no para reemplazar la tabla `users`.

**Acción exacta 2:**

```sh
osqueryi --json "SELECT pid,port,address,protocol FROM listening_ports;" | tee ~/lab/evidencias/taller-07/09-osquery-listeners.json
```

**Resultado esperado y significado.** Filas de puertos que osquery observa como escuchando en este endpoint. Un resultado vacío es **no observado**, no una garantía de que no exista actividad en la red.

**Segunda evidencia 2:**

```sh
labctl status | tee ~/lab/evidencias/taller-07/09-status-listeners.json
```

La salud del agente permite comprobar el host y disponibilidad de osquery; no sustituye una captura de red.

**Si difiere.** Si una tabla está vacía o no disponible, conservar la salida, comprobar host/usuario y repetir una sola vez sin cambiar de estación. No iniciar escaneos ni consultar direcciones externas. La conectividad de administración del laboratorio sigue siendo una excepción pedagógica.

### 10. Endurecer permisos y probar escritura como `student`

**Propósito.** Demostrar un control de permisos real sobre `controller.conf`. Antes de esta barrera, la preparación deja el archivo en modo equivalente a `0666` y propiedad del usuario de laboratorio; después, la barrera deja `0640`, propietario `root` y grupo `student`.

**Acción exacta:**

```sh
labctl harden os | tee ~/lab/evidencias/taller-07/10-harden-os-evento.json
```

**Resultado esperado y significado.** Evento directo `lab.endpoint` con acción `harden-os`, resultado `success` y mensaje que indica `mode=0640 owner=root`. Controla el archivo indicado, no aplica un hardening universal del kernel, SELinux, AppArmor ni una política de red.

**Segunda evidencia:**

```sh
stat -c 'path=%n mode=%a uid=%u user=%U gid=%g group=%G' /home/student/lab/controller.conf | tee ~/lab/evidencias/taller-07/10-stat-after-os-hardening.txt
```

El modo debe ser equivalente a `0640`; `user` debe ser `root` y `group` `student`. Los números UID/GID son variables y se conservan tal cual.

```sh
osqueryi --json "SELECT path,mode,uid,gid FROM file WHERE path='/home/student/lab/controller.conf';" | tee ~/lab/evidencias/taller-07/10-osquery-after-os-hardening.json
```

La consulta osquery es la segunda fuente del estado del archivo.

**Prueba de escritura exacta:**

```sh
printf 'student-write-test\n' >> /home/student/lab/controller.conf
```

**Resultado esperado y significado.** El shell debe devolver `Permission denied` y no anexar la línea como `student`. Un lector que tenga permiso puede seguir leyendo el archivo; protección de escritura no significa cifrado ni control de contenido.

**Si difiere.** Si el append tiene éxito, no aprobar el paso: guardar `stat`, osquery y `labctl status`, porque el propietario/modo no coincide. Si `stat` muestra números diferentes pero nombres `root`/`student` correctos, no tratarlo como fallo. Si se ejecutó `labctl reset` después del hardening, el modo vuelve a la base vulnerable; aplicar de nuevo `labctl harden os` para repetir la prueba.

### 11. Verificar la consulta programada sin confundir fuentes

**Propósito.** Separar la consulta manual ejecutada ahora de los resultados que `osqueryd` programa y envía al collector. La guía no promete una latencia fija ni un valor concreto.

**Acción exacta:**

```sh
labctl evidence | tee ~/lab/evidencias/taller-07/11-evidence-osqueryd-path.json
```

**Resultado esperado y significado.** El objeto contiene la lista reciente de eventos del endpoint y el campo `osquery_logs` con la ruta del log programado. Los eventos `lab.endpoint` son logs de aplicación, no detecciones independientes de osqueryd.

**Segunda evidencia, solo lectura del collector:**

```sh
tail -n 20 /evidence/osquery/osqueryd.results.log | tee ~/lab/evidencias/taller-07/11-osqueryd-tail.txt
```

Si hay líneas, sirven para buscar las consultas programadas de `processes`, `downloads`, `config_integrity`, `inventory` y `listeners`. La consulta hash manual de firmware no demuestra que `osqueryd` monitorice `firmware.bin`: el schedule conocido no incluye ese archivo.

**Si difiere.** Si el log no existe, no se puede leer o no contiene una fila coincidente, registrar **no observado**, conservar el mensaje y usar `osqueryi` local como la evidencia manual. No redirigir ni modificar el archivo del collector. No atribuir a osqueryd una detección solo porque apareció un evento `lab.endpoint`.

### 12. Consolidar evidencia local y comprobación visual opcional

**Propósito.** Entregar una traza reproducible con comandos, endpoint, hora UTC, resultado y limitación, sin aprobar el taller por haber pulsado un botón.

**Acción exacta:**

```sh
labctl evidence | tee ~/lab/evidencias/taller-07/12-evidence-cierre.json
```

**Resultado esperado y significado.** Se conservan los últimos eventos del endpoint y la ruta del log osqueryd; `reset` no borra estos eventos. Revisar los archivos de `~/lab/evidencias/taller-07/` y anotar allí, en el informe de entrega, el hash realmente capturado, el host y la hora UTC.

**Segunda evidencia opcional en Firefox local:**

- En `http://kibana:5601`, Discover, data view `retail-ot-*`, ventana reciente y refresco periódico, usar KQL (no SQL):

```kql
event.dataset : "osquery" AND host.name : "ws-engineering"
```

```kql
event.dataset : "lab.endpoint" AND host.name : "ws-engineering"
```

```kql
event.dataset : "lab.control"
```

Para una alerta Suricata, solo si la sesión produjo tráfico de esa práctica, el filtro es:

```kql
event.dataset : "suricata" AND event.action : "alert"
```

**Significado:** `osquery` y `lab.endpoint` deben filtrarse por `ws-engineering`; `lab.control` puede tener como host `plc`, `gateway` o el endpoint solicitante. Suricata usa el host `sensor`. Kibana es una segunda vista; no sustituye el JSON de la terminal ni convierte una consulta vacía en ausencia absoluta.

**Si difiere.** Si no hay datos en Kibana, comprobar primero los archivos locales y `labctl evidence`; conservar la ventana de consulta y marcar el dato como no observado. No cambiar de host para fabricar una coincidencia, no editar eventos y no exportar notificaciones reales a ANCI.

## Qué controla cada barrera y qué no controla

| Barrera | Antes | Después | Controla | No demuestra |
|---|---|---|---|---|
| `harden supply-chain` | El texto candidato puede reemplazar `firmware.bin`. | El candidato con SHA-256 distinto se rechaza y el archivo vuelve a la referencia nominal. | Integridad de este archivo ficticio frente al candidato fijo del ejercicio. | Firma PKI, identidad del proveedor, arranque seguro, firmware ejecutable o cadena empresarial de confianza. |
| `harden os` | `controller.conf` parte con permisos de laboratorio equivalentes a `0666`. | Queda `0640`, `root:student`; `student` no puede anexar. | Permisos Linux del archivo indicado. | SELinux/AppArmor, hardening universal del kernel, control de secretos o autorización OT completa. |
| `osqueryi` manual | Una consulta puntual sobre el endpoint actual. | Entrega filas o vacío para esa instantánea. | Observabilidad local de tablas autorizadas. | Monitoreo continuo; `osqueryi` manual es independiente de `osqueryd` programado y de Suricata. |
| `osqueryd`/collector | Resultados programados pueden tardar o no observar un evento. | Se consulta su log y dataset como segunda fuente. | Evidencia programada de las consultas configuradas. | Que el schedule incluya `firmware.bin`; no se debe afirmar eso. |

`labctl reset` conserva evidencia, restablece las políticas del endpoint actual y termina procesos benignos registrados, pero no restaura firmware ni modifica PLC/gateway. `labctl reset-all` coordina el aula completa y no debe ejecutarse unilateralmente.

## Cierre coordinado y limpieza

Después de guardar toda la evidencia, la persona que coordina puede dejar este endpoint en estado nominal de archivo y vulnerable de política para la siguiente práctica:

```sh
labctl harden supply-chain | tee ~/lab/evidencias/taller-07/13-restore-nominal-evento.json
```

```sh
labctl reset | tee ~/lab/evidencias/taller-07/14-reset-local-evento.json
```

El orden importa: `harden supply-chain` restaura el contenido; `reset` quita la política y conserva ese contenido nominal. No ejecutar `docker compose down -v`, porque elimina volúmenes y evidencia. Si se requiere volver a la base de toda el aula, avisar y ejecutar `labctl reset-all` solo con coordinación:

```sh
labctl reset-all
```

Volver a verificar con `labctl classroom-state`; su salida es solo lectura y conserva el gemelo. Un reset global es una operación de aula, no una prueba adicional de este control.

## Solución razonada y criterios de éxito

La resolución completa es: preparar el endpoint correcto; capturar el hash nominal; ejecutar una alteración ficticia sin protección; verificar el cambio con `cat`, `sha256sum` y osquery; activar la validación; repetir exactamente la misma actualización; demostrar `blocked` y que el archivo no cambió; luego consultar configuración y telemetría local con osquery y probar el control de permisos. Las salidas capturadas prevalecen sobre el resultado que se esperaba.

Se considera satisfactorio cuando la carpeta `~/lab/evidencias/taller-07/` contiene, como mínimo, el baseline, hash nominal, alteración, hash alterado, restauración, rechazo, `detect`, consultas osquery, `stat` posterior a `harden os`, error de escritura como `student` y `labctl evidence`. La evidencia debe indicar comando, endpoint, hora UTC, resultado permitido/bloqueado, efecto observado, fuente y limitación.

Criterios concretos:

- Hash nominal inicial documentado con `sha256sum` y consulta `hash` de osquery, sin inventar el valor.
- Hash nominal nuevamente observado después de `harden supply-chain`.
- Mismo candidato rechazado después de activar la política, con contenido nominal conservado.
- `labctl detect` interpretado como consulta de `controller.conf`, no como hash de firmware.
- Diferencia entre `osqueryi` manual, `osqueryd`, logs `lab.endpoint`, `lab.control` y Suricata explicada.
- Limitación de ausencia de firma PKI explicada.
- Protección de permisos `0640 root:student` y `Permission denied` del append como `student` documentados.

## Referencias y uso responsable

- **MITRE ATT&CK for ICS:** el taller representa una cadena de suministro de forma controlada; no atribuye una campaña, TTP real ni un exploit.
- **IEC 62443:** se conserva la relación pedagógica con FR3 y la referencia IEC 62443-4-1. El `SL-T` debe definirse mediante análisis de riesgo de cada zona; un `success` de laboratorio no entrega `SL-A` ni certificación.
- **Ley 21.663:** los registros del ejercicio sirven como trazabilidad interna del taller, no como declaración de cumplimiento ni como notificación. No enviar notificaciones reales a ANCI desde esta maqueta.
- Solo aula aislada y autorizada. No conectar a PLC, HMI, RTU o tiendas reales; no usar escaneo, explotación, cifrado, direcciones externas, `sudo`, Docker ni Git desde la estación. El modelo de proceso y el firmware son educativos; una simulación no demuestra una APT ni seguridad operacional real.
