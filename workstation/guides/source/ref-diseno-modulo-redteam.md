# Módulo 10 — Red/Purple Team de protocolos e inspector activo

El módulo amplía el mismo laboratorio Docker y supermercado SCL-01. No agrega objetivos externos, exploits, malware ni inundaciones de red. Se mantiene la escena visible y no se asignan duraciones sugeridas ni puntuación por velocidad.

## Pruebas y contramedidas

Se implementaron escrituras reales Modbus FC06 y FC16 con destinos internos fijos; modificación de consigna, sesgo del sensor y ráfaga pequeña de escrituras. La defensa es validación centralizada de valores, protección de registros de entrada, allowlist de funciones/direcciones en pasarela y límite acotado de escrituras. Una ráfaga finita enseña detección de abuso y control de tasa; no demuestra un DoS real.

En OPC UA se comparan Write anónimo/None, Write cifrado de usuario sin permiso y validación semántica del valor. Se separan autorización por nodo, autenticación de usuarios de aula y selección de endpoint SignAndEncrypt sin None. El módulo antiguo de solo lectura permanece disponible para contraste. Los certificados/credenciales son de aula: no representan una PKI productiva.

El gemelo distingue temperatura física simulada, lectura de sensor, consigna, compresor, deshielo, sensor válido y stock. La manipulación del sensor no es una animación independiente: modifica el mismo estado que consume la lógica del PLC.

## Anatomy

CPU muestra código Python real de `plc/control_logic.py` y recorrido del ciclo de control. I/O explica entrada PT100 con módulo RTD compatible o transmisor 4–20 mA con módulo AI apropiado, entrada digital de puerta y salidas de relé hacia contactor/alarma; nunca conexión directa de potencia del compresor al PLC. El usuario puede conectar/desconectar la señal de entrenamiento y observar validación y respaldo. La protección ante pérdida de señal es una decisión didáctica específica del modelo, no una receta universal de seguridad funcional.

El despiece SVG tiene partes seleccionables con ratón y teclado; la selección abre el contenido correspondiente. Se usan componentes Mantine en los nuevos paneles de prácticas e inspector, manteniendo el canvas Three.js y las guías existentes.

## Referencias de implementación

- Modbus Organization, especificaciones y Modbus Security: https://www.modbus.org/modbus-specifications. FC16 es 0x10; Modbus Security usa TLS/certificados y puerto 802. El aula continúa en Modbus TCP 502 y no promete TLS Modbus.
- Formato de FC06/FC16 y direccionamiento base cero: https://www.modbustools.com/modbus.html.
- OPC Foundation, objetivos de seguridad: https://reference.opcfoundation.org/Core/Part2/v105/docs/4.2. Autenticación, autorización y confidencialidad son controles distintos.
- Mantine Tabs accesibles y controladas: https://mantine.dev/core/tabs/.

MITRE ATT&CK for ICS e IEC 62443 se mapean en la guía como referencias de diseño, no certificación. Los plazos de Ley 21.663 se mantienen en su guía de respuesta; no son tiempos de resolución de alumnos.
