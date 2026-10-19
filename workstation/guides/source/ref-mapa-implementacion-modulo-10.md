# Mapa de implementación del módulo 10

El laboratorio sigue arrancando con `docker compose up -d`. No hay nuevos puertos públicos ni acceso al socket Docker. Docker copia source/bundles y guías; Node solo hace falta si se desea editar los paneles Mantine.

| Archivo | Responsabilidad | Punto de hardening |
|---|---|---|
| `plc/control_logic.py` | Validación central y ciclo térmico | `validate_change`, `apply_changes`, `control_cycle` |
| `plc/main.py` | Servidor Modbus FC03/FC06/FC16 y OPC UA | Guard de atributo con usuario/rango; endpoint sin None configurable |
| `gateway/main.py` | Conducto de aplicación | Allowlist función/dirección/cantidad/valor, presupuesto Write |
| `app/redteam.py` | Pruebas de destino fijo | No IP/puerto/payload libre; ocho solicitudes máximo en ráfaga |
| `app/redteam-catalog.json` | Seis prácticas estructuradas | Impacto, comandos, criterio de éxito y referencia |
| `app/main.py` | Orquestación, código CPU e I/O del aula | `/api/anatomy` y `/api/anatomy/wiring`, fuera de banda declarado |
| `workstation/agent.py`, `labctl.py` | Comandos desde cinco Linux | Lista explícita de acciones |
| `ui/instructor.jsx` | Paneles Mantine de prácticas e inspector | Estado real del backend, sin código libre ni telemetría inventada |
| `app/static/anatomy.js` | Despiece kit Anatomy | Ratón/teclado y selección sincronizada |
| `app/static/scene.js` | Animación Three.js | Compresor/sensor/alarma según proceso, no resultado ficticio |
| `ids/retail.rules` | Evidencia IDS | SID 1000004 FC16 y 1000005 sesgo de sensor |
| `scripts/verify-redteam.py` | 28 comprobaciones end-to-end | Modifica/restablece el aula sin borrar evidencia |
| `tests/test_redteam_logic.py` | Unit tests de lógica y aislamiento | Atomicidad, I/O, cuarentena y destinos fijos |

La guía de solución incluye secuencias reproducibles para todas las prácticas. No hay una herramienta de pentest genérica reorientable a otra infraestructura. Cambiar objetivos o límites requiere modificar el código y revisar su autorización; no está disponible por CLI ni formulario del alumno.
