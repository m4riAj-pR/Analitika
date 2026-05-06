SET FOREIGN_KEY_CHECKS = 0;

DROP TABLE IF EXISTS conversions;
DROP TABLE IF EXISTS clicks;
DROP TABLE IF EXISTS tracking_links;
DROP TABLE IF EXISTS channels;
DROP TABLE IF EXISTS campaigns;
DROP TABLE IF EXISTS user_company;
DROP TABLE IF EXISTS companies;
DROP TABLE IF EXISTS users;
DROP TABLE IF EXISTS role_has_permissions;
DROP TABLE IF EXISTS permissions;
DROP TABLE IF EXISTS role;
DROP TABLE IF EXISTS persons;

SET FOREIGN_KEY_CHECKS = 1;

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
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- =====================
-- ROLE
-- El backend usa la tabla en singular: role
-- =====================
CREATE TABLE role (
    id_role INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- =====================
-- PERMISSIONS
-- El backend usa id_permissions como PK
-- =====================
CREATE TABLE permissions (
    id_permissions INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE,
    description VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- =====================
-- ROLE_HAS_PERMISSIONS
-- =====================
CREATE TABLE role_has_permissions (
    id_role_permission INT AUTO_INCREMENT PRIMARY KEY,
    id_role INT NOT NULL,
    id_permission INT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY uq_role_permission (id_role, id_permission),
    CONSTRAINT fk_role_permissions_role
        FOREIGN KEY (id_role) REFERENCES role(id_role),
    CONSTRAINT fk_role_permissions_permission
        FOREIGN KEY (id_permission) REFERENCES permissions(id_permissions)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- =====================
-- USERS
-- =====================
CREATE TABLE users (
    id_user INT AUTO_INCREMENT PRIMARY KEY,
    id_person INT NOT NULL,
    id_company INT NULL,
    id_role INT NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_users_id_person (id_person),
    INDEX idx_users_id_company (id_company),
    INDEX idx_users_id_role (id_role),
    CONSTRAINT fk_users_person
        FOREIGN KEY (id_person) REFERENCES persons(id_person),
    CONSTRAINT fk_users_role
        FOREIGN KEY (id_role) REFERENCES role(id_role)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- =====================
-- COMPANIES
-- =====================
CREATE TABLE companies (
    id_company INT AUTO_INCREMENT PRIMARY KEY,
    id_user INT NULL,
    name VARCHAR(150) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_companies_id_user (id_user),
    CONSTRAINT fk_companies_user
        FOREIGN KEY (id_user) REFERENCES users(id_user)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

ALTER TABLE users
    ADD CONSTRAINT fk_users_company
        FOREIGN KEY (id_company) REFERENCES companies(id_company);

-- =====================
-- USER_COMPANY
-- =====================
CREATE TABLE user_company (
    id_user_company INT AUTO_INCREMENT PRIMARY KEY,
    id_user INT NOT NULL,
    id_company INT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY uq_user_company (id_user, id_company),
    INDEX idx_user_company_id_user (id_user),
    INDEX idx_user_company_id_company (id_company),
    CONSTRAINT fk_user_company_user
        FOREIGN KEY (id_user) REFERENCES users(id_user),
    CONSTRAINT fk_user_company_company
        FOREIGN KEY (id_company) REFERENCES companies(id_company)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- =====================
-- CAMPAIGNS
-- =====================
CREATE TABLE campaigns (
    id_campaign INT AUTO_INCREMENT PRIMARY KEY,
    id_company INT NOT NULL,
    name VARCHAR(150) NOT NULL,
    description VARCHAR(255),
    status ENUM('draft', 'active', 'paused', 'finished') DEFAULT 'draft',
    start_date DATE,
    end_date DATE,
    spent DECIMAL(10,2) NOT NULL DEFAULT 0.00,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CHECK (start_date IS NULL OR end_date IS NULL OR start_date <= end_date),
    INDEX idx_campaigns_id_company (id_company),
    CONSTRAINT fk_campaigns_company
        FOREIGN KEY (id_company) REFERENCES companies(id_company)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- =====================
-- CHANNELS
-- =====================
CREATE TABLE channels (
    id_channel INT AUTO_INCREMENT PRIMARY KEY,
    id_campaign INT NULL,
    name VARCHAR(150) NOT NULL,
    description VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_channels_id_campaign (id_campaign),
    CONSTRAINT fk_channels_campaign
        FOREIGN KEY (id_campaign) REFERENCES campaigns(id_campaign)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- =====================
-- TRACKING LINKS
-- =====================
CREATE TABLE tracking_links (
    id_link INT AUTO_INCREMENT PRIMARY KEY,
    id_campaign INT NOT NULL,
    id_channel INT NULL,
    destination TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_tracking_links_id_campaign (id_campaign),
    INDEX idx_tracking_links_id_channel (id_channel),
    CONSTRAINT fk_tracking_links_campaign
        FOREIGN KEY (id_campaign) REFERENCES campaigns(id_campaign),
    CONSTRAINT fk_tracking_links_channel
        FOREIGN KEY (id_channel) REFERENCES channels(id_channel)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

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
    INDEX idx_clicks_id_link (id_link),
    INDEX idx_clicks_clicked_at (clicked_at),
    CONSTRAINT fk_clicks_tracking_link
        FOREIGN KEY (id_link) REFERENCES tracking_links(id_link)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- =====================
-- CONVERSIONS
-- =====================
CREATE TABLE conversions (
    id_conversion INT AUTO_INCREMENT PRIMARY KEY,
    id_click INT NOT NULL,
    id_campaign INT NULL,
    revenue DECIMAL(10,2) NOT NULL DEFAULT 0.00,
    type ENUM('sale', 'lead', 'signup', 'download', 'contact', 'other') NOT NULL DEFAULT 'other',
    source VARCHAR(100),
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_conversions_id_click (id_click),
    INDEX idx_conversions_id_campaign (id_campaign),
    CONSTRAINT fk_conversions_click
        FOREIGN KEY (id_click) REFERENCES clicks(id_click),
    CONSTRAINT fk_conversions_campaign
        FOREIGN KEY (id_campaign) REFERENCES campaigns(id_campaign)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Datos mínimos para que /register funcione.
INSERT INTO role (id_role, name)
VALUES
    (1, 'admin'),
    (2, 'user')
ON DUPLICATE KEY UPDATE name = VALUES(name);
