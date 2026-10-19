# 03 · HMI: allowlisting e integridad

> **Tipo de actividad:** laboratorio controlado de Retail OT. No es una presentación ni una prueba contra sistemas reales.
>
> **Estación recomendada:** `ws-hmi`, con Firefox y la **Terminal del laboratorio** del mismo escritorio noVNC.
>
> **Fuente de instrucciones:** este documento debe abrirse como guía HTML local mediante `labctl guides`. No es necesario volver al portal para seguir los pasos.

## Objetivos medibles

Al terminar, el operador debe poder:

- Distinguir entre **recibir un archivo** y **ejecutarlo**.
- Reproducir una ejecución benigna antes y después de activar el guard de aplicación.
- Verificar que una política de aplicación detiene un proceso local ya existente y bloquea una repetición.
- Comprobar una barrera de permisos Linux: `controller.conf` pasa de `0666` y propiedad de `student` a `0640`, propiedad `root:student`.
- Comprobar que un candidato de firmware ficticio cambia su SHA-256 sin protección y que la política de supply chain restaura la referencia y rechaza el mismo candidato.
- Entregar evidencia con al menos dos fuentes cuando corresponda: respuesta del agente más consulta local con `stat`/`osqueryi`, o hash manual más consulta de hash.

El laboratorio usa únicamente el artefacto benigno fijo del aula en `/home/student/lab`. No contiene malware operativo, no cifra datos y no representa una APT.

## Alcance y reglas de ejecución

- **Todos los bloques se ejecutan en la Terminal real del noVNC recomendado**, no en la consola web del portal, una consola de Firefox ni una shell del anfitrión.
- Firefox sirve para leer esta guía local y, de manera opcional, observar el panel/Kibana. Terminal y Firefox conviven en el escritorio.
- En noVNC: usar el botón **Copiar** de la guía y pegar con `Ctrl+Shift+V` en xfce4-terminal. No copiar el `$` del prompt ni una salida JSON como si fuera un comando. Como alternativa, seleccionar el código dentro de Firefox y usar `Ctrl+C` allí, seguido de `Ctrl+Shift+V` en Terminal.
- La maqueta es compartida. `labctl reset-all` es una operación global que afecta a las cinco estaciones y al proceso; solo se ejecuta con coordinación de la cohorte. Mantiene la evidencia, pero no borra eventos ni PCAP.
- `labctl reset` solo restablece el endpoint actual. **No restaura `firmware.bin`**; para dejar el firmware en su referencia se usa primero `labctl harden supply-chain` y después el reset que corresponda.
- No usar `sudo`, `docker`, `git`, `iptables`, escaneo, payloads libres ni direcciones externas. No modificar los archivos del laboratorio fuera de los comandos indicados.

### Mapa de alcance local y global

| Comando | Alcance | Qué demuestra o cambia |
|---|---|---|
| `hostname`, `id`, `labctl status`, `inventory`, `baseline`, `detect`, `evidence` | Endpoint actual | Identidad, estado y consultas locales de `ws-hmi`. |
| `simulate malware`, `harden application`, `harden os`, `simulate firmware`, `harden supply-chain` | Endpoint actual | Artefacto/proceso, guard de ejecución, permisos del archivo y referencia de firmware de este HMI. |
| `labctl classroom-state` | Aula, solo lectura | Consulta el gemelo del panel (`/api/state`): proceso, gateway, endpoints, políticas, eventos e historial. |
| `labctl reset-all` | Aula completa, coordinado | Restablece proceso, políticas y endpoints; conserva evidencia. No mueve el rol del terminal ni restaura firmware por sí solo. |
| `labctl guides` | Navegador local | Abre las guías HTML locales; no es una shell ni la interfaz de control. |

Los comandos de esta guía no cambian automáticamente de host. La terminal debe seguir en `ws-hmi` durante todo el taller.

## Preparación limpia

### Paso 1. Coordinar el reinicio de aula

**Propósito.** Evitar que una política, proceso o escenario de otro alumno contamine la comparación antes/después. Esta operación debe anunciarse al grupo porque es global.

**Acción exacta.** Solo el operador autorizado por la cohorte ejecuta en la Terminal del laboratorio:

```sh
labctl reset-all
```

**Resultado esperado y significado.** La respuesta debe indicar que se reiniciaron el proceso, las políticas y los endpoints, conservando la evidencia. La forma exacta del JSON depende del comando nuevo implementado por el laboratorio; no asumir una ruta como `.event.outcome`. Un reset de aula no es una certificación de seguridad ni una limpieza de los archivos de evidencia.

**Segunda evidencia.** Consultar el gemelo, sin modificarlo:

```sh
labctl classroom-state
```

Debe ser posible identificar en el JSON los campos `process`, `gateway`, `endpoints`, `policies`, `events`, `history`, `last_update` y `errors`. En `policies` globales, `network` y `access` deberían estar desactivadas; en el endpoint `ws-hmi`, las políticas locales deberían estar desactivadas. Leer el JSON completo; no inventar valores faltantes.

**Si difiere.** No comenzar el ataque. Guardar la salida completa, comprobar `errors` y coordinar con el responsable del aula. No repetir `reset-all` mientras otro alumno esté usando la maqueta. Un `classroom-state` con un endpoint `unavailable` es una condición de disponibilidad, no evidencia de que una barrera funcionó.

### Paso 2. Confirmar estación y usuario

**Propósito.** Asegurar que las consultas y los cambios se harán en el HMI correcto y con el usuario limitado del taller.

**Acción exacta.** Ejecutar cada línea y esperar su salida:

```sh
hostname
id
labctl status
```

**Resultado esperado y significado.** `hostname` debe identificar `ws-hmi`. `id` debe mostrar al usuario de laboratorio `student`; los grupos concretos pueden variar y deben conservarse tal como se impriman. `labctl status` debe mostrar el host/rol, las políticas del endpoint y el modo actual de `controller.conf`. Tras una preparación limpia, se espera que las políticas locales estén en `false` y que el modo sea equivalente a `0666`; el campo de versión de osquery es variable.

**Segunda evidencia.** En el mismo terminal:

```sh
labctl classroom-state
```

En `endpoints.ws-hmi` debe aparecer el mismo host y un estado de políticas coherente con `labctl status`. La consulta es de solo lectura y sirve para comparar endpoint y panel; no reemplaza la evidencia local.

**Si difiere.** Si el host no es `ws-hmi`, detenerse y volver al escritorio noVNC de HMI; la guía no cambia el rol por sí sola. Si `id` no es `student`, no usar `sudo` ni continuar. Si el estado local y el de aula difieren, conservar ambos JSON y revisar `errors`, disponibilidad del agente y coordinación del reset.

### Paso 3. Abrir la guía local y verificar inventario

**Propósito.** Trabajar con una copia local de las instrucciones y confirmar que `osqueryi` está consultando el endpoint observado, no un SOC remoto.

**Acción exacta.** Para abrir la guía local, ejecutar:

```sh
labctl guides
```

Luego, en la Terminal del laboratorio, verificar el inventario:

```sh
labctl inventory
```

**Resultado esperado y significado.** Firefox debe abrir las guías locales. `labctl inventory` devuelve un objeto cuyo `source` es `osqueryi` y una lista `rows` con datos de hardware del endpoint. Los valores de CPU y memoria son variables; no son un identificador de seguridad.

**Segunda evidencia.** Confirmar la versión de sistema consultada localmente:

```sh
osqueryi --json "SELECT name,version,platform FROM os_version;"
```

La salida JSON debe ser de esta estación. Una fila vacía significa **no observado** en esa consulta, no ausencia absoluta de actividad.

**Si difiere.** Si `labctl guides` no abre Firefox, continuar solo si se dispone de esta copia local y registrar el error; no usar el portal como sustituto de la Terminal. Si `inventory` o `osqueryi` fallan, no atribuirlo a una política de allowlisting: verificar host, usuario y disponibilidad del agente.

### Paso 4. Capturar la línea base de configuración

**Propósito.** Medir la condición vulnerable antes del endurecimiento sin inventar permisos, propietario ni grupo.

**Acción exacta.** Ejecutar:

```sh
labctl baseline
```

La respuesta de este comando incluye un evento manual y `rows`/`policies`; no asumir que su resultado usa la misma forma que `labctl status`.

```sh
stat -c 'mode=%a owner=%U group=%G path=%n' /home/student/lab/controller.conf
```

**Resultado esperado y significado.** La referencia inicial conocida es modo equivalente a `0666`, con propietario `student`; el grupo debe tomarse de la salida real. Este archivo de configuración es un recurso Linux del aula, no la lógica de seguridad de un PLC real.

**Segunda evidencia.** Consultar el mismo objeto con osquery:

```sh
osqueryi --json "SELECT path,mode,uid,gid FROM file WHERE path='/home/student/lab/controller.conf';"
```

Debe aparecer la ruta exacta y campos de modo/UID/GID coherentes con `stat`. Los tipos y la representación del modo dependen de osquery; comparar el valor efectivo y no solo el texto.

**Si difiere.** Si el archivo no existe, hay otro propietario o el modo ya es `0640`, guardar la salida y revisar si el endpoint fue reiniciado de forma limpia. No corregirlo manualmente con `chmod`/`chown`; ejecutar primero la preparación coordinada o diagnosticar el estado heredado.

### Paso 5. Capturar la referencia de firmware sin publicar el hash

**Propósito.** Tener una referencia de comparación para el archivo educativo antes de simular una alteración. El hash debe ser capturado en esta sesión, no escrito de memoria.

**Acción exacta.** Ejecutar ambos comandos y conservar sus salidas:

```sh
sha256sum /home/student/lab/firmware.bin
```

```sh
osqueryi --json "SELECT path,sha256 FROM hash WHERE path='/home/student/lab/firmware.bin';"
```

**Resultado esperado y significado.** `sha256sum` debe imprimir una línea con un hash de 64 caracteres hexadecimales y la ruta. La consulta `hash` debe devolver la misma ruta y un hash comparable. No se proporciona ni se inventa un valor concreto: el valor válido es el capturado en el HMI de esta sesión. La consulta manual de osquery es evidencia local independiente de la consulta programada de `osqueryd`.

**Segunda evidencia.** Repetir la consulta de archivo, sin cambiarlo:

```sh
stat -c 'mode=%a owner=%U group=%G size=%s mtime=%y path=%n' /home/student/lab/firmware.bin
```

Debe confirmar que el archivo existe y permitir anotar su tamaño/fecha reales. `stat` no prueba la autenticidad del contenido; el hash sí permite comparar contenido.

**Si difiere.** Si el hash o el tamaño ya corresponden a una alteración, guardar la evidencia, ejecutar `labctl harden supply-chain` para restaurar la referencia y repetir este paso antes de continuar. Si osquery no devuelve fila, registrar **no observado** y no declarar que el archivo no existe sin verificar `stat`.

## Allowlisting de aplicación: antes, barrera y después

### Paso 6. Reproducir la descarga y ejecución benigna antes de la barrera

**Propósito.** Separar la recepción del archivo de su ejecución. El comando solicita el artefacto fijo al panel, lo deja bajo `/home/student/lab/downloads/` y, cuando no hay guard local, inicia un `sleep` benigno con nombre de proceso controlado.

**Acción exacta.** Ejecutar de inmediato, sin cambiar parámetros:

```sh
labctl simulate malware
```

**Resultado esperado y significado.** La respuesta es un evento directo del agente, no necesariamente un objeto `{event: ...}`. En el JSON debe observarse un objeto `event` con `dataset` `lab.endpoint`, `action` `malware-emulation` y `outcome` `success`. El mensaje orientativo es `BENIGN: marker download + 45 second sleep; nothing encrypted`. La marca `success` significa que se descargó el marcador y se inició el proceso benigno; no significa que exista malware ni que el HMI esté comprometido.

**Segunda evidencia.** Verificar el archivo descargado localmente:

```sh
osqueryi --json "SELECT path,mode,uid,gid FROM file WHERE path='/home/student/lab/downloads/retail-marker.txt';"
```

Y, mientras la ventana del proceso siga vigente, consultar el proceso:

```sh
osqueryi --json "SELECT pid,name,path,cmdline FROM processes WHERE cmdline LIKE '%retail-benign-malware%';"
```

La primera consulta debe mostrar la ruta del marcador; la segunda puede mostrar un PID variable y la línea de proceso benigno. No inventar PID ni asumir que un resultado vacío prueba bloqueo: el proceso es temporal.

**Si difiere.** Si aparece `blocked` antes de haber aplicado `harden application`, revisar `hostname` y `labctl status`: puede haber quedado `os=true` o `application=true` de una sesión previa. Si aparece `success` pero no se observa el proceso, repetir solo después de verificar que el guard está desactivado y ejecutar la consulta de procesos inmediatamente. Un proceso que desapareció por el paso del tiempo no demuestra una barrera.

### Paso 7. Activar el allowlisting del lanzador

**Propósito.** Aplicar la barrera de aplicación del endpoint actual. Esta política mata los procesos benignos registrados por el agente y bloquea futuras ejecuciones de `simulate malware`; no es una allowlist universal del sistema operativo.

**Acción exacta.** Ejecutar en `ws-hmi`:

```sh
labctl harden application
```

**Resultado esperado y significado.** La respuesta es un evento directo con `event.dataset` `lab.endpoint`, `event.action` `harden-application` y `event.outcome` `success`. El mensaje indica que se aplicó la política de aplicación. El proceso iniciado en el paso anterior debe ser terminado por la acción local.

**Segunda evidencia.** Comprobar la política y consultar procesos:

```sh
labctl status
```

```sh
osqueryi --json "SELECT pid,name,path,cmdline FROM processes WHERE cmdline LIKE '%retail-benign-malware%';"
```

En `labctl status`, `policies.application` debe ser `true`. La consulta de procesos debería no devolver el marcador después de la detención; `[]` significa que no se observó ese proceso en ese instante, no que se demostró una protección global.

**Si difiere.** Si la política no aparece en `true`, conservar la respuesta y la salida de `status`; verificar que el comando se ejecutó en `ws-hmi` y que el agente está disponible. Si el proceso ya no estaba vivo, la respuesta puede ser correcta pero no permite demostrar la detención: repetir la secuencia desde el paso 6 después de verificar el estado, no declarar un bloqueo a partir de un proceso que expiró.

### Paso 8. Repetir exactamente la misma acción después de la barrera

**Propósito.** Obtener una comparación reproducible: misma estación, mismo comando y mismo artefacto, cambiando solo la política.

**Acción exacta.** No agregar flags ni ejecutar scripts externos:

```sh
labctl simulate malware
```

**Resultado esperado y significado.** La respuesta es un evento directo con `event.action` `malware-emulation` y `event.outcome` `blocked`. El mensaje orientativo es `Local artifact downloaded; training execution guard blocked benign process`. El archivo sigue siendo descargable/observable, pero el proceso no debe iniciarse. Esta es la diferencia didáctica entre **recepción** y **ejecución**.

**Segunda evidencia.** Consultar primero el marcador y luego el proceso:

```sh
osqueryi --json "SELECT path,mode,uid,gid FROM file WHERE path='/home/student/lab/downloads/retail-marker.txt';"
```

```sh
osqueryi --json "SELECT pid,name,path,cmdline FROM processes WHERE cmdline LIKE '%retail-benign-malware%';"
```

Debe existir una fila del archivo si la descarga terminó, mientras que el proceso no debería observarse. La respuesta del agente y estas consultas son fuentes diferentes; un evento `lab.endpoint` aislado no es una detección independiente de osquery.

**Si difiere.** Si el resultado es `success`, detener la repetición y guardar la salida: normalmente indica que se ejecutó en otro host, que `application` no está activa o que hubo un reset posterior. Ejecutar `hostname` y `labctl status`, y corregir solo tras coordinar. Si el archivo no aparece, comprobar disponibilidad del panel y conservar el error; no convertir una consulta vacía en prueba de bloqueo. Si aparece un proceso, no concluir que el guard falló hasta verificar la política del endpoint actual.

## Integridad del endpoint y de la cadena de suministro

### Paso 9. Endurecer el archivo de configuración del HMI

**Propósito.** Aplicar la barrera de permisos real implementada por el agente, manteniendo lectura para el grupo `student` pero retirando la escritura del usuario del laboratorio.

**Acción exacta.** Ejecutar:

```sh
labctl harden os
```

**Resultado esperado y significado.** La respuesta es un evento directo con acción `harden-os`, resultado `success` y un mensaje que indica `mode=0640 owner=root`. En este taller se espera que `/home/student/lab/controller.conf` quede con propietario `root`, grupo `student` y modo efectivo `0640`. Esto no es SELinux, AppArmor, una GPO ni hardening universal del kernel.

**Segunda evidencia.** Medir permisos y propietario desde la estación:

```sh
stat -c 'mode=%a owner=%U group=%G path=%n' /home/student/lab/controller.conf
```

Debe imprimir `mode=640`, `owner=root`, `group=student` y la ruta exacta. Complementar con:

```sh
osqueryi --json "SELECT path,mode,uid,gid FROM file WHERE path='/home/student/lab/controller.conf';"
```

Los UID/GID numéricos deben corresponder a los nombres mostrados por `stat`; no inventar números si la imagen los presenta de otra manera.

**Si difiere.** Si el modo sigue en `0666`, o la propiedad no es `root:student`, comprobar `hostname`, `id` y `labctl status`; no usar `sudo chmod` ni `sudo chown`. Si el endpoint no está disponible, conservar la salida y usar `classroom-state` solo para diagnosticar disponibilidad, no para declarar un cambio local.

### Paso 10. Demostrar lectura permitida y escritura rechazada

**Propósito.** Verificar la consecuencia de `0640`: `student` puede consultar el archivo, pero no debe poder modificarlo. La prueba no debe alterar el archivo.

**Acción exacta.** Primero leer solo metadatos y contenido mediante las herramientas autorizadas:

```sh
osqueryi --json "SELECT path,mode,uid,gid FROM file WHERE path='/home/student/lab/controller.conf';"
```

Luego intentar un append controlado como `student`:

```sh
bash -c 'printf "%s\n" "student-write-test" >> /home/student/lab/controller.conf'
```

**Resultado esperado y significado.** La consulta de lectura debe devolver la fila. El segundo comando debe terminar con `Permission denied` y un estado de error; ese mensaje es evidencia de que el usuario de laboratorio no puede escribir. No se debe interpretar el permiso de lectura como integridad criptográfica.

**Segunda evidencia.** Confirmar que el modo no cambió y que la ruta sigue siendo la misma:

```sh
stat -c 'mode=%a owner=%U group=%G size=%s mtime=%y path=%n' /home/student/lab/controller.conf
```

El archivo debe seguir en `0640 root:student`; el tamaño y `mtime` no deben cambiar por el intento rechazado. Si se necesita volver a leerlo, usar osquery, no modificarlo.

**Si difiere.** Si el append tiene éxito, detenerse: revisar `id`, `stat` y `labctl status`, porque el usuario o el host no son los esperados o la política no está aplicada. No repetir la escritura, no usar `sudo` y no borrar el archivo. Si el archivo cambió pese al error aparente, conservar tamaño/fecha y tratarlo como evidencia de una discrepancia.

### Paso 11. Alterar el firmware ficticio sin protección

**Propósito.** Mostrar que una modificación de texto cambia el contenido y su hash cuando la política de supply chain está desactivada. Este archivo no es firmware ejecutable de un PLC real.

**Acción exacta.** Ejecutar:

```sh
labctl simulate firmware
```

**Resultado esperado y significado.** La respuesta es un evento directo con `event.action` `firmware` y `event.outcome` `success`. El mensaje indica `Fictitious firmware file altered; no executable firmware`. El candidato es texto educativo alterado; la marca `success` no demuestra que se haya cargado en un controlador.

**Segunda evidencia.** Comparar con el hash capturado en el paso 5:

```sh
sha256sum /home/student/lab/firmware.bin
```

```sh
osqueryi --json "SELECT path,sha256 FROM hash WHERE path='/home/student/lab/firmware.bin';"
```

El hash actual debe ser distinto del valor de referencia que el operador capturó antes del paso 11, y ambos comandos deben referirse a la misma ruta. No escribir un hash esperado en la guía ni sustituirlo por uno inventado.

**Si difiere.** Si el hash no cambia, comprobar `labctl status` para saber si `supply-chain` ya estaba activo y revisar que la consulta apunta exactamente a `/home/student/lab/firmware.bin`. Si el evento no es `success`, conservar el JSON; no concluir que se rechazó correctamente sin identificar la política que lo produjo.

### Paso 12. Restaurar la referencia y activar la validación de supply chain

**Propósito.** Restaurar el contenido original conocido por el laboratorio y activar la comprobación que compara el candidato con esa referencia.

**Acción exacta.** Ejecutar:

```sh
labctl harden supply-chain
```

**Resultado esperado y significado.** La respuesta es un evento directo con `event.action` `harden-supply-chain` y `event.outcome` `success`. La acción restaura el texto de referencia y activa `policies.supply-chain` en el endpoint actual. No se calcula una firma empresarial ni se implementa PKI: es una comparación SHA-256 del artefacto fijo del aula.

**Segunda evidencia.** Verificar política y hash restaurado:

```sh
labctl status
```

```sh
sha256sum /home/student/lab/firmware.bin
```

El hash debe volver a ser igual al valor capturado en el paso 5. La igualdad se verifica comparando las dos salidas reales de esta sesión; no se publica un valor predeterminado.

**Si difiere.** Si `supply-chain` no figura como `true`, comprobar que el comando se ejecutó en `ws-hmi`. Si el hash no vuelve al valor de referencia, guardar ambas salidas y no continuar con una afirmación de integridad. `labctl reset` no corrige por sí solo este archivo.

### Paso 13. Repetir el candidato y demostrar el rechazo

**Propósito.** Verificar la contramedida con el mismo candidato alterado utilizado en el paso 11, sin cambiar objetivo ni parámetros.

**Acción exacta.** Ejecutar:

```sh
labctl simulate firmware
```

**Resultado esperado y significado.** La respuesta debe ser un evento directo con `event.action` `firmware` y `event.outcome` `blocked`. El mensaje orientativo es `SHA256 manifest mismatch; fictitious update rejected`. La política rechaza el contenido antes de escribirlo; no significa que exista una firma de producción ni que se haya probado una actualización real.

**Segunda evidencia.** Confirmar que el hash no cambió después del rechazo:

```sh
sha256sum /home/student/lab/firmware.bin
```

```sh
osqueryi --json "SELECT path,sha256 FROM hash WHERE path='/home/student/lab/firmware.bin';"
```

El valor debe seguir igual al hash capturado después del paso 12. Las consultas manuales no sustituyen un monitoreo programado: el schedule de osquery no incluye `firmware.bin`; el hash manual y el evento del agente son fuentes complementarias.

**Si difiere.** Si el evento vuelve a ser `success`, detenerse y revisar `labctl status`, `hostname` y el hash de referencia. Si el hash cambia pese a un evento `blocked`, conservar el orden temporal de comandos y las salidas: es una discrepancia que debe diagnosticarse, no maquillarse como éxito.

## Observabilidad y segunda fuente opcional

Las comprobaciones locales anteriores son suficientes para resolver el taller. La observación visual es opcional y se realiza en la misma Firefox, sin convertirla en requisito ni usarla para inventar una salida.

- Panel interno, si está disponible: `http://panel:8000`.
- Kibana interno, si está disponible: `http://kibana:5601/app/dashboards#/view/retail-overview`.
- En Discover, elegir el data view `retail-ot-*`, una ventana reciente adecuada y refresco de 5 segundos. Copiar KQL, no SQL.

Consultas útiles:

```kql
event.dataset : "osquery" AND host.name : "ws-hmi"
```

```kql
event.dataset : "lab.endpoint" AND host.name : "ws-hmi"
```

```kql
event.dataset : "lab.control"
```

```kql
event.dataset : "suricata" AND event.action : "alert"
```

Interpretación:

- `lab.endpoint` contiene los eventos del agente del HMI, incluida la respuesta de `simulate malware` y las políticas locales.
- Los eventos `osquery` programados son otra fuente; sus cambios de configuración pueden aparecer como `config_integrity`. Las consultas manuales `osqueryi` son independientes de `osqueryd`.
- `lab.control` usa el host de la fuente PLC, gateway o endpoint solicitante; no filtrar todo por `ws-hmi`.
- Suricata usa el host `sensor`. Un resultado vacío significa que no se observó un evento en el filtro y ventana elegidos, no que no haya actividad histórica.
- Un evento `lab.endpoint` o `lab.control` no es por sí solo una detección independiente de osquery o Suricata.

Para el escenario de este taller, el panel también puede mostrar el gemelo mediante `classroom-state`. No usar `/api/packets` o `/api/capture` como evidencia de una ejecución de aplicación: esos endpoints están destinados a comprobaciones de Modbus/PCAP y no sustituyen las consultas locales de proceso, permisos o hash.

## Evidencia entregable y cierre

### Paso 14. Guardar evidencia en el directorio del alumno

**Propósito.** Conservar resultados reales, timestamp y eventos sin redirigir datos al directorio del collector. La evidencia debe permitir reconstruir qué comando se ejecutó, en qué endpoint y con qué resultado.

**Acción exacta.** Crear el directorio de evidencia del taller y guardar el resumen final del agente:

```sh
mkdir -p ~/lab/evidencias/taller-03
```

```sh
labctl evidence | tee ~/lab/evidencias/taller-03/labctl-evidence.json
```

**Resultado esperado y significado.** Se crea `~/lab/evidencias/taller-03/labctl-evidence.json` con el host, los últimos eventos del agente y la referencia al log de resultados de osqueryd. La respuesta contiene datos de esta sesión; timestamps, PID, hashes y detalles son variables y deben conservarse sin reemplazarlos por ejemplos.

**Segunda evidencia.** Guardar una ficha de cierre con identidad, estado, permisos y hash actual:

```sh
{
  printf '%s\n' '### UTC'; date -u +"%Y-%m-%dT%H:%M:%SZ"
  printf '%s\n' '### hostname'; hostname
  printf '%s\n' '### id'; id
  printf '%s\n' '### status'; labctl status
  printf '%s\n' '### config'; stat -c 'mode=%a owner=%U group=%G path=%n' /home/student/lab/controller.conf
  printf '%s\n' '### firmware'; sha256sum /home/student/lab/firmware.bin
} | tee ~/lab/evidencias/taller-03/cierre.txt
```

La ficha agrega separadores locales, pero deja las salidas de las herramientas sin modificar. Para cada resultado importante, anotar también en el informe: comando, endpoint, hora UTC, permitido/bloqueado, efecto sobre el proceso, fuente de evidencia y limitación.

**Si difiere.** Si no se puede escribir en `~/lab/evidencias/taller-03`, no usar `/evidence` del collector como destino: registrar el error y conservar las salidas en el terminal para que el responsable indique un destino del alumno. Si `labctl evidence` devuelve un error, guardar igualmente `status`, consultas osquery, `stat` y hashes; la ausencia de un índice de Kibana no borra la evidencia local.

### Paso 15. Dejar el HMI listo sin perder la evidencia

**Propósito.** Restaurar el firmware de referencia y liberar la estación para la siguiente práctica, respetando el alcance compartido.

**Acción exacta.** Después de guardar la evidencia, restaurar la referencia del firmware en este HMI:

```sh
labctl harden supply-chain
```

Luego, si el coordinador autoriza el reset del endpoint actual:

```sh
labctl reset
```

**Resultado esperado y significado.** `harden supply-chain` vuelve a escribir la referencia original de `firmware.bin`. `labctl reset` deja las políticas del endpoint en `false`, detiene los procesos registrados, devuelve `controller.conf` a la condición vulnerable del aula y conserva los eventos. El reset no borra la evidencia y no debe confundirse con una recuperación operacional real.

**Segunda evidencia.** Verificar que el endpoint está limpio y que el firmware fue restaurado:

```sh
labctl status
```

```sh
sha256sum /home/student/lab/firmware.bin
```

El estado local debe reflejar políticas desactivadas y el hash debe coincidir con el valor de referencia capturado en el paso 5. Si se requiere liberar toda la clase, el coordinador puede ejecutar después `labctl reset-all`, siempre avisando a los demás y comprobando con `labctl classroom-state`.

**Si difiere.** Si `controller.conf` vuelve a `0666` pero el firmware no coincide, ejecutar `labctl harden supply-chain` y verificar de nuevo `stat` y `sha256sum`; si el cambio sigue sin explicarse, conservar la evidencia y escalarlo al coordinador. Si otro alumno necesita la estación, no ejecutar `reset-all` sin aviso.

## Solución razonada y criterios de éxito

La solución es la comparación controlada, no el simple hecho de pulsar un botón:

1. Confirmar `ws-hmi`, usuario `student`, estado y línea base antes de actuar.
2. Ejecutar `simulate malware` sin la política: el marcador se recibe y el proceso benigno puede observarse.
3. Activar `harden application` en ese mismo endpoint: el proceso registrado se detiene y la misma acción posterior devuelve `blocked`.
4. Comprobar por separado que el archivo descargado sigue observable. Una descarga visible con proceso ausente es precisamente el resultado esperado después del guard; no es evidencia de que el archivo haya sido eliminado.
5. Activar `harden os` y demostrar con `stat`, osquery y un intento de append que `student` conserva lectura, pero no escritura, sobre `controller.conf`.
6. Alterar el firmware ficticio y verificar que su hash cambia; activar `harden supply-chain`, verificar la restauración del hash capturado y repetir el mismo candidato para obtener `blocked` sin cambio posterior.
7. Guardar las salidas reales en `~/lab/evidencias/taller-03/`, registrar el UTC y explicar toda discrepancia en vez de reemplazarla por el resultado esperado.

Se consideran criterios de éxito del taller:

- Descarga del marcador visible sin ejecución posterior tras `harden application`.
- Proceso benigno detenido por la política de aplicación o, si expiró antes de la comprobación, una repetición controlada que lo demuestre.
- Evento `blocked` del agente distinto de la consulta local de osquery.
- `controller.conf` en `0640 root:student`, con lectura para `student` y escritura rechazada.
- Hash de `firmware.bin` cambiado en la simulación sin protección, restaurado por `harden supply-chain` y estable después del rechazo.
- Evidencia trazable por host, comando, hora UTC, resultado y limitación.

Un botón, un JSON de aplicación o una vista de Kibana no bastan por sí solos: la respuesta del agente debe correlacionarse con la segunda fuente adecuada.

## Diagnóstico compacto

| Diferencia observada | Comprobación inmediata | Interpretación y acción |
|---|---|---|
| `hostname` distinto de `ws-hmi` | `hostname`, `id`, `labctl status` | Se está trabajando en otra estación. Detenerse y cambiar al noVNC de HMI; no intentar modificar el rol desde el comando. |
| `simulate malware` devuelve `blocked` antes del paso 7 | `labctl status`, `classroom-state` | Quedó `os`/`application` activo o se ejecutó un reset parcial. No declarar un resultado nuevo; coordinar y restablecer la línea base. |
| No se observa el proceso del paso 6 | Repetir la consulta `processes` inmediatamente tras `simulate malware` | La ventana del `sleep` es temporal. Un resultado vacío tardío es **no observado**, no prueba de bloqueo. |
| Paso 8 devuelve `success` | `hostname`, `labctl status`, `classroom-state` | Política aplicada en otro host, política local en `false` o reset concurrente. Conservar salida, corregir el host y repetir solo coordinadamente. |
| Append de `controller.conf` tiene éxito | `id`, `stat`, `labctl status` | Usuario, host o permisos inesperados. Detenerse; no usar `sudo`, no repetir y no borrar evidencia. |
| Hash no cambia en paso 11 | `labctl status`, `sha256sum`, ruta exacta | `supply-chain` pudo estar activo o el comando no llegó al endpoint. No afirmar que se alteró el firmware. |
| Paso 13 devuelve `success` o el hash cambia después de `blocked` | `labctl status`, dos hashes y salida completa de ambos comandos | La barrera no estaba activa o existe una discrepancia temporal. Conservar todos los resultados y escalar; no sustituirlos. |
| `osqueryi` devuelve `[]` | `stat` de la ruta y repetición de la consulta | Registrar **no observado**. La consulta manual no demuestra ausencia absoluta ni sustituye osqueryd. |
| `classroom-state` muestra `unavailable` o Kibana no carga | `labctl status`, `inventory`, errores completos | Es una condición de disponibilidad/observabilidad. Continuar solo con evidencia local válida o detenerse; no convertir un panel vacío en éxito. |

No se deben introducir `jq` ni rutas de JSON supuestas: `labctl` usa wrappers diferentes según el comando. Leer la respuesta real antes de elegir un campo.

## MITRE ATT&CK for ICS, IEC 62443 y Ley 21.663

- **MITRE ATT&CK for ICS:** el ejercicio ilustra una defensa de aplicación y una comprobación de integridad de archivos dentro de una maqueta. No demuestra malware avanzado, persistencia, evasión ni cobertura de un endpoint real.
- **IEC 62443:** el trabajo se alinea de forma pedagógica con requisitos fundacionales de protección del sistema y autenticidad/integridad de activos, especialmente FR3 y FR7 en el alcance de la guía original. El nivel de seguridad objetivo (`SL-T`) debe definirse por análisis de riesgo de cada zona; un conjunto de comandos de aula no produce un `SL-A` ni una certificación.
- **Ley 21.663:** esta práctica puede servir como registro interno de una verificación técnica acotada en una organización chilena, pero no acredita cumplimiento jurídico, no reemplaza responsables, análisis de riesgos, procedimientos de continuidad ni las obligaciones que correspondan a la organización.

## Qué controla realmente cada barrera y qué no controla

- **Allowlisting de aplicación:** controla el lanzador benigno registrado por el agente en el endpoint actual. No es un antivirus global, no cubre todas las rutas o procesos y no impide por sí solo la descarga del archivo.
- **Permisos `0640`:** restringen la escritura del usuario `student` sobre un archivo Linux concreto y conservan lectura del grupo. No son control de acceso industrial, MAC del kernel ni firma de configuración.
- **Supply chain:** compara el candidato de texto fijo con un SHA-256 de referencia y rechaza el mismo candidato alterado. No es PKI empresarial, firma de fabricante, control de arranque ni despliegue seguro de firmware real.
- **Reset:** restablece políticas/proceso y conserva evidencia. No es recuperación de una planta, no libera stock cuarentenado y no revierte por sí solo el firmware; por eso el cierre restaura primero supply chain.
- **Observabilidad:** `lab.endpoint`, `lab.control`, osquery, Kibana, Suricata y PCAP son fuentes distintas con alcances distintos. Un log de aplicación no se debe presentar como detección independiente de osquery o Suricata.

La maqueta no equivale a SELinux/AppArmor, GPO, firewall transparente, protección endpoint completa, SIS, PLC certificado ni proceso alimentario real. La simulación acelerada no permite calcular salud alimentaria ni tomar decisiones sobre una tienda o planta.

## Uso responsable y siguiente paso fuera del aula

Usar este taller solo en la maqueta aislada y autorizada. No conectar HMI, PLC, RTU, gateways ni tiendas reales; no enviar notificaciones reales a ANCI. Un caso contextual para discusión —sin atribuirlo a una organización— es un proveedor con acceso compartido, copia de configuración sin hash y cambios de HMI sin validación del proceso. En una operación real, el siguiente paso sería identificar al dueño del activo, documentar el cambio y su reversión, probar fuera de producción y acordar una ventana con operaciones. No bloquear remotamente una planta sin evaluar la seguridad física.

Este borrador cubre únicamente el taller 03. No usa este flujo como sustituto de las ampliaciones específicas de otras guías: el desafío 09 debe separar hosts y sus siete controles, y el módulo 10 debe desarrollar individualmente sus seis prácticas.
