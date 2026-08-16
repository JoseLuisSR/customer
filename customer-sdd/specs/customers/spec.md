# Especificación funcional de API — Gestión de Customers

> Esta especificación define el comportamiento funcional de una API para administrar clientes y sus direcciones.  
> No incluye decisiones de implementación, arquitectura, framework, base de datos ni infraestructura.

---

## 1. Información general

### 1.1 Nombre de la funcionalidad

Gestión de clientes y direcciones.

### 1.2 Identificador

`API-CUSTOMERS-001`

### 1.3 Estado

- [x] Borrador
- [ ] En revisión
- [ ] Aprobada
- [ ] Implementada
- [ ] Obsoleta

### 1.4 Responsable funcional

`[Pendiente por definir]`

### 1.5 Fecha y versión

- **Versión:** `0.1.0`
- **Fecha:** `2026-07-24`

---

## 2. Objetivo

Permitir que los consumidores autorizados de la API creen, consulten, actualicen y eliminen clientes, junto con sus direcciones asociadas, aplicando las reglas de negocio definidas para unicidad de correo electrónico y cantidad máxima de direcciones.

---

## 3. Problema o necesidad

La aplicación web requiere una API que permita administrar la información de clientes y sus direcciones de forma consistente, validando que no existan clientes con correos electrónicos duplicados y que cada cliente tenga como máximo cinco direcciones asociadas.

---

## 4. Alcance

### 4.1 Incluido

- Crear clientes.
- Consultar un cliente por su identificador interno.
- Consultar la lista de clientes.
- Actualizar los datos de un cliente.
- Eliminar un cliente.
- Registrar direcciones asociadas a un cliente.
- Consultar las direcciones de un cliente.
- Actualizar una dirección.
- Eliminar una dirección.
- Informar el resultado de cada operación.
- Validar la unicidad del correo electrónico.
- Validar el límite máximo de cinco direcciones por cliente.

### 4.2 Fuera de alcance

- Autenticación y autorización.
- Gestión de usuarios de la aplicación.
- Historial de cambios.
- Importación o exportación masiva.
- Validación de direcciones contra servicios postales externos.
- Geolocalización.
- Facturación, pagos o pedidos.
- Definición de tecnologías o arquitectura.

---

## 5. Actores y consumidores

| Actor o consumidor | Descripción | Permisos o responsabilidades |
|---|---|---|
| Aplicación web | Interfaz que consume la API | Crear, consultar, actualizar y eliminar clientes y direcciones |
| Sistema autorizado | Integración externa permitida | Ejecutar las operaciones habilitadas sobre clientes y direcciones |

---

## 6. Precondiciones

- El consumidor debe tener acceso autorizado a la API.
- Para consultar, actualizar o eliminar un cliente, este debe existir.
- Para registrar, consultar, actualizar o eliminar una dirección, el cliente relacionado debe existir.
- Para actualizar o eliminar una dirección, esta debe existir y pertenecer al cliente indicado.

---

## 7. Requisitos funcionales

### RF-001 — Crear cliente

**Descripción**

La API debe permitir registrar un cliente con nombre, identificación, edad, correo electrónico y una lista opcional de direcciones.

**Actor**

Aplicación web o sistema autorizado.

**Entrada funcional**

- `name`
- `identification`
- `age`
- `email`
- `addresses` opcional

**Resultado esperado**

La API debe crear el cliente cuando la información sea válida y devolver un resultado que indique el estado final de la operación y de la entidad.

**Reglas relacionadas**

- RN-001
- RN-002
- RN-003

---

### RF-002 — Consultar cliente

**Descripción**

La API debe permitir consultar un cliente por su identificador interno.

**Resultado esperado**

La API debe devolver la información del cliente y sus direcciones asociadas, junto con el estado actual de la entidad.

---

### RF-003 — Consultar clientes

**Descripción**

La API debe permitir consultar la lista de clientes registrados.

**Resultado esperado**

La API debe devolver los clientes disponibles y el estado de la operación.

---

### RF-004 — Actualizar cliente

**Descripción**

La API debe permitir modificar los datos de un cliente existente.

**Resultado esperado**

La API debe guardar los cambios válidos y devolver un resultado que indique el estado final de la operación y de la entidad.

**Reglas relacionadas**

- RN-001
- RN-002

---

### RF-005 — Eliminar cliente

**Descripción**

La API debe permitir eliminar un cliente existente.

**Resultado esperado**

La API debe eliminar el cliente y devolver un resultado que confirme el estado final de la operación.

**Reglas relacionadas**

- RN-004

---

### RF-006 — Crear dirección

**Descripción**

La API debe permitir registrar una dirección asociada a un cliente existente.

**Resultado esperado**

La API debe crear la dirección cuando el cliente tenga menos de cinco direcciones y devolver el estado final de la operación y de la entidad.

**Reglas relacionadas**

- RN-003
- RN-005

---

### RF-007 — Consultar direcciones

**Descripción**

La API debe permitir consultar las direcciones asociadas a un cliente.

**Resultado esperado**

La API debe devolver únicamente las direcciones relacionadas con el cliente solicitado.

---

### RF-008 — Actualizar dirección

**Descripción**

La API debe permitir modificar los datos de una dirección existente que pertenezca al cliente indicado.

**Resultado esperado**

La API debe guardar los cambios y devolver el estado final de la operación y de la entidad.

---

### RF-009 — Eliminar dirección

**Descripción**

La API debe permitir eliminar una dirección existente asociada a un cliente.

**Resultado esperado**

La API debe eliminar la dirección y devolver un resultado que confirme el estado final de la operación.

---

## 8. Operaciones funcionales de la API

| Operación | Propósito | Actor | Recurso | Resultado esperado |
|---|---|---|---|---|
| Crear | Registrar un nuevo cliente | Consumidor autorizado | Customer | Cliente creado o rechazo informado |
| Consultar | Obtener un cliente | Consumidor autorizado | Customer | Cliente encontrado o no encontrado |
| Listar | Obtener los clientes | Consumidor autorizado | Customer | Lista de clientes |
| Actualizar | Modificar un cliente | Consumidor autorizado | Customer | Cliente actualizado o rechazo informado |
| Eliminar | Eliminar un cliente | Consumidor autorizado | Customer | Cliente eliminado o rechazo informado |
| Crear | Registrar una dirección | Consumidor autorizado | Address | Dirección creada o rechazo informado |
| Consultar | Obtener direcciones de un cliente | Consumidor autorizado | Address | Lista de direcciones |
| Actualizar | Modificar una dirección | Consumidor autorizado | Address | Dirección actualizada o rechazo informado |
| Eliminar | Eliminar una dirección | Consumidor autorizado | Address | Dirección eliminada o rechazo informado |

---

## 9. Reglas de negocio

### RN-001 — Correo electrónico único

No se permite registrar más de un cliente con el mismo correo electrónico.

La validación debe aplicarse tanto al crear como al actualizar un cliente.

### RN-002 — Datos obligatorios del cliente

Todo cliente debe tener los siguientes datos:

- Nombre.
- Identificación.
- Edad.
- Correo electrónico.

### RN-003 — Máximo de direcciones

Un cliente puede tener como máximo cinco direcciones asociadas.

La API debe rechazar cualquier operación que produzca una sexta dirección.

### RN-004 — Eliminación del cliente

Al eliminar un cliente, ninguna dirección puede permanecer asociada a dicho cliente.

### RN-005 — Relación obligatoria

Toda dirección debe estar asociada a un único cliente existente.

Una dirección no puede existir sin un cliente relacionado.

### RN-006 — Resultado de las operaciones

Cada operación debe devolver un resultado que permita conocer:

- Si la operación fue exitosa o fallida.
- El tipo de operación ejecutada.
- El estado final de la entidad.
- Un mensaje descriptivo.
- Los datos resultantes cuando corresponda.
- El motivo del rechazo cuando la operación falle.

---

## 10. Datos funcionales

### 10.1 Entidad Customer

| Campo | Descripción | Obligatorio | Restricciones funcionales |
|---|---|---:|---|
| `id` | Identificador interno del cliente | Generado | Debe identificar de forma única al cliente |
| `name` | Nombre del cliente | Sí | No debe estar vacío |
| `identification` | Número o código de identificación | Sí | No debe estar vacío |
| `age` | Edad del cliente | Sí | Debe ser un número entero no negativo |
| `email` | Correo electrónico | Sí | Debe tener formato válido y ser único |
| `addresses` | Direcciones del cliente | No | Puede contener entre cero y cinco direcciones |
| `status` | Estado actual de la entidad | Sí | Debe reflejar el resultado o estado vigente |

### 10.2 Entidad Address

| Campo | Descripción | Obligatorio | Restricciones funcionales |
|---|---|---:|---|
| `id` | Identificador interno de la dirección | Generado | Debe identificar de forma única la dirección |
| `customer_id` | Cliente relacionado | Sí | Debe corresponder a un cliente existente |
| `country` | País | Sí | No debe estar vacío |
| `state` | Estado, departamento o provincia | Sí | No debe estar vacío |
| `city` | Ciudad | Sí | No debe estar vacío |
| `address` | Dirección física | Sí | No debe estar vacía |
| `postal_code` | Código postal | Sí | No debe estar vacío |
| `status` | Estado actual de la entidad | Sí | Debe reflejar el resultado o estado vigente |

### 10.3 Resultado funcional de operación

| Campo | Descripción | Obligatorio |
|---|---|---:|
| `success` | Indica si la operación fue exitosa | Sí |
| `operation` | Operación ejecutada | Sí |
| `entity` | Tipo de entidad afectada | Sí |
| `entity_status` | Estado final de la entidad | Sí |
| `message` | Descripción del resultado | Sí |
| `data` | Datos de la entidad o resultado | Cuando aplique |
| `errors` | Motivos del rechazo o validaciones fallidas | Cuando aplique |

---

## 11. Validaciones funcionales

| Código | Validación | Resultado esperado cuando no se cumple |
|---|---|---|
| VAL-001 | El correo electrónico debe tener formato válido | Rechazar la operación |
| VAL-002 | El correo electrónico no debe estar registrado por otro cliente | Rechazar la operación por duplicidad |
| VAL-003 | El nombre no debe estar vacío | Rechazar la operación |
| VAL-004 | La identificación no debe estar vacía | Rechazar la operación |
| VAL-005 | La edad debe ser un entero no negativo | Rechazar la operación |
| VAL-006 | El cliente debe existir | Informar que el cliente no fue encontrado |
| VAL-007 | El cliente no debe tener más de cinco direcciones | Rechazar la creación de una nueva dirección |
| VAL-008 | La dirección debe pertenecer al cliente indicado | Rechazar la operación |
| VAL-009 | Los campos obligatorios de la dirección no deben estar vacíos | Rechazar la operación |
| VAL-010 | La dirección debe existir para ser actualizada o eliminada | Informar que la dirección no fue encontrada |

---

## 12. Escenarios funcionales

### Escenario 1 — Crear cliente correctamente

**Dado que** no existe un cliente con el correo suministrado  
**Cuando** el consumidor envía los datos válidos del cliente  
**Entonces** la API crea el cliente y devuelve un resultado exitoso con el estado de la entidad

### Escenario 2 — Rechazar correo duplicado

**Dado que** existe un cliente con el correo suministrado  
**Cuando** se intenta crear o actualizar otro cliente con el mismo correo  
**Entonces** la API rechaza la operación e informa la duplicidad

### Escenario 3 — Crear dirección correctamente

**Dado que** el cliente existe y tiene menos de cinco direcciones  
**Cuando** se envía una dirección válida  
**Entonces** la API crea la dirección y la relaciona con el cliente

### Escenario 4 — Rechazar sexta dirección

**Dado que** el cliente ya tiene cinco direcciones  
**Cuando** se intenta registrar una dirección adicional  
**Entonces** la API rechaza la operación e informa que se alcanzó el máximo permitido

### Escenario 5 — Consultar cliente inexistente

**Dado que** no existe un cliente con el identificador solicitado  
**Cuando** se realiza la consulta  
**Entonces** la API informa que el cliente no fue encontrado

### Escenario 6 — Actualizar dirección ajena

**Dado que** una dirección no pertenece al cliente indicado  
**Cuando** se intenta actualizarla mediante dicho cliente  
**Entonces** la API rechaza la operación

### Escenario 7 — Eliminar cliente

**Dado que** el cliente existe  
**Cuando** se solicita su eliminación  
**Entonces** la API elimina el cliente, evita direcciones huérfanas y devuelve el resultado final

---

## 13. Manejo funcional de errores

| Código funcional | Situación | Mensaje esperado | Resultado |
|---|---|---|---|
| ERR-001 | Datos obligatorios inválidos o ausentes | Datos de entrada inválidos | Operación rechazada |
| ERR-002 | Correo electrónico duplicado | Ya existe un cliente con el correo indicado | Operación rechazada |
| ERR-003 | Cliente inexistente | Cliente no encontrado | Sin modificación de datos |
| ERR-004 | Dirección inexistente | Dirección no encontrada | Sin modificación de datos |
| ERR-005 | Máximo de direcciones alcanzado | El cliente ya tiene cinco direcciones | Operación rechazada |
| ERR-006 | Relación cliente-dirección inválida | La dirección no pertenece al cliente indicado | Operación rechazada |
| ERR-007 | Error no controlado | No fue posible completar la operación | Estado final informado |

---

## 14. Autorización y acceso funcional

La definición de roles y permisos específicos queda pendiente.

Como requisito mínimo, únicamente consumidores autorizados deben poder ejecutar operaciones CRUD sobre clientes y direcciones.

---

## 15. Criterios de aceptación

### CA-001 — Creación de cliente

- **Dado:** un correo electrónico no registrado
- **Cuando:** se envían datos válidos
- **Entonces:** se crea el cliente y se informa un resultado exitoso

### CA-002 — Unicidad de correo

- **Dado:** un correo electrónico ya asociado a otro cliente
- **Cuando:** se intenta crear o actualizar un cliente con dicho correo
- **Entonces:** la operación es rechazada sin modificar los datos existentes

### CA-003 — Consulta de cliente

- **Dado:** un cliente existente
- **Cuando:** se solicita por su identificador
- **Entonces:** se devuelve el cliente con sus direcciones y estado actual

### CA-004 — Actualización de cliente

- **Dado:** un cliente existente
- **Cuando:** se envían cambios válidos
- **Entonces:** la información es actualizada y se devuelve el estado final

### CA-005 — Eliminación de cliente

- **Dado:** un cliente existente
- **Cuando:** se solicita su eliminación
- **Entonces:** el cliente es eliminado y no quedan direcciones huérfanas

### CA-006 — Creación de dirección

- **Dado:** un cliente con menos de cinco direcciones
- **Cuando:** se envía una dirección válida
- **Entonces:** la dirección es creada y asociada al cliente

### CA-007 — Límite de direcciones

- **Dado:** un cliente con cinco direcciones
- **Cuando:** se intenta crear una dirección adicional
- **Entonces:** la operación es rechazada

### CA-008 — Resultado obligatorio

- **Dado:** cualquier operación CRUD
- **Cuando:** la operación finaliza
- **Entonces:** la respuesta indica éxito o fallo, operación, entidad, estado, mensaje y datos o errores aplicables

---

## 16. Casos límite

- Cliente creado sin direcciones.
- Cliente creado con exactamente cinco direcciones.
- Intento de crear un cliente con seis direcciones.
- Correo con diferencias únicamente de mayúsculas y minúsculas.
- Correo con espacios antes o después.
- Edad igual a cero.
- Edad negativa.
- Actualización del correo por el mismo cliente sin cambiar su valor.
- Eliminación de un cliente con direcciones asociadas.
- Dirección con uno o más campos obligatorios vacíos.
- Actualización o eliminación repetida de una entidad ya eliminada.
- Solicitudes simultáneas que intenten registrar el mismo correo.
- Solicitudes simultáneas que intenten superar el máximo de cinco direcciones.

---

## 17. Dependencias funcionales

- Mecanismo de identificación única para clientes.
- Mecanismo de identificación única para direcciones.
- Mecanismo de autorización para consumidores de la API.
- Definición posterior del contrato formal de la API.

---

## 18. Supuestos y restricciones

### Supuestos

- Cada cliente tiene un identificador interno único.
- Cada dirección tiene un identificador interno único.
- El correo electrónico se compara de forma normalizada.
- El resultado de la operación se devuelve en todas las respuestas.

### Restricciones

- No se permiten clientes con correo electrónico repetido.
- Un cliente no puede tener más de cinco direcciones.
- Toda dirección debe pertenecer a un cliente.
- No se permiten direcciones huérfanas.

---

## 19. Trazabilidad

| Requisito | Regla de negocio | Criterio de aceptación | Escenario |
|---|---|---|---|
| RF-001 | RN-001, RN-002, RN-003, RN-006 | CA-001, CA-002, CA-008 | Escenarios 1 y 2 |
| RF-002 | RN-006 | CA-003, CA-008 | Escenario 5 |
| RF-003 | RN-006 | CA-008 | N/A |
| RF-004 | RN-001, RN-002, RN-006 | CA-002, CA-004, CA-008 | Escenario 2 |
| RF-005 | RN-004, RN-006 | CA-005, CA-008 | Escenario 7 |
| RF-006 | RN-003, RN-005, RN-006 | CA-006, CA-007, CA-008 | Escenarios 3 y 4 |
| RF-007 | RN-005, RN-006 | CA-008 | N/A |
| RF-008 | RN-005, RN-006 | CA-008 | Escenario 6 |
| RF-009 | RN-005, RN-006 | CA-008 | Escenario 6 |

---

## 20. Preguntas abiertas

| ID | Pregunta | Responsable | Estado |
|---|---|---|---|
| Q-001 | ¿La identificación del cliente también debe ser única? | Negocio | Abierta |
| Q-002 | ¿La edad tiene un valor mínimo o máximo permitido? | Negocio | Abierta |
| Q-003 | ¿Qué estados funcionales puede tener un cliente o una dirección? | Negocio | Abierta |
| Q-004 | ¿La eliminación debe ser lógica o definitiva? | Negocio | Abierta |
| Q-005 | ¿El código postal es obligatorio para todos los países? | Negocio | Abierta |
| Q-006 | ¿La consulta de clientes requiere paginación, filtros u ordenamiento? | Negocio | Abierta |

---

## 21. Criterios de aprobación

La especificación puede considerarse lista cuando:

- [x] El objetivo y el alcance están definidos.
- [x] Los actores están identificados.
- [x] Los requisitos funcionales son verificables.
- [x] Las reglas de negocio están documentadas.
- [x] Los datos de entrada y salida están definidos.
- [x] Los errores y casos límite están contemplados.
- [x] Cada requisito tiene criterios de aceptación.
- [ ] Las preguntas abiertas críticas fueron resueltas.
- [ ] Las partes interesadas aprobaron la especificación.
