# 📄 PDF-extractext

> API REST para extracción de texto y gestión de documentos PDF, desarrollada con arquitectura de 3 capas y FastAPI.

![Python](https://img.shields.io/badge/Python-3.12+-3776AB?style=flat-square&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.111+-009688?style=flat-square&logo=fastapi&logoColor=white)
![MongoDB](https://img.shields.io/badge/MongoDB-7.0+-47A248?style=flat-square&logo=mongodb&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-compose-2496ED?style=flat-square&logo=docker&logoColor=white)
![UV](https://img.shields.io/badge/UV-package_manager-DE5FE9?style=flat-square)
![License](https://img.shields.io/badge/licencia-MIT-blue?style=flat-square)

---

## 📑 Tabla de Contenidos

- [Descripción](#-descripción)
- [Características](#-características)
- [Arquitectura](#-arquitectura)
- [Tecnologías](#-tecnologías)
- [Endpoints](#-endpoints-de-la-api)
- [Instalación](#-instalación-y-ejecución)
- [Testing](#-testing)
- [Principios aplicados](#-principios-aplicados)
- [Equipo](#-equipo)
- [Licencia](#-licencia)

---

## 📌 Descripción

**PDF-extractext** es una API REST que permite subir archivos PDF, extraer su contenido textual de forma automática y almacenarlo de manera persistente. Los documentos quedan disponibles para consultarse, modificarse o eliminarse a través de endpoints estándar.

El proyecto está desarrollado como trabajo práctico universitario, aplicando arquitectura limpia de 3 capas, metodología TDD y los principios de programación vistos en la materia.

---

## ✨ Características

- 📤 **Subida y procesamiento de PDFs** con validación de formato y tamaño
- 🔍 **Extracción automática de texto** del contenido del PDF
- 🗃️ **Almacenamiento persistente** en MongoDB con metadatos completos
- 🔁 **API RESTful** con los 5 métodos CRUD sobre documentos
- 🏗️ **Arquitectura de 3 capas** (Presentación, Negocio, Datos)
- 🧪 **Desarrollo guiado por tests** (TDD) con cobertura por capa
- ⚙️ **Gestión de configuración** siguiendo los primeros 6 factores de 12-Factor App
- 🐳 **Containerizado con Docker** para ejecución y testing reproducibles

---

## 🏛️ Arquitectura

El proyecto aplica una arquitectura de **3 capas con separación estricta de responsabilidades**. Cada capa solo conoce a la inmediatamente inferior y se comunica a través de interfaces (contratos), lo que garantiza bajo acoplamiento y alta cohesión.

```
┌─────────────────────────────────────────────┐
│           CAPA DE PRESENTACIÓN              │
│   Routers · Controllers · DTOs · Validators │
└──────────────────┬──────────────────────────┘
                   │  interfaces / contratos
┌──────────────────▼──────────────────────────┐
│            CAPA DE NEGOCIO                  │
│  Services · Entities · Domain Logic         │
└──────────────────┬──────────────────────────┘
                   │  interfaces / contratos
┌──────────────────▼──────────────────────────┐
│             CAPA DE DATOS                   │
│   Repositories (MongoDB) · Models · DTOs    │
└─────────────────────────────────────────────┘
```

### Estructura de carpetas

```
pdf-extractext/
├── app/
│   ├── main.py                    # Entrada de la aplicación FastAPI
│   ├── config.py                  # Variables de entorno
│   ├── dependencies.py            # Inyección de dependencias
│   │
│   ├── presentation/
│   │   ├── routers/               # Definición de rutas HTTP
│   │   ├── controllers/           # Orquestación del flujo
│   │   ├── dto/                   # Objetos de transferencia de datos
│   │   └── validators/            # Validación de formato y tamaño
│   │
│   ├── business/
│   │   ├── services/              # Lógica de negocio principal
│   │   ├── entities/              # Entidades del dominio
│   │   ├── domain/                # Extracción, checksum, validaciones
│   │   └── repositories/         # Interfaces de repositorio
│   │
│   └── data/
│       ├── repositories/          # Implementación con MongoDB
│       ├── models/                # Esquemas de persistencia
│       ├── database/              # Conexión y configuración MongoDB
│       └── dto/                   # DTOs internos entre capas
│
├── tests/
│   ├── unit/
│   │   ├── test_presentation/
│   │   ├── test_business/
│   │   └── test_data/
│   └── integration/
│
├── docs/
├── docker-compose.yml             # Stack de producción/desarrollo
├── docker-compose.test.yml        # Stack de testing aislado
├── Dockerfile
├── Dockerfile.test
├── pyproject.toml
└── README.md
```

---

## 🛠️ Tecnologías

| Tecnología | Rol en el proyecto |
|---|---|
| **Python 3.12+** | Lenguaje principal |
| **FastAPI** | Framework web para la API REST |
| **UV** | Gestor de paquetes y entornos virtuales |
| **MongoDB** | Base de datos NoSQL para persistencia |
| **Motor** | Driver asíncrono de MongoDB para Python |
| **Pydantic** | Validación de datos y DTOs |
| **PyMuPDF / pdfplumber** | Extracción de texto de archivos PDF |
| **Docker & Docker Compose** | Containerización y orquestación |
| **pytest + pytest-asyncio** | Framework de testing |

---

## 🔌 Endpoints de la API

Base URL: `http://localhost:8000/api/v1`

| Método | Endpoint | Descripción | Cuerpo (Request) | Respuesta |
|---|---|---|---|---|
| `POST` | `/documents` | Sube un PDF y extrae su texto | `multipart/form-data` con el archivo PDF | Documento creado con texto extraído |
| `GET` | `/documents` | Lista todos los documentos almacenados | — | Array de documentos |
| `GET` | `/documents/{id}` | Obtiene un documento específico por ID | — | Documento con metadatos y texto |
| `PUT` | `/documents/{id}` | Actualiza los metadatos de un documento | JSON con campos a modificar | Documento actualizado |
| `DELETE` | `/documents/{id}` | Elimina un documento del sistema | — | Mensaje de confirmación |
| `GET` | `/documents/{id}/download` | Descarga el texto extraído como archivo `.txt` usando el nombre original del PDF | — | Archivo `.txt` con el contenido de `extracted_text` |

### Ejemplo de respuesta — `POST /documents`

```json
{
  "id": "664f2a1b3e8c1a2b3c4d5e6f",
  "name": "informe-final.pdf",
  "checksum": "a3f1d29e...",
  "extracted_text": "Contenido extraído del documento PDF...",
  "created_at": "2024-05-23T10:30:00",
  "updated_at": "2024-05-23T10:30:00"
}
```

### Descarga del texto extraído — `GET /documents/{id}/download`

Este endpoint permite descargar el texto extraído de un documento como un archivo de texto plano. El archivo descargado conserva el nombre original del PDF, pero con extensión `.txt`.

Ejemplo de uso con `curl`:

```bash
curl -v -o output.txt "http://localhost:8000/api/v1/documents/<DOCUMENT_ID>/download"
```

Respuesta esperada:
- Código HTTP: `200 OK` — archivo adjunto con `Content-Disposition: attachment; filename="original_name.txt"`
- Si el documento no existe: `404 Not Found` con cuerpo en formato ProblemDetail (RFC 9457) incluyendo `type`, `title`, `status`, `detail` e `instance`.


---

## 🚀 Instalación y Ejecución

### Prerrequisitos

- [Docker](https://docs.docker.com/get-docker/) y [Docker Compose](https://docs.docker.com/compose/) instalados

### ⚠️ Permisos en Linux

En Linux, el daemon de Docker requiere permisos especiales. Si al ejecutar `docker compose` aparece un error como:

```
permission denied while trying to connect to the Docker daemon socket at unix:///var/run/docker.sock
```

La solución es agregar tu usuario al grupo `docker` (solo se hace una vez):

```bash
sudo usermod -aG docker $USER
```

Luego aplicá el cambio sin cerrar sesión:

```bash
newgrp docker
```

> En **Windows** con Docker Desktop este problema no aplica: el instalador configura los permisos automáticamente.

---

### Con Docker (recomendado)

**1. Clonar el repositorio**

```bash
git clone https://github.com/tu-usuario/pdf-extractext.git
cd pdf-extractext
```

**2. Configurar variables de entorno**

Crear un archivo `.env` en la raíz del proyecto:

```env
MONGODB_URL=mongodb://mongo:27017
DATABASE_NAME=pdf_extractext
MAX_PDF_SIZE_MB=10
```

**3. Levantar los servicios**

```bash
docker compose up --build
```

Esto levanta la API y MongoDB juntos. La API queda disponible en `http://localhost:8000`.

**4. Acceder a la documentación interactiva**

Abrí en el navegador: [http://localhost:8000/docs](http://localhost:8000/docs)

> Este proyecto es una API backend pura. No incluye frontend ni páginas estáticas.

---

### Sin Docker (alternativa local)

Requiere Python 3.12+, [UV](https://docs.astral.sh/uv/) y MongoDB corriendo localmente.

```bash
# Instalar dependencias
uv sync

# Configurar .env con MongoDB local
echo "MONGODB_URL=mongodb://localhost:27017" > .env
echo "DATABASE_NAME=pdf_extractext" >> .env
echo "MAX_PDF_SIZE_MB=10" >> .env

# Ejecutar la aplicación
uv run fastapi dev app/main.py
```

---

## 🧪 Testing

El proyecto sigue la metodología **TDD**: los tests se escriben antes que el código de producción.
Hay tests unitarios por capa y tests de integración para el flujo completo.

### Con Docker (recomendado)

Levanta un entorno aislado con su propia base de datos de test y ejecuta toda la suite:

```bash
docker compose -f docker-compose.test.yml up --build --abort-on-container-exit
```

### Sin Docker

Los **tests unitarios** no dependen de ningún servicio externo y pueden correrse directamente:

```bash
# Tests unitarios (no requieren MongoDB)
PYTHONPATH=. uv run pytest tests/unit/ -v

# Por capa específica
PYTHONPATH=. uv run pytest tests/unit/test_presentation/
PYTHONPATH=. uv run pytest tests/unit/test_business/
PYTHONPATH=. uv run pytest tests/unit/test_data/

# Con cobertura
PYTHONPATH=. uv run pytest tests/unit/ --cov=app --cov-report=term-missing
```

> ⚠️ Los **tests de integración** requieren MongoDB corriendo. Si querés ejecutarlos
> localmente sin Docker, levantá primero una instancia de MongoDB en `localhost:27017`
> o usá el docker-compose.test.yml que lo hace automáticamente.

> ⚠️ Si al ejecutar `docker compose up` aparece el error `port is already allocated` en el puerto 27017,
> significa que tenés otro contenedor de MongoDB corriendo. Detenelo primero:
> ```bash
> docker rm -f mongo-test
> ```
> Luego volvé a ejecutar `docker compose up --build`.

---

## 📐 Principios aplicados

- **Arquitectura de 3 capas** con separación estricta de responsabilidades
- **TDD** (Test-Driven Development): tests primero, código después
- **12-Factor App** (factores I–VI): codebase, dependencias, configuración, servicios de respaldo, build/run/release, procesos
- **Principios SOLID** aplicados en el diseño de clases y módulos
- **Inyección de dependencias** para desacoplar capas e interfaces

---

## 👥 Equipo

> Completar con los integrantes del grupo.

---

## 📄 Licencia

Este proyecto está bajo la licencia MIT. Ver el archivo [LICENSE](LICENSE) para más detalles.