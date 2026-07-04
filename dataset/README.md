# KSP Sentinel AI - Backend Operations Engine

This is the production-grade Python FastAPI backend foundation for **KSP Sentinel AI** (Karnataka State Police Intelligence Investigation Co-pilot).

## Architecture Layout

```
backend/
├── app/
│   ├── api/
│   │   └── routes/
│   │       ├── health.py     # System and Database health checks
│   │       ├── cases.py      # FIR cases (Stubs)
│   │       ├── accused.py    # Suspect biometrics dossiers (Stubs)
│   │       ├── reports.py    # Intelligence reports export (Stubs)
│   │       └── chat.py       # AI investigation query endpoints (Stubs)
│   ├── core/
│   │   └── config.py         # Pydantic v2 Environment settings
│   ├── database/
│   │   └── connection.py     # SQLAlchemy 2.0 DB Engine and session lifecycle
│   ├── models/               # Placeholders for SQLAlchemy models
│   ├── schemas/              # Placeholders for Pydantic validation schemas
│   ├── services/             # Placeholders for business logic services
│   ├── utils/                # Placeholders for utility functions
│   └── main.py               # Application entry point & custom middleware
├── requirements.txt          # Python packaging list
├── .env.example              # Variables blueprint
└── README.md                 # Setup documentation
```

## Features

- **FastAPI Framework**: High performance web framework with automatic OpenAPI and Swagger UI generation at `/docs`.
- **SQLAlchemy 2.0**: Setup database engines using custom connection pooling (pre-ping enabled for connection stability checks) and dynamic session managers.
- **Pydantic v2 Settings**: Safe parsing of environment configuration variables through Pydantic models.
- **Structured Error Handling**: Unified interception of validation exceptions (`RequestValidationError`) and server errors via customized Starlette exception handlers to hide runtime stack traces from front-end users.
- **Logging Setup**: Formatted debug/info streaming outputs to stdout/stderr.
- **Cross-Origin Resource Sharing (CORS)**: Configurable origins via `BACKEND_CORS_ORIGINS` to allow communication with frontend servers (e.g. Vite, React).

## Getting Started

### 1. Requirements
Ensure you have **Python 3.12+** and a running **PostgreSQL** instance.

### 2. Installation
Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

Install requirements:
```bash
pip install -r requirements.txt
```

### 3. Environment Setup
Copy the example environment settings file and customize the credentials to match your local database instance:
```bash
cp .env.example .env
```

### 4. Running the application
Start the development server with hot-reload enabled:
```bash
# From within the backend directory:
PYTHONPATH=. python app/main.py
# Or using uvicorn directly:
uvicorn app.main:app --reload
```

The service will boot at `http://127.0.0.1:8000`. You can access the API documentation at `http://127.0.0.1:8000/docs`.
