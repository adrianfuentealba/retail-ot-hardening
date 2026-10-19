# Guías locales noVNC · Actualización y validación

## Qué se entrega

Los diez talleres se ampliaron con preparación por host, propósito, comandos cortos copiables, resultados esperados, significado, segunda evidencia, diagnóstico, criterios y solución. El desafío 09 separa los roles; el módulo 10 desarrolla sus seis prácticas. No se asignan duraciones ni velocidad objetivo.

Cada imagen de estación incluye una guía de inicio, talleres, solución y referencias: HTML/CSS/JS y copias Markdown locales, generados desde `exercises/` y `docs/`. No usa CDN, dependencias del navegador ni lectura de guías desde el portal. **Guías paso a paso — Retail OT** abre Firefox en `http://127.0.0.1:8010/guides/` dentro de Linux; la misma URL en el anfitrión no tiene ese significado.

`labctl guides` abre el inicio; `labctl guides 10` abre módulo 10. Los nuevos `classroom-state` y `reset-all` delegan respectivamente consulta GET y reset global al orquestador. `reset` conserva alcance local. Mantener orquestación por labctl fue una decisión explícita: no se movió la generación de tráfico de protocolo al origen de cada estación. Las guías no ejecutan comandos automáticamente.

## Actualizar una instalación existente

**Pausar el trabajo de los alumnos antes de recrear estaciones.** Cerrar y guardar documentos y evidencia manual de `~/lab/evidencias/`, ya que el home de la estación no está montado en volumen persistente. Los volúmenes automáticos de evidencia/Elastic se conservan; no ejecutar `down -v`. Tampoco usar reset-all como sustituto de una actualización.

Los siguientes comandos se ejecutan en el **anfitrión que tiene Docker**, no dentro del noVNC:

```bash
cd retail-ot-hardening
git pull --ff-only origin main
docker compose up -d --build --no-deps ws-corporate ws-vendor ws-engineering ws-hmi ws-soc panel
docker compose ps -a
```

Esto construye las imágenes actualizadas y recrea las cinco estaciones y el portal para que sus guías coincidan. No solicita recrear PLC/gateway/Elastic/sensor. Las políticas del agente y su home pueden perderse al recrear cada endpoint; coordinar la práctica antes de actualizar. Para un aula nueva:

```bash
git clone https://github.com/vtomasv/retail-ot-hardening.git
cd retail-ot-hardening
docker compose up -d --build
```

Dentro de cada noVNC, abrir **Guías paso a paso** o ejecutar en Terminal:

```bash
labctl guides
```

Resultado esperado: Firefox muestra identidad local, índice de talleres y bloques verdes de comandos con Copiar. Ctrl+Shift+V en Terminal, revisión y Enter. Si XFCE pide confiar en el lanzador, verificar que sea Guias.desktop incluido en el laboratorio. Los bloques de resultados no tienen Copiar. Selección manual en Firefox/Ctrl+C es alternativa si el portapapeles web no se habilita.

## Validación del 19-10-2026

| Prueba | Resultado | Evidencia |
|---|---|---|
| Contrato, lógica y guías compiladas | 20/20 PASS | `tests/` |
| Guías/identidad/CLI student en cinco roles | 5/5 PASS | `local-guides-runtime-results.json` |
| Navegación de diez talleres, advertencia de rol, copiado, fuentes/resultados y ancho | 18/18 PASS | `local-guides-ui-results.json` |
| Firefox Linux → clipboard X11 → Terminal student → ejecución de hostname/id | PASS | `local-guides-clipboard-results.json`, captura 16 |
| Rutas de helper y reset local/global | 3/3 PASS, transporte simulado | `local-guides-helper-results.json` |

Se probaron contenedores QA con nombres DNS y puertos diferentes a los del aula. Los cinco usan la imagen de estación candidata, mismo usuario student y cinco roles. La lectura y el estado del aula se probaron sin escribir en PLC/gateway. **No se reiniciaron las estaciones de clase ni se ejecutó un reset global real.** La publicación del código no actualiza automáticamente las máquinas ya abiertas: aplicar los comandos anteriores durante una pausa.

En el ensayo X11 el botón Copiar escribió `hostname` e `id`, sin prompt, en el clipboard Linux; Ctrl+Shift+V los pegó y se ejecutaron después de revisar/pulsar Enter. Terminal devolvió ws-hmi y uid/gid de student. No se usó portapapeles del anfitrión ni pivote al portal. Las capturas son de la interfaz real, sin composición o datos inventados.

La prueba como student detectó permisos de lectura insuficientes de labctl en la imagen candidata. Dockerfile ahora fija `755`, independiente del modo del archivo al crear el contexto. La verificación de runtime exige `labctl status` como student en los cinco roles, no solo HTTP de root.

Las suites ofensivas/defensivas 28/28 y 39/39 y observabilidad 58/58 son evidencia previa; no se volvieron a ejecutar durante la clase activa. No se afirma validación humana exhaustiva de todos los pasos ni nueva matriz amd64. ARM64 de Docker Desktop ejecutado; límites de física, certificados compartidos y guards de entrenamiento permanecen.

## Regenerar cuando se editan fuentes

Solo el autor necesita la dependencia de compilación; los alumnos reciben HTML listo. Desde el anfitrión del repositorio, usar un entorno virtual propio:

```bash
python3 -m venv .work/guides-venv
.work/guides-venv/bin/python -m pip install -r scripts/requirements-guides.txt
.work/guides-venv/bin/python scripts/build-local-guides.py
python3 -m unittest discover -s tests -v
```

Los hashes del manifest deben coincidir con todas las fuentes. Si los tests indican desincronización, regenerar antes de construir. No editar HTML generado a mano. Durante una pausa, comprobar la instalación actualizada con:

```bash
python3 scripts/verify-local-guides.py
```

Es una comprobación de lectura; no ejecuta escenarios ni reset. Para aprender el flujo completo, leer [Empieza aquí](inicio-desde-novnc.md). Para respuesta legal/seguridad, conservar las referencias de cada taller: exclusivamente aula autorizada, sin envío real a ANCI ni exposición pública de los puertos.
