# Citas Médicas - AI Agent + Amazon Connect

Asistente conversacional omnicanal (chat y voz) para la gestión de citas médicas en **Amazon Connect**. Permite consultar disponibilidad, agendar, consultar, reagendar y cancelar citas en lenguaje natural.

Un **AI Agent (Amazon Q in Connect, tipo Orchestration)** gestiona la conversación y el razonamiento, mientras que este repositorio contiene el backend serverless (**AWS Lambda + DynamoDB**) que ejecuta las reglas de negocio estrictas.

---

## Arquitectura

El proyecto nació como una comparación técnica entre un bot de **Amazon Lex V2 tradicional** (basado en intents/slots) y una arquitectura basada en **AI Agents (LLMs con Tools)**.

![Arquitectura](docs/assets/arquitectura.png)

```text
Cliente (chat/voz)
       │
       ▼
Contact Flow (Amazon Connect)
       │
       ▼
Bot Lex "Puente" (Sin intents, solo reenvía)
       │
       ▼
AI Agent (Amazon Q in Connect) ──(Razonamiento LLM)
       │
       ▼ (Invoca Tool)
Flow Module ("CitasMedicasTool")
       │
       ▼
AWS Lambda (Este repositorio) ──► Repository Pattern ──► DynamoDB
```

---

## Estructura del Proyecto

El código está deliberadamente desacoplado en capas para permitir reutilización de lógica entre diferentes interfaces o canales:

```text
citas-medicas-ai-agent/

├── template.yaml                 # Infraestructura como código (SAM: Lambda + DynamoDB + IAM)
├── src/                          # Código fuente desplegado en Lambda
│   ├── lambda_function.py        # Router de entrada
│   ├── channel_adapter.py        # Adaptador de formato (Connect String Map <-> Dict)
│   ├── repository.py             # Operaciones DynamoDB (Repository Pattern)
│   ├── utils.py                  # Normalización y utilidades puras
│   └── handlers/                 # Reglas de negocio
├── tests/                        # Pruebas unitarias con pytest y unittest.mock
├── scripts/                      # Scripts de utilidades
│   └── seed_especialidades.py    # Carga inicial de especialidades
└── docs/                         # Guías de configuración y arquitectura
    ├── deploy-backend.md         # Guía de despliegue del backend
    ├── amazon-connect-setup.md   # Configuración de Amazon Connect
    ├── prompt-agente.md          # Reglas del AI Agent
    └── troubleshooting.md        # Problemas y limitaciones
```

---

## Guías de Instalación y Configuración

Para desplegar y configurar el proyecto completo, sigue estas guías:

* 🚀 [Despliegue del Backend (SAM + Lambda + DynamoDB)](docs/deploy-backend.md)
* 🛠️ [Configuración en Amazon Connect, Lex y Q in Connect](docs/amazon-connect-setup.md)
* 📜 [Prompting y Reglas del AI Agent](docs/prompt-agente.md)
* ❓ [Troubleshooting y Limitaciones Conocidas](docs/troubleshooting.md)

---

## Requisitos Previos

* Python 3.13
* AWS SAM CLI
* AWS CLI configurado
* Cuenta de AWS
* Cuenta de Amazon Connect con Amazon Q in Connect activo

---

## Quickstart Backend

Si acabas de clonar el repositorio y quieres desplegar el backend:

```powershell
git clone <URL_DEL_REPOSITORIO>

cd citas-medicas-ai-agent

python -m venv .venv

.venv\Scripts\Activate.ps1

pip install -r requirements.txt
```

### Opcional: ejecutar pruebas unitarias

Puedes validar la lógica de negocio antes del despliegue:

```powershell
pytest tests/ -v
```

Las pruebas se ejecutan localmente y no requieren servicios de AWS.

### Desplegar en AWS

```powershell
sam build
sam deploy --guided

Después, cuando ya exista la configuración, podrás usar simplemente:
sam deploy
```

Después del despliegue, carga las especialidades iniciales:

```powershell
python scripts/seed_especialidades.py
```

💡 **¿Primera vez desplegando el backend?**

Consulta la [Guía Completa de Despliegue del Backend](docs/deploy-backend.md) para conocer los requisitos, la configuración de AWS SAM, las pruebas, la verificación del despliegue y la ejecución local con Docker.

---

## Resultado de las Pruebas Unitarias

Las pruebas se ejecutan **100% en memoria**, sin consumo de servicios de AWS.

| Módulo de prueba   | Descripción                                        | Pruebas | Resultado       |
| ------------------ | -------------------------------------------------- | ------: | --------------- |
| `test_handlers.py` | Lógica de agendar, consultar, cancelar y reagendar |      13 | PASSED          |
| `test_utils.py`    | Normalización de datos y extracción de códigos     |      15 | PASSED          |
| **Total**          | **Cobertura de las reglas de negocio**             |  **28** | **100% PASSED** |
