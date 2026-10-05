# Troubleshooting, Flujo de Pruebas y Limitaciones


## 1. Flujo de Pruebas Recomendado (Test Chat)

Puedes probar el asistente punto a punto desde la consola de **Amazon Connect** utilizando **Test Chat**.

### 1.1 Saludo Inicial

**Cliente:**

```text
hola
```

**Resultado esperado:**

El agente debe responder con un saludo amigable y comenzar la interacción.

---

### 1.2 Consulta de Catálogo

**Cliente:**

```text
¿qué especialidades hay?
```

**Resultado esperado:**

El agente debe listar únicamente las cinco especialidades disponibles:

* `medicina general`
* `odontologia`
* `pediatria`
* `ginecologia`
* `psicologia`

---

### 1.3 Consulta de Disponibilidad

**Cliente:**

```text
disponibilidad de odontología para mañana
```

**Resultado esperado:**

El agente debe identificar la acción `consultar_disponibilidad` e invocar la tool con los parámetros correspondientes.

La fecha debe enviarse en formato:

```text
YYYY-MM-DD
```

---

### 1.4 Flujo de Agendamiento

**Cliente:**

Solicita agendar una cita proporcionando los datos necesarios.

**Resultado esperado:**

El agente debe recopilar la información necesaria y solicitar una **confirmación explícita** antes de ejecutar:

```text
agendar_cita
```

La tool solo debe ejecutarse después de que el cliente confirme.

---

### 1.5 Validación de Reglas de Negocio

**Cliente:**

```text
quiero agendar cardiología
```

**Resultado esperado:**

El agente debe rechazar amablemente la solicitud e indicar las cinco especialidades disponibles.

No debe intentar ejecutar la tool con una especialidad que no esté permitida.

---

## 2. Matriz de Resolución de Problemas

| Síntoma                                                                                  | Causa probable                                                      | Solución                                                                                                                         |
| ---------------------------------------------------------------------------------------- | ------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------- |
| Tool en estado rojo (`Insufficient`) en el AI Agent                                      | Falta asignar permisos en el perfil de seguridad                    | Ve a **Security Profiles → Flow Modules** y asigna **Access** sobre la tool.                                                     |
| El agente responde pero nunca invoca la tool                                             | `Description` del módulo ambigua o faltan campos en el Input Schema | Revisa la descripción, los parámetros y los tipos definidos en el Flow Module.                                                   |
| El agente responde: "No atendemos esa especialidad" incluso para una especialidad válida | La tabla `citas-medicas-especialidades` en DynamoDB está vacía      | Ejecuta `python scripts/seed_especialidades.py`.                                                                                 |
| `sam local invoke` genera un timeout de 8 segundos                                       | Tablas no creadas o problema de red entre SAM y Docker en Windows   | Valida directamente la función desplegada en AWS utilizando `aws lambda invoke`.                                                 |
| El Lambda ignora la acción enviada en el evento                                          | Los cambios del código no fueron desplegados                        | Ejecuta nuevamente `sam build` y `sam deploy`.                                                                                   |
| `ImportError` al invocar la función Lambda                                               | Existe una discrepancia en los nombres o imports de los módulos     | Verifica que `lambda_function.py` utilice correctamente `extraer_parametros` y `construir_respuesta` desde `channel_adapter.py`. |

---

## 3. Alcance y Limitaciones Conocidas

### 3.1 Condición de Carrera al Agendar

La validación de disponibilidad y la reserva se realizan actualmente en dos operaciones independientes.

Por lo tanto, solicitudes simultáneas para el mismo horario podrían generar un **sobreagendamiento**.

**Pendiente:**

Implementar expresiones de condición en las operaciones de escritura de DynamoDB para garantizar que un horario no pueda reservarse simultáneamente por dos solicitudes.

---

### 3.2 Rango de Códigos de Cita

Los códigos de cita se generan dentro del siguiente rango:

```text
CITA-9000
     ↓
CITA-9999
```

Esto representa un total de **1,000 combinaciones** y utiliza reintentos para evitar duplicados.

Este mecanismo es suficiente para un entorno de **pruebas o prototipo**, pero debería reemplazarse por una estrategia más robusta para un entorno productivo de mayor escala.

---

### 3.3 Trazabilidad de Logs y Datos Personales

Actualmente, el evento de entrada puede registrarse completo en **CloudWatch Logs**, incluyendo potencialmente datos personales como el documento del paciente.

Esto representa un riesgo de exposición innecesaria de información sensible.

**Pendiente antes de producción:**

* Implementar enmascaramiento de datos personales.
* Evitar registrar información sensible innecesaria.
* Revisar las políticas de retención de CloudWatch Logs.
* Aplicar controles de acceso adecuados sobre los logs.

---

### 3.4 Normalización de Formatos

La conversión y validación de formatos de fecha y hora depende actualmente de las instrucciones proporcionadas al LLM mediante el **prompt** y la descripción de la tool.

No existe una capa estricta de normalización de respaldo en `utils.py`.

Por ejemplo, el agente debe transformar correctamente una fecha proporcionada en lenguaje natural a:

```text
YYYY-MM-DD
```

y una hora a:

```text
HH:MM
```

**Pendiente:**

Incorporar validaciones y normalización determinísticas en el backend para que los datos recibidos sean validados independientemente del comportamiento del LLM.

---

## 4. Recomendaciones Antes de un Despliegue Productivo

Antes de utilizar este proyecto en un entorno real, se recomienda abordar principalmente las siguientes limitaciones:

1. **Evitar condiciones de carrera** mediante escrituras condicionales en DynamoDB.
2. **Implementar una estrategia robusta para generar códigos de cita.**
3. **Enmascarar o eliminar datos personales de los logs.**
4. **Validar fecha, hora y otros parámetros directamente en el backend.**
5. **Revisar permisos IAM siguiendo el principio de mínimo privilegio.**
6. **Configurar correctamente la retención y acceso a CloudWatch Logs.**
7. **Agregar pruebas de concurrencia y casos de error adicionales.**

---

## 5. Resumen del Flujo de Diagnóstico

Ante un problema durante las pruebas, se recomienda revisar los componentes en este orden:

```text
Amazon Connect
      │
      ▼
Amazon Lex V2
      │
      ▼
AI Agent
      │
      ├── ¿Tool disponible?
      │       │
      │       └── Revisar Security Profile
      │
      ▼
Flow Module
      │
      ├── ¿Schema correcto?
      ├── ¿Description correcta?
      └── ¿Lambda configurado?
      │
      ▼
AWS Lambda
      │
      ├── ¿Código actualizado?
      ├── ¿Imports correctos?
      └── ¿Parámetros recibidos?
      │
      ▼
DynamoDB
      │
      ├── ¿Tabla existe?
      ├── ¿Datos iniciales cargados?
      └── ¿Operación correcta?
```

Este flujo permite aislar rápidamente si el problema se encuentra en la configuración de **Amazon Connect**, la orquestación del **AI Agent**, el **Flow Module**, la función **Lambda** o la persistencia en **DynamoDB**.

---

[← Volver al README principal](../README.md)