# 10 · Red / Purple Team: Modbus y OPC UA en supermercado retail

## Objetivos medibles

El alumno debe demostrar cómo una escritura de protocolo altera la cadena de frío de SCL-01, localizar dónde se valida una orden, construir contramedidas y verificar que no se rompe la operación legítima. Debe comparar FC06 y FC16; proteger señales de entrada; separar límites de tasa de límites de proceso; distinguir autenticación, cifrado y autorización OPC UA; y explicar el código CPU y las conexiones I/O en Anatomy.

**A tu ritmo:** no se asigna duración de resolución ni se evalúa velocidad. Las esperas que aparezcan en comandos responden a la telemetría del sistema, no a un tiempo objetivo del alumno.

> Escenarios exclusivamente controlados del aula. Destinos internos fijos, sin IP configurable, exploit, escaneo, MITM, captura de credenciales, malware ni flood. La ráfaga tiene exactamente ocho operaciones secuenciales. No conectar las herramientas ni redes a tiendas, PLC o RTU reales.

## Preparación y roles

Desde el anfitrión, dentro del repositorio:

```sh
docker compose up -d
docker compose ps -a
```

Abrir [módulo 10](http://127.0.0.1:8090/labs/10). La pestaña **Red Team** también está disponible desde los otros talleres. Para cada práctica elegir una prueba, leer su impacto, ejecutar los pasos y observar la escena fija. Los paneles Práctica / Por qué y defensa / Evidencia muestran solo el contexto de la prueba seleccionada.

Asignar Red a ingeniería, Blue a SOC y un operador de proceso para decidir recuperación y stock. En noVNC ingeniería abrir Terminal del laboratorio. `labctl` funciona igualmente desde la consola acotada del portal. **Restablecer aula antes de cada práctica**, después de guardar evidencias; no simultanear escenarios de diferentes alumnos sobre el mismo estado.

La temperatura grande es la **física simulada**, no una lectura de sensor de una instalación. Debajo se muestran AI0, compresor, deshielo y respaldo. Esto permite detectar pantalla aparentemente fría mientras el producto se calienta. El modelo es acelerado e idealizado: no es una predicción sanitaria ni termodinámica.

## A. FC06: escritura de consigna sin validación semántica

Primero registrar lectura legítima:

```sh
labctl redteam baseline
```

Esperado: FC03 lee ocho registros; no hay excepción. Consigna 2 °C, lectura nominal, compresor operativo. La respuesta incluye bytes de solicitud/respuesta reales a través de la pasarela.

```sh
labctl redteam modbus-write
```

Esperado: FC06 escribe registro 0 a 50, respuesta eco; `after.setpoint=50`, deshielo ON y compresor OFF. Observar subida en el gemelo; stock puede pasar a riesgo/cuarentena. No inventar una exposición si aún no aparece en el backend.

**Anatomía de solicitud Modbus TCP del ejercicio:**

```text
A0 28 00 00 00 06 01 06 00 00 00 32
│TID│ PID  │ LEN │U │FC│ ADDR │VALUE│
41000   0      6    1   6   0     50
```

TID correlaciona respuesta; no es token de autenticación. Length cuenta Unit ID + PDU. TCP no lleva CRC RTU. Registro 0 es dirección de protocolo base cero, no “registro uno” textual de una hoja de fabricante.

Aplicar guard central de proceso y repetir exactamente la misma operación:

```sh
labctl harden plc
labctl redteam modbus-write
labctl redteam baseline
```

Esperado: excepción FC `0x86`, código `0x03` Illegal Data Value; consigna nominal 2 °C, FC03 disponible. La regla vive en `validate_change()` y se aplica antes de mutar el PLC. No rehabilita alimentos ya comprometidos. Abrir Anatomy → CPU → **Código CPU** y localizar el rango `0 <= value <= 6`.

## B. FC16: evadir una denylist incompleta

Restablecer aula desde el portal. Activar deliberadamente el **antipatrón controlado** de gateway que bloquea solo FC06:

```sh
labctl redteam fc06-only
labctl redteam modbus-write
```

Esperado: FC06 bloqueada por pasarela. No concluir que todas las escrituras están protegidas.

```sh
labctl redteam modbus-fc16
```

Esperado: Write Multiple Registers FC16 pasa el filtro incompleto y modifica la misma consigna a 50. El gemelo muestra el mismo impacto. Este ejemplo utiliza **un registro** con FC16, válido en el protocolo; no se requiere escribir varios para usar esta función.

```text
A0 29 00 00 00 09 01 10 00 00 00 01 02 00 32
│TID│ PID  │ LEN │U │FC│ ADDR │ QTY │BC│DATA │
41001   0      9    1  16   0     1    2   50
```

Respuesta normal: FC16, dirección inicial y cantidad; no eco de todos los valores. FC16 admite hasta 123 registros según especificación, pero el mapa de este PLC ficticio solo permite posiciones 0, 4 y 5 como escrituras independientes. Si una transacción incluye telemetría read-only, se rechaza completa antes de mutar.

```sh
labctl harden modbus
labctl redteam modbus-fc16
labctl redteam baseline
labctl recover
```

Esperado: `0x90/0x03`, FC03 conservada, frío recuperado. La allowlist controla **función + Unit ID + dirección + cantidad + valor**, no solo un puerto. En este modelo autoriza escrituras remotas únicamente al registro de consigna y dentro de 0–6. El interlock PLC añade defensa si otra ruta llegara al controlador.

## C. Sensor alterado: leer frío falso y detener refrigeración

Restablecer aula. La calibración remota débil permite una escritura al registro 4:

```sh
labctl redteam modbus-sensor
```

Se escribe 800, que el mapa traduce a `(800-1000)/10 = -20 °C` de sesgo. No es alteración de un sensor físico: es un defecto de diseño simulado en el PLC de aula. AI0 aparece muy por debajo de la física, la lógica cree que está demasiado frío y detiene DO0 compresor; el producto se calienta aunque la lectura sea fría.

```sh
labctl harden inputs
labctl redteam modbus-sensor
labctl harden modbus
```

Esperado: sesgo restaurado a cero, sensor conectado, escritura remota rechazada `0x86/0x02` Illegal Data Address. La pasarela ahora también excluye esos registros. Validación de señal y dominio de mantenimiento no se sustituyen con cifrado del transporte.

### Cablear y comprender en Anatomy

Abrir **Entradas / Salidas → Entender**. Ver AI0 PT100/módulo RTD o transmisor 4–20 mA, DI0 puerta, DO0 compresor, DO1 deshielo y DO2 alarma. La elección PT100 directo vs transmisor requiere módulos distintos. No conectar potencia del compresor directamente al PLC: DO0 manda un relé/contactor con protecciones apropiadas.

En **Conectar / Probar**, desactivar AI0. La señal se desconecta en el backend del proceso; después de aplicar input_guard, aparecen alarma y respaldo ideal. Rehabilitar AI0 y comprobar retorno a señal primaria. Desactivar DI0 representa puerta abierta del modelo y añade carga térmica/alarma.

**Límite obligatorio:** el respaldo usa temperatura ideal conocida por el simulador. Una planta no dispone mágicamente de ese valor: requiere sensor redundante físico, diagnóstico, modo degradado aprobado y análisis de riesgo operacional. No extrapolar el comportamiento a seguridad funcional de un sistema real.

## D. Ráfaga finita: tasa no reemplaza integridad

Restablecer aula:

```sh
labctl redteam modbus-burst
```

Esperado: exactamente ocho FC06 secuenciales, ocho aceptadas, consigna de deshielo. No hay parámetros para ampliar carga. Las estadísticas no son un ensayo de disponibilidad ni un DoS demostrado.

```sh
labctl harden write-rate
labctl redteam modbus-burst
labctl redteam baseline
```

Esperado: algunas escrituras se rechazan con excepción `0x86/0x06` Server Device Busy; la pasarela mantiene FC03. Se limita presupuesto Write por fuente mientras las lecturas no consumen ese presupuesto. Por diseño todas estas pruebas se originan en el orquestador de aula; no se afirma rate-limiting por cada usuario noVNC.

```sh
labctl harden plc
labctl redteam modbus-burst
labctl recover
```

Justificación: las primeras órdenes de una ráfaga pueden ser peligrosas aunque las demás se rechacen. **Control de tasa + validación de consigna + allowlist de conducto** son barreras complementarias.

## E. OPC UA: un canal cifrado no significa permiso Write

Restablecer aula. Empezar con usuario anónimo y endpoint None:

```sh
labctl redteam opcua-anonymous
```

Esperado: Write real a `ns=2;s=Setpoint`, 50. El servidor débil autoriza por defecto. La propiedad `after.setpoint` y la evolución física acreditan el impacto.

```sh
labctl redteam opcua-observer
```

Este cliente utiliza SignAndEncrypt y credencial **pública de ejemplo de aula** `observer / retail-observer-lab`. Al faltar RBAC, todavía escribe 50. No se roba contraseña: el cliente de práctica usa identidad conocida del laboratorio. El certificado de aula está fijado y compartido: no representa identidad de aplicación independiente por workstation.

```sh
labctl harden opcua-rbac
labctl redteam opcua-observer
labctl recover
labctl redteam opcua-engineer
```

Esperado: observador recibe **BadUserAccessDenied**, ingeniería `engineer / retail-engineer-lab` conserva Write autorizado a **3 °C**. La barrera se aplica en **servidor**, no porque el cliente voluntariamente se niegue a escribir. Esto distingue autenticación de autorización por usuario/nodo/operación.

```sh
labctl harden plc
labctl redteam opcua-overrange
```

Esperado: incluso ingeniería recibe **BadOutOfRange** al solicitar 50, antes de mutar estado. Ser usuario autorizado no autoriza parámetros inseguros. Confirmar consigna nominal y comparar `plc/control_logic.py` con el servicio de atributos de `plc/main.py`.

El taller 06 conserva su política anterior **read-only para todos** (`harden opcua`). No mezclarla en esta práctica si se desea verificar Write legítimo de ingeniería: usar Restablecer aula antes de cambiar de modelo de autorización.

## F. Cerrar None sin romper el cliente legítimo

Restablecer aula:

```sh
labctl redteam opcua-anonymous
labctl recover
labctl harden opcua-channel
labctl redteam opcua-anonymous
```

Esperado: None deja de estar publicado por el servidor y el intento sin política cifrada no puede abrir conexión/sesión compatible. El comando cambia la configuración y reinicia solo el endpoint OPC UA del modelo, no el PLC físico. `opcua_ready` indica disponibilidad después del cambio; registrar cualquier fallo sin declarar que es siempre una denegación correcta.

```sh
labctl harden opcua-rbac
labctl redteam opcua-browse
labctl redteam opcua-engineer
```

Esperado: Browse/Read seguro conservado y Write a 3 permitido para ingeniería. Si el servicio cifrado tampoco funciona, el resultado es **indisponibilidad**, no hardening exitoso.

**Contramedida productiva a discutir:** política de certificados/TrustLists y claves por aplicación, ciclo de renovación/revocación, usuarios individuales, auditoría, permiso mínimo por nodo, deshabilitar políticas obsoletas y prueba de interoperabilidad fuera de producción. El aula no implementa una PKI empresarial ni prueba MITM.

## Evidencia común y consultas

En portal **Paquetes**, revisar payload capturado; descargar PCAP real. Wireshark: filtro `modbus` o `tcp.port == 502`; OPC UA `tcp.port == 4840`. Una firma HEL señala presencia, no Write malicioso ni contenido de un canal cifrado.

En Kibana Discover `retail-ot-*`, seleccionar la ventana que contenga las acciones propias. Usar KQL, no SQL:

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

El último filtro identifica la firma de sesgo de sensor del escenario fijo. Las firmas simples asumen PDU alineada en payload y no hacen análisis universal de fragmentación TCP. Logs de PLC/pasarela/cliente, PCAP y estado del proceso son fuentes diferentes. osquery observa endpoints Linux; no prueba por sí mismo la autorización de una variable OPC UA.

```sh
labctl evidence
```

Guardar respuesta del cliente, código de excepción/estado UA, fuente que denegó, consigna, física, AI0 y estado de actuadores, junto con PCAP y `_id` de eventos. No concluir protección por un color verde del botón.

## Solución razonada y criterios de éxito

La solución completa es la secuencia A→F, restableciendo entre prácticas. El alumno aprueba si muestra FC06 inicialmente aceptada y luego excepción, FC16 atravesando denylist incompleta y después bloqueada, entrada protegida contra sesgo y comportamiento de desconexión, tasa acotada sin romper Read, Write observador denegado pero Write de ingeniería permitido, consigna insegura denegada incluso a ingeniería, y None cerrado sin perder conexión cifrada.

La rúbrica evalúa exactitud de decodificación, identificación de la barrera correcta, continuidad legítima, evidencia independiente y explicación de límites. No otorga puntaje por terminar más rápido. Para cada práctica repetir **la misma acción y mismo objetivo** después del control; cambiar de valor/host para “hacer que pase” invalida la comparación.

### Matriz de hardening y referencia

| Prueba | Control principal | Verificación legítima | Referencia |
|---|---|---|---|
| FC06/FC16 consigna | Validación central y allowlist | FC03 disponible | IEC 62443 FR3/FR5/FR7; MITRE ICS T0836/T0831 |
| Sesgo de sensor | Entrada remota protegida, plausibilidad y respaldo declarado | Reconectar AI0 devuelve señal | FR3/FR7; T0856 como representación de reporting falso |
| Ráfaga finita | Presupuesto Write + guard semántico | Read no consume presupuesto | FR7; sin declarar DoS probado |
| OPC UA observador | Autorización de servidor por usuario/nodo | Ingeniero Write 3 °C | FR1/FR2/FR3; T0836 |
| OPC UA None | Publicar solo SignAndEncrypt + RBAC | Browse/Read y Write legítimos | FR1/FR2/FR4 |

SL-T se define por riesgo de zona/conducto; SL-A no se obtiene por estas acciones. Los mapeos son pedagógicos, no una afirmación de cumplimiento de todos los SR de IEC 62443.

## Contexto chileno y errores típicos a discutir

Antipatrones hipotéticos aplicables a retail/plantas chilenas: una sola contraseña de mantenimiento, tratar “puerto 502 bloqueado” como política completa, habilitar todas las escrituras OPC UA porque el canal usa certificados, calibración remota sin gestión de cambios y considerar alimentos seguros solo porque el frío volvió. No se atribuyen estas prácticas a organizaciones reales.

Ley 21.663: evaluar si la entidad/servicio y el incidente cumplen la obligación de notificar; alerta temprana T+3 h, reporte general T+72 h y excepción OIV indicada en `docs/respuesta-chile.md`. Estos son plazos normativos, no duración de taller. El ejercicio prepara un borrador y conserva evidencia, **no envía a ANCI**. No asumir condición OIV ni número de designados sin verificar resolución vigente. Sanciones dependen de obligación, gravedad y sujeto; ver la guía normativa existente.

## Referencias

[Modbus Organization](https://www.modbus.org/modbus-specifications): funciones de aplicación y Modbus Security TLS puerto 802, distinto del TCP 502 implementado aquí. [Formato Modbus](https://www.modbustools.com/modbus.html): FC06/FC16 y direccionamiento base cero. [OPC Foundation Part 2](https://reference.opcfoundation.org/Core/Part2/v105/docs/4.2): autenticación, autorización, integridad, confidencialidad y disponibilidad. [NIST SP 800-82 Rev. 3](https://csrc.nist.gov/pubs/sp/800/82/r3/final): priorizar seguridad física y continuidad OT al modificar controles.

## Prueba automática del módulo

En anfitrión, sin otro taller activo:

```sh
python3 scripts/verify-redteam.py
```

Prueba paquetes, impacto, guards, código CPU, señal Anatomy y eventos IDS; restablece el aula al finalizar conservando evidencia. Los resultados están en `docs/redteam-verification-results.json`. Un error se conserva y se corrige; no reemplazarlo por un resultado esperado.
