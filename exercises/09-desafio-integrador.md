# 09 · Desafío integrador: turno de madrugada

Aula compartida, exclusivamente educativa y aislada.

## Encargo

SCL-01 presenta aumento térmico y actividad benigna endpoint simultánea. No existe evidencia suficiente para atribuir ambos a una campaña única. Debe proteger la operación, documentar siete barreras y preparar un expediente. La escena representa una tienda; las cinco estaciones no son cinco tiendas. Multitienda se trabaja como ejercicio de mesa, no como cinco procesos térmicos independientes implementados.

## Preparación

En portal Restablecer aula. Abrir ws-engineering y ws-soc, coordinar roles. En ingeniería:

```sh
labctl baseline
labctl simulate defrost
labctl simulate malware
labctl evidence
```

Guardar PCAP y expediente inicial ANTES de endurecer. Esperar 20 segundos observando temperatura y stock. Completar `docs/respuesta-chile.md` con hechos e hipótesis separados.

## Solución copiar y pegar

Ejecutar un comando por vez, registrar respuesta y esperar al menos dos segundos:

```sh
labctl harden os
labctl harden application
labctl harden plc
labctl harden network
labctl harden access
labctl harden opcua
labctl harden supply-chain
labctl recover
```

**Por qué:** `os` modifica permisos reales del archivo de ingeniería; `application` restringe su lanzador; `plc` limita consigna local; `network` bloquea FC06 de gateway y marcadores en agentes; `access` limita rol de mantenimiento; `opcua` protege la variable y usa canal seguro en cliente pedagógico; `supply-chain` valida integridad del archivo ficticio. Hardening de endpoint es por estación: repetir `harden os`, `harden application` y `harden supply-chain` en HMI si también debe protegerlo.

## Prueba de regresión

```sh
labctl simulate defrost
labctl simulate malware
labctl simulate lateral
labctl simulate opcua
labctl simulate firmware
labctl status
labctl evidence
```

Rechazos esperados: FC06 de pasarela, emulación endpoint, marcadores en dos targets, OPC UA Write, firmware alterado. FC03 debe continuar. `simulate opcua` usa Read seguro, pero el Write es read-only. Revisar dashboard central y cada endpoint; las fuentes no se confunden.

En HMI validar archivo:

```sh
osqueryi --json "SELECT path,mode,uid FROM file WHERE path='/home/student/lab/controller.conf';"
osqueryi --json "SELECT pid,name,cmdline FROM processes WHERE cmdline LIKE '%retail-benign-malware%';"
```

## Rúbrica (100 puntos)

- 20: inventario, topología y excepción de administración correctamente declaradas.
- 20: dos evidencias independientes para la escritura y su bloqueo.
- 20: permisos/allowlist por endpoint y proceso benigno detenido.
- 15: OPC UA seguro y Write rechazado, sin afirmar retiro de None.
- 10: integridad del archivo ficticio y límites de firma PKI.
- 10: recuperación y cuarentena conservada.
- 5: borrador Ley 21.663, aplicabilidad y RACI. No se envía a autoridades.

No hay certificación IEC/SL-A. Reporte con ausencia de evidencia reconocida puede ser correcto; inventar una alerta es un error de evaluación.
