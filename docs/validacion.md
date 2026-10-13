# Validación del perfil ampliado Retail OT

**La cadena cinco estaciones → collector → Logstash → Elasticsearch → Kibana está ejecutándose y pasó las pruebas.** Última validación UTC: 2026-10-13T02:53:06Z.

## Resultados comprobados

| Suite | Resultado | Evidencia |
|---|---|---|
| Escenarios/hardening e integración | 39/39 PASS | `verification-results.json` |
| Observabilidad fresca y accesos | 58/58 PASS | `observability-verification-results.json` |
| Contrato estático de aislamiento | 4/4 PASS | `tests/test_contract.py` |
| Núcleo OT (validación anterior) | 13/13 PASS | `core-verification-results.json` |

Pruebas de escenarios: cinco versiones osquery reales, SQL local, noVNC HTML, permisos `0640 root`, proceso benigno, bloqueo de ejecución, dos marcadores laterales permitidos/bloqueados, FC06 aceptado y rechazo PLC/pasarela, OPC UA Write None y Read SignAndEncrypt con Write denegado, archivo firmware ficticio, payload Tshark/PCAP, eventos de cinco hosts, Suricata indexada y dashboard importado.

Pruebas reforzadas: **cinco WebSocket→VNC reales con saludo RFB**, proceso `sleep` real observado por osqueryd y registro del agente en eventos NUEVOS, bloqueo NUEVO indexado por host, escritura de configuración rechazada para usuario `student`, pipeline Logstash con salida positiva, general de seis paneles, cinco búsquedas guardadas y cinco dashboards con filtro de host.

Python compila y JavaScript pasa `node --check`. Elasticsearch se observó **green**. Bootstrap importó 18 objetos sin errores. Se comprobó visualmente XFCE/noVNC con usuario `student`, host HMI y versión osquery; dashboard general con gráficos de activos/fuentes y documentos; dashboard HMI filtrado. No se afirma auditoría visual de todos los tamaños ni validación funcional amd64.

## Latencia medida de esta ejecución

Tiempo acción→consulta ES que observa **ambos** documentos, no SLA ni MTTD. El refresco visual de Kibana añade hasta su siguiente ciclo (configurado en 5 s). Las mediciones incluyen polling y comandos de verificación.

| Endpoint | Segundos | ID agente | ID osquery |
|---|---|---|---|
| ws-corporate | 8.06 | `R_4sM6EBtGY_hDSKeE0a` | `S_4sM6EBtGY_hDSKgE0Y` |
| ws-vendor | 3.58 | `Yf4sM6EBtGY_hDSKt032` | `Y_4sM6EBtGY_hDSKt033` |
| ws-engineering | 8.12 | `ef4sM6EBtGY_hDSK503X` | `gf4sM6EBtGY_hDSK903Z` |
| ws-hmi | 3.68 | `lf4tM6EBtGY_hDSKL02L` | `l_4tM6EBtGY_hDSKL02T` |
| ws-soc | 8.1 | `tv4tM6EBtGY_hDSKX02L` | `uf4tM6EBtGY_hDSKZ01y` |

Rango 3.58–8.12 s; media 6.31 s. Los IDs documentan las filas de esta ejecución local, no existen por adelantado en una nueva instalación. No confundir un registro osqueryi manual con los logs osqueryd programados.

## Plataforma y versiones

- Docker Desktop sobre macOS, contenedores **Linux ARM64**, 16 vCPU y aproximadamente 62.4 GiB disponibles al motor durante inspección; sin alterar recursos ni configuración del anfitrión.
- XFCE/noVNC 1.3.0, osquery 5.23.1; paquetes oficiales ARM64/amd64 incluidos con SHA256.
- Elasticsearch/Logstash/Kibana 8.17.3; Suricata 7.0.3; asyncua 1.1.5; bibliotecas visuales locales.
- Se resolvieron los timeouts de registry al reintentar; no se modificó DNS, VPN, Docker Desktop ni se montó socket Docker dentro de contenedores.

## Correcciones realizadas al cerrar la integración

1. Construcción efectiva del endpoint con osquery local y arranque XFCE/noVNC.
2. Parámetro logger osquery en CLI; propietario de lanzadores de escritorio corregido; metadatos noVNC para evitar 404 del paquete.
3. Collector espera bootstrap y Logstash healthy; snapshots osquery preservados completos; codecs JSON lines sin advertencias ECS por conexión.
4. Dashboard general con dos gráficos + cuatro fuentes, y cinco dashboards por host, todos importables desde NDJSON.
5. Prueba de paquetes corregida: visor es una ventana móvil de 60 payloads; ahora genera y observa FC06 reciente. El primer intento fue 38/39 por ventana antigua; tras corrección, 39/39.
6. Prueba reforzada evita auto-coincidencia de osqueryi: exige columna `name=sleep` y timestamp nuevo. Verifica bloqueo indexado y permiso Linux con alumno no privilegiado.
7. Tutorial completo, enlaces en portal y pruebas reutilizables.

## Reproducir

```sh
docker compose up -d
docker compose ps -a
python3 scripts/verify-lab.py
python3 scripts/verify-observability.py
```

Ejecutar pruebas **una tras otra**, nunca simultáneas ni durante un taller activo: ambas restablecen proceso y políticas sin eliminar evidencia. `bootstrap` finalizado 0 es normal. Revisar `tutorial-observabilidad.md` para los pasos como alumno y `operacion-y-diagnostico.md` ante errores.

NoVNC `6081–6085`, portal `8090`, Kibana `5601` solo loopback. PLC/gateway/ES/Logstash no publicados al anfitrión. El perfil queda activo localmente; `docker compose down` detiene conservando volúmenes.

## Límites que permanecen

- Cinco endpoints son cinco roles, no cinco procesos térmicos independientes de supermercados.
- Malware/lateralidad/firmware son emulaciones benignas por APIs internas fijas. El guard de ejecución no es antivirus ni allowlisting global; pasarela de aplicación no es firewall kernel transparente. No hay MFA real ni explotación APT.
- Modbus es real pero PLC/térmica/stock son modelos de aula; no extrapolar a salud ni seguridad industrial.
- OPC UA usa certificado/clave compartidos de laboratorio; None permanece interno; variable read-only no representa PKI independiente ni autenticación robusta por usuario.
- osquery hace consultas programadas, no auditd/eBPF ni detección infalible. TCP de collector tiene límites de duplicación/pérdida en fallos; no promete entrega exactly-once ni custodia certificada.
- ELK/noVNC sin autenticación es únicamente aceptable como aula local aislada. No se certifica IEC 62443 ni SL-A. No se publicó repositorio ni servicio a una audiencia externa.
- ARM64 probado; amd64 tiene dependencias preparadas, pero aún no se ejecutó esa matriz de plataforma. No se han ejecutado talleres humanos completos ni prueba de carga de una cohorte.
