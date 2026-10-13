# Mapeo de conductas y controles

| Taller | Conducta representada | MITRE ICS | Referencia IEC 62443 | Evidencia |
|---|---|---|---|---|
| 01 | Inventario defensivo | No asignación adversaria | FR6/FR7 | osquery + FC03 |
| 02–03 | Proceso benigno y permiso inseguro | No demuestra APT ni explotación | FR2/FR3 | file, processes, endpoint |
| 04 | Cambio de consigna y deshielo | T0836 Modify Parameter; T0831 Manipulation of Control | FR3/FR7 | FC06, readback, PCAP, EVE |
| 05 | Marcadores entre agentes / Write acotado | Lateralidad representada, no exploit; T0836 si Write | FR1/FR2/FR5 | guard + rechazo gateway |
| 06 | OPC UA Write consigna | T0836 Modify Parameter | FR2/FR3/FR4 | respuesta Write/Read y captura |
| 07 | Archivo firmware ficticio | No atribución técnica de compromiso real | FR3; 62443-4-1 como ciclo de desarrollo | hash y eventos |
| 08–09 | Impacto de proceso y recuperación | T0836/T0831 solo en maqueta | FR6/FR7 | expediente y cuarentena |

FR1 identificación/autenticación; FR2 control de uso; FR3 integridad; FR4 confidencialidad; FR5 flujo de datos restringido; FR6 respuesta oportuna a eventos; FR7 disponibilidad de recursos. Las referencias son pedagógicas, no certificación ni cumplimiento de cada SR. El guard basado en hostname no satisface autenticación robusta por sí solo.

IEC 62443-3-2 informa evaluación de riesgo y zonas/conductos; 3-3 requisitos del sistema; 2-1 programa de seguridad del asset owner; 2-3 gestión de parches como referencia; 4-1 ciclo seguro del proveedor y 4-2 componentes. No se reproduce el texto normativo de pago. SL-T se define por riesgo de cada zona; SL-A requiere evaluación sustentada. Un entorno Docker aislado y siete barreras no establecen un SL numérico.

NIST SP 800-82 Rev.3 prioriza características OT de seguridad física, rendimiento y confiabilidad. Planificar reversión y validación del proceso antes de aplicar controles en producción. MITRE no prueba autoría ni causalidad de los dos incidentes periodísticos.

## Módulo 10

FC06/FC16 y OPC UA Write de consigna representan T0836 Modify Parameter y, en el modelo térmico, T0831 Manipulation of Control. Sesgo del sensor representa información falsa al controlador (referencia T0856 Spoof Reporting), no inyección sobre un lazo físico. Ráfaga finita representa abuso acotado de órdenes; no se declara DoS probado. Las barreras implementadas se describen en [guía y solución](../exercises/10-redteam-modbus-opcua.md), con FR1/FR2/FR3/FR4/FR5/FR7 según control. No se infiere SL-A.
