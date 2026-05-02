# 📄 PDF-extractext

> API REST para extracción de texto y gestión de documentos PDF, desarrollada con arquitectura de 3 capas y FastAPI.

![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=flat-square&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.111+-009688?style=flat-square&logo=fastapi&logoColor=white)
![MongoDB](https://img.shields.io/badge/MongoDB-7.0+-47A248?style=flat-square&logo=mongodb&logoColor=white)
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
├── pyproject.toml
└── README.md
```

---

## 🛠️ Tecnologías

| Tecnología | Rol en el proyecto |
|---|---|
| **Python 3.11+** | Lenguaje principal |
| **FastAPI** | Framework web para la API REST |
| **UV** | Gestor de paquetes y entornos virtuales |
| **MongoDB** | Base de datos NoSQL para persistencia |
| **Motor** | Driver asíncrono de MongoDB para Python |
| **Pydantic** | Validación de datos y DTOs |
| **PyMuPDF / pdfplumber** | Extracción de texto de archivos PDF |
| **Modelo de IA** | Generación de resúmenes *(por definir)* |
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

---

## 🚀 Instalación y Ejecución

### Prerrequisitos

- Python 3.11 o superior
- [UV](https://docs.astral.sh/uv/) instalado
- MongoDB corriendo localmente o una URI de MongoDB Atlas

### Pasos

**1. Clonar el repositorio**

```bash
git clone https://github.com/tu-usuario/pdf-extractext.git
cd pdf-extractext
```

**2. Instalar dependencias con UV**

```bash
uv sync
```

**3. Configurar variables de entorno**

Crear un archivo `.env` en la raíz del proyecto:

```env
MONGODB_URL=mongodb://localhost:27017
DATABASE_NAME=pdf_extractext
MAX_PDF_SIZE_MB=10
```

**4. Ejecutar la aplicación**

```bash
uv run fastapi dev app/main.py
```

**5. Acceder a la documentación interactiva**

Abrí en el navegador: [http://localhost:8000/docs](http://localhost:8000/docs)

**Como acceder el frontend:

Abrir una segunda terminal y ejecutar:
cd frontend
python3 -m http.server 5500

Luego abrí en el navegador: [http://localhost:5500] (http://localhost:5500)
---

## 🧪 Testing

El proyecto sigue la metodología **TDD**: los tests se escriben antes que el código de producción. Hay tests unitarios por capa y tests de integración para el flujo completo.

**Ejecutar todos los tests:**

```bash
uv run pytest
```

**Ejecutar tests de una capa específica:**

```bash
uv run pytest tests/unit/test_presentation/
uv run pytest tests/unit/test_business/
uv run pytest tests/unit/test_data/
```

**Ver cobertura:**

```bash
uv run pytest --cov=app --cov-report=term-missing
```

---

## 📐 Principios Aplicados

### Metodologías

- **TDD** — Los tests se escriben antes del código de producción
- **GitHub Flow** — Ramas por feature, Pull Requests con revisión entre pares
- **12-Factor App** — Se aplican los primeros 6 factores (codebase, dependencias, configuración, servicios de respaldo, build/run/release, procesos)

### Principios de Programación

- **KISS** *(Keep It Simple, Stupid)* — Soluciones simples y directas, sin complejidad innecesaria
- **DRY** *(Don't Repeat Yourself)* — Sin duplicación de lógica ni código
- **YAGNI** *(You Aren't Gonna Need It)* — Solo se implementa lo que se necesita ahora
- **SOLID** — Especialmente SRP (una responsabilidad por clase) y DIP (dependencias hacia abstracciones)

### Arquitectura

- **Clean Architecture** — Separación estricta de responsabilidades entre capas
- **Dependency Injection** — Las dependencias se inyectan, no se instancian internamente
- **Interface Segregation** — Las capas se comunican a través de contratos (interfaces), no implementaciones concretas

---

## 👥 Equipo

Proyecto desarrollado como trabajo práctico universitario.

| Apellido y Nombre | Capa | GitHub |
|---|---|---|
| Piasterlini, Luciana Camila | Presentación | [@luciana208](https://github.com/luciana208) |
| Flores, Fabio Javier | Negocio | [@fabjav](https://github.com/fabjav) |
| Roa, Celina Juana Esmeralda | Datos | [@LinaJER](https://github.com/LinaJER) |
