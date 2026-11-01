# Uso de Copilot para apoyar la documentación técnica

El Tema 16 plantea el uso de una herramienta generativa como Microsoft Copilot para acelerar la preparación de una plantilla de documentación técnica basada en ISO/IEC 23053. En este proyecto, Copilot puede usarse como apoyo de redacción, no como fuente de verdad ni como sustituto de la revisión técnica.

## Prompt sugerido

> Actúa como asistente de documentación técnica. A partir exclusivamente de los archivos del repositorio, redacta/actualiza una sección de documentación de despliegue del sistema de clasificación de tickets. Organiza la información tomando ISO/IEC 23053:2022 como referencia conceptual: propósito, alcance, datos de entrada y salida, componentes, modelo ML y encoder, interfaz API, entorno reproducible, proceso de construcción Docker, pruebas locales, estrategia de nube, monitoreo, riesgos, límites y responsables. No inventes resultados de pruebas, URLs, cuentas cloud, métricas ni aprobaciones. Marca como “pendiente” cualquier actividad que no tenga evidencia. Explica que BANKING77 traducido es un benchmark y que el umbral de confianza no está calibrado ni aprobado para producción. Devuelve una lista de afirmaciones que requieren validación humana.

## Evidencia recomendada

- Guardar el prompt utilizado y la fecha.
- Conservar el borrador generado.
- Revisar las versiones, comandos y nombres de archivos contra el repositorio real.
- Registrar correcciones aplicadas por el responsable del proyecto.
- No compartir con Copilot datos reales de clientes, secretos, tokens ni información bancaria confidencial.

No se afirma que Copilot haya sido ejecutado desde este entorno; este archivo contiene una guía reproducible para documentar su uso si la actividad lo solicita.
