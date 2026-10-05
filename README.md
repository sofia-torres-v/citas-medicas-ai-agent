# Citas Médicas - AI Agent + Amazon Connect

Asistente conversacional para la gestión de citas médicas mediante **chat en Amazon Connect**. Permite consultar disponibilidad, agendar, consultar, reagendar y cancelar citas utilizando lenguaje natural.

Un **AI Agent (Amazon Q in Connect, tipo Orchestration)** gestiona la conversación y el razonamiento, mientras que este repositorio contiene el backend serverless (**AWS Lambda + DynamoDB**) que ejecuta las reglas de negocio y procesa las operaciones sobre las citas.

---

## 1. Arquitectura

El proyecto nació como una comparación técnica entre un bot de **Amazon Lex V2 tradicional** (basado en intents/slots) y una arquitectura basada en **AI Agents (LLMs con Tools)**.

![Arquitectura](docs/assets/arquitectura.png)

```text
Usuario
   │
   ▼
Chat
   │
   ▼
Contact Flow
(Amazon Connect)
   │
   ▼
Bot Lex "Puente"
(sin intents, solo reenvía)
   │
   ▼
AI Agent
(Amazon Q in Connect)
   │
   │ Razonamiento + decisión
   ▼
Tool
(Flow Module)
   │
   ▼
AWS Lambda
   │
   ▼
Repository Pattern
   │
   ▼
DynamoDB
```

---

## 2. Estructura del Proyecto

El código está deliberadamente desacoplado en capas para separar la entrada desde Amazon Connect, la lógica de negocio y el acceso a datos.

```text
citas-medicas-ai-agent/

├── template.yaml                 # Infraestructura como código (SAM: Lambda + DynamoDB + IAM)
├── src/                          # Código fuente desplegado en Lambda
│   ├── lambda_function.py        # Router de entrada
│   ├── channel_adapter.py        # Adaptador de formato (Connect String Map <-> Dict)
│   ├── repository.py             # Operaciones DynamoDB (Repository Pattern)
│   ├── utils.py                  # Normalización y utilidades puras
│   └── handlers/                 # Reglas de negocio
│
├── tests/                        # Pruebas unitarias con pytest y unittest.mock
│
├── events/                       # Eventos utilizados para pruebas
│
├── scripts/                      # Scripts de utilidades
│   └── seed_especialidades.py    # Carga inicial de especialidades
│
└── docs/                         # Guías de configuración y arquitectura
    ├── deploy-backend.md         # Guía de despliegue del backend
    ├── amazon-connect-setup.md   # Configuración de Amazon Connect
    ├── prompt-agente.md          # Reglas del AI Agent
    └── troubleshooting.md        # Problemas y limitaciones
```

---

## 3. Guías de Instalación y Configuración

Para desplegar y configurar el proyecto, consulta las siguientes guías:

* 🚀 [Despliegue del Backend (SAM + Lambda + DynamoDB)](docs/deploy-backend.md)
* 🛠️ [Configuración en Amazon Connect, Lex y Q in Connect](docs/amazon-connect-setup.md)
* 📜 [Prompt y reglas del AI Agent](docs/prompt-agente.md)
* ❓ [Troubleshooting y limitaciones conocidas](docs/troubleshooting.md)

---

## 4. Requisitos Previos

* Python 3.13
* AWS SAM CLI
* AWS CLI configurado
* Cuenta de AWS
* Cuenta de Amazon Connect con Amazon Q in Connect activo

> Docker Desktop es opcional y solo es necesario para ejecutar Lambda localmente mediante `sam local invoke`.

---

## 5. Quickstart Backend

Si acabas de clonar el repositorio y quieres preparar el entorno local:

```powershell
git clone <URL_DEL_REPOSITORIO>

cd citas-medicas-ai-agent

python -m venv .venv

.venv\Scripts\Activate.ps1

pip install -r requirements.txt
```

### 5.1 Ejecutar pruebas unitarias

Puedes validar la lógica de negocio antes del despliegue:

```powershell
pytest tests/ -v
```

Las pruebas se ejecutan localmente y no requieren servicios de AWS.

### 5.2 Construir el proyecto

Valida la plantilla SAM y construye el paquete de despliegue:

```powershell
sam validate

sam build
```

### 5.3 Primer despliegue en AWS

Si es la primera vez que despliegas el proyecto, utiliza el modo guiado:

```powershell
sam deploy --guided
```

Durante este proceso SAM solicitará información como el nombre del stack, región y configuración de permisos.

Una vez completada la configuración inicial, los siguientes despliegues pueden realizarse simplemente con:

```powershell
sam deploy
```

### 5.4 Cargar datos iniciales

Después del despliegue, carga las especialidades iniciales:

```powershell
python scripts/seed_especialidades.py
```

💡 **¿Primera vez desplegando el backend?**

Consulta la [Guía Completa de Despliegue del Backend](docs/deploy-backend.md) para conocer los requisitos, la configuración de AWS SAM, las pruebas, la verificación del despliegue y la ejecución local con Docker.

---

## 6. Resultado de las Pruebas Unitarias

Las pruebas se ejecutan **100% en memoria**, sin consumir servicios reales de AWS.

| Módulo de prueba   | Descripción                                        | Pruebas | Resultado       |
| ------------------ | -------------------------------------------------- | ------: | --------------- |
| `test_handlers.py` | Lógica de agendar, consultar, cancelar y reagendar |      13 | PASSED          |
| `test_utils.py`    | Normalización de datos y extracción de códigos     |      15 | PASSED          |
| **Total**          | **Cobertura de las reglas de negocio**             |  **28** | **100% PASSED** |

---

## 7. Nota sobre Datos

Este proyecto utiliza datos ficticios para demostración y pruebas.

No utilizar información real de pacientes ni datos personales en los archivos de prueba, eventos o logs.
