# Troubleshooting, Flujo de Pruebas y Limitaciones

## 1. Flujo de Pruebas Recomendado (Test Chat)

Puedes probar el asistente punto a punto desde la consola de **Amazon Connect** utilizando **Test Chat**.

### 1.1 Saludo Inicial

**Cliente:**

```text
hola
```

**Resultado esperado:** el agente debe responder con un saludo amigable y comenzar la interacción.

---

### 1.2 Consulta de Catálogo

**Cliente:**

```text
¿qué especialidades hay?
```

**Resultado esperado:** el agente debe listar únicamente las cinco especialidades disponibles:

* `medicina general`
* `pediatria`
* `odontologia`
* `dermatologia`
* `oftalmologia`

---

### 1.3 Consulta de Disponibilidad

**Cliente:**

```text
disponibilidad de odontologia para mañana
```

**Resultado esperado:** el agente debe identificar la acción `consultar_disponibilidad` e invocar la tool con los parámetros correspondientes. La fecha debe enviarse en formato `YYYY-MM-DD`.

---

### 1.4 Flujo de Agendamiento

**Cliente:** solicita agendar una cita proporcionando los datos necesarios.

**Resultado esperado:** el agente debe recopilar la información necesaria y solicitar una **confirmación explícita** antes de ejecutar `agendar_cita`. La tool solo debe ejecutarse después de que el cliente confirme.

---

### 1.5 Validación de Reglas de Negocio

**Cliente:**

```text
quiero agendar cardiologia
```

**Resultado esperado:** el agente debe rechazar amablemente la solicitud e indicar las cinco especialidades disponibles, sin mencionar `cardiologia` de nuevo ni ninguna otra especialidad inexistente como ejemplo. No debe intentar ejecutar la tool con una especialidad que no esté permitida.

---

## 2. Matriz de Resolución de Problemas

| Síntoma | Causa probable | Solución |
|---|---|---|
| Tool en estado rojo (`Insufficient`) en el AI Agent | Falta asignar permisos en el perfil de seguridad | Ve a **Security Profiles → Flow Modules** y asigna **Access** sobre la tool. Si persiste, recarga la página (`Ctrl+F5`) o quita y vuelve a agregar la tool. |
| El agente responde pero nunca invoca la tool | `Description` del módulo ambigua o faltan campos en el Input Schema | Revisa la descripción, los parámetros y los tipos definidos en el Flow Module. |
| El agente responde "No atendemos esa especialidad" incluso para una válida | La tabla `citas-medicas-especialidades` en DynamoDB está vacía | Ejecuta `python scripts/seed_especialidades.py`. |
| `sam local invoke` genera un timeout de 8 segundos | Antes del deploy: tablas no creadas. Después: posible problema de red/comunicación entre SAM y Docker en Windows | Valida directamente la función desplegada con `aws lambda invoke` (no usa Docker). |
| El Lambda ignora la acción enviada en el evento | Los cambios del código no fueron desplegados | Ejecuta nuevamente `sam build` y `sam deploy`. |
| `ImportError` al invocar la función Lambda | Discrepancia entre imports planos (`CodeUri: src/`) y referencias con prefijo `src.` en algún archivo | Todos los imports internos deben ser planos: `from channel_adapter import ...`, `from handlers import ...`, `from utils import ...`, `import repository as repo`. |

### Diagnóstico real del timeout de `sam local invoke` (documentado en una sesión concreta)

Se descartaron, en orden, con pruebas directas:
1. Bloqueo de red del contenedor (DNS) — `docker run ... socket.gethostbyname(...)` resolvió una IP real.
2. Bloqueo de conexión HTTPS (firewall/VPN) — `docker run ... urllib.request.urlopen(...)` devolvió `200`.
3. Perfil de AWS incorrecto — el log `--debug` mostró `'awsProfileProvided': False`, no era la causa.
4. Región no propagada al contenedor — se agregó `--region us-east-1` explícito y el timeout persistió.

Conclusión: problema de comunicación interna SAM↔Docker específico de esa
máquina Windows, sin causa raíz única confirmada en los foros de
`aws-sam-cli`. **No es bloqueante**: `aws lambda invoke` valida el Lambda
real sin pasar por Docker en absoluto.

---

## 3. Alcance y Limitaciones Conocidas

### 3.1 Condición de Carrera al Agendar

La validación de disponibilidad y la reserva se realizan actualmente en dos operaciones independientes. Solicitudes simultáneas para el mismo horario podrían generar un **sobreagendamiento**.

**Pendiente:** implementar expresiones de condición (`ConditionExpression`) en las operaciones de escritura de DynamoDB para garantizar que un horario no pueda reservarse simultáneamente por dos solicitudes.

### 3.2 Rango de Códigos de Cita

Los códigos de cita se generan en el rango `CITA-9000`–`CITA-9999` (1,000 combinaciones), con reintentos para evitar duplicados. Suficiente para pruebas/prototipo; para producción conviene una estrategia más robusta (UUID corto, contador incremental).

### 3.3 Trazabilidad de Logs y Datos Personales

El evento de entrada se registra completo en CloudWatch Logs, incluyendo potencialmente el documento del paciente. Riesgo de exposición innecesaria de información sensible.

**Pendiente antes de producción:** enmascarar datos personales en logs, revisar políticas de retención de CloudWatch, y aplicar controles de acceso adecuados.

### 3.4 Normalización de Formatos

La conversión de fecha/hora depende de que el LLM respete el formato indicado en el prompt y en la description de la tool. No hay una capa de normalización de respaldo en `utils.py`.

**Pendiente:** incorporar validación/normalización determinística en el backend, independiente del comportamiento del LLM.

---

## 4. Recomendaciones Antes de un Despliegue Productivo

1. Evitar condiciones de carrera mediante escrituras condicionales en DynamoDB.
2. Implementar una estrategia más robusta para generar códigos de cita.
3. Enmascarar o eliminar datos personales de los logs.
4. Validar fecha, hora y otros parámetros directamente en el backend.
5. Revisar permisos IAM siguiendo el principio de mínimo privilegio.
6. Configurar correctamente la retención y acceso a CloudWatch Logs.
7. Agregar pruebas de concurrencia y casos de error adicionales.

---

## 5. Resumen del Flujo de Diagnóstico

Ante un problema durante las pruebas, revisar los componentes en este orden (sigue el camino real de la conversación, de afuera hacia adentro):

```text
Amazon Connect (Contact Flow)
      │
      ▼
Bot puente de Lex V2
      │  (solo reenvía; revisar el switch "AI agent intent" si no lo hace)
      ▼
AI Agent
      │
      ├── ¿Tool disponible?
      │       │
      │       └── Revisar Security Profile
      │
      ▼
Flow Module (la tool)
      │
      ├── ¿Schema correcto?
      ├── ¿Description correcta?
      └── ¿Lambda configurado?
      │
      ▼
AWS Lambda
      │
      ├── ¿Código actualizado? (sam build && sam deploy)
      ├── ¿Imports planos correctos?
      └── ¿Parámetros recibidos? (ver CloudWatch: "EVENTO RECIBIDO")
      │
      ▼
DynamoDB
      │
      ├── ¿Tabla existe?
      ├── ¿Datos iniciales cargados? (seed_especialidades.py)
      └── ¿Operación correcta?
```

Este orden permite aislar rápido si el problema está en Connect, el bot puente, el AI Agent, el Flow Module, el Lambda o DynamoDB.

---

[← Volver al README principal](../README.md)