# Anatomy activo: CPU, señales y contramedidas

## Cómo usarlo

En el portal, seleccionar un activo y pulsar **Explorar anatomía**. El despiece de Anatomy permite pulsar la CPU, I/O, alimentación, interfaces o tapa/memoria; también funciona con Tab y Enter/Espacio. Separar componentes para acceder a piezas ocultas. El selector de componente es una alternativa accesible.

En escritorio ancho el inspector queda en el lado derecho; el supermercado y su telemetría siguen visibles a la izquierda. En pantallas pequeñas el inspector se apila y tiene scroll propio. Los cambios de estado son compartidos por toda la cohorte: no ejecutar dos prácticas independientes sobre el mismo PLC.

**Entender** explica la pieza. **Código CPU** muestra el archivo real `plc/control_logic.py`, servido por `/api/anatomy`; no es una captura de código ni pseudocódigo inventado. **Conectar / Probar** cambia señales o aplica una política al backend que alimenta el mismo canvas.

## CPU / Lógica de control

La entrada remota pasa por `validate_change()` y `apply_changes()` antes de mutar parámetros. FC06, FC16 y Write OPC UA comparten esa validación. FC16 valida todas las direcciones primero: una operación rechazada no deja medio cambio aplicado.

`control_cycle()` ejecuta el recorrido del modelo:

1. AI0: temperatura física del simulador más sesgo, o sin valor al desconectar.
2. Validación de rango y coherencia contra referencia ideal, únicamente si se endureció la entrada.
3. Histéresis del compresor y decisión de deshielo.
4. DO0/DO1/DO2 y estado de alarma.
5. Evolución térmica, exposición acelerada y cuarentena irreversible hasta reset de aula.

La consigna es un parámetro de ingeniería, no una medición. Cifrar el transporte no hace segura una consigna 50 °C. El interlock impide el cambio incluso cuando el usuario de ingeniería tiene Write legítimo.

## Entradas / salidas

| Canal conceptual | Dispositivo a conectar | Interpretación didáctica | Hardening |
|---|---|---|---|
| AI0 | PT100 con módulo RTD compatible, o transmisor 4–20 mA con módulo AI apropiado | Temperatura de cámara | Dominio de calibración restringido; lectura válida y diagnóstico |
| DI0 | Contacto de puerta | Cerrado normal; abrir agrega carga y alarma | Validar estado e integrar procedimiento operativo |
| DO0 | Relé de mando hacia contactor de compresor | Compresor ON/OFF | Interlocks, feedback y protección de potencia en instalación real |
| DO1 | Relé/contactor de deshielo | Deshielo ficticio cuando consigna >6 | Límites de parámetros; no habilitar deshielo por cualquier orden remota |
| DO2 | Señal de alarma a HMI/sirena | Alarma por respaldo o puerta | Registrar, mantener canal de alarma y verificar atención operacional |

PT100 y 4–20 mA **no se conectan indistintamente** al mismo módulo sin configuración/hardware correctos. La relación ilustrativa para rango −30…50 °C es `I=4+16*(T+30)/80 mA`. No existe corriente física en Docker. No conectar potencia del compresor al PLC; el dibujo no define tensión, fabricante, conexión eléctrica ni reemplaza planos verificados.

### Experimento AI0

Desde I/O → Conectar / Probar, desactivar el sensor. Sin protección, el modelo no conoce una señal y detiene compresor. Aplicar **Proteger entrada**, que restaura el sensor y activa guard. Desconectar nuevamente: aparece respaldo del modelo y alarma. Reconectar: retorna señal primaria.

El banco de señales usa `/api/anatomy/wiring`, una **API pedagógica fuera de banda**. No demuestra un atacante tocando cableado físico. `harden inputs` bloquea calibración remota por protocolos, no el banco del instructor.

El respaldo conoce la temperatura ideal del propio simulador. En planta real debe sustituirse por redundancia física y modos degradados analizados con operaciones. No afirmar SIS certificado, SIL, fail-safe universal ni protección de todas las fallas.

## Interfaces y memoria

Modbus TCP 502, ocho registros de mapa fijo; UA TCP 4840 con nodestrings del aula. En módulo 10 se comparan denylist incompleta, allowlist, presupuesto Write y validación del PLC. OPC UA distingue None/SignAndEncrypt, identidad y permiso por nodo.

La pestaña de memoria explica revisión de fuente/configuración y firmware ficticio con manifiesto; no acepta cargas de código ni compila lógica arbitraria desde el navegador. Las identidades `engineer` y `observer` y los certificados compartidos están documentados para aprendizaje local, no son secretos reutilizables de producción.

## Evidencia esperada

El inspector debe mostrar estado de fuente y proceso; el gemelo debe variar después de una entrada/orden real del modelo; logs PLC y respuestas Modbus/UA deben acreditar aceptación/denegación. El click solo cambia la vista; nunca es prueba de control aplicado. La UI no sustituye PCAP, osquery ni logs de servidor.

Ver [módulo 10 y solución](../exercises/10-redteam-modbus-opcua.md) y [arquitectura](arquitectura.md). Ley 21.459: mantener autorización y límites del aula. Ley 21.663: documentar impacto y evidencia antes de borradores de notificación; no hay envío real. Referencias IEC 62443 FR2/FR3/FR5/FR7 son objetivos pedagógicos, no certificación.
