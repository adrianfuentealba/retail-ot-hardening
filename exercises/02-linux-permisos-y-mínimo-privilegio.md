# 02 · Linux: permisos y mínimo privilegio

> **Taller local del laboratorio Retail OT.** Este documento es autosuficiente: las instrucciones se ejecutan en la terminal real de la estación noVNC indicada y la guía se consulta en el Firefox local. No es necesario volver al portal para saber qué hacer.

## Ficha del taller

- **Estación recomendada:** `ws-hmi`, rol HMI. Abrir su escritorio en noVNC y hacer doble clic en **Terminal del laboratorio**.
- **Usuario esperado:** `student`, sin `sudo` general. Las comprobaciones de archivo y las consultas `osqueryi` se ejecutan localmente en esa estación.
- **Objetivos medibles:**
  1. observar el estado inicial de `controller.conf` (`0666`, propietario del estudiante);
  2. aplicar el cambio real a `0640`, propietario `root` y grupo `student`;
  3. demostrar que el estudiante conserva lectura, pero no escritura;
  4. distinguir el permiso DAC del archivo del guard de ejecución del agente;
  5. comparar una actividad benigna permitida con el mismo intento bloqueado y entregar dos fuentes de evidencia.
- **Límite:** se descarga solamente un marcador de texto interno y se crea `sleep 45`; no hay malware operativo, explotación, cifrado, escaneo ni conexión a activos reales.

### Cómo pegar comandos

La guía debe estar abierta en el Firefox local mediante `labctl guides` o mediante el lanzador local que entregue el aula. Copiar un bloque sin el `$` del prompt ni una salida JSON y pegarlo en la **Terminal del laboratorio** con `Ctrl+Shift+V` de xfce4-terminal. No usar el portapapeles del anfitrión ni una consola web como sustituto de la terminal. Ejecutar cada bloque por separado y conservar la salida real; los PID, timestamps, tamaños, `_id` y hashes son variables y **no se deben inventar**.

## Alcance: estación actual frente a aula completa

| Acción | Alcance real | Qué no demuestra |
|---|---|---|
| `hostname`, `id`, `labctl status`, `inventory`, `baseline`, `detect`, `simulate malware`, `harden os`, `harden application`, `reset`, `evidence`, `osqueryi`, `stat` | Solo el endpoint donde está la terminal | No inspecciona mágicamente otra estación ni cambia PLC/gateway |
| `labctl classroom-state` | Lectura del gemelo de aula desde el panel; no cambia estado | No es una segunda detección independiente del endpoint |
| `labctl reset-all` | Restablece políticas/proceso y endpoints del aula completa y conserva evidencia | Afecta a los demás alumnos; requiere coordinación previa |
| Firefox con Kibana | Comprobación visual opcional de los documentos ya colectados | No ejecuta comandos en la estación |

`labctl reset` es únicamente el reset del endpoint actual. Para una línea base de toda el aula debe usarse `labctl reset-all`, implementado por el coordinador, y avisar antes a quienes compartan el entorno. No se debe ejecutar `docker`, `git`, `sudo chmod`, `sudo iptables` ni comandos de host desde esta terminal. Si la infraestructura no está disponible, el coordinador corrige el entorno fuera de la estación; no se reemplaza este procedimiento con `docker compose exec`.

## Preparación limpia y coordinada

### 0.1 Abrir la guía y acordar el reset de aula

**Propósito.** Asegurar que la guía es la copia local y que nadie pierde el estado de otra práctica.

```sh
labctl guides
```

**Resultado esperado y significado.** El comando abre o presenta las guías HTML/locales entregadas por el aula. No se usa su salida como evidencia técnica. `labctl guides`, `labctl classroom-state` y `labctl reset-all` son comodidades coordinadas por el padre; no asumir un formato JSON que la implementación no haya mostrado.

**Segunda comprobación.** Confirmar visualmente en Firefox que el título local es `02 · Linux: permisos y mínimo privilegio`; no usar el portal como fuente de instrucciones.

**Si difiere.** Si se abre la interfaz del portal o no aparece una guía local, no continuar con una guía vieja: avisar al coordinador para corregir el lanzador local. No cambiar rutas ni instalar herramientas.

### 0.2 Restablecer el aula, solo con coordinación

**Propósito.** Partir de políticas y procesos conocidos en las cinco estaciones sin borrar la evidencia histórica.

```sh
labctl reset-all
```

**Resultado esperado y significado.** La respuesta real del comando debe confirmar que el reset de aula fue aceptado. El reset conserva eventos, PCAP y marcadores; no es una limpieza forense ni un borrado de índices.

**Segunda comprobación.**

```sh
labctl classroom-state
```

El JSON debe incluir, al menos, las secciones del panel `/api/state`: `process`, `gateway`, `endpoints`, `policies`, `events`, `history`, `last_update` y `errors`. En la línea base, las políticas globales deben estar desactivadas y `ws-hmi` debe estar disponible; los valores de temperatura, contadores y timestamps se registran tal como aparezcan.

**Si difiere.** Si `reset-all` es rechazado, si hay otro escenario activo o si `errors` indica un componente caído, detenerse y coordinar. No repetir el reset de forma ciega: afecta a toda la cohorte. Un `labctl reset` posterior solo corregiría `ws-hmi`, no la discrepancia global.

### 0.3 Identificar host, usuario y hora

**Propósito.** Evitar atribuir una evidencia de HMI a otra estación y fijar la hora UTC de la comparación.

```sh
hostname
```

**Resultado esperado y significado.** Debe ser `ws-hmi` para esta ejecución. El nombre es la identidad del endpoint, no el nombre del portal.

**Segunda comprobación.**

```sh
id
```

Se espera un usuario `student` (normalmente UID 1000) y sus grupos locales; no asumir más privilegios por el hecho de poder solicitar una acción a `labctl`.

**Si difiere.** Si el host es `ws-engineering`, `ws-vendor`, `ws-corporate` o `ws-soc`, no adaptar la evidencia manualmente: cambiar a la estación `ws-hmi` recomendada y repetir esta identificación. Si el usuario no es `student`, detenerse y pedir corrección del escritorio.

```sh
date -u +%Y-%m-%dT%H:%M:%SZ
```

Registrar la salida junto con cada resultado. No sustituirla por una hora escrita a mano.

### 0.4 Crear el expediente local y tomar línea base

**Propósito.** Guardar las salidas del taller en el espacio permitido del estudiante, no en el volumen del collector.

```sh
mkdir -p ~/lab/evidencias/taller-02
```

**Resultado esperado y significado.** Se crea o reutiliza `~/lab/evidencias/taller-02`. No se escribe en `/evidence`; ese directorio pertenece al collector y solo se referencia mediante lecturas autorizadas.

**Segunda comprobación.**

```sh
labctl status
```

El resultado es la respuesta directa de `/health` del agente: `host`, `role`, `policies`, `mode` y versión de `osquery`. En una línea base limpia, `host` es `ws-hmi`, las políticas locales están en `false` y el modo de `controller.conf` es `0o666`.

**Si difiere.** Un modo `0o640`, `application: true`, `os: true` o un host distinto indica estado heredado o estación equivocada. No lo borres como si fuera evidencia: coordina el reset y vuelve a capturar `status`.

```sh
labctl inventory
```

**Resultado esperado y significado.** La respuesta tiene el envoltorio real `{"source":"osqueryi","rows":[...]}`; `rows` es el inventario local de `system_info`. No asumir que todas las acciones de `labctl` tienen `.event.outcome`.

**Segunda comprobación.**

```sh
osqueryi --json "SELECT hostname,cpu_type,physical_memory FROM system_info;"
```

Los campos deben identificar la misma estación y máquina. Los valores de CPU y memoria pueden variar y se conservan literalmente.

**Si difiere.** Si `inventory` funciona pero la consulta manual está vacía o falla, registrar la salida y revisar que se está en la terminal local de `ws-hmi`; `osqueryi` manual es independiente del `osqueryd` programado. No declarar que el host está limpio por una consulta vacía.

```sh
labctl baseline
```

**Resultado esperado y significado.** El agente devuelve un objeto con `event`, `rows` y `policies`; `rows` consulta el modo y UID de `/home/student/lab/controller.conf`. El evento de consulta es evidencia de que se hizo una lectura manual, no un certificado de seguridad.

**Segunda comprobación.**

```sh
stat -c 'mode=%a owner=%U group=%G uid=%u gid=%g path=%n' /home/student/lab/controller.conf
```

En la línea base se espera `mode=666`, dueño del estudiante y el path exacto. Conservar el resultado real, incluidos nombres y UID/GID.

**Si difiere.** Verificar el path con `hostname` y repetir `stat`; si el archivo no existe, `labctl status` tampoco será una línea base válida. Si el modo ya es restringido, no forzar `chmod`: coordinar `reset-all` y registrar el estado anómalo.

## Acciones paso a paso

### 1. Reproducir actividad benigna antes del control

**Propósito.** Establecer el antes: un endpoint sin las políticas de este taller acepta el flujo educativo y el agente crea un marcador local más un proceso `sleep` identificado.

```sh
labctl simulate malware
```

**Resultado esperado y significado.** La respuesta directa contiene `event.action: "malware-emulation"` y `event.outcome: "success"`, con un mensaje que identifica un marcador benigno y `sleep 45`. El archivo queda en `/home/student/lab/downloads/retail-marker.txt`. Esto no es malware ni prueba una intrusión real.

**Segunda evidencia: proceso local.** Ejecutarla inmediatamente, porque el proceso es temporal:

```sh
osqueryi --json "SELECT pid,name,cmdline,uid FROM processes WHERE name='sleep' AND cmdline LIKE '%retail-benign-malware%';"
```

La fila observada debe corresponder a `sleep`, mostrar el `cmdline` del escenario y el UID real. El PID no se predetermina.

**Segunda evidencia: archivo descargado.**

```sh
osqueryi --json "SELECT path,mode,uid,size FROM file WHERE path='/home/student/lab/downloads/retail-marker.txt';"
```

La fila acredita la presencia del marcador y su tamaño real; no asumir propietario, modo ni tamaño.

**Si difiere.**

- Si el evento ya aparece `blocked`, capturar `labctl status` y `classroom-state`: puede haber quedado una política de `os` o `application`; coordinar reset local/aula antes de repetir.
- Si la consulta de procesos queda vacía, anotarlo como **no observado en esa consulta**, no como ausencia absoluta: el `sleep 45` pudo terminar. Repetir solo después de una línea base coordinada y lanzar la consulta inmediatamente.
- Si falta el marcador o hay error de conexión, conservar el mensaje de error y comprobar `labctl status`; no descargar el artefacto desde otra URL.

### 2. Demostrar por separado el guard de aplicación

**Propósito.** Aislar el control de ejecución del permiso de archivo. Esta ronda usa solo `ws-hmi`; el reset local no restablece PLC, gateway ni otras estaciones.

```sh
labctl reset
```

**Resultado esperado y significado.** El evento `reset` confirma reset del endpoint actual, conserva evidencia y deja el archivo en la línea base vulnerable. No interpretar esta salida como reset de aula.

**Segunda comprobación.**

```sh
labctl status
```

Se espera `application: false`, `os: false` y modo `0o666`. Si el proceso anterior sigue registrado, el agente intenta terminarlo durante el reset.

**Si difiere.** Si otra estación necesita reset o hay una sesión concurrente, detenerse y usar la coordinación de `reset-all`; no afectar a otros alumnos desde esta guía.

```sh
labctl harden application
```

**Resultado esperado y significado.** La respuesta contiene un evento `harden-application` con resultado `success`; el guard local queda activado y termina procesos benignos registrados por el agente. El modo de `controller.conf` **no cambia** por esta acción.

**Segunda comprobación.**

```sh
stat -c 'mode=%a owner=%U group=%G uid=%u gid=%g path=%n' /home/student/lab/controller.conf
```

Debe continuar en `0666` y con su propietario de línea base. Esta es la evidencia diferencial que separa guard de ejecución y permiso DAC.

**Si difiere.** Si el modo cambió, no atribuirlo a `harden application`: revisar si se ejecutó antes `harden os`, si el reset fue realmente local y conservar ambas salidas para diagnóstico.

```sh
labctl simulate malware
```

**Resultado esperado y significado.** El evento `malware-emulation` queda en `blocked`. El marcador de texto puede descargarse todavía, porque el agente lo obtiene antes de evaluar el guard; no debe iniciarse un nuevo `sleep` del escenario. El guard es una barrera del lanzador conocido, no un antivirus global.

**Segunda evidencia.**

```sh
osqueryi --json "SELECT pid,name,cmdline,uid FROM processes WHERE name='sleep' AND cmdline LIKE '%retail-benign-malware%';"
```

Después del control no debe observarse un proceso nuevo de ese cmdline. Una fila antigua puede desaparecer en el siguiente ciclo o estar terminada; correlacionar siempre con la hora del evento y no inventar PID.

**Si difiere.** Si aparece un `sleep` nuevo, revisar `labctl status` para confirmar `application: true`, comprobar que se ejecutó exactamente `labctl simulate malware` y no otro comando, y repetir solo tras `labctl reset` coordinado. No afirmar bloqueo total de la ejecución de Linux.

### 3. Aplicar permisos mínimos al archivo de configuración

**Propósito.** Cambiar solo el permiso del artefacto y su propietario/grupo mediante el agente autorizado, sin otorgar `sudo` al estudiante.

```sh
labctl reset
```

**Resultado esperado y significado.** Se vuelve a una línea base local para que el siguiente cambio sea atribuible a `harden os`; la evidencia anterior no se borra.

**Segunda comprobación.**

```sh
stat -c 'mode=%a owner=%U group=%G uid=%u gid=%g path=%n' /home/student/lab/controller.conf
```

Debe mostrar el modo y dueño de la línea base. Si no, detener la comparación y corregir el estado antes de aplicar la política.

```sh
labctl harden os
```

**Resultado esperado y significado.** La respuesta directa contiene `event.action: "harden-os"` y `event.outcome: "success"`. El agente hace `chmod 0640` y asigna propietario UID 0 (`root`) y grupo UID 1000 (`student`); además, en este agente la política `os` activa el guard que se verá en el reintento. Esta última función de guard es del escenario, no una propiedad automática de todos los archivos `0640`.

**Segunda evidencia: `stat`.**

```sh
stat -c 'mode=%a owner=%U group=%G uid=%u gid=%g path=%n' /home/student/lab/controller.conf
```

El resultado esperado es `mode=640 owner=root group=student uid=0 gid=1000` para el path exacto. Los nombres pueden depender de la resolución local; los UID/GID son la comprobación objetiva.

**Segunda evidencia: osquery manual.**

```sh
osqueryi --json "SELECT path,mode,uid,gid FROM file WHERE path='/home/student/lab/controller.conf';"
```

Debe devolver una fila para el mismo path y los UID/GID nuevos. La representación de `mode` puede ser serializada de forma distinta por la versión, por lo que se interpreta en octal junto con `stat`; no reemplazar la salida real por un número inventado.

**Si difiere.**

- Si `labctl harden os` falla, conservar el error y revisar `labctl status`; no ejecutar `sudo chmod` ni corregir a mano.
- Si `stat` no es `0640:root:student`, verificar host, path y que no se haya ejecutado `reset` después de hardening.
- Si osquery no devuelve filas, registrar **no observado**, repetir la consulta en la estación correcta y usar `stat` como evidencia local; una consulta vacía no prueba ausencia del archivo.

### 4. Verificar que el estudiante puede leer, pero no escribir

**Propósito.** Probar el efecto práctico de `0640 root:student`: lectura por grupo, escritura denegada para `student`.

```sh
cat /home/student/lab/controller.conf
```

**Resultado esperado y significado.** El comando puede leer el contenido actual como `student`. No usar ni mostrar contenido inventado; guardar literalmente lo que exista. La lectura no implica permiso de modificar.

**Segunda comprobación.**

```sh
printf 'student-write-test\n' >> /home/student/lab/controller.conf
```

Debe fallar con un mensaje de `Permission denied` y no modificar el archivo. No anteponer `sudo`.

**Si difiere.** Si la escritura funciona, capturar inmediatamente `id`, `stat` y `labctl status`: puede ser otro usuario, otro host, un modo distinto o un cambio fuera de la guía. Si el archivo no es legible, comprobar grupo/UID con `id` y `stat`; no relajar el modo para “hacer pasar” el taller. Si el texto del error cambia, importa el código/efecto real: la prueba debe ser no escritura.

```sh
stat -c 'mode=%a owner=%U group=%G uid=%u gid=%g size=%s mtime=%Y path=%n' /home/student/lab/controller.conf
```

**Resultado esperado y significado.** El modo, dueño, grupo y tamaño deben seguir iguales después del intento denegado. `mtime` y `size` son valores variables: registrar la salida real y no fabricar una marca temporal.

### 5. Comprobar el guard de ejecución después del hardening

**Propósito.** Repetir exactamente el mismo intento de la línea base, sin cambiar objetivo, para separar el bloqueo del agente del cambio de DAC.

```sh
labctl simulate malware
```

**Resultado esperado y significado.** La acción devuelve `event.action: "malware-emulation"` con `event.outcome: "blocked"`. El texto del marcador puede quedar visible en `downloads`; esto no contradice el bloqueo porque el guard ocurre después de la descarga. No se debe iniciar un `sleep` nuevo del escenario.

**Segunda evidencia.**

```sh
osqueryi --json "SELECT pid,name,cmdline,uid FROM processes WHERE name='sleep' AND cmdline LIKE '%retail-benign-malware%';"
```

Registrar si no hay fila o si solo quedan procesos antiguos terminados; correlacionar la hora y no concluir a partir de un PID no observado.

**Si difiere.** Si sale `success`, comprobar `labctl status` y que `os: true` o `application: true`; una política no aplicada requiere repetir el hardening, no editar el archivo. Si `status` está correcto pero aparece un proceso, conservar ambos resultados para el coordinador: el guard de este agente solo cubre el flujo y proceso benignos registrados, no cualquier proceso del sistema.

### 6. Recoger detección programada y evidencia independiente

**Propósito.** Comparar la lectura manual con `osqueryd` programado y demostrar el cambio de integridad sin confundir fuentes.

```sh
labctl detect
```

**Resultado esperado y significado.** El resultado real contiene `event`, `rows` y `policies`; `rows` vuelve a mostrar el archivo local después de aplicar `0640`. Es una consulta manual del agente, aunque se llame `detect`.

**Segunda evidencia local.**

```sh
osqueryi --json "SELECT path,mode,uid,gid FROM file WHERE path='/home/student/lab/controller.conf';"
```

Comparar path, modo y UID/GID con la salida de `stat`. Registrar literalmente cualquier diferencia entre las tres fuentes.

**Si difiere.** Recordar que `osqueryi` y `osqueryd` no son el mismo proceso: la consulta manual no obliga a que el evento programado ya esté indexado. Revisar host, hora UTC y ventana de búsqueda; no llamar “ausencia” a una fila todavía no observada.

#### Consultas manuales de solo lectura

Cada consulta se ejecuta en `ws-hmi`, no en SOC para inspeccionar mágicamente otro contenedor. Las siguientes conservan las comprobaciones útiles del taller; sus valores son variables:

```sh
osqueryi --json "SELECT name,version,platform FROM os_version;"
```

Identifica la versión local de Linux/osquery.

```sh
osqueryi --json "SELECT pid,name,path,cmdline FROM processes WHERE cmdline LIKE '%retail-%';"
```

Busca procesos del escenario; un resultado vacío significa solamente no observado en esa consulta.

```sh
osqueryi --json "SELECT uid,username,shell FROM users;"
```

Acredita el mapa de usuarios disponible en el endpoint.

```sh
osqueryi --json "SELECT pid,port,address,protocol FROM listening_ports;"
```

Acredita listeners locales; no es prueba de que un puerto sea seguro o de que exista conectividad desde otra zona.

```sh
osqueryi --json "SELECT path,sha256 FROM hash WHERE path='/home/student/lab/firmware.bin';"
```

Es una lectura manual de hash con valor variable. Este taller no altera firmware y `osqueryd` no programa automáticamente esa consulta: no inventar ni comparar contra un hash escrito de memoria.

## Observabilidad opcional desde Firefox local

La observación visual no reemplaza las salidas de la terminal. En la misma Firefox del escritorio se puede abrir el panel interno `http://panel:8000` y Kibana interno `http://kibana:5601`; no usar `localhost` de la estación como si fuera el panel. En Kibana, elegir la data view `retail-ot-*`, una ventana que incluya la hora UTC capturada y refresco de la interfaz. Pegar **KQL**, no SQL.

### Agente y estado del endpoint

```kql
event.dataset : "lab.endpoint" AND host.name : "ws-hmi"
```

Debe permitir localizar `malware-emulation`, `harden-os`, `harden-application` y `reset`, con su `event.outcome` real. `lab.endpoint` es el registro del agente, no una detección independiente de osquery o Suricata.

### Osquery y cambio de configuración

```kql
host.name : "ws-hmi" AND event.dataset : "osquery" AND osquery.name : "config_integrity"
```

Revisar las filas `added`/`removed` y sus `osquery.columns` para modo, UID/GID y, si está presente, hash. Cambiar permisos no implica cambiar el hash del contenido. Si la consulta devuelve documentos de otro host, corregir el filtro; si no devuelve todavía documentos, anotar “no observado en la ventana” y usar la evidencia local.

```kql
host.name : "ws-hmi" AND event.dataset : "osquery" AND osquery.name : "processes"
```

Correlacionar el cmdline del `sleep` benigno con la hora de la primera prueba y su ausencia posterior. El collector, Logstash y el refresco de Kibana añaden latencia; no convertir una consulta vacía en una afirmación absoluta.

### Fuentes no pertinentes para aprobar este taller

```kql
event.dataset : "lab.control"
```

Es una consulta del proceso PLC/gateway; puede no aportar documentos para permisos Linux y no prueba `0640`.

```kql
event.dataset : "suricata" AND event.action : "alert"
```

Suricata usa el host `sensor`; una alerta de red no prueba un permiso de archivo local. Los PCAP tampoco reemplazan `stat` u osquery.

## Evidencia entregable y cierre

### 7. Guardar el expediente de la estación

**Propósito.** Entregar la secuencia real con host, resultado y límites, sin editar los logs del collector.

```sh
labctl evidence | tee ~/lab/evidencias/taller-02/labctl-evidence.json
```

**Resultado esperado y significado.** La respuesta contiene el `host`, los últimos eventos del agente y una referencia a `osquery_logs`, normalmente `/evidence/osquery/osqueryd.results.log`. La ruta del collector es una referencia de lectura; no redireccionar datos hacia ella ni modificarla.

**Segunda fuente.** Conservar en el mismo expediente las salidas reales de `hostname`, `id`, `status`, `baseline`, `detect`, `stat`, las consultas osquery y la prueba `Permission denied`. En Kibana, si está disponible, guardar las filas filtradas por `host.name`, acción, resultado y hora UTC; no usar una captura inventada ni tratar el botón como aprobación.

**Si difiere.** Si `labctl evidence` falla, conservar el error, repetir `labctl status` y consultar al coordinador. No reconstruir eventos desde el resultado esperado. Un `reset` posterior conserva estos eventos y marcadores.

### 8. Confirmar y cerrar con coordinación

Antes de cerrar, revisar que el expediente contiene como mínimo:

- línea base: `ws-hmi`, usuario `student`, `controller.conf` en `0666`;
- actividad inicial permitida con marcador y, si se observó, el proceso benigno real;
- hardening de aplicación con modo aún `0666` y reintento bloqueado;
- hardening de OS con `0640`, `root:student`, UID/GID reales;
- lectura permitida y escritura real denegada como `student`;
- reintento bloqueado, consulta de proceso y `config_integrity` cuando haya sido observado;
- dos fuentes adecuadas para cada afirmación y una limitación explícita.

Consultar el gemelo una última vez, sin cambiarlo:

```sh
labctl classroom-state
```

**Resultado esperado y significado.** Se conserva una instantánea final del aula con eventos e historial. No interpretar `process`, `gateway` o `endpoints` como evidencia de permisos del archivo: son fuentes de contexto.

Después de guardar la evidencia, coordinar el reset de aula para no dejar controles activados a la siguiente práctica:

```sh
labctl reset-all
```

**Segunda comprobación.**

```sh
labctl classroom-state
```

El estado de políticas y endpoints debe reflejar la respuesta real del reset, mientras los eventos históricos y el expediente local permanecen. No ejecutar `docker compose down -v`: eliminaría volúmenes y evidencia. Si solo se necesita limpiar `ws-hmi` en una repetición aislada y el coordinador lo autoriza, `labctl reset` es local y nunca equivale a `reset-all`.

## Criterios de éxito y solución razonada

La solución completa es: **reset de aula coordinado → identificar `ws-hmi`/`student` → línea base → `simulate malware` permitido → reset local → `harden application` y reintento bloqueado sin cambiar el modo → reset local → `harden os` → comprobar `0640 root:student` con `stat` y osquery → probar lectura y escritura denegada → repetir la emulación y comprobar bloqueo → recoger evidencia y reset de aula coordinado**.

Se aprueba técnicamente solo cuando se comparan resultados reales, no cuando un botón cambia de color:

- **Permiso de archivo:** la barrera real es DAC de Linux sobre `controller.conf`; `0640 root:student` permite lectura al grupo y evita la escritura del usuario `student`.
- **Guard de aplicación:** la barrera real es el agente del laboratorio para el lanzador y proceso benignos registrados; puede dejar el marcador descargado. No es antivirus, allowlisting global, SELinux, AppArmor ni protección completa de endpoint.
- **Osquery:** la consulta manual demuestra lo que el endpoint devuelve en ese instante; `osqueryd` programado y Kibana son otra fuente, con su propia latencia. Un evento `lab.endpoint` no es independiente de ese agente.
- **Configuración:** un cambio de permisos puede producir `config_integrity` aunque el contenido y su hash no cambien.

Si una salida no coincide, conservarla y diagnosticar en este orden: **host/usuario → política efectiva (`status`/`classroom-state`) → path y modo (`stat`) → consulta osquery → ventana y fuente de observabilidad**. No sustituir una salida distinta por la esperada ni inventar PID, hash, timestamp o `_id`.

## Límites, uso responsable y referencias de control

Solo se permite el aula aislada y autorizada. No conectar a PLC, HMI, RTU, tiendas ni redes reales. El archivo bajo `/home/student/lab` es un artefacto de entrenamiento. La simulación de `sleep 45` no demuestra una APT ni impacto ICS.

**MITRE ATT&CK for ICS.** El taller ejercita emulación controlada de actividad en endpoint; no se asigna una técnica ICS de impacto porque no cambia el proceso físico.

**IEC 62443.** La práctica ilustra FR2 (control de uso) y FR3 (integridad del sistema) a nivel de requisitos fundacionales y diseño pedagógico. El alcance no calcula un SL-T ni acredita SL-A; una secuencia de botones no es certificación.

**Ley 21.663.** El expediente conserva hechos, fuente, host, hora UTC y limitaciones para el análisis interno del aula. No se envían notificaciones reales a ANCI ni se atribuye el ejemplo a una organización.

**Antipatrón contextual.** Un acceso compartido de proveedor sin ventana, una copia de configuración sin hash y cambios del HMI sin validación del proceso son situaciones para discutir, no observaciones atribuidas a una empresa. El lunes: identificar al dueño del activo, documentar cambio y reversión, probar fuera de producción y acordar una ventana con operaciones; no bloquear remotamente una planta sin evaluar la seguridad física.

Para observabilidad general puede consultarse el tutorial local [cinco estaciones, osquery y Elastic paso a paso](../docs/tutorial-observabilidad.md), siempre desde la guía local y sin ejecutar verificaciones automáticas en paralelo con una práctica activa.

## Delimitación frente a otros talleres

Este documento resuelve únicamente el taller **02**. No sustituye las prácticas OPC UA/Modbus del módulo 10 ni el desafío 09 de controles multi-host; esas guías deben separar sus propios hosts, controles y fuentes. Aquí no se ejecutan `harden network`, `harden access`, simulaciones laterales, firmware, PLC ni OPC UA: mezclar esos escenarios rompería la atribución de evidencia de permisos Linux.
