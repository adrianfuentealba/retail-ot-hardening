# Empieza aquí · Trabaja dentro de noVNC

Las once entradas de inicio y talleres, la solución y las referencias están incluidas en la imagen de cada una de las cinco estaciones. **No debes volver al portal para leer ni copiar instrucciones.** Las guías se sirven desde `127.0.0.1:8010` dentro del Linux que estás viendo. Ese localhost no es el de tu computador anfitrión.

## 1 · Abre la guía y una terminal

Doble clic en **Guías paso a paso — Retail OT**. Si XFCE pregunta si confías en el lanzador, confirma únicamente ese archivo creado en el laboratorio. También puedes abrir Terminal del laboratorio y ejecutar:

```bash
labctl guides
```

**Resultado esperado:** Firefox muestra «Guías locales · Retail OT» y la identidad de la estación. No abre el portal ni crea una conexión de pentest. Si Firefox no abre, ejecuta desde la terminal gráfica de noVNC, no desde una terminal sin DISPLAY del anfitrión. Alternativa: escribir `http://127.0.0.1:8010/guides/` en Firefox dentro de la estación.

Abre **Terminal del laboratorio** y coloca ambas ventanas lado a lado; arrastra cada barra de título hacia el borde de la pantalla para organizarte.

## 2 · Verifica tu identidad antes de copiar

```bash
hostname
id
```

**Resultado esperado:** uno de los cinco nombres siguientes y usuario `student`. Los identificadores numéricos son datos del sistema, no una contraseña. Si estás en otra máquina, los comandos locales actúan allí aunque estés leyendo una guía de otro rol.

| Estación | Rol | Taller recomendado | noVNC desde el anfitrión |
|---|---|---|---|
| ws-corporate | TI L4 | Inventario y consulta de referencias | 127.0.0.1:6081 |
| ws-vendor | Proveedor L3.5 | 05, y etapa de proveedor del 09 | 127.0.0.1:6082 |
| ws-engineering | Ingeniería L3 | 04, 06, 07, 09 y 10 | 127.0.0.1:6083 |
| ws-hmi | HMI L2 | 01, 02, 03 y 08 | 127.0.0.1:6084 |
| ws-soc | SOC | Evidencia y correlación de todos | 127.0.0.1:6085 |

Todos tienen las guías completas. **Esto no cambia automáticamente el rol de ejecución.** En talleres multihost, abre el noVNC del host indicado; ya encontrarás la misma guía allí. No es necesario copiar un comando al anfitrión y luego a otra máquina.

## 3 · Copia y pega sin pivote

En un bloque marcado **COMANDO · TERMINAL LINUX**, pulsa **Copiar**. Vuelve a la Terminal de ese mismo escritorio y pulsa **Ctrl + Shift + V**. Revisa la línea y pulsa Enter.

**Resultado esperado:** solo se pega el comando; no se ejecuta al copiar. El portapapeles es el de Firefox/Terminal de la estación Linux. No uses el panel de portapapeles de noVNC ni el del anfitrión para este flujo. En un terminal Linux, Ctrl+C interrumpe un proceso; no es el atajo para pegar.

Si el botón no copia, selecciona el texto en Firefox y pulsa Ctrl+C **dentro de Firefox**, luego Ctrl+Shift+V en Terminal. También puedes usar el menú Editar → Pegar en Terminal. Los bloques **RESULTADO / REFERENCIA · NO EJECUTAR** no tienen botón Copiar; son ejemplos a interpretar, no comandos. No copies `$`, prompts, JSON de salida ni comentarios narrativos como si fueran órdenes.

## 4 · Confirma el agente local y el proceso compartido

```bash
labctl status
```

**Resultado esperado:** JSON con `host`, `role`, `policies`, `mode` y versión osquery. `host` debe coincidir con hostname. `policies` son del endpoint actual; no significan que el PLC/gateway ya estén protegidos.

```bash
labctl classroom-state | jq '{process, gateway, policies, errors}'
```

**Resultado esperado:** JSON del orquestador con estado del PLC, gateway, políticas globales y errores. Si `process` es null o hay servicios unavailable, no declares éxito a partir de una animación o salida antigua: pide al instructor revisar el stack. Leer las guías sigue siendo local; las acciones de proceso siguen pasando por el orquestador como antes.

## 5 · Distingue reset local y reset del aula

```bash
labctl reset
```

**Resultado esperado:** elimina las políticas de **tu endpoint actual** y detiene sus procesos benignos registrados. No reinicia PLC, gateway, stock ni otros endpoints; tampoco restaura firmware ficticio. Mantiene la evidencia. Úsalo cuando la guía indica una preparación local.

**El siguiente comando es global: coordina con el grupo antes de ejecutarlo.** No lo uses para «arreglar» tu terminal mientras otro alumno trabaja sobre el proceso.

```bash
labctl reset-all
```

**Resultado esperado:** aviso en Terminal y evento de reset de aula; PLC vuelve a consigna 2 °C, políticas globales y de endpoints se restablecen, stock del modelo vuelve a referencia de aula. Logs y PCAP no se borran. Comprueba después `labctl classroom-state` y `labctl status`. Un reset de stock solo es una operación pedagógica, no recuperación sanitaria.

## 6 · Guarda evidencia sin mezclarla con la captura automática

```bash
mkdir -p ~/lab/evidencias/inicio
labctl status > ~/lab/evidencias/inicio/estado-endpoint.json
labctl classroom-state > ~/lab/evidencias/inicio/estado-aula.json
ls -lh ~/lab/evidencias/inicio
```

**Resultado esperado:** dos archivos JSON no vacíos de tu sesión. Los talleres usan una carpeta distinta por número. `~/lab` vive en la capa de la estación: conserva los archivos antes de recrearla. `/evidence` es el volumen de telemetría automática persistente; no lo borres ni guardes falsas observaciones allí. Captura automática y evidencia manual son fuentes diferentes.

## 7 · Consulta resultados visuales sin salir del Linux

El gemelo y Kibana son observadores del aula, no el lugar obligatorio para copiar instrucciones. Puedes abrirlos en pestañas de Firefox **dentro de noVNC**:

- Gemelo: `http://panel:8000`.
- Módulo 10: `http://panel:8000/labs/10`.
- Dashboard general: `http://kibana:5601/app/dashboards#/view/retail-overview`.

También puedes mantener el gemelo en el navegador del anfitrión. En cambio, los comandos se copian y pegan siempre dentro de noVNC. No uses `http://127.0.0.1:5601` desde la estación: no es Kibana allí. Las URLs publicadas del README son para el anfitrión.

## 8 · Si algo no coincide

| Síntoma | Qué verificar | Qué no concluir |
|---|---|---|
| No abre guía | Icono o `labctl guides`; agente local activo; imagen nueva construida | Que el portal deba actuar como pivote |
| Copiar no hace nada | Selección manual/Ctrl+C en Firefox y Ctrl+Shift+V en Terminal | Que necesites copiar al anfitrión |
| Guía advierte otro host | `hostname`; cambia al noVNC del rol indicado | Que elegir taller cambie tu estación |
| Error Connection refused en labctl | El agente local no responde; informar al instructor | Que la contramedida bloqueó un ataque |
| Proceso benigno no aparece | Es temporal; verificar políticas y repetir emulación si corresponde | Que ausencia tardía sea prueba de detección |
| Datos viejos en Kibana | Hora/host/filtro, documentos nuevos y refresh | Que un evento histórico acredite tu intento |
| Operation not permitted con sudo | Student no tiene sudo general; usar comandos de la guía | Que debas desactivar restricciones del contenedor |
| Un paso sale blocked desde el inicio | Políticas heredadas y host; reset solo según alcance coordinado | Que ya demostraron antes/después |

## Criterio de éxito de este inicio

Debes poder abrir una guía local, identificar tu host, copiar un bloque y ejecutarlo en Terminal sin usar el portapapeles del anfitrión; distinguir estado endpoint/global y guardar evidencia con fuente explícita. Las guías no ejecutan comandos automáticamente.

El laboratorio es exclusivamente educativo, con destinos internos fijos y sin conexión a sistemas industriales reales. No hay evaluación por velocidad ni duraciones de resolución. [Tutorial de observabilidad](tutorial-observabilidad.md), [arquitectura y límites](arquitectura.md) y [respuesta chilena](respuesta-chile.md) siguen disponibles como referencias locales.
