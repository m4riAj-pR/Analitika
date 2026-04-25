-- =====================
-- PERSONS
-- =====================
CREATE TABLE persons (
    id_person INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100),
    lastname VARCHAR(100),
    email VARCHAR(150) UNIQUE,
    phone VARCHAR(50)
);

-- =====================
-- ROLES
-- =====================
CREATE TABLE roles (
    id_role INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100)
);

-- =====================
-- PERMISSIONS
-- =====================
CREATE TABLE permissions (
    id_permission INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100),
    description VARCHAR(255)
);

-- =====================
-- ROLE_HAS_PERMISSIONS
-- =====================
CREATE TABLE role_has_permissions (
    id_role_permission INT AUTO_INCREMENT PRIMARY KEY,
    id_role INT,
    id_permission INT,
    FOREIGN KEY (id_role) REFERENCES roles(id_role),
    FOREIGN KEY (id_permission) REFERENCES permissions(id_permission)
);

-- =====================
-- USERS
-- =====================
CREATE TABLE users (
    id_user INT AUTO_INCREMENT PRIMARY KEY,
    id_person INT,
    id_company INT NULL, -- legacy
    id_role INT,
    password_hash VARCHAR(255),
    FOREIGN KEY (id_person) REFERENCES persons(id_person),
    FOREIGN KEY (id_role) REFERENCES roles(id_role)
);

-- =====================
-- COMPANIES
-- =====================
CREATE TABLE companies (
    id_company INT AUTO_INCREMENT PRIMARY KEY,
    id_user INT NULL, -- legacy creator
    name VARCHAR(150),
    FOREIGN KEY (id_user) REFERENCES users(id_user)
);

-- =====================
-- USER_COMPANY (relación principal)
-- =====================
CREATE TABLE user_company (
    id_user_company INT AUTO_INCREMENT PRIMARY KEY,
    id_user INT,
    id_company INT,
    FOREIGN KEY (id_user) REFERENCES users(id_user),
    FOREIGN KEY (id_company) REFERENCES companies(id_company)
);

-- =====================
-- CAMPAIGNS
-- =====================
CREATE TABLE campaigns (
    id_campaign INT AUTO_INCREMENT PRIMARY KEY,
    id_company INT,
    name VARCHAR(150),
    description VARCHAR(255),
    status ENUM('draft','active','paused','finished'),
    start_date DATE,
    end_date DATE,
    spent DECIMAL(10,2),
    FOREIGN KEY (id_company) REFERENCES companies(id_company)
);

-- =====================
-- TRACKING LINKS
-- =====================
CREATE TABLE tracking_links (
    id_link INT AUTO_INCREMENT PRIMARY KEY,
    id_campaign INT,
    destination TEXT,
    FOREIGN KEY (id_campaign) REFERENCES campaigns(id_campaign)
);

-- =====================
-- CLICKS
-- =====================
CREATE TABLE clicks (
    id_click INT AUTO_INCREMENT PRIMARY KEY,
    id_link INT,
    ip_address VARCHAR(100),
    user_agent TEXT,
    referrer TEXT,
    country VARCHAR(50),
    clicked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (id_link) REFERENCES tracking_links(id_link)
);

-- =====================
-- CONVERSIONS
-- =====================
CREATE TABLE conversions (
    id_conversion INT AUTO_INCREMENT PRIMARY KEY,
    id_campaign INT NULL, -- legacy
    id_click INT,
    revenue DECIMAL(10,2),
    type VARCHAR(100),
    source VARCHAR(100),
    notes TEXT,
    FOREIGN KEY (id_campaign) REFERENCES campaigns(id_campaign),
    FOREIGN KEY (id_click) REFERENCES clicks(id_click)
);

-- =====================
-- DATOS INICIALES (opcional)
-- =====================
INSERT INTO roles (name) VALUES ('admin'), ('user');

INSERT INTO permissions (name, description) VALUES
('create_campaign', 'Crear campañas'),
('view_reports', 'Ver reportes');

INSERT INTO role_has_permissions (id_role, id_permission) VALUES
(1,1),(1,2),(2,2);