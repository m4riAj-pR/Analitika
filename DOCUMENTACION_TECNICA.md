# Documentación Técnica — Analitika Backend API

> **Proyecto:** Analitika CRUD (Backend)  
> **Repositorio:** [github.com/m4riAj-pR/Analitika](https://github.com/m4riAj-pR/Analitika)  
> **Stack:** Python 3.12 · FastAPI · MySQL (PyMySQL) · Railway  
> **Última actualización:** 20 de mayo de 2026

---

## Tabla de Contenidos

1. [Uso de Repositorios y Control de Versiones](#1-uso-de-repositorios-y-control-de-versiones)
2. [Criterio de Separación de Módulos](#2-criterio-de-separación-de-módulos)
3. [Reuso de Componentes](#3-reuso-de-componentes)
4. [Lógica de Presentación](#4-lógica-de-presentación)
5. [Estrategias de Código Aplicadas](#5-estrategias-de-código-aplicadas)

---

## 1. Uso de Repositorios y Control de Versiones

### 1.1 Plataforma y Repositorio

| Aspecto | Detalle |
|---|---|
| **Plataforma** | GitHub |
| **Repositorio remoto** | `https://github.com/m4riAj-pR/Analitika.git` |
| **VCS** | Git |
| **Hosting de producción** | Railway (PaaS) |

### 1.2 Estrategia de Ramas

```
main (rama principal — producción)
├── cambios-santiago          (rama de feature/desarrollador)
└── railway/fix-deploy-d8d47e (rama de hotfix de despliegue)
```

- **`main`**: Rama principal y de producción. Railway despliega automáticamente desde esta rama.
- **`cambios-santiago`**: Rama de feature para cambios del desarrollador Santiago, siguiendo un flujo básico de feature branching.
- **`railway/fix-deploy-d8d47e`**: Rama generada por Railway para correcciones de despliegue urgentes (hotfix).

### 1.3 Historial de Commits

El proyecto cuenta con **~70 commits** que documentan la evolución del sistema. Los mensajes siguen un estilo descriptivo en inglés/español mixto:

```
13d38de  Update routs.py
391b22f  Add technical docs and filter tracking links
c1d054b  Add campaign budget, alerts and CSV export
592004c  Role-aware access, /me endpoint, migration script
6213b3c  Add admin router and role migration
a8c3653  Add multi-company support and DB schema updates
1d85254  feat: add public /register endpoint with bcrypt hashing
537f8ae  estructrua base para backend
ba5bb63  Initial commit
```

### 1.4 Archivos Ignorados (`.gitignore`)

```
.venv/          # Entorno virtual de Python
__pycache__/    # Cache de bytecode
*.pyc           # Bytecode compilado
.env            # Variables de entorno (secretos)
*.log           # Archivos de log
```

### 1.5 Despliegue Continuo

El despliegue se realiza mediante **Railway**, configurado en `railway.json`:

```json
{
  "deploy": {
    "startCommand": "uvicorn app.main:app --host 0.0.0.0 --port $PORT"
  }
}
```

Railway detecta automáticamente `requirements.txt` y construye el entorno Python.

---

## 2. Criterio de Separación de Módulos

### 2.1 Arquitectura General

La aplicación sigue una **arquitectura en capas** (Layered Architecture) con separación clara de responsabilidades:

```
analitika_CRUD/
├── app/                          # Paquete principal de la aplicación
│   ├── __init__.py               # Inicialización (carga .env)
│   ├── main.py                   # Punto de entrada FastAPI
│   ├── config.py                 # Gestión de configuración
│   ├── security.py               # Autenticación y autorización JWT
│   ├── routers/                  # Capa de Controladores (endpoints)
│   │   ├── routs.py              # CRUD principal (12 entidades)
│   │   ├── auth.py               # Autenticación (login/register)
│   │   ├── tracking.py           # Tracking de clics y analytics
│   │   ├── notifications.py      # Notificaciones del usuario
│   │   └── admin.py              # Panel de administración
│   ├── schemas/                  # Capa de Validación (DTOs Pydantic)
│   │   ├── auth.py               # LoginRequest, RegisterRequest, TokenResponse
│   │   ├── campaigns.py          # Campaign + CampaignStatus enum
│   │   ├── clicks.py             # Click (con campos UTM)
│   │   ├── conversions.py        # Conversion + ConversionType enum
│   │   ├── notifications.py      # NotificationBase/Create/Public
│   │   ├── persons.py            # Person
│   │   ├── users.py              # User
│   │   ├── companies.py          # Company
│   │   ├── channels.py           # Channel
│   │   ├── tracking_links.py     # TrackingLink
│   │   ├── role.py               # Role
│   │   ├── permissions.py        # Permission
│   │   ├── role_has_permissions.py
│   │   └── user_company.py       # UserCompany (tabla intermedia)
│   ├── services/                 # Capa de Lógica de Negocio
│   │   ├── a_service.py          # Servicio centralizado (~1021 líneas)
│   │   └── email_service.py      # Servicio de correo (SendGrid API)
│   ├── db/                       # Capa de Acceso a Datos
│   │   ├── database.py           # Conexión MySQL y función run_query()
│   │   └── migrations.py         # Migraciones automáticas al inicio
│   ├── templates/                # Plantillas HTML (Jinja2)
│   │   └── campana.html          # Landing page de campañas
│   └── static/                   # Archivos estáticos
│       └── styles.css            # Estilos CSS base
├── scripts/                      # Scripts de mantenimiento
│   └── migrations/
│       ├── migrate_roles.py      # Migración de roles
│       └── migrate_utm.py        # Migración de campos UTM
├── init.sql                      # Script DDL de la base de datos
├── requirements.txt              # Dependencias Python
├── railway.json                  # Configuración de despliegue
└── .env                          # Variables de entorno (excluido de Git)
```

### 2.2 Criterio por Capa

| Capa | Directorio | Responsabilidad |
|---|---|---|
| **Controladores** | `routers/` | Recibir peticiones HTTP, validar permisos básicos, delegar a servicios |
| **Schemas** | `schemas/` | Validación de entrada/salida con Pydantic (DTOs) |
| **Servicios** | `services/` | Lógica de negocio, operaciones CRUD, autorización granular |
| **Base de Datos** | `db/` | Conexión raw SQL (PyMySQL), migraciones |
| **Seguridad** | `security.py` | JWT, hashing de contraseñas, middleware de autenticación |
| **Configuración** | `config.py` | Carga de `.env`, validación de variables obligatorias |
| **Presentación** | `templates/` + `static/` | Landing page HTML para campañas (Jinja2) |

### 2.3 Separación de Routers por Dominio

Cada router agrupa endpoints por **dominio funcional**:

| Router | Prefijo | Responsabilidad | Autenticación |
|---|---|---|---|
| `routs.py` | `/analitika` | CRUD completo de las 12 entidades + analytics | JWT requerido |
| `auth.py` | `/` (raíz) | Login, registro, `/me`, recuperación de contraseña | Mixto (público + JWT) |
| `tracking.py` | `/` (raíz) | Landing de campaña, registro de clics, métricas | Mixto |
| `notifications.py` | `/analitika/notifications` | Gestión de notificaciones del usuario | JWT requerido |
| `admin.py` | `/analitika/admin` | Panel Super Admin (empresas, roles) | JWT + rol Super_Admin |

### 2.4 Modelo de Base de Datos

El esquema relacional consta de **11 tablas** definidas en `init.sql`:

**Tablas principales:** `persons`, `roles`, `permissions`, `role_has_permissions`, `users`, `companies`, `user_company`, `campaigns`, `channels`, `tracking_links`, `clicks`, `conversions`, `notifications`

**Relaciones clave:**
- `persons → users` (1:N): Una persona puede tener un usuario
- `users ↔ companies` (N:M via `user_company`): Relación multi-empresa
- `companies → campaigns` (1:N): Una empresa tiene múltiples campañas
- `campaigns → tracking_links` (1:1): Cada campaña tiene un link de tracking
- `tracking_links → clicks` (1:N): Un link genera múltiples clics
- `clicks → conversions` (1:N): Un clic puede generar conversiones

**Roles del sistema** (IDs fijos):

| ID | Rol | Permisos |
|---|---|---|
| 1 | `Super_Admin` | Acceso total a todas las empresas y datos |
| 2 | `Owner` | CRUD completo sobre su(s) empresa(s) |
| 3 | `Manager` | Solo lectura + creación limitada (no puede editar ni eliminar) |

---

## 3. Reuso de Componentes

### 3.1 Función Centralizada `run_query()`

Toda interacción con la base de datos pasa por una **única función reutilizable** en `db/database.py`:

```python
def run_query(sql, params=None, fetch=False, return_lastrowid=False):
```

- Abre conexión, ejecuta, commit y cierra (patrón per-request)
- Soporta `fetch=True` para SELECT y `return_lastrowid=True` para INSERT
- Manejo centralizado de rollback en caso de error

### 3.2 Helpers de Autorización Reutilizables

El servicio define una **cadena de funciones `ensure_*_access()`** que se reusan en todos los routers:

```
ensure_company_access()        ← Base de la cadena
    ↑
ensure_campaign_access()       ← Verifica campaña → delega a company
    ↑
ensure_tracking_link_access()  ← Verifica link → delega a campaign
    ↑
ensure_click_access()          ← Verifica click → delega a tracking_link
    ↑
ensure_conversion_access()     ← Verifica conversión → delega a click
```

Cada función resuelve la **propiedad transitiva** de acceso: un usuario tiene acceso a un recurso si pertenece a la empresa que lo contiene, siguiendo la cadena relacional de la BD.

Funciones auxiliares compartidas:
- `get_user_company_ids()` — Obtiene todas las empresas de un usuario
- `build_in_clause()` — Genera cláusulas `IN (...)` parametrizadas
- `read_table_for_user()` — Lectura genérica filtrada por empresa/rol
- `read_table()` — Lectura sin filtro (para tablas globales)

### 3.3 Schemas Pydantic Reutilizados

Los schemas se usan tanto para **validación de entrada** (request body) como para **tipado de respuesta**:

- `LoginRequest` se reutiliza como base de `RegisterRequest` (herencia).
- `CampaignStatus` y `ConversionType` son enums compartidos entre schemas y lógica de negocio.
- `NotificationBase → NotificationCreate → NotificationPublic` siguen un patrón de herencia jerárquica.

### 3.4 Seguridad Reutilizable

El módulo `security.py` expone funciones usadas en múltiples routers:

| Función | Uso |
|---|---|
| `get_current_user()` | Dependencia FastAPI (`Depends()`) inyectada en todos los endpoints protegidos |
| `hash_password()` | Registro, creación de usuario, reset de contraseña |
| `verify_and_upgrade_password()` | Login (soporta migración transparente de MD5/texto plano a bcrypt) |
| `create_access_token()` | Login + Registro |

### 3.5 Patrón CRUD Uniforme

Todas las entidades siguen el **mismo patrón de funciones** en el servicio:

```
insert_{entidad}()           → CREATE
update_{entidad}_service()   → UPDATE
delete_{entidad}_service()   → DELETE (con validación de dependencias)
```

Y en el router:

```
POST   /analitika/{entidad}      → create
GET    /analitika/{entidad}      → list (filtrado por empresa/rol)
PUT    /analitika/{entidad}/{id} → update
DELETE /analitika/{entidad}/{id} → delete
```

---

## 4. Lógica de Presentación

### 4.1 API REST como Capa Principal

La aplicación es principalmente una **API REST** que sirve JSON. La presentación se delega al frontend móvil (React Native / Expo). El backend solo genera HTML en un caso específico:

### 4.2 Landing Page de Campañas (Server-Side Rendering)

El endpoint `GET /c/{id_link}` renderiza una **landing page HTML** usando Jinja2:

```python
env = Environment(loader=FileSystemLoader("app/templates"))
template = env.get_template("campana.html")
html = template.render(nombre=..., descripcion=..., id_click=...)
return HTMLResponse(content=html)
```

La landing page (`campana.html`):
- **Tema claro** con tipografía Outfit (Google Fonts)
- Botón de conversión one-click que envía un `POST /conversion/public`
- Animaciones CSS (`fadeIn`, `scaleUp`) para UX fluida
- Diseño responsive (max-width 480px)
- Variables CSS para consistencia visual (`--primary: #6366f1`)

### 4.3 Respuestas JSON Estandarizadas

Las respuestas del API siguen patrones consistentes:

```python
# Operaciones exitosas
{"ok": True}
{"ok": True, "id_campaign": 42}

# Autenticación
{"access_token": "...", "token_type": "bearer", "user": {...}}

# Errores
{"detail": "Mensaje descriptivo del error"}
```

### 4.4 Templates de Email (HTML Inline)

El servicio de email genera **correos HTML con estilos inline** para compatibilidad con clientes de correo:

- **Email de bienvenida** — Branding Analitika con CTA al dashboard
- **Email de recuperación** — Clave temporal con diseño prominente

Ambos usan la paleta `#6366f1` (indigo) como color primario de marca.

---

## 5. Estrategias de Código Aplicadas

### 5.1 Nomenclatura y Convenciones

| Elemento | Convención | Ejemplo |
|---|---|---|
| **Archivos Python** | `snake_case` | `email_service.py`, `a_service.py` |
| **Funciones** | `snake_case` descriptivo | `ensure_campaign_access()`, `get_user_company_ids()` |
| **Clases (schemas)** | `PascalCase` | `LoginRequest`, `CampaignStatus` |
| **Variables** | `snake_case` | `id_user`, `company_ids`, `temp_pass` |
| **Tablas BD** | `snake_case` plural | `persons`, `tracking_links`, `role_has_permissions` |
| **Columnas BD** | `snake_case` con prefijo `id_` | `id_campaign`, `password_hash`, `clicked_at` |
| **URLs del API** | `kebab-case` | `/tracking-links`, `/role-permissions`, `/user-company` |
| **Prefijos de rutas** | Agrupados por dominio | `/analitika/*`, `/analitika/admin/*` |

### 5.2 Gestión de Configuración

Estrategia de carga de entorno con **doble protección**:

1. `config.py` → `load_env_file()` lee el `.env` solo en desarrollo (idempotente con flag `_ENV_LOADED`)
2. `__init__.py` y `main.py` invocan `load_env_file()` antes de cualquier importación
3. Railway inyecta variables en producción sin necesidad de `.env`
4. `validate_environment()` valida al arranque que `JWT_SECRET` y `DATABASE_URL` existan

Variables de entorno utilizadas:

| Variable | Obligatoria | Descripción |
|---|---|---|
| `DATABASE_URL` | Sí | URL de conexión MySQL |
| `JWT_SECRET` | Sí | Clave para firmar tokens JWT |
| `JWT_ALGORITHM` | No | Algoritmo JWT (default: `HS256`) |
| `JWT_EXPIRE_MINUTES` | No | Expiración del token (default: `1440` min = 24h) |
| `CORS_ALLOW_ORIGINS` | No | Orígenes permitidos (default: `*`) |
| `SENDGRID_API_KEY` | No | Clave API de SendGrid para emails |
| `SENDGRID_FROM` | No | Email remitente |

### 5.3 Seguridad y Autenticación

**Estrategia de autenticación JWT con migración de hashes:**

```
Login → Verificar credenciales → ¿Hash bcrypt? → verify_password()
                                → ¿Hash MD5?    → Comparar → Migrar a bcrypt
                                → ¿Texto plano? → Comparar → Migrar a bcrypt
```

- Todos los endpoints protegidos usan `Depends(get_current_user)` como inyección de dependencias.
- La migración de contraseñas es **transparente**: el usuario no nota el cambio.
- El endpoint `/forgot-password` genera una contraseña temporal aleatoria de 8 caracteres.

**Control de acceso basado en roles (RBAC):**

```python
# Patrón usado en todos los endpoints destructivos
if current_user["id_role"] == 3:  # Manager
    raise HTTPException(status_code=403, detail="Permiso denegado")
```

### 5.4 Manejo de Errores

Estrategia consistente en tres niveles:

1. **Nivel Router** — Validación de permisos y parámetros con `HTTPException`
2. **Nivel Servicio** — Captura de `IntegrityError` de PyMySQL → HTTP 400
3. **Nivel Base de Datos** — Rollback automático en `run_query()` + cierre de conexión en `finally`

```python
# Patrón de validación de dependencias antes de eliminar
def delete_campaign_service(id_campaign):
    result_links = run_query("SELECT COUNT(*) ...", fetch=True)
    if result_links[0]['total'] > 0:
        raise HTTPException(status_code=400, 
            detail="No se puede eliminar: tiene tracking links asociados.")
    run_query("DELETE FROM campaigns WHERE ...", (id_campaign,))
```

### 5.5 Migraciones de Base de Datos

Se emplean **dos estrategias complementarias**:

| Estrategia | Ubicación | Ejecución |
|---|---|---|
| **Migraciones automáticas** | `db/migrations.py` | Al arranque de la app (`@app.on_event("startup")`) |
| **Scripts manuales** | `scripts/migrations/` | Ejecutados manualmente por el desarrollador |

Las migraciones automáticas verifican con `SHOW COLUMNS` antes de aplicar `ALTER TABLE`, garantizando **idempotencia**.

### 5.6 Motor de Análisis Inteligente

El servicio incluye un **motor de recomendaciones automáticas** (`generate_auto_recommendations()`) que analiza campañas activas y genera notificaciones basadas en umbrales:

| Métrica | Niveles | Acción |
|---|---|---|
| **ROI** | Crítico / Bajo / Aceptable / Bueno / Excelente | Alertas + recomendaciones de optimización |
| **CPC** | Crítico (>$3000) / Alto / Aceptable / Eficiente | Sugerencias de segmentación |
| **Tasa de Conversión** | Crítico (<1%) / Bajo / Aceptable / Bueno / Excelente | Recomendaciones de landing page |
| **Crecimiento semanal** | Estancado / Lento / Saludable | Alertas de tendencia |
| **Presupuesto** | 80% consumido / 100% agotado | Alertas de budget |

Las notificaciones son **deduplicadas** por ventana de 24 horas para evitar spam.

### 5.7 Procesamiento Asíncrono

Tareas no críticas se ejecutan en **background** con `BackgroundTasks` de FastAPI:

- Geolocalización de IP al registrar clics (API externa `ip-api.com`)
- Envío de emails de bienvenida y recuperación de contraseña (SendGrid API)

### 5.8 Dependencias del Proyecto

```
fastapi==0.135.1       # Framework web
uvicorn==0.41.0        # Servidor ASGI
pydantic==2.12.5       # Validación de datos
pymysql==1.1.2         # Conector MySQL
python-jose[crypto]    # Tokens JWT
passlib[bcrypt]        # Hashing de contraseñas
bcrypt==4.0.1          # Backend de passlib
jinja2==3.1.6          # Templates HTML
starlette==0.52.1      # Base de FastAPI
```

> **Nota:** No se utiliza ORM (como SQLAlchemy). Todas las consultas son **SQL raw parametrizado** ejecutadas a través de `run_query()`, lo que otorga control total sobre las queries y mejor rendimiento en operaciones simples.
