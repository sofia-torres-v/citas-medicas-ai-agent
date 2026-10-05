# Despliegue del Backend (SAM + Lambda + DynamoDB)

Esta guía explica cómo preparar el entorno local, ejecutar las pruebas unitarias y desplegar la infraestructura serverless del proyecto utilizando **AWS SAM CLI**.

---

## 1. Requisitos Previos

Antes de comenzar, asegúrate de tener instalado:

* **Python 3.13**
* **AWS SAM CLI**

  * [Instalación oficial de AWS SAM CLI](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/install-sam-cli.html)
* **AWS CLI**, configurado con credenciales activas.
* **Docker Desktop** *(opcional, solo necesario para ejecutar Lambda localmente con `sam local invoke`)*.

Para comprobar las instalaciones:

```powershell
python --version
sam --version
aws --version
```

Para verificar que AWS CLI tiene una identidad configurada:

```powershell
aws sts get-caller-identity
```

---

## 2. Clonar el Repositorio y Preparar el Entorno

Los siguientes comandos están orientados a **Windows + PowerShell**.

### Clonar el proyecto

```powershell
git clone <URL_DEL_REPOSITORIO>

cd citas-medicas-ai-agent
```

### Crear el entorno virtual

```powershell
python -m venv .venv
```

### Activar el entorno virtual

```powershell
.venv\Scripts\Activate.ps1
```

### Instalar dependencias

```powershell
pip install -r requirements.txt
```

---

## 3. Ejecutar las Pruebas Unitarias

Las pruebas utilizan **pytest** y `unittest.mock`.

Se ejecutan **100% en memoria**, sin interactuar con servicios reales de AWS.

Ejecuta:

```powershell
pytest tests/ -v
```

Actualmente el proyecto cuenta con **28 pruebas unitarias**:

| Módulo de prueba   | Qué valida                                                      | Cantidad |
| ------------------ | --------------------------------------------------------------- | -------: |
| `test_utils.py`    | Normalización de texto, documento y código de cita              |       15 |
| `test_handlers.py` | Reglas de negocio para agendar, consultar, cancelar y reagendar |       13 |
| **Total**          |                                                                 |   **28** |

Resultado actual:

```text
28 passed
```

Estas pruebas permiten validar la lógica de negocio antes de desplegar el backend.

---

## 4. Construcción y Despliegue con AWS SAM

### 4.1 Validar la plantilla SAM

Antes de construir el proyecto, valida la plantilla de infraestructura:

```powershell
sam validate
```

### 4.2 Construir el proyecto

Construye el paquete que será desplegado en AWS:

```powershell
sam build
```

El proyecto utiliza:

```yaml
CodeUri: src/
```

Esto indica que el contenido de `src/` será empaquetado como código de la función Lambda.

Por ello, los módulos internos se importan directamente, por ejemplo:

```python
from channel_adapter import extraer_parametros
```

Después de una construcción exitosa, SAM genera los artefactos dentro de:

```text
.aws-sam/build/
```

### 4.3 Primer despliegue en AWS

Si es la primera vez que despliegas el proyecto, utiliza el modo guiado:

```powershell
sam deploy --guided
```

Durante este proceso SAM solicitará información como el nombre del stack, región y configuración de permisos.

Como referencia, puedes utilizar:

| Parámetro                            | Valor                 |
| ------------------------------------ | --------------------- |
| Stack Name                           | `citas-medicas-stack` |
| AWS Region                           | `us-east-1`           |
| Confirm changes before deploy        | `Y`                   |
| Allow SAM CLI IAM role creation      | `Y`                   |
| Save arguments to configuration file | `Y`                   |

> **Nota:** `sam deploy --guided` genera un archivo `samconfig.toml` con la configuración del despliegue. Este archivo es específico de tu entorno y está excluido del repositorio mediante `.gitignore`.

Una vez completada la configuración inicial, los siguientes despliegues pueden realizarse simplemente con:

```powershell
sam deploy
```

---

## 5. Cargar Datos Iniciales

Después del despliegue, carga las especialidades iniciales:

```powershell
python scripts/seed_especialidades.py
```

El script carga las especialidades utilizadas por el asistente:

* Medicina general
* Pediatría
* Odontología
* Dermatología
* Oftalmología

---

## 6. Verificar el Despliegue

### 6.1 Consultar los Outputs del Stack

Para consultar los recursos creados por CloudFormation:

```powershell
aws cloudformation describe-stacks `
  --stack-name citas-medicas-stack `
  --query "Stacks[0].Outputs" `
  --output table
```

Entre los outputs se encuentra el ARN de la función Lambda, que posteriormente se utiliza en la integración con Amazon Connect.

### 6.2 Invocar la función Lambda en AWS

Puedes probar directamente la función Lambda desplegada utilizando el evento incluido en el repositorio:

```powershell
aws lambda invoke `
  --function-name citas-medicas-ai-agent `
  --cli-binary-format raw-in-base64-out `
  --payload file://events/evento_connect_disponibilidad.json `
  respuesta.json
```

Después puedes revisar la respuesta:

```powershell
Get-Content respuesta.json
```

El archivo:

```text
events/evento_connect_disponibilidad.json
```

contiene datos ficticios para realizar esta prueba.

---

## 7. Prueba Local del Lambda

Si tienes **Docker Desktop** instalado y ejecutándose, puedes probar la función Lambda localmente:

```powershell
sam local invoke CitasMedicasFunction `
  --event events/evento_connect_disponibilidad.json `
  --region us-east-1
```

Esta opción permite validar cambios localmente antes de realizar un nuevo despliegue.

La ejecución local con Docker es **opcional**. Si `sam local invoke` presenta problemas relacionados con Docker o la red, puedes utilizar `aws lambda invoke` para probar directamente la función desplegada en AWS.

---

## 8. Flujo de Despliegue

El flujo general del backend es:

```text
Código Python
     │
     ▼
Entorno virtual (.venv)
     │
     ▼
Pruebas unitarias
28 tests
     │
     ▼
sam validate
     │
     ▼
sam build
     │
     ▼
sam deploy
     │
     ├── AWS Lambda
     ├── DynamoDB
     └── IAM
     │
     ▼
seed_especialidades.py
     │
     ▼
Backend listo
     │
     ▼
Integración con Amazon Connect
```

Una vez desplegada la infraestructura y cargadas las especialidades, el backend queda preparado para conectarse con el **AI Agent mediante Amazon Connect**.

Para configurar la integración completa con Amazon Connect, Amazon Lex y Amazon Q in Connect, consulta:

[`amazon-connect-setup.md`](amazon-connect-setup.md)

---

## 9. Datos de Prueba y Seguridad

Este proyecto utiliza **datos ficticios** para demostración y pruebas.

No utilizar información real de pacientes ni datos personales en:

* Archivos dentro de `events/`
* Pruebas unitarias
* Logs
* Datos de desarrollo
* Scripts de carga inicial

Las credenciales de AWS tampoco deben almacenarse dentro del repositorio.

---

[← Volver al README principal](../README.md)
