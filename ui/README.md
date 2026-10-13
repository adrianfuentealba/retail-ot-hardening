# Paneles Mantine del laboratorio

Los paneles Red/Purple Team y Anatomy usan React 19.1.1 y Mantine 8.3.1; el canvas permanece en Three.js. Bundle local ya incluido: Docker no instala Node ni requiere CDN para abrir el laboratorio.

Para modificar y reconstruir, desde `ui/`:

```sh
npm ci
npm run build
```

La compilación produce `app/static/instructor.bundle.js` y `.css`. No ejecutar builds desde el navegador del alumno. Los eventos se obtienen del backend del mismo proceso; los componentes no inventan telemetría.
