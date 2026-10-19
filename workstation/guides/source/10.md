# 10 · Red / Purple Team: Modbus y OPC UA en supermercado retail

> **Guía local del laboratorio Retail OT.** Todo el procedimiento se ejecuta desde la Terminal del laboratorio en el noVNC de **ingeniería (`ws-engineering`)**. La guía se abre localmente con `labctl guides`; el portal no se usa para recibir instrucciones. La vista del gemelo y Kibana son comprobaciones visuales opcionales desde el mismo Firefox.

## Alcance y reglas de seguridad

Las pruebas son exclusivamente escenarios controlados del aula. Los destinos, puertos, identidades, valores y número de operaciones están fijados por el laboratorio: no hay IP, payload ni cantidad configurables. No se permite conectar estas herramientas a tiendas, PLC, RTU o redes reales; no hay exploit, escaneo, MITM, captura de credenciales, malware ni flood. La ráfaga tiene exactamente ocho solicitudes secuenciales.

Los comandos se escriben en la Terminal real del noVNC. En Firefox local, el botón **Copiar** de esta guía se pega con `Ctrl+Shift+V` en xfce4-terminal; no se usa el portapapeles del anfitrión ni un pivote. Pegue solo el comando, sin el `$` del prompt ni el JSON de una salida anterior.

Las esperas que aparezcan se deben a disponibilidad o telemetría; **no son tiempos objetivo de resolución**. El modelo de temperatura es acelerado e idealizado: no es una predicción termodinámica ni sanitaria y no permite calcular inocuidad alimentaria real.

## Objetivos medibles

Al terminar, el alumno podrá:

1. Demostrar una escritura Modbus que modifica la consigna de SCL-01 y localizar dónde se valida la orden.
2. Comparar FC06 y FC16, incluyendo una denylist incompleta y una allowlist por función, Unit ID, dirección, cantidad y valor.
3. Proteger señales de entrada y distinguir una lectura falsa de una condición física real.
4. Separar límite de tasa, integridad de la consigna y continuidad de lectura.
5. Distinguir autenticación, cifrado y autorización OPC UA: usuario anónimo, observador y operador autorizado.
6. Explicar el código CPU, el mapa de registros y las conexiones I/O en Anatomy sin presentarlos como un PLC o SIS certificado.
7. Entregar evidencia independiente: respuesta del cliente, estado del proceso, pasarela/servidor, eventos y, cuando exista, paquete o PCAP.

## Preparación, roles y alcance de los controles

### 1. Abrir la guía local y confirmar la estación

**Propósito.** Trabajar desde la copia local de la guía y evitar depender de la interfaz del portal.

**Acción exacta** — en la Terminal del noVNC de ingeniería:

```sh
labctl guides
```

**Resultado esperado y significado.** Se abre o identifica la guía HTML local de la estación. Es normal que el comando solo muestre una ruta o una confirmación; no asumir un formato adicional.

**Segunda evidencia.** La pestaña local de Firefox debe mostrar este contenido. La vista opcional del gemelo puede abrirse en `http://panel:8000/labs/10`, pero allí solo se observa estado; las instrucciones son las de esta guía.

**Si difiere.** Si Firefox muestra únicamente el portal o no aparece la guía local, no iniciar las pruebas: revisar que se está en el escritorio noVNC de ingeniería y pedir al responsable que complete la implementación de `labctl guides`.

### 2. Confirmar host, usuario y estado inicial

**Propósito.** Demostrar desde qué estación se ejecutará el tráfico y que el usuario no tiene privilegios de administrador.

```sh
hostname
id
labctl status
```

**Resultado esperado y significado.** `hostname` debe identificar la estación de ingeniería recomendada; `id` debe mostrar al usuario del laboratorio y no una sesión root. `labctl status` informa el estado local del endpoint, sus políticas, modo de `controller.conf` y disponibilidad de osquery. No se exige un PID, hash ni timestamp concreto.

**Segunda evidencia.** Comparar el host y el rol que aparezcan en `labctl status` con `classroom-state` en el paso siguiente. El host de la Terminal es el origen operativo del comando; los ejercicios Red Team, sin embargo, usan la pasarela y destinos internos fijos del aula, no una IP elegida por el alumno.

**Si difiere.** Si no es ingeniería, cambiar al noVNC de `ws-engineering` y repetir. Si `id` muestra root, detenerse. Si el endpoint aparece no disponible, conservar la salida y corregir la disponibilidad antes de atribuir una denegación a un control.

### 3. Crear la carpeta de evidencia y leer el gemelo

**Propósito.** Separar las evidencias del alumno del colector y verificar el alcance global antes de cambiarlo.

```sh
mkdir -p ~/lab/evidencias/taller-10
labctl classroom-state
```

**Resultado esperado y significado.** `classroom-state` es una consulta de solo lectura que conserva un JSON con `process`, `gateway`, `endpoints`, `policies` y, si están disponibles, eventos/historial. Tras un aula limpia se esperan políticas de proceso y pasarela desactivadas, consigna nominal y endpoints disponibles; temperatura, ciclo y timestamps son variables.

**Segunda evidencia.** `labctl status` acredita el endpoint local; `classroom-state` acredita el gemelo del panel. Son fuentes distintas y no deben intercambiarse.

**Si difiere.** Si el JSON muestra una política heredada, un proceso en riesgo o un endpoint no disponible, no adaptar la prueba para “hacerla pasar”. Coordinar un reset global con los demás alumnos.

### 4. Restablecer el aula de forma coordinada

**Propósito.** Comenzar cada práctica con PLC, gateway y endpoints en un estado comparable, conservando la evidencia previa.

```sh
labctl reset-all
labctl classroom-state
```

**Resultado esperado y significado.** El primer comando coordina el reset de aula completo: políticas/proceso y endpoints, sin borrar la evidencia. El segundo debe mostrar el estado resultante. `reset-all` es global y puede afectar a otros alumnos: se ejecuta solo después de avisar y verificar que no hay otra sesión activa.

**Segunda evidencia.** Comparar `process`, `gateway`, `endpoints` y `policies` del segundo JSON con el `status` local. El proceso debe volver a la consigna nominal y los indicadores de estado deben ser coherentes; no se espera un número fijo de ciclo o temperatura.

**Si difiere.** Si algún servicio sigue no disponible, guardar ambos JSON y detenerse. `labctl reset` solo restablece las políticas del endpoint actual; no sustituye este reset global ni restaura por sí solo PLC, gateway u otras estaciones. El firmware original, cuando corresponda a otro taller, se recupera con `harden supply-chain` y después `reset`, no con `reset` solo.

### Roles y fronteras

- **Red Team:** ejecuta las acciones fijas desde la Terminal de ingeniería.
- **Blue/SOC:** observa eventos, paquetes y consultas de Kibana desde Firefox, sin cambiar el estado durante la comparación.
- **Operador de proceso:** decide `recover` y documenta la condición del stock.
- `harden plc`, `harden modbus`, `harden inputs`, `harden write-rate`, `harden opcua-rbac` y `harden opcua-channel` cambian el gemelo central PLC/gateway/servidor; aunque se lancen desde una terminal, son controles globales del aula.
- `labctl reset` es local al endpoint actual. `labctl reset-all` es global y coordinado.
- Los comandos Red Team no convierten el origen de tráfico en cada noVNC: la pasarela y el orquestador usan destinos internos fijos. No se agregan hosts ni se eligen objetivos.

## Anatomía técnica común

El mapa educativo usa, entre otros, el registro 0 para la consigna en °C, el registro 4 para el sesgo de sensor (décimas más 1000) y el registro 5 para conexión de sensor. La CPU valida FC06, FC16 y Write OPC UA con la misma barrera semántica antes de mutar el estado; FC16 es atómica en este modelo.

En la solicitud Modbus TCP, el TID correlaciona una respuesta, pero **no es un token de autenticación**; `Length` cuenta Unit ID + PDU y TCP no lleva CRC RTU. Las direcciones del mapa son base cero. Esta representación es una decodificación orientativa del ejercicio, no una captura nueva:

```text
A0 28 00 00 00 06 01 06 00 00 00 32
│ TID │ PID │LEN│U│FC│ ADDR │VALUE│
 41000   0    6  1  6    0      50
```

FC16 con un registro usa una solicitud de este tipo:

```text
A0 29 00 00 00 09 01 10 00 00 00 01 02 00 32
│ TID │ PID │LEN│U│FC│ ADDR │QTY│BC│DATA│
 41001   0    9  1 16    0     1   2   50
```

La UI puede presentar `heater=true` como deshielo o forzado térmico según la vista. En esta guía se nombran también los campos JSON reales (`heater`, `compressor`, `setpoint`, `temperature`) para no confundir una etiqueta visual con una salida capturada.

---

# Práctica A · FC06: escritura de consigna sin validación semántica

**Pregunta.** ¿Qué ocurre cuando la pasarela transporta una escritura válida de protocolo, pero el PLC no impone todavía un rango operativo?

### A1. Registrar la lectura legítima

**Propósito.** Obtener la referencia Modbus y del proceso antes de escribir.

```sh
labctl redteam baseline | tee ~/lab/evidencias/taller-10/A1-baseline.json
```

**Resultado esperado y significado.** La respuesta JSON Red Team contiene `event`, `result`, `before` y `after`. En `result` se espera `protocol: "Modbus TCP"`, `function: 3`, `exception: false`, una solicitud/respuesta hexadecimal y `source` indicando respuesta TCP real. FC03 lee ocho registros del mapa; la consigna inicial suele ser 2 °C, pero el ciclo, la temperatura y los contadores son variables.

**Segunda evidencia.** Ejecutar `labctl classroom-state` y guardar su salida como evidencia separada. El `process` debe coincidir con la consigna nominal y `gateway` debe mostrar la política inicial.

**Si difiere.** Si `exception` es verdadero o FC03 no está disponible, revisar primero gateway y PLC en `classroom-state`; no interpretar la falla como protección semántica hasta confirmar la fuente.

### A2. Repetir la misma acción de escritura FC06

**Propósito.** Demostrar el impacto de escribir 50 en el registro de consigna sin guard central.

```sh
labctl redteam modbus-write | tee ~/lab/evidencias/taller-10/A2-fc06-antes.json
```

**Resultado esperado y significado.** `result` debe mostrar función 6, `exception: false` y respuesta eco. En `after`, la consigna queda en `setpoint: 50`; el modelo activa `heater: true` y desactiva `compressor: false`. La física puede comenzar a subir y el stock puede pasar a riesgo/cuarentena en ciclos posteriores. No inventar una temperatura o exposición concreta justo después del comando.

**Segunda evidencia.** `labctl classroom-state` y, si está disponible, `curl -sS http://panel:8000/api/packets` muestran respectivamente el estado del proceso y los paquetes/eventos observados por el panel.

**Si difiere.** Si la respuesta es una excepción, conservar `exception_code` y comprobar qué barrera la originó. Si todavía no aparece una exposición en el backend, no afirmar que el stock ya fue comprometido; el modelo necesita ciclos.

### A3. Inspeccionar dónde debe vivir la barrera

**Propósito.** Separar una validación de proceso de un filtro de red.

```sh
curl -sS http://panel:8000/api/anatomy | tee ~/lab/evidencias/taller-10/A3-anatomy.json
```

**Resultado esperado y significado.** La respuesta identifica `source_path: "plc/control_logic.py"`, devuelve el código de aula y el proceso. En `validate_change()` debe localizarse el rango `0 <= value <= 6` cuando `plc_guard` está activo. Es código Python educativo, no firmware ni lógica de seguridad certificada.

**Segunda evidencia.** Comparar el `process` de la respuesta con `classroom-state`; ambos deben reflejar la misma consigna de la práctica, aunque los ciclos avancen.

**Si difiere.** Si el código no está disponible, guardar el error y usar el estado para no inventar una validación. Una puerta de red o un TID no prueban por sí mismos integridad de la orden.

### A4. Activar el guard central del PLC

**Propósito.** Aplicar una validación semántica independiente de la forma de transporte.

```sh
labctl harden plc | tee ~/lab/evidencias/taller-10/A4-harden-plc.json
```

**Resultado esperado y significado.** La respuesta contiene un evento de hardening; el panel debe indicar que el PLC valida la consigna y vuelve el valor nominal. El formato de esta acción puede ser un evento directo, no asumir que siempre existe `event.outcome` anidado.

**Segunda evidencia.** `labctl classroom-state` debe mostrar `process.plc_guard: true` y la consigna nominal. El gateway puede seguir sin allowlist: esto demuestra que la barrera está en el PLC.

**Si difiere.** Si `plc_guard` no aparece activo, no continuar con la comparación; revisar la salida completa y la disponibilidad de `plc`.

### A5. Repetir FC06 y demostrar continuidad de lectura

**Propósito.** Comparar exactamente la misma orden después del control, sin cambiar valor ni host.

```sh
labctl redteam modbus-write | tee ~/lab/evidencias/taller-10/A5-fc06-despues.json
labctl redteam baseline | tee ~/lab/evidencias/taller-10/A5-read-despues.json
```

**Resultado esperado y significado.** La escritura debe devolver `exception: true`, `exception_code: 3` y una función de excepción `0x86` (Illegal Data Value). `after.setpoint` debe permanecer nominal y FC03 debe seguir disponible. La validación ocurre antes de mutar el PLC. Este guard no rehabilita alimentos ya comprometidos.

**Segunda evidencia.** `classroom-state` debe confirmar la consigna nominal y `plc_guard: true`; la respuesta de `baseline` confirma una lectura independiente del intento de escritura.

**Si difiere.** Si FC06 sigue aceptada, verificar que se ejecutó A4 en el mismo aula y que `plc_guard` está activo. Si FC03 falla, diagnosticar disponibilidad del servicio antes de atribuirlo a la política.

---

# Práctica B · FC16: evadir una denylist incompleta

**Pregunta.** ¿Por qué bloquear solo FC06 no equivale a proteger todas las escrituras?

### B1. Aislar la práctica

**Propósito.** Quitar el guard de A y empezar con el gateway sin la política anterior.

```sh
labctl reset-all
labctl classroom-state
```

**Resultado esperado y significado.** El aula vuelve a nominal; la evidencia anterior se conserva. Este reset afecta a otros alumnos, por lo que debe estar coordinado.

**Segunda evidencia.** `classroom-state` debe mostrar políticas `fc06_only`, `modbus_allowlist` y `write_rate` desactivadas, además de `plc_guard` desactivado.

**Si difiere.** No ejecutar FC16 sobre un estado heredado; repetir el reset coordinado o pedir intervención del responsable.

### B2. Activar deliberadamente el antipatrón FC06-only

**Propósito.** Construir una denylist incompleta de forma controlada.

```sh
labctl redteam fc06-only | tee ~/lab/evidencias/taller-10/B2-fc06-only.json
```

**Resultado esperado y significado.** `gateway.fc06_only` debe quedar verdadero. La salida puede contener `event` y `gateway`; no asumir otro envoltorio.

**Segunda evidencia.** `labctl classroom-state` debe reflejar `gateway.fc06_only: true` y todavía no `modbus_allowlist`.

**Si difiere.** Si aparece una allowlist o un PLC guard heredado, detenerse y volver a B1; la comparación dejaría de aislar el antipatrón.

### B3. Mostrar que FC06 está bloqueada, pero no toda escritura

**Propósito.** Verificar el primer lado de la comparación.

```sh
labctl redteam modbus-write | tee ~/lab/evidencias/taller-10/B3-fc06-bloqueada.json
```

**Resultado esperado y significado.** La escritura FC06 debe resultar bloqueada por la pasarela; se espera una excepción de función `0x86` y un código de excepción de política, normalmente `1` (Illegal Function). No concluir que el registro está protegido contra otra función.

**Segunda evidencia.** `classroom-state` debe mantener `fc06_only: true`; `/api/evidence` puede mostrar el evento del panel y `/api/packets` el intercambio observado.

**Si difiere.** Si FC06 atraviesa la pasarela, revisar el campo de política y el host antes de probar FC16. Si el PLC devuelve un rechazo semántico, el estado no era el inicial.

### B4. Repetir el objetivo usando FC16

**Propósito.** Demostrar el bypass de la denylist con Write Multiple Registers, usando un solo registro válido.

```sh
labctl redteam modbus-fc16 | tee ~/lab/evidencias/taller-10/B4-fc16-atraviesa.json
```

**Resultado esperado y significado.** `result` debe indicar FC16, `exception: false` y una respuesta normal que confirma dirección inicial y cantidad, no un eco de todos los valores. En `after`, `setpoint` queda en 50 y el impacto físico es el mismo. FC16 admite hasta 123 registros en el protocolo, pero el mapa ficticio de este PLC solo autoriza posiciones concretas y esta prueba usa exactamente una.

**Segunda evidencia.** `classroom-state` debe mostrar `fc06_only: true` y la consigna 50; el paquete FC16 en `/api/packets` o en el PCAP confirma que cambió la función, no el objetivo.

**Si difiere.** Si FC16 también es bloqueada, no atribuirlo a la denylist incompleta: comprobar que no quedó una allowlist o un guard PLC activo. Si el impacto todavía no se ve en la temperatura, esperar telemetría y observar `setpoint`/`heater` antes de concluir.

### B5. Aplicar allowlist completa y repetir FC16

**Propósito.** Verificar control de función, Unit ID, dirección, cantidad y valor en la pasarela.

```sh
labctl harden modbus | tee ~/lab/evidencias/taller-10/B5-allowlist.json
labctl redteam modbus-fc16 | tee ~/lab/evidencias/taller-10/B5-fc16-bloqueada.json
```

**Resultado esperado y significado.** `gateway.modbus_allowlist` debe quedar activo. La misma FC16 a 50 debe devolver función de excepción `0x90` y `exception_code: 3` (Illegal Data Value); la orden no debe mutar la consigna. La allowlist del modelo permite escrituras remotas solo a la consigna y dentro de 0–6; el interlock PLC es una defensa adicional, no un reemplazo.

**Segunda evidencia.** `classroom-state` debe mostrar `modbus_allowlist: true`, la consigna sin el cambio solicitado y contadores/eventos de gateway. La respuesta Modbus y el estado son fuentes diferentes.

**Si difiere.** Si la orden pasa, revisar que se llamó `harden modbus` y que el mismo gateway recibe el tráfico. Si la consigna ya estaba en 50 por B4, no usar ese valor como prueba de aceptación: verificar que no cambió después de B5 y hacer `recover`.

### B6. Confirmar lectura legítima y recuperar el proceso

**Propósito.** Demostrar que el control no elimina FC03 y devolver el proceso a condición operativa del aula.

```sh
labctl redteam baseline | tee ~/lab/evidencias/taller-10/B6-read-legitima.json
labctl recover | tee ~/lab/evidencias/taller-10/B6-recover.json
labctl classroom-state
```

**Resultado esperado y significado.** FC03 debe responder sin excepción. `recover` detiene marcadores benignos, vuelve la consigna/flujo a condición nominal y deja constancia de que el stock ya puesto en cuarentena no se “des-estropea”. Las políticas del gateway siguen activas hasta el próximo `reset-all`.

**Segunda evidencia.** `classroom-state` debe mostrar lectura disponible y el proceso enfriándose; la evidencia de gateway debe conservar los rechazos.

**Si difiere.** Si la lectura no funciona, revisar gateway antes de afirmar que la allowlist es demasiado estricta. Si el stock sigue en cuarentena, es el comportamiento esperado del laboratorio.

---

# Práctica C · Sensor alterado: leer frío falso y detener refrigeración

**Pregunta.** ¿Cómo puede una señal aparentemente fría ocultar que el producto se calienta?

### C1. Aislar la práctica

**Propósito.** Quitar las políticas de B antes de cambiar una entrada.

```sh
labctl reset-all
labctl classroom-state
```

**Resultado esperado y significado.** PLC, gateway y entradas vuelven a la línea base, con `sensor_bias: 0.0` y `sensor_connected: true`.

**Segunda evidencia.** `classroom-state` y `labctl status` deben mostrar, respectivamente, el gemelo y el endpoint actual.

**Si difiere.** No interpretar un sesgo heredado como resultado de C2; repetir el reset coordinado.

### C2. Inyectar el sesgo fijo del escenario

**Propósito.** Usar la calibración remota débil del mapa de aula para alterar AI0, sin tocar un sensor físico.

```sh
labctl redteam modbus-sensor | tee ~/lab/evidencias/taller-10/C2-sensor-antes.json
```

**Resultado esperado y significado.** La solicitud FC06 escribe 800 en el registro 4. El modelo traduce `(800 - 1000) / 10` a `sensor_bias: -20.0` °C. `measured_temperature` queda artificialmente por debajo de la física y normalmente `compressor: false`, aunque la temperatura real del modelo siga calentándose. Esto es un defecto de diseño simulado, no una alteración de un sensor físico.

**Segunda evidencia.** `classroom-state` debe comparar `temperature`, `measured_temperature`, `sensor_bias`, `compressor` y `sensor_valid`. `/api/packets` aporta el intercambio Modbus.

**Si difiere.** Si `sensor_bias` no cambia, guardar respuesta y comprobar que el registro 4 está accesible y que el aula estaba limpia. No concluir que el sensor físico está frío a partir de `measured_temperature`.

### C3. Inspeccionar CPU, mapa y cableado

**Propósito.** Relacionar AI0, DI0 y salidas con la lógica de control sin confundir señales con potencia.

```sh
curl -sS http://panel:8000/api/anatomy | tee ~/lab/evidencias/taller-10/C3-anatomy.json
```

**Resultado esperado y significado.** `source_path` identifica el código Python de aula y la respuesta contiene el estado de proceso. En Anatomy, **Entradas / Salidas → Entender**, AI0 representa PT100/módulo RTD o un transmisor 4–20 mA; DI0 es puerta; DO0 es compresor, DO1 deshielo y DO2 alarma. PT100 directo y transmisor requieren módulos distintos. DO0 debe mandar un relé/contactor con protecciones adecuadas: no se conecta potencia del compresor directamente al PLC.

**Segunda evidencia.** Comparar el `source` devuelto con `plc/control_logic.py` y el estado con `classroom-state`. La fuente de Anatomy es pedagógica y no prueba seguridad funcional.

**Si difiere.** Si la UI no carga, usar la respuesta de `/api/anatomy`; si tampoco existe, registrar el fallo y no afirmar una conexión no observada.

### C4. Proteger las entradas remotas y repetir el sesgo

**Propósito.** Impedir que una calibración remota cambie AI0/los bornes y comprobar que el valor previo se conserva.

```sh
labctl harden inputs | tee ~/lab/evidencias/taller-10/C4-input-guard.json
labctl redteam modbus-sensor | tee ~/lab/evidencias/taller-10/C4-sensor-bloqueado-plc.json
```

**Resultado esperado y significado.** `process.input_guard` debe quedar activo. La misma escritura 800 debe ser rechazada con función `0x86`, `exception_code: 2` (Illegal Data Address); `sensor_bias` debe volver o conservar `0.0` y `sensor_connected` permanecer verdadero. La validación de señal y el dominio de mantenimiento no se sustituyen con cifrado de transporte.

**Segunda evidencia.** `classroom-state` debe mostrar `input_guard: true`, sesgo cero y el estado de AI0; los eventos del panel/gateway muestran la orden rechazada.

**Si difiere.** Si el sesgo cambia, no continuar: comprobar el estado de `input_guard` y que el valor fue exactamente 800. Si la escritura es bloqueada por el gateway en vez del PLC, verificar si se dejó una política de B.

### C5. Añadir exclusión en gateway y repetir la misma orden

**Propósito.** Mostrar defensa en profundidad y que el gateway tampoco permite el registro de calibración.

```sh
labctl harden modbus | tee ~/lab/evidencias/taller-10/C5-allowlist-inputs.json
labctl redteam modbus-sensor | tee ~/lab/evidencias/taller-10/C5-sensor-bloqueado-gateway.json
```

**Resultado esperado y significado.** La misma orden FC06 al registro 4 debe ser rechazada por la allowlist con `0x86/0x02`; el gateway ahora solo autoriza la consigna dentro de 0–6. Esta repetición usa el mismo valor y objetivo para que el cambio de barrera sea comparable.

**Segunda evidencia.** `classroom-state` debe mostrar `modbus_allowlist: true` e `input_guard: true`; `/api/evidence` y `/api/packets` permiten contrastar evento y tráfico. No deducir la fuente solo por el color de un botón.

**Si difiere.** Si la respuesta pasa, detenerse y revisar ambas políticas. Si el código de excepción coincide con C4, usar logs de gateway/PLC y el estado de políticas para ubicar la barrera; no inventar una procedencia.

### C6. Desconectar y reconectar AI0/DI0 en el modelo

**Propósito.** Observar la reacción de entrada desconectada y diferenciarla de una calibración falsa. La acción es una API fija del aula, no un destino configurable.

```sh
curl -sS -X POST http://panel:8000/api/anatomy/wiring -H 'Content-Type: application/json' -d '{"signal":"AI0","connected":false}'
labctl classroom-state
curl -sS -X POST http://panel:8000/api/anatomy/wiring -H 'Content-Type: application/json' -d '{"signal":"AI0","connected":true}'
```

**Resultado esperado y significado.** Tras desconectar AI0, el estado debe mostrar `sensor_connected: false`; con `input_guard` activo, el modelo puede activar `fallback_active` y `alarm`, usando una referencia ideal interna. Al reconectar, debe volver la señal primaria. Esa referencia es conocida mágicamente por el simulador: una planta real necesitaría sensor redundante físico, diagnóstico, modo degradado aprobado y análisis de riesgo.

**Segunda evidencia.** Guardar el JSON de `classroom-state` entre desconexión y reconexión. Para representar puerta abierta, se puede repetir la misma API con `{"signal":"DI0","connected":false}` y luego `true`; se espera `door_open`/alarma según el estado del modelo.

**Si difiere.** Si `fallback_active` no aparece, revisar `input_guard`, disponibilidad del PLC y que se observó el estado después de la llamada. No extrapolar este respaldo a seguridad funcional real.

---

# Práctica D · Ráfaga finita: la tasa no reemplaza la integridad

**Pregunta.** ¿Qué protege un límite de tasa y qué no protege?

### D1. Aislar la práctica y ejecutar las ocho operaciones

**Propósito.** Medir la ráfaga finita del aula sin convertirla en un ensayo de disponibilidad.

```sh
labctl reset-all
labctl redteam modbus-burst | tee ~/lab/evidencias/taller-10/D1-burst-sin-control.json
```

**Resultado esperado y significado.** `result` debe indicar `sent: 8`, una lista de ocho paquetes FC06 secuenciales y `notice` de ejercicio finito. Sin rate limit ni guard PLC, normalmente las ocho son aceptadas y la consigna termina en 50; no hay parámetros para ampliar la carga. Esto no demuestra DoS ni indisponibilidad.

**Segunda evidencia.** `classroom-state` muestra la consigna y `gateway` sus contadores. `/api/packets` debe contener los intercambios que el sistema haya capturado.

**Si difiere.** Si no hay exactamente ocho paquetes en la respuesta, conservarla y detenerse. Si alguna es rechazada, comprobar políticas heredadas y disponibilidad; no declarar un control de tasa sin `gateway.write_rate` activo.

### D2. Aplicar límite de escritura y comprobar que Read sigue vivo

**Propósito.** Separar presupuesto de Write de continuidad de lectura.

```sh
labctl harden write-rate | tee ~/lab/evidencias/taller-10/D2-write-rate.json
labctl redteam modbus-burst | tee ~/lab/evidencias/taller-10/D2-burst-rate.json
labctl redteam baseline | tee ~/lab/evidencias/taller-10/D2-read-no-consume-rate.json
```

**Resultado esperado y significado.** La ráfaga sigue teniendo ocho solicitudes, pero algunas se rechazan con `exception_code: 6` (Server Device Busy); en una llamada rápida son posibles dos aceptadas y seis rechazadas, pero no fijar esa proporción como dato capturado. FC03 de `baseline` debe continuar sin excepción: las lecturas no consumen el presupuesto Write. El límite se aplica por fuente del orquestador del aula, no prueba rate-limiting por cada usuario noVNC.

**Segunda evidencia.** `classroom-state` debe mostrar `gateway.write_rate: true`, contadores `accepted_writes`/`blocked_writes` y una lectura disponible. El evento del gateway es independiente de la respuesta del cliente.

**Si difiere.** Si las ocho pasan, confirmar que `harden write-rate` se aplicó al gateway correcto y que el intervalo no permitió vaciar la ventana. Si FC03 falla, diagnosticar disponibilidad, no aumentar la ráfaga.

### D3. Añadir integridad de proceso y repetir la ráfaga

**Propósito.** Mostrar que la tasa por sí sola puede dejar pasar órdenes peligrosas, mientras que el guard semántico valida cada valor.

```sh
labctl harden plc | tee ~/lab/evidencias/taller-10/D3-plc-guard.json
labctl redteam modbus-burst | tee ~/lab/evidencias/taller-10/D3-burst-rate-y-plc.json
labctl recover | tee ~/lab/evidencias/taller-10/D3-recover.json
```

**Resultado esperado y significado.** Con ambos controles, las primeras solicitudes pueden llegar al PLC y las restantes ser bloqueadas por tasa; las que llegan con 50 deben ser rechazadas por el PLC con `0x86/0x03`, y las bloqueadas en la pasarela pueden mostrar `exception_code: 6`. La distribución exacta depende de la ventana y no debe inventarse. `recover` devuelve el flujo nominal y detiene marcadores benignos; no des-cuarentena stock ya afectado.

**Segunda evidencia.** Comparar cada elemento de `result.packets` con `classroom-state.process.rejected_writes`, `plc_guard` y los contadores del gateway. Esta es la evidencia de barreras complementarias.

**Si difiere.** Si todas las órdenes se rechazan con el mismo código, usar gateway y PLC para distinguir origen; no llamar “rate limit” a un `0x03` del PLC ni al revés.

---

# Práctica E · OPC UA: canal cifrado no significa permiso Write

**Pregunta.** ¿Puede un cliente autenticado y cifrado escribir un nodo sin autorización para ese usuario?

### E1. Aislar y probar usuario anónimo con endpoint None

**Propósito.** Establecer la línea base del servidor OPC UA débil.

```sh
labctl reset-all
labctl redteam opcua-anonymous | tee ~/lab/evidencias/taller-10/E1-opcua-anonimo.json
```

**Resultado esperado y significado.** `result` debe indicar `protocol: "OPC UA"`, `operation: "Write"`, `identity: "anonymous"`, `security: "None"`, `requested: 50`, `outcome: "success"` y lectura posterior coherente. `after.setpoint` queda en 50. El servidor de práctica autoriza por defecto; esto no representa un servidor productivo.

**Segunda evidencia.** `classroom-state` muestra el cambio de consigna y el estado OPC UA; `/api/evidence` conserva el evento del panel.

**Si difiere.** Si None no conecta, confirmar que el aula realmente fue restablecida y que no quedó `opcua_tls_only`; una falla de conexión no prueba RBAC.

### E2. Probar el observador con SignAndEncrypt, antes de RBAC

**Propósito.** Separar confidencialidad/integridad del canal de autorización de escritura.

```sh
labctl redteam opcua-observer | tee ~/lab/evidencias/taller-10/E2-opcua-observer-antes.json
```

**Resultado esperado y significado.** El resultado usa `identity: "observer"`, `security: "SignAndEncrypt"`, la credencial pública de ejemplo `observer / retail-observer-lab`. Es la identidad conocida del aula: no se roba ninguna contraseña. El certificado de aula está fijado y compartido; no representa una identidad de aplicación independiente por workstation. Como todavía no hay RBAC, el observador puede escribir 50.

**Segunda evidencia.** `classroom-state` debe mostrar la consigna cambiada y el estado de políticas aún sin autorización por rol. La respuesta de OPC UA y el evento del panel son fuentes distintas.

**Si difiere.** Si el cliente seguro no abre sesión, guardar el error y verificar el estado del endpoint; no llamar “autorización” a un fallo de disponibilidad. Si el observador ya es rechazado, probablemente quedó RBAC de otra práctica.

### E3. Aplicar RBAC de servidor y repetir la misma escritura

**Propósito.** Comprobar que el servidor decide por usuario/nodo/operación, aunque el cliente use SignAndEncrypt.

```sh
labctl harden opcua-rbac | tee ~/lab/evidencias/taller-10/E3-rbac.json
labctl redteam opcua-observer | tee ~/lab/evidencias/taller-10/E3-observer-bloqueado.json
```

**Resultado esperado y significado.** `process.opcua_rbac` debe quedar activo. La misma escritura del observador debe devolver `outcome: "blocked"` y un estado de clase `BadUserAccessDenied`; no debe modificar la consigna. El servidor aplica la barrera: no depende de que el cliente “decida portarse bien”. Si E2 dejó 50, que el valor siga 50 en este punto no significa que E3 lo haya aceptado.

**Segunda evidencia.** `classroom-state` debe conservar el valor previo y mostrar `opcua_rbac: true`; `/api/evidence` debe contener el evento de la acción.

**Si difiere.** Si el observador sigue escribiendo, revisar que se llamó `harden opcua-rbac` y que el cliente usa exactamente la identidad fija del ejercicio. Si el comando no puede conectar, separar disponibilidad de autorización.

### E4. Recuperar y comprobar el Write legítimo del ingeniero

**Propósito.** Demostrar continuidad operativa con permiso mínimo, sin reutilizar la consigna insegura.

```sh
labctl recover | tee ~/lab/evidencias/taller-10/E4-recover.json
labctl redteam opcua-engineer | tee ~/lab/evidencias/taller-10/E4-engineer-3.json
```

**Resultado esperado y significado.** `recover` vuelve la consigna nominal y deja constancia de que stock ya puesto en cuarentena no se recupera solo. El cliente de ingeniería usa `engineer / retail-engineer-lab`, `SignAndEncrypt`, solicita exactamente 3 °C y debe devolver `outcome: "success"` con `readback: 3` o el equivalente numérico del servicio. El permiso está en el servidor para esa identidad y ese nodo; no es un permiso universal de escritura.

**Segunda evidencia.** `classroom-state` debe reflejar `setpoint: 3` y `opcua_rbac: true`; la respuesta contiene `identity`, `security`, `requested` y `readback`.

**Si difiere.** Si ingeniería también es rechazada, revisar endpoint seguro, credencial de aula y política RBAC. Si el valor no vuelve a nominal antes del Write, conservar el `before` y no atribuir a ingeniería un cambio previo.

### E5. Rechazar un valor inseguro incluso a un usuario autorizado

**Propósito.** Separar autorización de usuario de validación de rango del proceso.

```sh
labctl harden plc | tee ~/lab/evidencias/taller-10/E5-plc-guard.json
labctl redteam opcua-overrange | tee ~/lab/evidencias/taller-10/E5-engineer-50-bloqueado.json
```

**Resultado esperado y significado.** El usuario de ingeniería sigue autenticado y autorizado para el nodo, pero 50 debe devolver `outcome: "blocked"` y un estado OPC UA equivalente a `BadOutOfRange`; la consigna no muta. El guard central valida antes de aplicar el valor, igual que para FC06/FC16.

**Segunda evidencia.** `classroom-state` debe mostrar `plc_guard: true`, consigna nominal y RBAC activo. Comparar el servicio de atributos del PLC y `control_logic.py` mediante la evidencia de Anatomy.

**Si difiere.** Si 50 se aplica, detenerse y comprobar `plc_guard`. Si el observador/ingeniero no conecta, no confundir un problema de canal con `BadOutOfRange`.

### E6. No mezclar el modelo del taller 06

El comando `labctl harden opcua` del taller 06 conserva la política anterior de variable **read-only para todos**. No ejecutarlo durante E si se quiere demostrar el Write legítimo de ingeniería; antes de cambiar de modelo hay que hacer `labctl reset-all`. Cifrado, autenticación y autorización son propiedades separadas.

---

# Práctica F · Cerrar None sin romper el cliente legítimo

**Pregunta.** ¿Puede el servidor retirar el endpoint None y conservar Browse/Read y Write legítimo en el canal seguro?

### F1. Confirmar el estado débil y volver a nominal

**Propósito.** Obtener una referencia explícita antes de cerrar la política None.

```sh
labctl reset-all
labctl redteam opcua-anonymous | tee ~/lab/evidencias/taller-10/F1-anonimo-antes.json
labctl recover | tee ~/lab/evidencias/taller-10/F1-recover.json
```

**Resultado esperado y significado.** En el estado limpio el anónimo puede escribir por `None`, como en E1; `recover` devuelve el proceso a condición nominal. Se conserva evidencia de ambas acciones.

**Segunda evidencia.** `classroom-state` debe mostrar la consigna nominal antes de cambiar el endpoint.

**Si difiere.** Si el anónimo ya está bloqueado, revisar si se ejecutó un reset global real y no un reset local; no saltar directamente a la conclusión de que el canal está endurecido.

### F2. Retirar None en el servidor

**Propósito.** Publicar solo el canal OPC UA `SignAndEncrypt` del escenario.

```sh
labctl harden opcua-channel | tee ~/lab/evidencias/taller-10/F2-canal-seguro.json
```

**Resultado esperado y significado.** La política del servidor queda `opcua_tls_only: true`; el endpoint seguro debe quedar listo (`opcua_ready: true`) cuando la acción termina. El comando cambia la configuración del endpoint OPC UA del modelo y no el PLC físico.

**Segunda evidencia.** `classroom-state` debe mostrar `opcua_tls_only` y `opcua_ready`. La lista de endpoints devuelta por Browse en F4 será la segunda evidencia del canal publicado.

**Si difiere.** Si el endpoint seguro no está listo, conservar la salida, verificar disponibilidad del servicio y no probar una denegación todavía. No asumir que la espera es un tiempo de resolución del taller.

### F3. Repetir el Write anónimo sin política cifrada

**Propósito.** Verificar que retirar None en el servidor impide abrir la sesión compatible, no solo que el cliente se niega voluntariamente.

```sh
labctl redteam opcua-anonymous | tee ~/lab/evidencias/taller-10/F3-anonimo-despues.json
```

**Resultado esperado y significado.** Se espera `outcome: "blocked"` con `security: "None"` y un estado de clase `BadSecurityPolicyRejected`, `BadSecurityModeRejected` o equivalente a “no hay endpoint compatible”. Si el cliente no puede negociar y el comando devuelve un error de conexión, eso describe **indisponibilidad o incompatibilidad**, no una denegación correcta por sí sola.

**Segunda evidencia.** `classroom-state` debe mantener `opcua_tls_only: true` y `opcua_ready: true`; conservar la salida completa para distinguir excepción UA de error de transporte.

**Si difiere.** Si el anónimo todavía escribe, F2 no se aplicó al servidor correcto. Si todo cliente falla, no declarar hardening exitoso: resolver primero el canal seguro.

### F4. Mantener Browse/Read y aplicar RBAC

**Propósito.** Comprobar descubrimiento/lectura segura antes de validar el Write legítimo.

```sh
labctl harden opcua-rbac | tee ~/lab/evidencias/taller-10/F4-rbac.json
labctl redteam opcua-browse | tee ~/lab/evidencias/taller-10/F4-browse-seguro.json
```

**Resultado esperado y significado.** Browse debe devolver `outcome: "success"`, `operation: "Read/Browse"`, `security: "SignAndEncrypt"`, lista de `objects` y `endpoints` seguros. RBAC queda activo y no se requiere habilitar None para leer. La consulta usa el objeto educativo conocido; no es un escaneo recursivo de red.

**Segunda evidencia.** `classroom-state` debe mostrar `opcua_tls_only: true`, `opcua_rbac: true` y `opcua_ready: true`; la lista de endpoints de la respuesta es la fuente independiente del estado del proceso.

**Si difiere.** Si Browse no funciona pero None está cerrado, clasificarlo como indisponibilidad/interoperabilidad y no como un éxito de hardening. Si aparece un endpoint None, verificar la política efectiva del servidor.

### F5. Mantener el Write legítimo de ingeniería

**Propósito.** Cerrar la comparación comprobando continuidad de operación autorizada en el canal seguro.

```sh
labctl redteam opcua-engineer | tee ~/lab/evidencias/taller-10/F5-engineer-seguro.json
labctl classroom-state
```

**Resultado esperado y significado.** El resultado debe indicar `identity: "engineer"`, `security: "SignAndEncrypt"`, `requested: 3`, `outcome: "success"` y lectura posterior 3. El servidor conserva la autorización mínima mientras retira None; no se implementa una PKI empresarial.

**Segunda evidencia.** `classroom-state` confirma la consigna 3 y las dos políticas OPC UA. La respuesta de Browse de F4 confirma que el canal seguro sigue publicado.

**Si difiere.** Si el Write legítimo falla, clasificar primero el problema de certificado, TrustList del aula, disponibilidad o interoperabilidad. No presentar la indisponibilidad como una denegación RBAC correcta.

---

## Evidencia común y consultas independientes

### Guardar respuestas sin inventar capturas

Conserve cada salida `tee` bajo `~/lab/evidencias/taller-10/`. Además, al cerrar cada práctica, recopile fuentes separadas:

```sh
labctl evidence | tee ~/lab/evidencias/taller-10/endpoint-evidence.json
curl -sS http://panel:8000/api/evidence | tee ~/lab/evidencias/taller-10/panel-evidence.json
curl -sS http://panel:8000/api/packets | tee ~/lab/evidencias/taller-10/packets.json
```

`labctl evidence` es evidencia del endpoint local y puede incluir el log de osquery; `/api/evidence` es el estado/evento de aplicación; `/api/packets` es la vista de paquetes del panel. No son intercambiables. No redirigir datos al `/evidence` del collector; solo consultar la evidencia que el sistema ya exponga.

Si el panel anuncia una captura lista, guárdela como PCAP local:

```sh
curl -fsS http://panel:8000/api/capture -o ~/lab/evidencias/taller-10/retail-ot-live.pcap
```

**Resultado esperado y significado.** Se conserva el PCAP real del aula; `-f` devuelve error si aún no está listo. En Wireshark, `modbus` o `tcp.port == 502` permite revisar Modbus; `tcp.port == 4840` permite ubicar OPC UA. Una firma HEL solo demuestra presencia de OPC UA: no demuestra Write malicioso ni contenido de un canal cifrado.

**Si difiere.** Si `/api/packets` está vacío o el PCAP no está listo, documentar “no disponible” junto con el timestamp real; no fabricar una captura. La respuesta del cliente, el estado del proceso y los logs siguen siendo evidencias válidas si se identifica su fuente.

### Kibana y eventos

Desde Firefox, Kibana es opcional y solo sirve para corroborar las acciones propias en `retail-ot-*`. Usar KQL, no SQL:

```kql
event.dataset : "lab.control" AND event.action : redteam-*
```

```kql
event.dataset : "lab.control" AND host.name : "plc" AND event.outcome : "blocked"
```

```kql
event.dataset : "suricata" AND suricata.alert.signature : *FC16*
```

```kql
event.dataset : "suricata" AND suricata.alert.signature_id : 1000005
```

La última firma identifica el sesgo de sensor del escenario fijo. Las firmas simples asumen PDU alineada en el payload y no son análisis universal de fragmentación TCP. Los logs de PLC, gateway y cliente, el PCAP y el estado del proceso son fuentes diferentes. Osquery observa endpoints Linux; no prueba por sí mismo la autorización de una variable OPC UA. Los `_id`, timestamps, hashes y PIDs de la evidencia son los que capture la sesión; no se rellenan con valores predeterminados.

### Entregable mínimo

Para cada una de A–F entregar:

- comando exacto y salida completa del cliente;
- estado `before`/`after` y una lectura de `classroom-state`;
- política que debía aceptar o rechazar la acción;
- código/estado de excepción real, o causa real de indisponibilidad;
- segunda fuente: evento, gateway/PLC, API de paquetes, PCAP o KQL;
- explicación de qué control actuó, qué no demuestra y cómo se conserva la operación legítima.

No se aprueba un resultado basado solo en un botón verde, en una captura de pantalla inventada o en un supuesto hash/PID.

## Solución razonada y criterios de éxito

La solución completa sigue **A → B → C → D → E → F**, ejecutando `labctl reset-all` de forma coordinada antes de cada práctica y guardando evidencia antes del siguiente reset. Para la misma práctica, la comparación repite la **misma acción, valor y objetivo** después del control; cambiar de host o valor para forzar otro resultado invalida la comparación.

La rúbrica comprueba:

- **A:** FC06 inicialmente aceptada; después del guard PLC, `0x86/0x03`, sin perder FC03.
- **B:** FC06 bloqueada por denylist incompleta; FC16 atraviesa y altera 50; luego la allowlist bloquea FC16 con `0x90/0x03` y FC03 sigue disponible.
- **C:** sesgo 800 → `-20.0` °C y compresor detenido por lectura falsa; después input guard y allowlist rechazan la misma orden; Anatomy y desconexión/reconexión se explican con sus límites.
- **D:** ráfaga exactamente de ocho; rate limit rechaza parte con `0x06` sin bloquear Read; el guard PLC evita consignas inseguras aunque algunas solicitudes lleguen.
- **E:** anónimo/None y observador cifrado escriben en el estado débil; RBAC deniega observador, permite ingeniería a 3 y el guard PLC rechaza 50 incluso para ingeniería.
- **F:** None deja de publicarse; Browse/Read y Write seguro de ingeniería siguen funcionando. Si el canal seguro queda indisponible, se reporta indisponibilidad, no hardening exitoso.

### Matriz de hardening y referencia

| Prueba | Control principal | Verificación legítima | Referencia |
|---|---|---|---|
| FC06/FC16 de consigna | Validación central y allowlist | FC03 disponible | IEC 62443 FR3/FR5/FR7; MITRE ICS T0836/T0831 |
| Sesgo de sensor | Entrada remota protegida, plausibilidad y respaldo declarado | Reconectar AI0 devuelve señal | IEC 62443 FR3/FR7; MITRE ICS T0856 como representación de reporting falso |
| Ráfaga finita | Presupuesto Write + guard semántico | Read no consume presupuesto | IEC 62443 FR7; no declarar DoS probado |
| OPC UA observador | Autorización de servidor por usuario/nodo | Ingeniería escribe 3 °C | IEC 62443 FR1/FR2/FR3; MITRE ICS T0836 |
| OPC UA None | Publicar solo SignAndEncrypt + RBAC | Browse/Read y Write legítimos | IEC 62443 FR1/FR2/FR4 |

SL-T se define por riesgo de zona/conducto; SL-A no se obtiene con estas acciones. Los mapeos son pedagógicos y no afirman cumplimiento de todos los SR de IEC 62443.

## Contexto chileno y errores típicos

Antipatrones hipotéticos aplicables a retail/plantas chilenas: una sola contraseña de mantenimiento; tratar “puerto 502 bloqueado” como una política completa; habilitar todas las escrituras OPC UA porque el canal usa certificados; calibración remota sin gestión de cambios; y considerar alimentos seguros solo porque el frío volvió. No se atribuyen estas prácticas a organizaciones reales.

Ley 21.663: evaluar si la entidad/servicio y el incidente cumplen la obligación de notificar; alerta temprana T+3 h, reporte general T+72 h y excepción OIV indicada en `docs/respuesta-chile.md`. Son plazos normativos, no duración del taller. El ejercicio prepara un borrador y conserva evidencia; **no envía notificaciones a ANCI**. No asumir condición OIV ni número de designados sin verificar la resolución vigente. Las sanciones dependen de obligación, gravedad y sujeto según la guía normativa existente.

## Referencias conservadas

- [Modbus Organization](https://www.modbus.org/modbus-specifications): funciones de aplicación y Modbus Security TLS en puerto 802, distinto del TCP 502 implementado aquí.
- [Formato Modbus](https://www.modbustools.com/modbus.html): FC06/FC16 y direccionamiento base cero.
- [OPC Foundation Part 2](https://reference.opcfoundation.org/Core/Part2/v105/docs/4.2): autenticación, autorización, integridad, confidencialidad y disponibilidad.
- [NIST SP 800-82 Rev. 3](https://csrc.nist.gov/pubs/sp/800/82/r3/final): priorizar seguridad física y continuidad OT al modificar controles.

La prueba automática de verificación del repositorio es una comprobación del personal del laboratorio, no un paso del alumno: esta guía está diseñada para resolverse desde la Terminal del noVNC y la guía local, sin volver al portal para instrucciones.

**Cierre.** Después de guardar todas las evidencias, coordinar cualquier `labctl reset-all` final con los demás alumnos. No usar `labctl reset` local como sustituto de la limpieza del aula ni declarar recuperado el stock solo porque el proceso vuelva a enfriarse.
