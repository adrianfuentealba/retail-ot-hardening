# Escenarios controlados de laboratorio

- **Deshielo:** cliente fijo envía FC06=50 a gateway→PLC ficticio. Contramedida: guard consigna <=6, gateway deny FC06, guard de rol de mantenimiento.
- **Actividad endpoint benigna:** descarga texto local desde panel, crea marcador y proceso sleep 45 con nombre retail-benign-malware. Contramedida: guard del agente y permisos de controller.conf. No es antivirus, malware ni exploit.
- **Lateralidad:** dos agentes fijos reciben marcadores por training. Contramedida: guard network/access en objetivos. No prueba movimiento lateral productivo ni routing de zonas Purdue.
- **OPC UA:** Write consigna en servidor real asyncua. Contramedida: variable read-only, cliente posterior con SignAndEncrypt. Endpoint None permanece para contraste.
- **Suministro:** archivo de texto ficticio alterado; hash embebido lo rechaza. No firmware de fabricante, firma digital de cadena de suministro ni exploit.

La emulación no usa URL externa, IP arbitraria ni consola remota del host. Malware avanzada se estudia como hipótesis y evidencias a buscar, no payload operativo. La página Anatomy explica hardware modular y controles; no analiza artefactos binarios automáticamente.
