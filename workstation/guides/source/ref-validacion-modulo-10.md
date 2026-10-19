# Validación del módulo 10 y Anatomy activo

Ampliación ejecutada sobre el laboratorio Docker local, contenedores Linux ARM64. No se añadieron puertos de protocolo públicos ni acceso al socket Docker. Los servicios conservan bind loopback y el expediente anterior permanece en volúmenes.

## Resultados

| Comprobación | Resultado | Evidencia reproducible |
|---|---|---|
| Lógica CPU y contrato estático | 13/13 PASS | `python3 -m unittest discover -s tests -v` |
| Módulo Red/Purple Team end-to-end | 28/28 PASS | `redteam-verification-results.json`, `scripts/verify-redteam.py` |
| Regresión de escenarios anteriores | 39/39 PASS | `verification-results.json`, `scripts/verify-lab.py` |
| UI e inspector en Chromium escritorio | 17/17 PASS | `redteam-ui-verification.json` |
| Observabilidad reforzada anterior | 58/58 PASS en ejecución previa | `observability-verification-results.json`; no se presenta como una nueva suite de este turno |

## Qué se comprobó

Escrituras TCP reales FC06/FC16 y respuestas de excepción; impacto en la misma térmica que usa el gemelo; denylist FC06 incompleta frente a FC16; allowlist función/dirección/valor; señal de sensor sesgada y escritura remota protegida; ráfaga finita de ocho operaciones y rechazos de tasa sin romper FC03; OPC UA Write None y cifrado; observador denegado por servidor y usuario de ingeniería autorizado; valor inseguro denegado aunque ingeniería tenga permiso; endpoint solo SignAndEncrypt con Browse/Read y Write legítimos conservados. PCAP/Tshark captura FC16 y la alerta Suricata se indexa en Elastic.

En UI se comprobó selección del módulo, canvas visible, señales, código CPU servido desde archivo real, inspector lateral sin invadir la escena, selección de piezas por ratón y teclado, explicación PT100/contactor, desconexión real de AI0 por switch y alarma/respaldo después de proteger entrada. También respuesta real de FC06 desde botón, conservación del panel tras ejecutar, cambio de pestaña sin perder canvas, ausencia de errores JavaScript y ausencia de duración sugerida.

Cinco capturas nuevas documentan módulo 10, CPU, señal desconectada, entrada protegida y sesgo de sensor. Se conservan las nueve anteriores como documentación histórica. La UI final usa un mismo evento de snapshot para escena y tarjetas Mantine, evitando mostrar dos polls distintos en capturas.

## Correcciones que se verificaron

- La capa de servicios de asyncua denegaba Write de todos los usuarios cifrados antes del control fino. Se permitió Read/Browse y Write llegar al guard de nodo; administración remota de nodos no se habilitó. Se verificó Write 3 °C de ingeniería y BadUserAccessDenied del observador.
- None se retiró del catálogo de endpoint del servidor, no solo del cliente. El rechazo por falta de endpoint compatible se diferencia de error de conexión/servidor. Un canal seguro legítimo debe seguir funcionando para considerar exitoso el control.
- El inspector fue alineado al panel de trabajo real, manteniendo escena completa a la izquierda en escritorio ancho.
- La prueba de switches usa su etiqueta visible; espera la reconexión registrada antes de repetir desconexión. No se cambió backend para simular un éxito.
- Validación de FC16 es atómica y la lógica es común con FC06/OPC UA, evitando una ruta de escritura equivalente sin interlock.

## Límites que no se deben ocultar

El código es un PLC ficticio Python, no firmware industrial ni SIS. La física, alarma, stock y los estados eléctricos son modelos educativos. `input_guard` usa una referencia ideal de temperatura del simulador: en planta se necesita redundancia física/diagnóstico y análisis de riesgo operacional. El banco Anatomy es una API pedagógica fuera de banda, no acceso físico remoto.

Las identidades OPC UA y el certificado/clave compartidos son públicos de aula, no PKI productiva. NoVNC/ELK continúan sin autenticación y solo en loopback. Todas las pruebas de protocolo parten del orquestador a gateway; cinco roles no son cinco orígenes de protocolo independientes. No hay MITM, flood, explotación de CVE, malware ni pentest contra tiendas reales. La ráfaga no demuestra un DoS. Las firmas simples FC06/FC16 requieren payload alineado; no son un IDS ICS completo ni descifran Write cifrado.

ARM64 se ejecutó; amd64 conserva dependencias, sin nueva matriz funcional. El flujo visual se verificó a 1600×1050 y se inspeccionó en navegador estrecho; no se afirma cobertura exhaustiva de todos los dispositivos ni validación humana de una cohorte. IEC 62443/MITRE son referencias didácticas, no certificación SL-A. El repositorio público previo no cambia por la entrega local de esta ampliación.

## Reproducir sin interferir con una clase

```sh
docker compose up -d
python3 -m unittest discover -s tests -v
python3 scripts/verify-redteam.py
python3 scripts/verify-lab.py
```

Ejecutar una suite después de otra; restablecen proceso y políticas sin eliminar evidencia. Usar el [tutorial del módulo](../exercises/10-redteam-modbus-opcua.md), [Anatomy paso a paso](anatomy-inspector-activo.md) y [mapa de implementación](mapa-implementacion-modulo-10.md). No evaluar a alumnos por velocidad ni convertir polling/plazos legales en duración de resolución.
