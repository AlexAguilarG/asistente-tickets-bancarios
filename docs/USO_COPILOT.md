# Uso de herramientas generativas para apoyar la documentación técnica

## 1. Propósito

El Tema 16 propone el uso de una herramienta generativa, como Microsoft Copilot, para acelerar la preparación de documentación técnica tomando ISO/IEC 23053:2022 como referencia conceptual.

En este proyecto se utilizó **ChatGPT** como asistente generativo para apoyar la planificación, redacción, revisión y explicación de documentación técnica, así como para orientar la corrección de archivos de configuración y procedimientos de validación. También se preparó esta guía para un posible uso complementario de GitHub Copilot.

**Transparencia:** no se afirma que GitHub Copilot o Microsoft Copilot se hayan ejecutado en este proyecto. El prompt de la sección 3 es una plantilla reproducible para una utilización posterior. Las sugerencias de IA no se consideran evidencia de ejecución ni sustituyen la revisión del responsable.

## 2. Actividades de apoyo generativo documentadas

- Organización de los apartados del manual de despliegue local y del manual propuesto para nube.
- Redacción y revisión de instrucciones reproducibles para Docker, FastAPI, Swagger y GitHub Actions.
- Explicación de errores observados durante la construcción de la imagen, ejecución de la API y pruebas de integración continua.
- Preparación de textos de validación que separan resultados observados, limitaciones y actividades no ejecutadas.
- Identificación de riesgos de interpretación: benchmark traducido, confianza no calibrada, clasificación fuera del dominio y ausencia de asignación automática de prioridad.

El responsable del proyecto verificó los comandos y resultados mediante la ejecución local de Docker, solicitudes a la API, registros del contenedor y ejecuciones de GitHub Actions. Las afirmaciones sobre la nube se dejaron como propuesta porque no se desplegó el servicio.

## 3. Prompt sugerido para GitHub Copilot o Microsoft Copilot

> Actúa como asistente de documentación técnica. Analiza exclusivamente los archivos del repositorio y redacta o actualiza la sección solicitada para el sistema de clasificación de tickets bancarios. Organiza la información tomando ISO/IEC 23053:2022 como referencia conceptual: propósito, alcance, datos de entrada y salida, componentes, encoder y modelo ML, interfaz API, entorno reproducible, proceso de construcción Docker, pruebas locales, estrategia de nube, monitoreo, seguridad, riesgos, límites y responsables. No inventes resultados de pruebas, URLs, cuentas cloud, métricas, costos exactos ni aprobaciones. Distingue entre actividades ejecutadas y propuestas. Marca como pendiente toda actividad sin evidencia. Explica que BANKING77 traducido es un benchmark y que las puntuaciones de confianza no están calibradas ni validadas con tickets reales de un banco mexicano. No afirmes que el prototipo asigna prioridad automáticamente. Devuelve una lista de afirmaciones que requieren validación humana y señala los archivos y secciones de origen usados.

## 4. Procedimiento sugerido para registrar una sesión de Copilot

Si el equipo decide utilizar GitHub Copilot posteriormente:

1. Abrir el repositorio y seleccionar únicamente los archivos necesarios para la tarea.
2. Evitar adjuntar información real de clientes, secretos, tokens, contraseñas o datos bancarios confidenciales.
3. Ejecutar el prompt anterior especificando el archivo y apartado que se desea documentar.
4. Comparar las propuestas contra el código, las pruebas y los manuales reales.
5. Corregir o descartar instrucciones incompatibles con la aplicación.
6. Registrar la fecha, herramienta/versión disponible, prompt, archivos consultados, resultado útil y correcciones aplicadas.
7. Someter el documento final a revisión del responsable antes de integrarlo al repositorio.

## 5. Registro de uso y limitaciones

| Herramienta | Uso documentado en este proyecto | Evidencia / límite |
|---|---|---|
| ChatGPT | Apoyo de planificación, redacción, revisión y explicación técnica durante el desarrollo y la documentación. | Interacción conversacional; el contenido se contrastó con archivos y pruebas del proyecto. |
| GitHub Copilot | Uso no realizado; se proporciona un prompt y procedimiento sugerido. | No hay sesión, salida ni captura de Copilot que presentar como evidencia. |
| GitHub Actions | Ejecución automatizada del workflow `tests.yml`. | La última ejecución registrada del commit `1d9ecf3` terminó correctamente (1/1 trabajo). |
| Docker | Construcción y ejecución local de la aplicación contenerizada. | Build 16/16 y contenedor en estado `healthy`, documentados en las evidencias de la Fase II. |
| Swagger UI / FastAPI | Inspección y pruebas directas de los endpoints HTTP. | Respuestas observadas 200 y 422 según los casos descritos en `VALIDACION_Y_PRUEBAS.md`. |

## 6. Criterios de revisión humana

La herramienta generativa puede proponer redacción, ejemplos, comandos y estructuras, pero el responsable debe verificar:

- Que los nombres de archivos, variables y endpoints existan en el repositorio.
- Que los comandos correspondan a Windows PowerShell cuando se indiquen para Windows.
- Que el manual de nube esté claramente marcado como no ejecutado.
- Que no se presenten datos de benchmark como evidencia de un banco mexicano.
- Que las puntuaciones del clasificador no se describan como probabilidades calibradas.
- Que no se afirme asignación automática de prioridad.
- Que las conclusiones estén respaldadas por capturas, registros o ejecuciones observables.

## 7. Referencia

ISO/IEC 23053:2022 se utiliza como referencia conceptual para ordenar la documentación del sistema de IA. Este uso no representa certificación ni conformidad formal con la norma.
