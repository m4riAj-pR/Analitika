-- =====================
-- PERSONS
-- =====================
CREATE TABLE persons (
    id_person INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    lastname VARCHAR(100),
    email VARCHAR(150) NOT NULL UNIQUE,
    phone VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- =====================
-- ROLES
-- =====================
CREATE TABLE roles (
    id_role INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- =====================
-- PERMISSIONS
-- =====================
CREATE TABLE permissions (
    id_permission INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE,
    description VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- =====================
-- ROLE_HAS_PERMISSIONS
-- =====================
CREATE TABLE role_has_permissions (
    id_role_permission INT AUTO_INCREMENT PRIMARY KEY,
    id_role INT NOT NULL,
    id_permission INT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE(id_role, id_permission),
    FOREIGN KEY (id_role) REFERENCES roles(id_role),
    FOREIGN KEY (id_permission) REFERENCES permissions(id_permission)
);

-- =====================
-- USERS
-- =====================
CREATE TABLE users (
    id_user INT AUTO_INCREMENT PRIMARY KEY,
    id_person INT NOT NULL,
    id_role INT NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (id_person) REFERENCES persons(id_person),
    FOREIGN KEY (id_role) REFERENCES roles(id_role)
);

-- =====================
-- COMPANIES
-- =====================
CREATE TABLE companies (
    id_company INT AUTO_INCREMENT PRIMARY KEY,
    id_user INT NULL,
    name VARCHAR(150) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (id_user) REFERENCES users(id_user)
);

-- =====================
-- USER_COMPANY (relación principal)
-- =====================
CREATE TABLE user_company (
    id_user_company INT AUTO_INCREMENT PRIMARY KEY,
    id_user INT NOT NULL,
    id_company INT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE(id_user, id_company),
    FOREIGN KEY (id_user) REFERENCES users(id_user),
    FOREIGN KEY (id_company) REFERENCES companies(id_company)
);

-- =====================
-- CHANNELS
-- =====================
CREATE TABLE channels (
    id_channel INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(150) NOT NULL,
    description VARCHAR(255),
    id_campaign INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,Corrige un bug crítico en un backend FastAPI relacionado con la variable de entorno JWT_SECRET.

CONTEXTO:
El proyecto usa autenticación JWT (python-jose). Actualmente, SECRET_KEY se obtiene con:

    SECRET_KEY = os.getenv("JWT_SECRET")

Problema:
Si JWT_SECRET no está definida en Railway (o entorno local), su valor es None.
Esto provoca errores 500 en runtime al intentar:
- crear tokens (create_access_token)
- validar tokens (jwt.decode)

El error es silencioso y difícil de diagnosticar.

OBJETIVO:
1. Validar que JWT_SECRET exista al arrancar el servidor
2. Fallar inmediatamente con un error claro si no está definida
3. Evitar que el sistema arranque en estado inválido

IMPLEMENTACIÓN REQUERIDA:

1) En app/main.py:

- Agregar un evento @app.on_event("startup")
- Dentro del evento:
    - verificar os.getenv("JWT_SECRET")
    - si no existe → lanzar RuntimeError con mensaje claro

Ejemplo esperado:

    import os
    from fastapi import FastAPI

    app = FastAPI()

    @app.on_event("startup")
    def validate_env():
        if not os.getenv("JWT_SECRET"):
            raise RuntimeError("JWT_SECRET no configurada en variables de entorno")

2) En app/security.py:

- Asegurar que SECRET_KEY se define así:

    SECRET_KEY = os.getenv("JWT_SECRET")

- Opcional: agregar validación defensiva adicional:

    if not SECRET_KEY:
        raise RuntimeError("JWT_SECRET no configurada")

3) NO cambiar la lógica de generación de tokens existente
4) NO hardcodear valores
5) Mantener compatibilidad con Railway (variables de entorno)

EXTRA (opcional pero recomendado):
- Validar también DATABASE_URL en el mismo startup
- Mensaje claro para debugging en producción

Archivos a modificar:
- app/main.py
- app/security.py

Resultado esperado:
- Si JWT_SECRET no existe → el servidor NO arranca
- Si existe → el sistema funciona normalmente
- Se elimina el error 500 silencioso en /login

No expliques nada, solo aplica los cambios y muestra el código final.
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (id_campaign) REFERENCES campaigns(id_campaign)
);

-- =====================
-- CAMPAIGNS
-- =====================
CREATE TABLE campaigns (
    id_campaign INT AUTO_INCREMENT PRIMARY KEY,
    id_company INT NOT NULL,
    name VARCHAR(150) NOT NULL,
    description VARCHAR(255),
    status ENUM('draft','active','paused','finished') DEFAULT 'draft',
    start_date DATE,
    end_date DATE,
    spent DECIMAL(10,2) NOT NULL DEFAULT 0.00,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CHECK (start_date IS NULL OR end_date IS NULL OR start_date <= end_date),
    FOREIGN KEY (id_company) REFERENCES companies(id_company),
    INDEX idx_id_company (id_company)
);

-- =====================
-- TRACKING LINKS
-- =====================
CREATE TABLE tracking_links (
    id_link INT AUTO_INCREMENT PRIMARY KEY,
    id_campaign INT NOT NULL,
    destination TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (id_campaign) REFERENCES campaigns(id_campaign)
);

-- =====================
-- CLICKS
-- =====================
CREATE TABLE clicks (
    id_click INT AUTO_INCREMENT PRIMARY KEY,
    id_link INT NOT NULL,
    ip_address_hash VARCHAR(64),
    consent_given BOOLEAN DEFAULT FALSE,
    user_agent TEXT,
    referrer TEXT,
    country VARCHAR(50),
    clicked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_id_link (id_link),
    INDEX idx_clicked_at (clicked_at),
    FOREIGN KEY (id_link) REFERENCES tracking_links(id_link)
);

-- =====================
-- CONVERSIONS
-- =====================
CREATE TABLE conversions (
    id_conversion INT AUTO_INCREMENT PRIMARY KEY,
    id_click INT NOT NULL,
    revenue DECIMAL(10,2),
    type ENUM('sale','lead','signup','download','contact','other') NOT NULL DEFAULT 'other',
    source VARCHAR(100),
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_id_click (id_click),
    FOREIGN KEY (id_click) REFERENCES clicks(id_click)
);

