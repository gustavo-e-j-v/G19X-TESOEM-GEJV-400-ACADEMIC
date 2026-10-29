# PRD y MVP — Motor de Optimización Logística de Almacenes

| Dato | Valor |
|---|---|
| Producto | Motor de Optimización Logística de Almacenes |
| Versión del documento | 1.0 |
| Autor | Gustavo Jiménez Valencia |
| Asesor externo | Edgar Loeffelmann |
| Organización | PluriOne, S.A. de C.V. |
| Estado del producto | Versión 0.7 estable + snapshots 0.8 a 0.12 (paquetes, rediseño de /docs, seguridad y configuración, refactor con pruebas y vista de análisis), en validación |

Este archivo tiene dos partes: la **Parte 1 (PRD)** define qué es el producto completo, y la **Parte 2 (MVP)** define la versión mínima que permite validarlo.

Estados usados en las tablas: **Hecho** (implementado y probado), **En validación** (implementado, falta probarlo en el entorno real), **Pendiente** y **Planeado**.

---

# PARTE 1 — PRD (Documento de requerimientos del producto)

## 1. Resumen del producto

Motor que ayuda a operar un almacén con menos recorridos y mejor uso del espacio. Calcula la ruta óptima de picking, clasifica los racks por rotación (ABC), predice la demanda, recomienda reubicaciones y apoya al personal con mensajes sobre qué paquetes entregar primero. Se usa desde una interfaz web protegida con inicio de sesión de Microsoft.

## 2. Problema y oportunidad

En muchos almacenes el surtido de pedidos (picking) consume buena parte del tiempo operativo. Las rutas se definen a mano y los productos se ubican por costumbre o por espacio disponible, sin considerar qué tanto rotan. Esto genera recorridos innecesarios, productos de alta rotación lejos de la salida, espacio mal aprovechado y entregas que se atrasan por falta de visibilidad de las fechas.

Los datos para mejorar esto ya existen (ubicaciones, ocupación, historial de recolecciones, fechas de entrega), pero rara vez se analizan de forma sistemática. Ese es el espacio que cubre el producto.

## 3. Objetivos

1. Reducir la distancia recorrida en el picking mediante rutas óptimas.
2. Mejorar la ubicación de los productos según su rotación (slotting).
3. Dar visibilidad por rack: cuántos paquetes hay y cuál es la entrega más próxima.
4. Apoyar al encargado y al empleado con mensajes claros y consejos accionables.
5. Proteger el acceso con identidad corporativa.

## 4. Métricas de éxito

Las metas son **propuestas** y deben validarse con la empresa tras medir con datos reales.

| Métrica | Cómo se mide | Meta propuesta |
|---|---|---|
| Reducción de distancia de picking | (distancia en orden de selección − distancia de ruta óptima) / distancia en orden de selección | ≥ 10% |
| Tiempo de cálculo de ruta | Tiempo de respuesta de `POST /api/v1/optimizar-ruta-bd` | ≤ 2 s con hasta 20 racks |
| Exactitud de alertas | % de paquetes vencidos o con entrega en ≤ 48 h que aparecen en los mensajes del asistente | 100% |
| Cobertura de seguridad | % de endpoints que exigen token válido | 100% (hoy: 9 de 9) |
| Adopción | % de paquetes del almacén registrados en el sistema | [Definir con la empresa] |

## 5. Usuarios

| Usuario | Qué necesita | Cómo lo usa |
|---|---|---|
| Empleado (surtidor) | Saber qué sacar primero y por dónde ir | Revisa el asistente, selecciona racks y calcula la ruta |
| Encargado de almacén | Supervisar entregas, cargas por rack y reubicaciones | Revisa alertas, registra paquetes, decide reubicaciones |
| Administrador de TI | Desplegar y dar acceso | Levanta los contenedores y administra usuarios en Entra ID |

### Historias de usuario principales

- Como empleado, quiero ver el almacén por pasillos con el estado de cada rack, para ubicar rápido lo que busco.
- Como empleado, quiero seleccionar racks y obtener la ruta más corta, para recorrer menos.
- Como empleado, quiero que el asistente me diga qué paquete entregar primero, para no atrasar envíos.
- Como encargado, quiero registrar los paquetes de un rack con su fecha de entrega, para tener el inventario al día.
- Como encargado, quiero ver cuántos paquetes tiene cada rack, para detectar cargas desbalanceadas.
- Como encargado, quiero recibir alertas de paquetes vencidos o por vencer, para reasignar al equipo a tiempo.
- Como encargado, quiero sugerencias de reubicación según la rotación, para acercar a la salida lo que más se pide.

## 6. Alcance

**Dentro del alcance:** mapa del almacén por pasillos, ruta óptima de picking (un recorrido), registro de paquetes por rack, mensajes del asistente por rol, clasificación ABC, predicción de demanda, recomendaciones de reubicación, autenticación con Microsoft Entra ID.

**Fuera del alcance (por ahora):** integración con un ERP o WMS, varios surtidores o vehículos a la vez, capacidad de carga por rack, lectura de códigos de barras o RFID, aplicación móvil nativa, despliegue en la nube.

## 7. Requerimientos funcionales

| ID | Requerimiento | Prioridad | Estado |
|---|---|---|---|
| RF-01 | Inicio de sesión con Microsoft Entra ID y token en cada petición | Alta | Hecho |
| RF-02 | Mostrar el almacén por pasillos, con color lleno/vacío por rack | Alta | Hecho |
| RF-03 | Seleccionar racks y calcular la ruta óptima (TSP, distancia Manhattan) con orden de visita numerado | Alta | Hecho |
| RF-04 | Listar las ubicaciones activas con su estado | Alta | Hecho |
| RF-05 | Registrar un paquete en un rack: código único, descripción opcional y fecha de entrega | Alta | En validación |
| RF-06 | Mostrar por rack el número de paquetes y la fecha de entrega más próxima | Alta | En validación |
| RF-07 | Ventana emergente por rack con la lista de paquetes y formulario para agregar | Alta | En validación |
| RF-08 | Eliminar un paquete (por ejemplo, al entregarlo) | Media | En validación |
| RF-09 | Marcar el rack como lleno al agregar un paquete y como vacío al eliminar el último | Media | En validación |
| RF-10 | Asistente con mensajes y consejos distintos para encargado y empleado | Alta | En validación |
| RF-11 | Mostrar la entrega más próxima y alertar paquetes vencidos, de hoy y de las próximas 48 h | Alta | En validación |
| RF-12 | Clasificación ABC de racks por rotación (vista Análisis) | Media | En validación |
| RF-13 | Predicción de demanda semanal por rack, con tendencia y gráfica (vista Análisis) | Media | En validación |
| RF-14 | Recomendaciones de reubicación (clase A lejos de la salida y rack vacío más cerca), en la vista Análisis | Media | En validación |
| RF-15 | Cargar historial de picking real (hoy es simulado) | Alta | Pendiente |
| RF-16 | Roles reales (encargado/empleado) ligados a Entra ID | Media | Pendiente |
| RF-17 | Mensajes redactados con un modelo de lenguaje (Azure OpenAI) | Baja | Planeado |
| RF-18 | Rediseño visual de la API y de la página de paquetes (temas y colores) | Media | API en validación; página de paquetes planeada |
| RF-19 | Dashboards de KPIs con Power BI | Baja | Planeado |
| RF-20 | Pruebas y despliegue automáticos con GitHub Actions | Media | Planeado |
| RF-21 | Ejecución local sin Entra ID (`AUTH_DISABLED`) para desarrollo y revisión | Media | En validación |
| RF-22 | Configuración por variables de entorno (`.env`): contraseñas, identificadores de Entra ID, CORS y dirección de la API | Alta | En validación |

## 8. Requerimientos no funcionales

| ID | Categoría | Requerimiento |
|---|---|---|
| RNF-01 | Seguridad | Todo endpoint exige un token válido de Entra ID (salvo en el modo local explícito); contraseñas e identificadores se leen de variables de entorno y no están en el código |
| RNF-02 | Privacidad | El sistema no almacena contraseñas ni datos personales de los usuarios |
| RNF-03 | Rendimiento | Respuesta de la ruta óptima en ≤ 2 s con hasta 20 racks (meta; falta medirla) |
| RNF-04 | Portabilidad | Backend y base de datos empaquetados con Docker; arranque con `docker compose up` |
| RNF-05 | Usabilidad | Interfaz simple, legible en tema oscuro, con estado de cada rack identificable por color |
| RNF-06 | Mantenibilidad | Separación en capas (interfaz, API, datos) y lógica de agentes en módulos propios |
| RNF-07 | Fiabilidad de fechas | Las fechas se calculan con la hora de México (zona configurable con `APP_TIMEZONE`) |
| RNF-08 | Escalabilidad | Diseño en contenedores listo para crecer; falta validarlo con carga real |
| RNF-09 | Calidad | Pruebas automáticas con pytest (ruta óptima, clasificación ABC, predicción de demanda y API): 17 pruebas |
| RNF-10 | Mantenibilidad | Backend dividido en módulos (`routers/`, `servicios/`, `schemas.py`, `config.py`), sin lógica duplicada |

## 9. Arquitectura y tecnologías

Arquitectura cliente-servidor en tres capas, comunicada por una API REST en JSON.

| Capa | Tecnología |
|---|---|
| Interfaz | React, Vite, MSAL (inicio de sesión con Microsoft) |
| API | Python 3.12, FastAPI, Pydantic, Uvicorn, fastapi-azure-auth |
| Algoritmos | OR-Tools (rutas), pandas y NumPy (ABC), scikit-learn (predicción) |
| Datos | PostgreSQL, SQLAlchemy |
| Despliegue | Docker y Docker Compose |
| Identidad | Microsoft Entra ID (OAuth 2.0, OpenID Connect, JWT) |

## 10. Modelo de datos

| Tabla | Contenido |
|---|---|
| `ubicaciones_racks` | id, nombre del producto, coordenadas x e y (x = posición, y = pasillo), activo, ocupado |
| `historial_picking` | rack, fecha, cantidad recogida |
| `paquetes` | código único, descripción, rack, fecha de entrega |

## 11. API

| Método y ruta | Función |
|---|---|
| `GET /api/v1/ubicaciones` | Racks con ocupación, número de paquetes y fecha de entrega más próxima |
| `POST /api/v1/optimizar-ruta-bd` | Ruta óptima de picking |
| `GET /api/v1/analisis-abc` | Clasificación ABC |
| `GET /api/v1/prediccion-demanda/{rack_id}` | Predicción de demanda semanal |
| `GET /api/v1/recomendaciones-espacio` | Reubicaciones sugeridas |
| `GET /api/v1/racks/{rack_id}/paquetes` | Paquetes de un rack |
| `POST /api/v1/racks/{rack_id}/paquetes` | Registrar un paquete |
| `DELETE /api/v1/paquetes/{paquete_id}` | Eliminar un paquete |
| `GET /api/v1/mensajes-agente?rol=` | Mensajes del asistente para `encargado` o `empleado` |

## 12. Supuestos, riesgos y dependencias

| Tema | Detalle | Mitigación |
|---|---|---|
| Datos simulados | La clasificación ABC y la predicción usan historial inventado | Cargar historial real antes de tomar decisiones con ellas |
| Cuentas personales | El acceso de cuentas personales o invitadas se controla con `AZURE_ALLOW_GUEST_USERS` (desactivado por defecto) | Activarlo solo en el tenant de pruebas; en producción usar cuentas de la organización |
| Credenciales | La contraseña de ejemplo de las primeras versiones quedó en el historial de Git (era un valor de ejemplo que no se usa en ningún sistema) | Resuelto en 0.10: ya no está en el código, se lee de `.env`, que no se sube a Git |
| CORS | Los orígenes permitidos se configuran con `CORS_ORIGINS` | Agregar el dominio real al desplegar |
| Un solo recorrido | La ruta considera un surtidor y regresa al origen | Documentarlo; ampliar en una versión posterior |
| PostgreSQL nativo | Un PostgreSQL instalado en Windows puede chocar con el puerto 5432 de Docker | Mantenerlo detenido o cambiar el puerto |
| Costo de Azure | Azure OpenAI y Azure ML tienen costo por uso | Se dejaron fuera del MVP; hay un punto de integración listo |
| Roles manuales | El rol del asistente se elige con un selector | Ligarlo a roles de Entra ID |
| Modo local sin autenticación | `AUTH_DISABLED=true` deja la API sin validar tokens | Usarlo solo en local; la documentación de la API muestra un aviso visible cuando está activo |

## 13. Hoja de ruta

| Versión | Contenido | Estado |
|---|---|---|
| 0.1 – 0.2 | Backend base y Dockerización | Hecho (snapshots) |
| 0.3 – 0.5 | Datos por pasillos, frontend React, autenticación | Hecho |
| 0.6 | Clasificación ABC y predicción de demanda | Hecho |
| 0.7 | Agente de recomendaciones de espacio | Hecho |
| 0.8 | Paquetes por rack, ventana emergente y asistente por rol | En validación (snapshot) |
| 0.9 | Rediseño de la documentación de la API (/docs) con paleta propia | En validación (snapshot) |
| 0.10 | Seguridad y configuración: contraseñas y identificadores fuera del código, modo local | En validación (snapshot) |
| 0.11 | Refactor del backend en módulos y pruebas con pytest | En validación (snapshot) |
| 0.12 | Vista de análisis en la interfaz (ABC, predicción y recomendaciones) | En validación (snapshot) |
| Después | Rediseño de la página de paquetes e historial de picking real | Planeado |
| Más adelante | Roles con Entra ID, Azure OpenAI, GitHub Actions, Power BI | Planeado |

## 14. Preguntas abiertas

- ¿Quién es el usuario final del producto y cuántos racks y pasillos reales tiene el almacén?
- ¿Existen datos históricos reales de picking que se puedan cargar?
- ¿Qué campos adicionales necesitan los paquetes (destinatario, prioridad, peso)?
- ¿Se necesita integrar el producto con un ERP o WMS existente?
- ¿Cómo se asignarán los roles de encargado y empleado en Entra ID?

---

# PARTE 2 — MVP (Producto mínimo viable)

## 1. Definición

El MVP es la versión más pequeña que ya resuelve el problema central y permite aprender de usuarios reales:

> Una persona inicia sesión, ve el almacén por pasillos, registra los paquetes de cada rack con su fecha de entrega, calcula la ruta óptima para recogerlos y recibe mensajes del asistente sobre qué entregar primero.

## 2. Hipótesis a validar

1. **Ruta:** una ruta óptima reduce de forma notable el recorrido frente a visitar los racks en el orden en que se seleccionan.
2. **Visibilidad:** ver el número de paquetes y la fecha más próxima por rack reduce entregas atrasadas.
3. **Asistente:** los mensajes por rol ayudan a priorizar el trabajo y la gente los consulta.

## 3. Qué incluye el MVP

| ID | Funcionalidad | Estado |
|---|---|---|
| RF-01 | Inicio de sesión con Microsoft Entra ID | Hecho |
| RF-02 | Mapa del almacén por pasillos con estado lleno/vacío | Hecho |
| RF-03 | Selección de racks y ruta óptima | Hecho |
| RF-05 a RF-09 | Registro de paquetes, contador por rack, ventana emergente y eliminación | En validación |
| RF-10 y RF-11 | Asistente por rol y alertas de entrega más próxima | En validación |
| RF-12 a RF-14 | Vista Análisis: clasificación ABC, predicción de demanda y recomendaciones de reubicación | En validación |
| RF-21 y RF-22 | Ejecución local sin Entra ID y configuración por variables de entorno | En validación |
| RNF-04 | Arranque con Docker Compose | Hecho |

## 4. Qué queda fuera del MVP

| Funcionalidad | Motivo |
|---|---|
| Texto con Azure OpenAI (RF-17) | Tiene costo y las plantillas actuales bastan para validar |
| Rediseño visual (RF-18) | Es de segunda prioridad; primero se valida la función |
| Dashboards de Power BI (RF-19) | Aportan después de tener datos reales acumulados |
| GitHub Actions (RF-20) | Mejora el proceso de desarrollo, no la validación con usuarios |
| Roles reales con Entra ID (RF-16) | El selector manual alcanza para probar |

## 5. Criterios de aceptación

| Funcionalidad | Criterio |
|---|---|
| Inicio de sesión | Sin token válido, la API responde con error y la interfaz muestra la pantalla de login |
| Ruta óptima | Dado un origen y varios racks, devuelve la secuencia que parte y regresa al origen, con la distancia total |
| Registrar paquete | Con código, fecha y rack válidos, el paquete aparece en la lista y el contador del rack sube en uno |
| Código duplicado | Un código repetido se rechaza con un mensaje claro |
| Estado del rack | Al agregar el primer paquete el rack pasa a lleno; al eliminar el último, a vacío |
| Alertas | Un paquete vencido, uno de hoy y uno a 2 días aparecen en los mensajes con el tipo correcto |
| Entrega más próxima | La tarjeta del asistente muestra el paquete con la fecha futura más cercana |
| Roles | Empleado y encargado reciben mensajes distintos con los mismos datos |

## 6. Criterios de éxito del MVP

El MVP se considera validado cuando se cumple lo siguiente con datos y usuarios reales:

- En una muestra de pedidos reales, la ruta óptima reduce la distancia frente al orden de selección en al menos la meta propuesta (≥ 10%).
- Las alertas del asistente coinciden al 100% con las fechas registradas.
- Al menos un encargado y un empleado completan el flujo (registrar paquetes, calcular ruta, leer mensajes) sin ayuda.
- Los usuarios reportan que los mensajes les sirven para priorizar.

## 7. Plan de validación

1. Cargar los racks reales del almacén y registrar un lote real de paquetes.
2. Medir la distancia de 10 a 20 pedidos reales con y sin ruta óptima.
3. Pedir a un encargado y a uno o dos empleados que usen el sistema durante una jornada.
4. Recoger sus comentarios con un cuestionario corto: qué les sirvió, qué les estorbó, qué falta.
5. Decidir con esos resultados si se avanza a la interfaz de ABC y predicción, o si primero se ajusta el flujo de paquetes.

## 8. Estado actual y siguientes pasos para cerrar el MVP

- [x] Autenticación con Microsoft Entra ID
- [x] Mapa por pasillos y ruta óptima
- [x] Backend de ABC, predicción y recomendaciones, con pruebas automáticas (pytest)
- [x] Contraseñas e identificadores fuera del código (archivos `.env`)
- [x] Vista Análisis en la interfaz, probada de punta a punta en modo local
- [x] Backend de paquetes y asistente probado de punta a punta con una base temporal
- [ ] Validar paquetes, ventana emergente y asistente en el entorno real
- [ ] Cargar datos reales de racks y paquetes
- [ ] Medir la reducción de distancia con pedidos reales
- [ ] Prueba con usuarios y cuestionario
- [ ] Aplicar el rediseño visual (cuando lleguen los ejemplos de diseño)

## 9. Riesgos del MVP

| Riesgo | Efecto | Acción |
|---|---|---|
| No hay datos reales a tiempo | No se pueden validar las hipótesis | Probar con un lote pequeño capturado a mano |
| Captura manual lenta | Baja adopción | Medir el tiempo de captura y simplificar el formulario |
| Pocos racks por pedido | La ruta óptima ahorra poco | Medir con pedidos de tamaño típico, no solo con los de prueba |
| Fallo de inicio de sesión | Nadie puede entrar | Documentar el alta de usuarios en Entra ID |
