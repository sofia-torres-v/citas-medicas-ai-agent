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

Si todas las pruebas son exitosas, deberías obtener un resultado similar a:

```text
==================== test session starts ====================

...

==================== 28 passed ====================
```

Estas pruebas permiten validar la lógica de negocio antes de desplegar el backend.

---

## 4. Construcción y Despliegue con AWS SAM

### 4.1 Validar la plantilla SAM

Antes de construir el proyecto, valida la plantilla de infraestructura:

```powershell
sam validate
```

### 4.2 Compilar el proyecto

Construye el paquete que será desplegado en AWS:

```powershell
sam build
```

### 4.3 Desplegar en AWS

La primera vez se recomienda utilizar el modo guiado:

```powershell
sam deploy --guided
```

Durante el proceso puedes utilizar los siguientes valores como referencia:

| Parámetro                            | Valor sugerido        |
| ------------------------------------ | --------------------- |
| Stack Name                           | `citas-medicas-stack` |
| AWS Region                           | `us-east-1`           |
| Confirm changes before deploy        | `Y`                   |
| Allow SAM CLI IAM role creation      | `Y`                   |
| Save arguments to configuration file | `Y`                   |

> **Nota:** `sam deploy --guided` puede generar un archivo `samconfig.toml` con la configuración del despliegue. Este archivo es específico de tu entorno y no es necesario para reproducir el proyecto.

Una vez completada la configuración inicial, los siguientes despliegues pueden realizarse con:

```powershell
sam deploy
```

---

## 5. Carga de Datos Iniciales

La tabla de DynamoDB `citas-medicas-especialidades` se crea inicialmente vacía.

Para cargar las **5 especialidades iniciales**, ejecuta:

```powershell
python scripts/seed_especialidades.py
```

El script inserta los datos necesarios para que el agente pueda consultar las especialidades disponibles.

---

## 6. Verificación del Despliegue

### 6.1 Consultar los Outputs del Stack

Para consultar información de los recursos creados por CloudFormation:

```powershell
aws cloudformation describe-stacks --stack-name citas-medicas-stack --query "Stacks[0].Outputs" --output table
```

Esto permite verificar los outputs definidos en la plantilla SAM.

### 6.2 Invocar la función Lambda en AWS

Puedes probar directamente la función Lambda desplegada utilizando uno de los eventos de prueba incluidos en el repositorio:

```powershell
aws lambda invoke `
  --function-name citas-medicas-ai-agent `
  --cli-binary-format raw-in-base64-out `
  --payload file://events/evento_connect_disponibilidad.json `
  respuesta.json
```

Luego puedes revisar la respuesta:

```powershell
Get-Content respuesta.json
```

> Los archivos dentro de `events/` utilizan datos ficticios para las pruebas y no deben contener información real de pacientes.

---

## 7. Prueba Local del Lambda

Si tienes **Docker Desktop** instalado y ejecutándose, puedes probar la función Lambda localmente sin desplegarla nuevamente en AWS:

```powershell
sam local invoke CitasMedicasFunction `
  --event events/evento_connect_disponibilidad.json `
  --region us-east-1
```

Esta opción es útil para validar cambios durante el desarrollo antes de realizar un nuevo despliegue.

---

## Flujo de Despliegue

El flujo general del backend es:

```text
Código Python
     │
     ▼
Entorno virtual (.venv)
     │
     ▼
Pruebas unitarias
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
     ├── Lambda
     ├── DynamoDB
     └── IAM / Recursos AWS
```

Una vez desplegada la infraestructura y cargadas las especialidades, el backend queda preparado para ser integrado con **Amazon Connect**.

---

[← Volver al README principal](../README.md)
