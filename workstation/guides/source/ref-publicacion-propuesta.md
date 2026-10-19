# Manifiesto de publicación aprobado

**Publicación pública autorizada por el titular el 13-10-2026.** La versión local fue ejecutada y probada. Este manifiesto registra el contenido aprobado; el estado remoto se verifica al publicar.

## Destino y configuración

- Cuenta propietaria: `vtomasv`.
- Nombre: `retail-ot-hardening`.
- URL prevista: https://github.com/vtomasv/retail-ot-hardening
- Visibilidad: **público**. Cualquier persona podrá ver y copiar los archivos publicados.
- Descripción: `Laboratorio educativo OT de hardening: supermercado 3D, cinco Linux noVNC, osquery, Elastic Stack y talleres guiados.`
- Rama inicial propuesta: `main`.
- Commit inicial propuesto: `feat: publish Retail OT hardening educational lab` con atribución de colaboración.
- No habilitar GitHub Pages ni publicar puertos/servicios del laboratorio.

## Contenido que se publicaría

- Código completo original del aula: Docker Compose/Dockerfiles, PLC y pasarela, agentes, collector, osquery, sensor/Suricata, portal Three.js y Anatomy.
- Ocho talleres y desafío integrador con solución, criterios y comandos copiar/pegar.
- Documentación de arquitectura, operación, observabilidad, marco chileno y límites de emulación.
- Capturas reales de portal, consola, topología, paquetes, cinco estaciones, Anatomy, Kibana general/HMI y escritorio noVNC.
- Dashboards Kibana exportables en NDJSON, pruebas y resultados JSON de validación local.
- PCAP de tráfico exclusivamente sintético del laboratorio; paquetes oficiales osquery ARM64 y amd64 con hashes.
- Avisos y licencias upstream de las bibliotecas conservados.

## Exclusiones

No subir `.env` privado, certificados/clave privada generados en volúmenes Docker, credenciales, logs del anfitrión, configuración de conectores, historiales de navegación, `.work/`, archivos temporales, bytecode ni socket Docker. La revisión textual del paquete no encontró claves privadas o tokens configurados; no es un sustituto de auditoría externa.

Las capturas muestran servicios de aula local, IP privadas sintéticas, hostnames de entrenamiento y eventos de prueba, no tiendas reales ni datos de terceros. Las capturas no están reconstruidas mediante IA.

## Ritmo de aprendizaje

Se retiraron duraciones sugeridas de talleres, secciones, solución docente, tutorial y UI. La evaluación se basa en evidencia y criterios, sin puntuar velocidad. Los intervalos de procesos/telemetría, ventanas de consulta y plazos legales permanecen por exactitud técnica; no son tiempos de resolución del alumno.

## Licencia

No se añadirá una licencia nueva al código original sin una elección explícita del titular. Se conservan las licencias de terceros. Repositorio público no implica automáticamente licencia de redistribución del código original.

## Autorización registrada

El titular confirmó: «Sí, publicar público tal como está». Se autorizaron la creación pública y el primer push a `vtomasv/retail-ot-hardening` con el contenido anterior.
