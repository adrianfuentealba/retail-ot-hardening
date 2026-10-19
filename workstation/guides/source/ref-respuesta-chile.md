# Ejercicio de respuesta y notificación: Chile

Borrador de aula, **no se envía a ANCI**. No todo supermercado es automáticamente prestador de servicio esencial u OIV. Verificar actividades concretas, resoluciones y sujeto obligado antes de aplicar plazos. La cantidad de OIV es dinámica: no usar “~250” como un dato vigente certificado.

Según FAQ oficial ANCI, para sujetos obligados e incidentes potencialmente significativos: alerta temprana tan pronto sea posible y máximo 3 horas desde conocimiento; actualización máximo 72 horas; informe final máximo 15 días corridos desde envío de alerta. Revisar reglamento y caso OIV afectación de servicio esencial para excepción de 24 horas; fuentes secundarias lo describen, no confundirlo con regla general. Confirmar plan de acción y cómputos en reglamento vigente antes de uso real. No sustituir validación legal con este taller.

El marco contempla multas que pueden llegar a 40.000 UTM para infracciones gravísimas de OIV, no multa automática por cualquier incidente. Texto legal y obligación dependen de conducta y clasificación. Ley 21.459: mantener autorización del aula y no operar infraestructura ajena. Ley 21.719: considerar minimización de datos y fecha de vigencia aplicable; no se presume vigente todo su régimen al 12-10-2026.

## Plantilla copiar y completar

```text
BORRADOR EDUCATIVO — NO ENVIAR
Institución ficticia: Retail SCL-01
Sujeto obligado / fundamento: [por verificar; no asumir OIV]
Responsable y delegado: [roles ficticios]
Hora de conocimiento (UTC y local):
Hora estimada de inicio / incertidumbre:
Activos: PLC-R01, ws-hmi, gateway
Hechos confirmados por evidencia:
- [hora, fuente, paquete o evento, acción]
Hipótesis no confirmadas:
Impacto de proceso: [temperatura y cuarentena didácticas]
Impacto de servicio y salud: [simulado; no extrapolar]
Medidas aplicadas y resultado probado:
Indicadores de entrenamiento: [hash marcador, hostname interno]
Próxima actualización / plazo aplicable:
Custodia de PCAP y bitácora:
```

## RACI de aula

| Decisión | Operación tienda | Ingeniería OT | SOC | CISO/delegado | Jurídico |
|---|---|---|---|---|---|
| Validar impacto físico/stock | A/R | C | I | I | I |
| Aplicar control del PLC | A | R | C | I | I |
| Preservar PCAP/eventos | C | C | R | A | I |
| Recuperar proceso | A | R | C | I | I |
| Determinar obligación de reporte | C | C | C | A | R |
| Aprobar y enviar reporte real | C | C | C | A/R | C |

No enviar una notificación real como parte del laboratorio. No concluir que recuperar frío permite vender stock comprometido. Evaluar cuarentena con responsable sanitario real en producción.

Fuente oficial: https://anci.gob.cl/preguntas-frecuentes/preguntas-frecuentes-portal-anci/
Texto ley: https://www.bcn.cl/leychile/navegar?idNorma=1202434
Reglamento y excepción de plazos (referencia secundaria a contrastar): https://www.az.cl/en/framework-cybersecurity-law-key-points-of-the-incident-reporting-regulation/
