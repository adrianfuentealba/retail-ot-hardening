# 09 · Desafío integrador: turno de madrugada

> **Aula compartida, exclusivamente educativa y aislada.** SCL-01 es una tienda simulada: las cinco estaciones no representan cinco tiendas ni cinco procesos térmicos independientes.

Esta guía es autosuficiente. Se trabaja desde la **Terminal real del noVNC recomendado**, con esta guía abierta en **Firefox local**. No es necesario volver al portal para seguir instrucciones. El navegador solo sirve para leer la guía y, de forma opcional, observar el panel local o Kibana; todas las acciones y evidencias se toman desde la Terminal.

## 1. Encargo y resultado que se debe demostrar

SCL-01 presenta un aumento térmico y actividad benigna en un endpoint al mismo tiempo. No hay evidencia suficiente para atribuir ambos hechos a una campaña única. El objetivo es proteger la operación, demostrar **siete barreras**, separar evidencia local de evidencia global y entregar un expediente razonado:

1. inventario, topología y excepción de administración;
2. línea base y ataques educativos controlados antes del endurecimiento;
3. dos fuentes independientes para la escritura Modbus y su bloqueo;
4. permisos, allowlist de aplicación y detención del proceso benigno en cada endpoint que se proteja;
5. OPC UA seguro y `Write` rechazado, sin afirmar que se eliminó todo canal `None`;
6. integridad del archivo ficticio y límites de la evidencia de firma/PKI;
7. recuperación operacional, con cuarentena conservada, más un borrador de aplicabilidad y RACI de Ley 21.663.

La rúbrica del taller es de 100 puntos: inventario/topología/excepción (20), dos evidencias de escritura y bloqueo (20), permisos/allowlist/proceso (20), OPC UA (15), integridad ficticia y límites de PKI (10), recuperación y cuarentena (10), y borrador Ley 21.663/RACI (5). **No hay certificación IEC/SL-A** y no se inventa una alerta cuando falta evidencia.

### Los siete controles

| Nº | Comando | Alcance real | Barrera que se demuestra | Qué no demuestra |
|---:|---|---|---|---|
| 1 | `labctl harden os` | Endpoint actual | `controller.conf` pasa a `0640`, propietario `root:student` | No endurece HMI, PLC ni las demás estaciones |
| 2 | `labctl harden application` | Endpoint actual | El lanzador local detiene el proceso benigno registrado y bloquea una nueva emulación | No es un antivirus global |
| 3 | `labctl harden plc` | Proceso/PLC del aula | La consigna queda limitada a `0–6 °C` y vuelve a nominal | No reemplaza una recuperación ni una cuarentena |
| 4 | `labctl harden network` | Gateway y guardas de los endpoints fijos | Bloquea FC06/FC16 en el gateway y marcadores laterales | No elimina la conectividad ni prueba aislamiento de producción |
| 5 | `labctl harden access` | Política global del aula | La ruta `simulate defrost` acepta el rol `ws-engineering` y rechaza otros hosts | No es MFA ni una compuerta universal para comandos Red/Purple Team |
| 6 | `labctl harden opcua` | Variable OPC UA del proceso | Cliente educativo con `SignAndEncrypt` y variable de solo lectura | No prueba PKI empresarial ni retiro universal de `None` |
| 7 | `labctl harden supply-chain` | Archivo ficticio del endpoint actual | Restaura la referencia y rechaza el mismo candidato alterado | No es firma de firmware productivo |

`labctl recover` es una **respuesta operacional**, no un octavo control: detiene marcadores disponibles y recupera la operación del modelo, pero no libera stock ni sustituye el endurecimiento.

## 2. Estaciones, alcance y orden de trabajo

Los comandos de endpoint operan en la estación donde está la Terminal. Cambiar de escritorio no ocurre automáticamente al ejecutar un comando.

| Host fijo | Uso en este desafío | Acciones permitidas/recomendadas |
|---|---|---|
| `ws-engineering` | Estación principal para preparar el escenario, aplicar controles del proceso y probar la excepción de administración | Ejecutar aquí las acciones globales y el endpoint local de ingeniería |
| `ws-hmi` | Segundo endpoint para probar que las políticas locales no se heredan | Repetir aquí `harden os`, `harden application` y `harden supply-chain` si la HMI también queda dentro del alcance |
| `ws-vendor` | Prueba negativa de rol después de `harden access` | Ejecutar solo la prueba de `simulate defrost`; no usarlo para afirmar que ingeniería está protegida |
| `ws-soc` | Observación y consulta de evidencia | Puede consultar `labctl classroom-state`; no hace falta mutar políticas |
| `ws-corporate` | Host fijo del aula, fuera de la ruta principal del escenario | No confundirlo con una quinta tienda |

Los controles de **proceso/gateway** (`harden plc`, `harden network`, `harden access`, `harden opcua`) se invocan desde `ws-engineering` y son globales según el panel. Los controles de **endpoint** (`os`, `application`, `supply-chain`) solo afectan al endpoint actual, aunque el panel muestre el gemelo de todos. Un `labctl reset` en HMI no equivale a endurecer ingeniería.

`labctl reset-all` es un reset coordinado del aula completa, conserva la evidencia y afecta a otros alumnos. No se ejecuta durante la sesión de otra persona. `labctl classroom-state` es solo lectura del gemelo (`process`, `gateway`, `endpoints`, `policies`, eventos e historial). `labctl guides` abre la guía HTML **local**, no la interfaz del portal.

## 3. Referencias y límites de interpretación

El ejercicio usa MITRE ATT&CK for ICS como vocabulario para cambios no autorizados de proceso, ejecución de artefactos y movimiento lateral; IEC 62443 como marco de zonas/conduits, mínimo privilegio, control de acceso, integridad y monitoreo; y Ley 21.663 como contexto para documentar aplicabilidad, roles y evidencia. Este mapeo es didáctico: **no declara cumplimiento, certificación, nivel SL, notificación efectiva ni una obligación legal concreta**.

| Hecho del desafío | MITRE ATT&CK for ICS, uso didáctico | IEC 62443, uso didáctico | Evidencia que sí se entrega |
|---|---|---|---|
| Consigna FC06/FC16 antes y después | Cambio remoto de parámetro/comando | Restricción de comunicaciones y mínimo privilegio | Respuesta TCP real, evento del panel y estado del gateway/PLC |
| Emulación de malware benigno | Ejecución de archivo/proceso en endpoint | Control de aplicación y defensa del componente | Evento local, `pgrep`, política y evidencia de endpoint |
| Marcadores entre hosts fijos | Movimiento lateral en red de entrenamiento | Segmentación/contención del conduit educativo | Resultados por target y políticas de endpoints |
| OPC UA `Write` | Cambio de variable de proceso | Canal protegido y autorización de variable | `security`, `before`, `readback`, estado del proceso |
| Firmware ficticio alterado | Manipulación de software de control | Integridad del componente y cadena de suministro | `sha256sum` antes/después, evento de rechazo |

El borrador Ley 21.663 se guarda como material de aula, no se envía a ANCI ni a ninguna autoridad. La aplicabilidad real y cualquier notificación requieren una revisión jurídica y organizacional separada.

## 4. Evidencia, copiado y forma de leer las salidas

- En Firefox local pulsa **Copiar** en esta guía y pega en `xfce4-terminal` con `Ctrl+Shift+V`. No uses el portapapeles del anfitrión, no copies el `$` del prompt y no pegues salidas JSON en la shell. Como alternativa, selecciona el comando en Firefox y usa `Ctrl+C` dentro del navegador/Terminal local.
- Cada bloque siguiente es para la Terminal del host indicado. Ejecuta **un comando por vez** y deja que termine antes de continuar. No se indican tiempos de resolución.
- Todas las evidencias del alumno se guardan en `~/lab/evidencias/taller-09/`, que en estas estaciones corresponde a `/home/student/lab/evidencias/taller-09/`. No redirijas datos al `/evidence` del collector.
- Timestamps, versión de `osquery`, host, PID, hash y cualquier valor de estado son variables. Se conservan literalmente tal como aparezcan; no se reemplazan por números de ejemplo.
- `labctl status` devuelve directamente el estado del endpoint actual. `baseline` y `detect` devuelven un envoltorio con `event`, `rows` y `policies`. `simulate defrost` devuelve `event` y `packet`. `simulate lateral` devuelve `targets`. `simulate opcua` devuelve `event`, `security`, `before` y `readback`. No supongas que todas las respuestas tienen `.event.outcome` en la misma ruta.
- El `event` de `labctl evidence` es la bitácora local del endpoint; `osquery_logs` es una ruta informativa del collector. El evento del panel, el estado del PLC/gateway, `osqueryi`, `stat`, `pgrep`, `sha256sum` y los paquetes son fuentes distintas.
- La observación visual opcional puede hacerse en la misma Firefox con `http://panel:8000/` y `http://kibana:5601/`. No hace falta una captura de pantalla inventada: la evidencia principal son los archivos JSON/texto guardados en la ruta anterior.

## 5. Procedimiento completo

### Paso 0 — Abrir la guía local y confirmar la estación recomendada

**Propósito.** Trabajar con la copia local de la guía, no con el portal, y comenzar en `ws-engineering`.

**Dónde.** Cambia el noVNC al escritorio `ws-engineering`, abre su Terminal y ejecuta:

```sh
labctl guides
```

**Resultado esperado y significado.** Firefox abre la guía HTML local del aula. La Terminal sigue siendo el lugar de ejecución; si se abre el portal, ciérralo y vuelve a la guía local.

**Segunda evidencia.** En la Terminal guarda la identidad de la estación:

```sh
hostname | tee ~/lab/evidencias/taller-09/00-hostname-before.txt
```

Debe registrarse el host fijo que aparece, sin sustituirlo por `ws-engineering` si no coincide.

**Si difiere.** Si `labctl guides` aún no existe, la implementación del padre no está disponible: no sustituyas el comando por una URL del portal. Si `hostname` no es `ws-engineering`, cambia de escritorio antes de mutar el aula.

### Paso 1 — Crear el expediente local

**Propósito.** Separar las evidencias del alumno del collector y dar un lugar único al informe.

**Acción exacta, en `ws-engineering`:**

```sh
mkdir -p ~/lab/evidencias/taller-09
```

**Resultado esperado y significado.** El comando termina sin error; la carpeta queda bajo `/home/student/lab` y no bajo `/evidence`.

**Segunda evidencia.**

```sh
stat -c '%A %a %U:%G %n' ~/lab/evidencias/taller-09 | tee ~/lab/evidencias/taller-09/01-evidence-dir.txt
```

Debe mostrar una carpeta accesible al usuario de la Terminal. El texto de permisos puede variar según la imagen, pero la ruta debe ser exactamente la del taller.

**Si difiere.** Si no se puede crear la carpeta, verifica que la Terminal sea del usuario del laboratorio y que no se esté usando `sudo`; no cambies permisos del sistema. Informa el error y no redirijas al collector.

### Paso 2 — Restablecer el aula, solo con coordinación

**Propósito.** Iniciar desde un estado común y evitar que políticas o procesos de otro alumno falseen la línea base. Este reset es global y conserva evidencia.

**Precondición.** Confirma en el canal del aula que ningún otro alumno está ejecutando una práctica. Solo entonces, en `ws-engineering`:

```sh
labctl reset-all | tee ~/lab/evidencias/taller-09/02-reset-all.json
```

**Resultado esperado y significado.** JSON de la operación de aula completa; se espera que políticas/proceso/endpoints queden disponibles para una línea base, pero la evidencia anterior no se borra.

**Segunda evidencia.**

```sh
labctl classroom-state | tee ~/lab/evidencias/taller-09/03-classroom-after-reset.json
```

Revisa los campos `process`, `gateway`, `endpoints` y `policies`. No uses `labctl status` de un solo host para declarar que el aula completa se restableció.

**Si difiere.** Si `reset-all` informa que no está disponible, detén el taller: no lo sustituyas por cinco `labctl reset` sin coordinación. Si algún endpoint aparece `unavailable`, conserva el JSON, cambia al host recomendado o informa al responsable del aula. Recuerda que `reset` no restaura por sí solo el firmware original.

### Paso 3 — Capturar host, usuario, estado local e inventario

**Propósito.** Probar quién ejecuta cada acción y distinguir estado local de estado global.

**Acción 1, en la misma Terminal:**

```sh
hostname | tee ~/lab/evidencias/taller-09/04-hostname.txt
```

**Resultado esperado y significado.** Un nombre de host fijo del laboratorio; es la estación desde la que se ejecutan los siguientes comandos.

**Segunda evidencia/diagnóstico.** Si no es `ws-engineering`, cambia de noVNC y repite el comando; no intentes corregirlo con variables de entorno.

**Acción 2:**

```sh
id | tee ~/lab/evidencias/taller-09/05-id.txt
```

**Resultado esperado y significado.** Identidad del usuario del laboratorio, normalmente `student`, sin asumir permisos administrativos generales.

**Segunda evidencia/diagnóstico.**

```sh
labctl status | tee ~/lab/evidencias/taller-09/06-status-initial.json
```

El resultado debe incluir `host`, `role`, `policies`, `mode` y `osquery`. `mode` refleja solo el `controller.conf` de esta estación. Si el host/rol no corresponde, cambia al escritorio correcto; si una política ya está activa, conserva el JSON y coordina otro `reset-all` antes de continuar.

**Acción 3:**

```sh
labctl inventory | tee ~/lab/evidencias/taller-09/07-inventory.json
```

**Resultado esperado y significado.** JSON con `source: osqueryi` y filas de `system_info`; es el inventario local del endpoint, no una enumeración de producción.

**Segunda evidencia/diagnóstico.** Compara el `hostname` capturado con el campo `host` de `labctl status`. Si `inventory` falla, no instales herramientas: guarda el error y usa el estado del endpoint para explicar la limitación.

### Paso 4 — Preparar una línea base vulnerable sin perder la referencia de firmware

**Propósito.** `labctl reset` devuelve políticas y permisos del endpoint, pero **no restaura `firmware.bin`**. Para que la emulación de firmware empiece desde la referencia, primero se usa `harden supply-chain` y después el reset local.

**Dónde.** En `ws-engineering` y luego en `ws-hmi`, una estación a la vez. En ingeniería:

```sh
labctl harden supply-chain | tee ~/lab/evidencias/taller-09/08-prep-engineering-supply-chain.json
```

**Resultado esperado y significado.** Evento local de `harden-supply-chain` y restauración del contenido de referencia del archivo ficticio. Esta aplicación de hardening es solo preparación; todavía se hará `reset` para dejar vulnerables las políticas del escenario.

**Segunda evidencia.**

```sh
sha256sum /home/student/lab/firmware.bin | tee ~/lab/evidencias/taller-09/09-firmware-reference-engineering.txt
```

Conserva el hash que aparezca, sin escribirlo en la guía ni inventar uno.

**Acción de cierre de la preparación local:**

```sh
labctl reset | tee ~/lab/evidencias/taller-09/10-reset-engineering.json
```

**Resultado esperado y significado.** Políticas del endpoint en falso, `controller.conf` vulnerable y evidencia conservada; el firmware queda en la referencia porque fue restaurado antes del reset.

**Segunda evidencia/diagnóstico.**

```sh
labctl status | tee ~/lab/evidencias/taller-09/11-status-engineering-vulnerable.json
```

Debe reflejar las políticas locales desactivadas y modo vulnerable. Si el hash o el modo no coinciden con la línea base, no continúes: repite `harden supply-chain` y luego `reset` en esa estación, dejando ambos eventos registrados.

**Repetición en HMI.** Cambia al escritorio `ws-hmi` y ejecuta exactamente `labctl harden supply-chain`, `sha256sum /home/student/lab/firmware.bin` y `labctl reset`, guardando los archivos con prefijo `hmi-`. Después vuelve a `ws-engineering`. Esta repetición es necesaria si la HMI forma parte del alcance; un reset de ingeniería no modifica la HMI.

### Paso 5 — Línea base del endpoint y permisos reales

**Propósito.** Documentar el archivo de ingeniería antes del ataque y probar que la consulta manual de `osqueryi` no se confunde con una consulta programada de `osqueryd`.

**Dónde.** `ws-engineering`, después de volver del escritorio HMI.

**Acción exacta:**

```sh
labctl baseline | tee ~/lab/evidencias/taller-09/12-baseline-engineering.json
```

**Resultado esperado y significado.** En `rows` aparece la consulta del `controller.conf`; en una línea base recién preparada se espera modo `0666` y usuario `1000`/`student`. El envoltorio también incluye un `event` manual y `policies` locales.

**Segunda evidencia:**

```sh
stat -c '%A %a %U:%G %n' /home/student/lab/controller.conf | tee ~/lab/evidencias/taller-09/13-controller-before.stat
```

Debe confirmar los permisos/propietario observados. `stat` es evidencia independiente de la fila de `osqueryi`.

**Si difiere.** Un modo ya endurecido significa que la preparación no fue vulnerable o que otro alumno actuó sobre la estación; conserva ambos resultados y coordina `reset-all`. No concluyas que `ws-hmi` o el PLC tienen el mismo estado.

### Paso 6 — Ataque controlado de consigna antes del hardening

**Propósito.** Registrar el aumento de consigna que se debe bloquear. La ruta fija envía una petición Modbus TCP real al gateway; no se usan IP, puertos ni payloads libres.

**Acción exacta, aún en `ws-engineering`:**

```sh
labctl simulate defrost | tee ~/lab/evidencias/taller-09/14-defrost-before.json
```

**Resultado esperado y significado.** En el estado vulnerable, la respuesta normalmente contiene `event` con acción `defrost` y un `packet` con `protocol: Modbus TCP`, `function: 6`, `source: actual TCP response` y `exception: false`; el valor solicitado por la simulación es 50. Estos son campos esperados del escenario, no una salida capturada por adelantado.

**Segunda evidencia:**

```sh
curl http://panel:8000/api/packets | tee ~/lab/evidencias/taller-09/15-packets-before.json
```

Busca una entrada de lectura/escritura compatible y conserva el paquete tal como lo devuelva el panel. La lectura FC03 periódica puede seguir apareciendo aunque la escritura sea permitida.

**Si difiere.** Si ya aparece `blocked`, consulta `labctl classroom-state`: puede haber quedado activa una política de gateway/PLC o el host no ser ingeniería. Si el `packet` no tiene `source: actual TCP response`, guarda el error y no lo presentes como prueba de red.

### Paso 7 — Actividad benigna del endpoint y su evidencia temporal

**Propósito.** Registrar el marcador de malware educativo y no confundir la ausencia posterior de un proceso temporal con un bloqueo.

**Acción exacta:**

```sh
labctl simulate malware | tee ~/lab/evidencias/taller-09/16-malware-before.json
```

**Resultado esperado y significado.** En la línea base, `event.action` es `malware-emulation`, `outcome` es `success` y el mensaje deja claro que es un marcador benigno y un `sleep` de 45 segundos; no se cifra nada ni se ejecuta malware real.

**Segunda evidencia:**

```sh
pgrep -af '[r]etail-benign-malware' | tee ~/lab/evidencias/taller-09/17-malware-process-before.txt || true
```

Si el proceso sigue vivo, su PID y línea de comando son evidencia capturada y deben conservarse sin inventar valores. Si no aparece, el proceso temporal puede haber terminado: no lo presentes como bloqueo.

**Si difiere.** Si no aparece y aún no se aplicó `harden application` ni `harden os`, ejecuta de nuevo `labctl simulate malware` en coordinación y repite `pgrep` inmediatamente. Si el evento ya es `blocked`, verifica `labctl status` y `classroom-state` antes de atribuir la causa.

### Paso 8 — Movimiento lateral educativo antes de las guardas

**Propósito.** Mostrar que el ejercicio usa solo los dos destinos fijos y que un marcador benigno no es explotación ni robo de credenciales.

**Acción exacta:**

```sh
labctl simulate lateral | tee ~/lab/evidencias/taller-09/18-lateral-before.json
```

**Resultado esperado y significado.** `targets` contiene únicamente `ws-engineering` y `ws-hmi`; en una línea base disponible, cada respuesta puede tener `event.action: lateral` y `outcome: success` con mensaje de marcador de entrenamiento.

**Segunda evidencia:**

```sh
labctl classroom-state | tee ~/lab/evidencias/taller-09/19-classroom-lateral-before.json
```

Confirma en `endpoints` el host y el rol de cada destino. No confundas `unreachable` con `blocked`: son diagnósticos diferentes.

**Si difiere.** Si aparece `blocked`, una guardia global ya estaba activa. Si aparece `unreachable`, conserva el detalle y no declares éxito ni aislamiento; el endpoint fijo puede no estar listo.

### Paso 9 — OPC UA antes de proteger canal y variable

**Propósito.** Capturar el contraste que luego se probará: el cliente educativo usa `None` y puede escribir en la variable antes del hardening.

**Acción exacta:**

```sh
labctl simulate opcua | tee ~/lab/evidencias/taller-09/20-opcua-before.json
```

**Resultado esperado y significado.** En un proceso vulnerable se esperan campos `security: None`, `event.action: opcua-write`, un resultado de escritura permitido y `readback` igual al valor solicitado por la simulación. El campo `before` debe conservarse tal como aparezca; el modelo nominal recién reiniciado parte de 2, pero la evidencia real manda.

**Segunda evidencia:**

```sh
labctl classroom-state | tee ~/lab/evidencias/taller-09/21-classroom-opcua-before.json
```

Compara el estado `process` con `before`/`readback`. Esta segunda lectura no reemplaza la respuesta del cliente OPC UA.

**Si difiere.** Si el cliente no conecta, guarda el tipo de error y revisa `process`/`gateway`; no declares que el Write fue bloqueado. Si ya aparece `SignAndEncrypt` o `blocked`, la línea base no estaba vulnerable y debe coordinarse un reset del aula.

### Paso 10 — Firmware ficticio antes de la integridad

**Propósito.** Demostrar que el archivo es una referencia educativa que cambia y luego puede rechazarse por hash, sin afirmar firma de firmware productivo.

**Acción 1:**

```sh
sha256sum /home/student/lab/firmware.bin | tee ~/lab/evidencias/taller-09/22-firmware-before-hash.txt
```

**Resultado esperado y significado.** Un hash capturado de la referencia preparada en el Paso 4. No se copia un hash de ejemplo desde esta guía.

**Acción 2:**

```sh
labctl simulate firmware | tee ~/lab/evidencias/taller-09/23-firmware-altered.json
```

**Resultado esperado y significado.** Evento local `firmware` con `outcome: success`; el texto del archivo ficticio se altera y no se instala firmware ejecutable.

**Acción 3:**

```sh
sha256sum /home/student/lab/firmware.bin | tee ~/lab/evidencias/taller-09/24-firmware-altered-hash.txt
```

**Segunda evidencia y diagnóstico.** El hash debe diferir del `22-firmware-before-hash.txt`. Si no difiere, el archivo no estaba en la referencia o la emulación no se ejecutó; conserva la salida y no inventes una alteración.

### Paso 11 — Expediente inicial: hechos, hipótesis y fuentes

**Propósito.** Separar hechos observados de hipótesis antes de cambiar la operación. No se edita el repositorio ni se escribe en `/lab/docs`.

**Acción exacta para crear una plantilla local:**

```sh
cat > ~/lab/evidencias/taller-09/respuesta-chile.md <<'EOF'
# SCL-01 — hechos, hipótesis y borrador Ley 21.663

## Hechos observados
- Host y usuario: completar desde 00/04/05.
- Línea base de controller.conf: completar desde 12/13.
- Consigna Modbus y paquete: completar desde 14/15.
- Actividad benigna y proceso: completar desde 16/17.
- Targets laterales: completar desde 18/19.
- OPC UA: completar desde 20/21.
- Firmware ficticio y hashes: completar desde 22/23/24.

## Hipótesis no confirmadas
- No atribuir el aumento térmico y el marcador benigno a una campaña única sin evidencia adicional.
- No inferir inocuidad alimentaria a partir de los ticks del simulador.
- No inferir PKI empresarial, certificación IEC/SL-A ni eliminación universal de OPC UA None.

## Aplicabilidad y RACI de aula
- Aplicabilidad: pendiente de validación jurídica y organizacional; este borrador no se envía a autoridades.
- R: operador/ingeniería ejecuta contención y recuperación.
- A: responsable de operación retail/OT acepta riesgo y cierre.
- C: SOC, proveedor y mantenimiento aportan evidencia y diagnóstico.
- I: cumplimiento, legal y dirección reciben el expediente según procedimiento interno.

## Decisiones y límites
- Mantener stock afectado en cuarentena hasta una decisión autorizada.
- No afirmar que un marcador benigno es malware real.
- Conservar evidencia aunque se haga reset coordinado posterior.
EOF
```

**Resultado esperado y significado.** Se crea un borrador local con campos para completar, sin hashes, PID ni timestamps inventados. Completa los campos con los archivos JSON/texto ya capturados.

**Segunda evidencia.**

```sh
stat -c '%A %a %U:%G %n' ~/lab/evidencias/taller-09/respuesta-chile.md | tee ~/lab/evidencias/taller-09/25-respuesta-stat.txt
```

**Si difiere.** Si el heredoc se pegó con el prompt `$` o quedó incompleto, abre el archivo con un editor local y corrige solo el expediente bajo `~/lab/evidencias/taller-09/`. No escribas en el repo.

## 6. Aplicar los siete controles, uno por uno

### Paso 12 — Control 1: endurecer permisos del endpoint de ingeniería

**Propósito.** Quitar la escritura pública del archivo de ingeniería sin afirmar que se endurecieron otras estaciones.

**Dónde.** Volver/continuar en `ws-engineering`.

**Acción exacta:**

```sh
labctl harden os | tee ~/lab/evidencias/taller-09/26-engineering-harden-os.json
```

**Resultado esperado y significado.** Evento local `harden-os` exitoso. El agente cambia realmente `controller.conf` a modo `0640` y propietario `root:student`.

**Segunda evidencia:**

```sh
osqueryi --json "SELECT path,mode,uid FROM file WHERE path='/home/student/lab/controller.conf';" | tee ~/lab/evidencias/taller-09/27-engineering-controller-osquery-after.json
```

Complementa con:

```sh
stat -c '%A %a %U:%G %n' /home/student/lab/controller.conf | tee ~/lab/evidencias/taller-09/28-engineering-controller-after.stat
```

La primera consulta debe mostrar el modo y UID observados; `stat` aporta grupo y propietario legibles. No inventes el formato exacto que use la imagen para `mode`.

**Prueba de escritura y lectura con el usuario del laboratorio:**

```sh
bash -c "printf '%s\n' '# unauthorized-append-test' >> /home/student/lab/controller.conf" 2>&1 | tee ~/lab/evidencias/taller-09/28b-engineering-append-denied.txt || true
```

Debe aparecer `Permission denied`; no se debe modificar el archivo. La lectura sigue permitida:

```sh
cat /home/student/lab/controller.conf | tee ~/lab/evidencias/taller-09/28c-engineering-controller-readable.txt
```

El contenido leído es una segunda evidencia funcional de que el control quita escritura pública sin quitar lectura. Si el append no es denegado, detén la actividad, conserva el resultado y no intentes corregir permisos con `sudo`.

**Si difiere.** Si sigue `0666` o `student:student`, revisa que estés en ingeniería y guarda `labctl status`; no uses `sudo chmod`. Si la consulta de `osqueryi` difiere de `stat`, reporta ambas fuentes y no fuerces una conclusión.

### Paso 13 — Control 2: endurecer el lanzador de aplicación de ingeniería

**Propósito.** Detener el proceso benigno registrado y bloquear una nueva emulación local.

**Acción exacta:**

```sh
labctl harden application | tee ~/lab/evidencias/taller-09/29-engineering-harden-application.json
```

**Resultado esperado y significado.** Evento local `harden-application` exitoso; el agente termina los procesos benignos que mantiene registrados y activa la política local.

**Segunda evidencia:**

```sh
pgrep -af '[r]etail-benign-malware' | tee ~/lab/evidencias/taller-09/30-engineering-malware-after.txt || true
```

La salida esperada después de la contención no contiene ese proceso. La prueba fuerte de bloqueo se obtiene con:

```sh
labctl simulate malware | tee ~/lab/evidencias/taller-09/31-engineering-malware-regression.json
```

Debe aparecer `event.action: malware-emulation`, `outcome: blocked`, con mensaje de descarga del marcador y guardia local de ejecución.

**Si difiere.** Si el proceso ya había terminado antes de `harden application`, su ausencia no demuestra que la barrera lo mató: usa el evento/`pgrep` del Paso 7 y el rechazo de `31` como pruebas separadas. Si `31` no queda bloqueado, revisa `labctl status` local; `harden application` no es una política global.

### Paso 14 — Control 3: endurecer el límite de la consigna en el PLC

**Propósito.** Validar en el modelo que una escritura fuera de `0–6 °C` se rechaza antes de cambiar la consigna.

**Acción exacta, en `ws-engineering`:**

```sh
labctl harden plc | tee ~/lab/evidencias/taller-09/32-harden-plc.json
```

**Resultado esperado y significado.** Evento de panel `harden-plc` exitoso. El PLC aplica el guard de consigna y vuelve a nominal.

**Segunda evidencia:**

```sh
labctl classroom-state | tee ~/lab/evidencias/taller-09/33-classroom-after-plc.json
```

En `process` busca el guard de PLC activo y un valor nominal; no calcules salud alimentaria desde `temperature` o `cycle`.

**Si difiere.** Si el evento de panel está presente pero el estado del proceso no cambia, conserva ambos JSON y no lo llames control efectivo. Si el endpoint no está disponible, no conviertas el modo demostración en ejecución real.

### Paso 15 — Aislar la evidencia del PLC antes de añadir el bloqueo de red

**Propósito.** Probar que el límite del PLC bloquea la misma FC06 incluso cuando el gateway todavía permite el paso.

**Acción exacta:**

```sh
labctl simulate defrost | tee ~/lab/evidencias/taller-09/34-defrost-after-plc-before-network.json
```

**Resultado esperado y significado.** Respuesta con `packet.function: 6` y `packet.exception: true`/evento `blocked`. La razón debe corresponder al límite del PLC, no a una afirmación genérica de red.

**Segunda evidencia:**

```sh
curl http://panel:8000/api/packets | tee ~/lab/evidencias/taller-09/35-packets-after-plc.json
```

Relaciona el paquete con el evento del Paso 34 y con `process` del Paso 33. FC03 de lectura puede continuar.

**Si difiere.** Si el paquete no queda bloqueado, verifica `process.plc_guard` en el classroom state y que sigas en ingeniería. Si ya aparece un bloqueo de gateway, una política de red estaba activa antes: documenta esa limitación y no atribuyas causalidad exclusiva al PLC.

### Paso 16 — Control 4: endurecer gateway y guardas laterales

**Propósito.** Bloquear FC06/FC16 en el gateway y activar la guarda de marcadores en los endpoints fijos, conservando la conectividad de lectura.

**Acción exacta, en ingeniería:**

```sh
labctl harden network | tee ~/lab/evidencias/taller-09/36-harden-network.json
```

**Resultado esperado y significado.** Evento global `harden-network` exitoso. El gateway debe reflejar `deny_writes: true`; los endpoints reciben su política local `network`.

**Segunda evidencia:**

```sh
labctl classroom-state | tee ~/lab/evidencias/taller-09/37-classroom-after-network.json
```

Revisa `gateway.deny_writes`, `gateway.blocked_writes` y `endpoints[*].policies.network`. Una lectura FC03 del panel puede continuar; el control no elimina conectividad.

**Si difiere.** Si solo cambia el endpoint actual, el comando no llegó al panel correcto: conserva la salida y usa `classroom-state`. Si no hay escritura bloqueada pero sí hay `deny_writes: true`, repite una prueba fija y captura su paquete; no uses un payload propio.

### Paso 17 — Control 5: habilitar la excepción de administración y probar el rol

**Propósito.** Aplicar la única excepción declarada: la ruta fija `simulate defrost` solo admite `ws-engineering`. No se debe describir como MFA ni como gate universal.

**Acción exacta, en `ws-engineering`:**

```sh
labctl harden access | tee ~/lab/evidencias/taller-09/38-harden-access.json
```

**Resultado esperado y significado.** Evento global `harden-access` exitoso; todos los endpoints fijos reciben la política de acceso.

**Segunda evidencia, desde `ws-engineering`:** cambia al noVNC de `ws-vendor` y ejecuta:

```sh
labctl simulate defrost | tee ~/lab/evidencias/taller-09/39-vendor-defrost-role-blocked.json
```

La respuesta debe ser un evento `defrost` con `outcome: blocked` y mensaje de gate de rol de entrenamiento, sin que se use como evidencia de MFA. Desde `ws-engineering`, una prueba posterior llegará al gateway y demostrará el bloqueo de escritura por red.

**Si difiere.** Si `ws-vendor` aparece `unreachable`, no lo llames rechazo de rol. Comprueba el `hostname`, `classroom-state.policies.access` y la disponibilidad del endpoint. Si una HMI o vendor puede escribir por otra ruta, eso no contradice este control: el guard solo cubre la ruta fija `simulate defrost`.

### Paso 18 — Control 6: proteger la variable OPC UA

**Propósito.** Usar el cliente educativo con `SignAndEncrypt` y confirmar que el `Write` queda rechazado por la variable de solo lectura.

**Dónde.** Vuelve a `ws-engineering`; no ejecutes esta acción desde `ws-vendor`.

**Acción exacta:**

```sh
labctl harden opcua | tee ~/lab/evidencias/taller-09/40-harden-opcua.json
```

**Resultado esperado y significado.** Evento global `harden-opcua` exitoso. La variable se protege y el cliente de la simulación queda preparado para canal `SignAndEncrypt`.

**Segunda evidencia y prueba:**

```sh
labctl simulate opcua | tee ~/lab/evidencias/taller-09/41-opcua-after.json
```

Debe conservar `security: SignAndEncrypt`, una operación `Write` con resultado `blocked` y `readback` sin el cambio solicitado. La respuesta es la evidencia del cliente; el `before` y el `readback` no se sustituyen por valores esperados.

**Tercera comprobación de estado:**

```sh
labctl classroom-state | tee ~/lab/evidencias/taller-09/42-classroom-after-opcua.json
```

Verifica los flags OPC UA del `process` y relaciona el evento con la respuesta real. **No afirmes que se eliminó `None` de todos los endpoints internos, que existe PKI empresarial o que hay certificación.**

**Si difiere.** Si `security` sigue siendo `None`, la política no quedó lista; conserva el error y el estado. Si el cliente falla antes de escribir, no lo presentes como `Write` rechazado: distingue error de conexión, rechazo de seguridad y rechazo de variable.

### Paso 19 — Control 7: restaurar y validar la cadena de suministro ficticia

**Propósito.** Restaurar la referencia del archivo y rechazar el mismo candidato alterado, dejando claro que el hash manual no equivale a una firma PKI.

**Acción exacta, en `ws-engineering`:**

```sh
labctl harden supply-chain | tee ~/lab/evidencias/taller-09/43-harden-supply-chain.json
```

**Resultado esperado y significado.** Evento local exitoso y `firmware.bin` restaurado a la referencia educativa.

**Segunda evidencia:**

```sh
sha256sum /home/student/lab/firmware.bin | tee ~/lab/evidencias/taller-09/44-firmware-restored-hash.txt
```

El hash de `44` debe coincidir con el hash capturado en `22`, comparando los textos reales, no un valor de esta guía.

**Prueba de regresión de la misma alteración:**

```sh
labctl simulate firmware | tee ~/lab/evidencias/taller-09/45-firmware-rejected.json
```

Debe aparecer `event.action: firmware`, `outcome: blocked` y mensaje de discrepancia SHA-256 del manifiesto ficticio. No se instala firmware ejecutable.

**Si difiere.** Si `44` no coincide con `22`, conserva ambos hashes y no declares restauración. Si `45` queda `success`, el estado local de `supply-chain` no está activo; revisa `labctl status` en ingeniería. Si solo se observa un hash manual, no lo presentes como firma digital ni certificación.

### Paso 20 — Repetir los tres controles locales en HMI

**Propósito.** Probar individualmente que el hardening de endpoint no se hereda desde ingeniería. Esta sección es obligatoria si la HMI se incluye en el alcance de SCL-01.

**Dónde.** Cambia al noVNC de `ws-hmi`; en cada bloque registra que el `hostname` sea HMI.

**20.1 OS:**

```sh
labctl harden os | tee ~/lab/evidencias/taller-09/46-hmi-harden-os.json
```

**Esperado/segunda evidencia:** `harden-os` local y, después:

```sh
osqueryi --json "SELECT path,mode,uid FROM file WHERE path='/home/student/lab/controller.conf';" | tee ~/lab/evidencias/taller-09/47-hmi-controller-osquery-after.json
```

`stat -c '%A %a %U:%G %n' /home/student/lab/controller.conf` puede guardarse como segunda lectura adicional. Debe resultar `0640` y `root:student`; si no, la HMI sigue vulnerable aunque ingeniería esté protegida.

**20.2 Aplicación:**

```sh
labctl harden application | tee ~/lab/evidencias/taller-09/48-hmi-harden-application.json
```

**Esperado/segunda evidencia:** el evento local es exitoso. Como la HMI puede no tener un proceso registrado, la prueba de guardia es:

```sh
labctl simulate malware | tee ~/lab/evidencias/taller-09/49-hmi-malware-blocked.json
```

Debe resultar `blocked`. Si hubo un proceso previo, `pgrep -af '[r]etail-benign-malware' || true` se guarda sin inventar PID.

**20.3 Cadena de suministro:**

```sh
labctl harden supply-chain | tee ~/lab/evidencias/taller-09/50-hmi-harden-supply-chain.json
```

**Esperado/segunda evidencia:** el archivo HMI vuelve a referencia. Verifica y prueba el candidato:

```sh
sha256sum /home/student/lab/firmware.bin | tee ~/lab/evidencias/taller-09/51-hmi-firmware-reference-hash.txt
```

```sh
labctl simulate firmware | tee ~/lab/evidencias/taller-09/52-hmi-firmware-blocked.json
```

El evento final debe quedar `blocked`. Los hashes de HMI y de ingeniería no tienen que ser escritos de memoria ni comparados entre hosts sin capturarlos.

**Si difiere.** Si alguno de los tres controles cambia también `ws-engineering`, se está confundiendo un comando local con uno global: usa `hostname` y `classroom-state`. Si HMI no está disponible, documenta el endpoint `unavailable` y no lo presentes como endurecido.

## 7. Recuperación y regresión final

### Paso 21 — Recuperar la operación sin liberar stock

**Propósito.** Detener marcadores disponibles, volver a la consigna nominal y conservar la cuarentena.

**Dónde.** Vuelve a `ws-engineering`.

**Acción exacta:**

```sh
labctl recover | tee ~/lab/evidencias/taller-09/53-recover.json
```

**Resultado esperado y significado.** Evento `recover` exitoso: el modelo reanuda el enfriamiento, detiene procesos benignos que estén disponibles y deja el stock afectado en cuarentena. Recuperar no endurece por sí solo, no borra evidencia y no libera producto.

**Segunda evidencia:**

```sh
labctl classroom-state | tee ~/lab/evidencias/taller-09/54-classroom-after-recover.json
```

Comprueba que el proceso vuelve hacia la consigna nominal, que los marcadores no siguen activos donde el endpoint respondió y que el indicador de producto afectado/quarantena no se interpreta como liberado. No calcules salud alimentaria real con `temperature`, `cycle` o ticks del simulador.

**Si difiere.** Si un endpoint aparece `unavailable`, el recuperador no pudo contenerlo: conserva el error y repite solo con ese host disponible, coordinando el aula. Si `spoiled`/cuarentena permanece, es el resultado esperado; `reset-all` puede rehabilitar el stock solo como operación de aula coordinada, no como recuperación real del producto.

### Paso 22 — Regresión de los cinco comportamientos, uno por uno

Ejecuta en `ws-engineering`, salvo la prueba HMI indicada. No agrupes las líneas en un bloque gigante.

**22.1 Consigna/FC06:**

```sh
labctl simulate defrost | tee ~/lab/evidencias/taller-09/55-defrost-final.json
```

**Esperado/segunda evidencia/diagnóstico.** `blocked`: en ingeniería debe verse la respuesta Modbus con excepción y el evento correspondiente. Confirma con `curl http://panel:8000/api/packets | tee ~/lab/evidencias/taller-09/55b-packets-final.json`. Si el mensaje atribuye el rechazo a la política de gateway, no lo atribuyas únicamente al PLC.

**22.2 Emulación de aplicación:**

```sh
labctl simulate malware | tee ~/lab/evidencias/taller-09/56-malware-final.json
```

**Esperado/segunda evidencia/diagnóstico.** `blocked`, con marcador local descargado pero sin ejecución; confirma con `pgrep -af '[r]etail-benign-malware' | tee ~/lab/evidencias/taller-09/56b-malware-final-process.txt || true`. Si no hay proceso, usa el evento `blocked`, no la mera ausencia de PID.

**22.3 Lateral:**

```sh
labctl simulate lateral | tee ~/lab/evidencias/taller-09/57-lateral-final.json
```

**Esperado/segunda evidencia/diagnóstico.** Los targets siguen siendo solo `ws-engineering` y `ws-hmi`, y sus eventos quedan `blocked` por las guardas. Confirma `endpoints[*].policies.network/access` con `labctl classroom-state | tee ~/lab/evidencias/taller-09/57b-classroom-lateral-final.json`. `unreachable` no equivale a `blocked`.

**22.4 OPC UA:**

```sh
labctl simulate opcua | tee ~/lab/evidencias/taller-09/58-opcua-final.json
```

**Esperado/segunda evidencia/diagnóstico.** `security: SignAndEncrypt`, operación `Write` `blocked` y `readback` sin el cambio; verifica los flags en `labctl classroom-state | tee ~/lab/evidencias/taller-09/58b-classroom-opcua-final.json`. Si falla la conexión, diagnostica conexión/seguridad antes de afirmar rechazo de escritura.

**22.5 Firmware:**

```sh
labctl simulate firmware | tee ~/lab/evidencias/taller-09/59-firmware-final.json
```

**Esperado/segunda evidencia/diagnóstico.** Candidato rechazado por discrepancia de referencia. Confirma que el hash del archivo sigue siendo el de referencia con `sha256sum /home/student/lab/firmware.bin | tee ~/lab/evidencias/taller-09/59b-firmware-final-hash.txt`; no escribas hashes esperados.

**22.6 Estado local:**

```sh
labctl status | tee ~/lab/evidencias/taller-09/60-status-final-engineering.json
```

**Esperado/segunda evidencia/diagnóstico.** El endpoint de ingeniería conserva `os`, `application` y `supply-chain` activos y el modo `0640`. `status` no enumera por sí solo las políticas globales: compáralo con `classroom-state`.

**22.7 Evidencia local:**

```sh
labctl evidence | tee ~/lab/evidencias/taller-09/61-evidence-final-engineering.json
```

**Esperado/segunda evidencia/diagnóstico.** Aparecen los últimos eventos locales y el campo informativo `osquery_logs`; se conserva evidencia aunque luego se haga un reset coordinado. Completa la segunda fuente global con `labctl classroom-state | tee ~/lab/evidencias/taller-09/62-classroom-final.json`.

## 8. Cierre y criterios de entrega

El expediente mínimo bajo `~/lab/evidencias/taller-09/` debe contener:

- `hostname`, `id`, `status` e `inventory` de ingeniería;
- confirmación coordinada de `reset-all` y el estado posterior;
- línea base de `controller.conf`, `stat` y consulta `osqueryi` antes/después;
- eventos y procesos de malware benigno, sin PID inventado;
- paquetes Modbus reales antes y después, con FC03 distinguido de FC06/FC16;
- resultados por target del lateral fijo;
- `security`, `before`, `readback` y estado OPC UA;
- hashes capturados antes, alterados y restaurados, sin valores inventados;
- evidencias locales separadas para HMI si fue incluida;
- `recover`, estado final y `respuesta-chile.md` con hechos, hipótesis, límites, aplicabilidad y RACI.

Antes de entregar, comprueba que el informe dice explícitamente:

- **Antes:** la escritura FC06/artefacto/proceso/OPC UA/firmware podía avanzar en la línea base vulnerable, según las evidencias realmente capturadas.
- **Después:** las siete barreras producen los rechazos descritos y sus fuentes independientes coinciden.
- **Límites:** la simulación es educativa; no prueba una tienda adicional, una campaña única, un antivirus global, aislamiento de producción, MFA universal, PKI empresarial, firma de firmware productivo, inocuidad alimentaria, certificación IEC/SL-A ni obligación de notificar.
- **Recuperación:** se detiene la actividad benigna y vuelve el proceso hacia nominal, pero el stock permanece en cuarentena hasta una decisión autorizada.

No ejecutes `labctl reset-all` para “limpiar” antes de copiar el expediente: altera el estado y afecta a otros alumnos. Si el aula debe quedar disponible para el siguiente grupo, coordina el reset-all después de preservar los JSON/textos y registra esa operación como un evento de cierre.

> **Delimitación con Módulo 10.** Las seis prácticas de Módulo 10 se realizan individualmente en su guía correspondiente. Este desafío 09 usa sus siete controles integrados, separa los hosts y no sustituye esas seis prácticas por un bloque Red/Purple Team genérico.
