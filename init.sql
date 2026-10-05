-- Analitika DB Initialization Script
-- Updated: 2026-05-07

SET FOREIGN_KEY_CHECKS = 0;

-- -----------------------------------------------------
-- Table `persons`
-- -----------------------------------------------------
DROP TABLE IF EXISTS `persons`;
CREATE TABLE `persons` (
  `id_person` INT NOT NULL AUTO_INCREMENT,
  `name` VARCHAR(100) NOT NULL,
  `lastname` VARCHAR(100) DEFAULT NULL,
  `email` VARCHAR(150) NOT NULL,
  `phone` VARCHAR(50) DEFAULT NULL,
  `created_at` TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id_person`),
  UNIQUE KEY `email` (`email`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- -----------------------------------------------------
-- Table `roles`
-- -----------------------------------------------------
DROP TABLE IF EXISTS `roles`;
CREATE TABLE `roles` (
  `id_role` INT NOT NULL AUTO_INCREMENT,
  `name` VARCHAR(100) NOT NULL,
  `created_at` TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id_role`),
  UNIQUE KEY `name` (`name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- -----------------------------------------------------
-- Table `permissions`
-- -----------------------------------------------------
DROP TABLE IF EXISTS `permissions`;
CREATE TABLE `permissions` (
  `id_permission` INT NOT NULL AUTO_INCREMENT,
  `name` VARCHAR(100) NOT NULL,
  `description` VARCHAR(255) DEFAULT NULL,
  `created_at` TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id_permission`),
  UNIQUE KEY `name` (`name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- -----------------------------------------------------
-- Table `role_has_permissions`
-- -----------------------------------------------------
DROP TABLE IF EXISTS `role_has_permissions`;
CREATE TABLE `role_has_permissions` (
  `id_role_permission` INT NOT NULL AUTO_INCREMENT,
  `id_role` INT NOT NULL,
  `id_permission` INT NOT NULL,
  `created_at` TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id_role_permission`),
  UNIQUE KEY `uq_role_permission` (`id_role`, `id_permission`),
  CONSTRAINT `fk_rhp_role` FOREIGN KEY (`id_role`) REFERENCES `roles` (`id_role`) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `fk_rhp_permission` FOREIGN KEY (`id_permission`) REFERENCES `permissions` (`id_permission`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- -----------------------------------------------------
-- Table `companies`
-- -----------------------------------------------------
DROP TABLE IF EXISTS `companies`;
CREATE TABLE `companies` (
  `id_company` INT NOT NULL AUTO_INCREMENT,
  `id_user` INT NOT NULL,
  `name` VARCHAR(150) NOT NULL,
  `created_at` TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id_company`),
  INDEX `idx_companies_id_user` (`id_user`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- -----------------------------------------------------
-- Table `users`
-- -----------------------------------------------------
DROP TABLE IF EXISTS `users`;
CREATE TABLE `users` (
  `id_user` INT NOT NULL AUTO_INCREMENT,
  `id_person` INT NOT NULL,
  `id_company` INT DEFAULT NULL,
  `id_role` INT NOT NULL,
  `username` VARCHAR(100) NOT NULL,
  `password_hash` VARCHAR(255) NOT NULL,
  `status` ENUM('active', 'inactive', 'blocked') DEFAULT 'active',
  `last_login` TIMESTAMP NULL DEFAULT NULL,
  `created_at` TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id_user`),
  UNIQUE KEY `username` (`username`),
  CONSTRAINT `fk_users_person` FOREIGN KEY (`id_person`) REFERENCES `persons` (`id_person`) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `fk_users_role` FOREIGN KEY (`id_role`) REFERENCES `roles` (`id_role`) ON DELETE RESTRICT ON UPDATE CASCADE,
  CONSTRAINT `fk_users_company` FOREIGN KEY (`id_company`) REFERENCES `companies` (`id_company`) ON DELETE SET NULL ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Adding foreign key back to companies now that users exists
ALTER TABLE `companies` 
ADD CONSTRAINT `fk_company_user` FOREIGN KEY (`id_user`) REFERENCES `users` (`id_user`) ON DELETE RESTRICT ON UPDATE CASCADE;

-- -----------------------------------------------------
-- Table `user_company`
-- -----------------------------------------------------
DROP TABLE IF EXISTS `user_company`;
CREATE TABLE `user_company` (
  `id_user_company` INT NOT NULL AUTO_INCREMENT,
  `id_user` INT NOT NULL,
  `id_company` INT NOT NULL,
  `created_at` TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id_user_company`),
  UNIQUE KEY `uq_user_company` (`id_user`, `id_company`),
  CONSTRAINT `fk_user_company_user` FOREIGN KEY (`id_user`) REFERENCES `users` (`id_user`) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `fk_user_company_company` FOREIGN KEY (`id_company`) REFERENCES `companies` (`id_company`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- -----------------------------------------------------
-- Table `campaigns`
-- -----------------------------------------------------
DROP TABLE IF EXISTS `campaigns`;
CREATE TABLE `campaigns` (
  `id_campaign` INT NOT NULL AUTO_INCREMENT,
  `id_company` INT NOT NULL,
  `name` VARCHAR(150) NOT NULL,
  `description` VARCHAR(255) DEFAULT NULL,
  `status` ENUM('draft', 'active', 'paused', 'finished') DEFAULT 'draft',
  `start_date` DATE DEFAULT NULL,
  `end_date` DATE DEFAULT NULL,
  `spent` DECIMAL(10, 2) NOT NULL DEFAULT '0.00',
  `created_at` TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id_campaign`),
  CONSTRAINT `fk_campaign_company` FOREIGN KEY (`id_company`) REFERENCES `companies` (`id_company`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- -----------------------------------------------------
-- Table `channels`
-- -----------------------------------------------------
DROP TABLE IF EXISTS `channels`;
CREATE TABLE `channels` (
  `id_channel` INT NOT NULL AUTO_INCREMENT,
  `id_campaign` INT DEFAULT NULL,
  `name` VARCHAR(150) NOT NULL,
  `description` VARCHAR(255) DEFAULT NULL,
  `created_at` TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id_channel`),
  CONSTRAINT `fk_channel_campaign` FOREIGN KEY (`id_campaign`) REFERENCES `campaigns` (`id_campaign`) ON DELETE SET NULL ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- -----------------------------------------------------
-- Table `tracking_links`
-- -----------------------------------------------------
DROP TABLE IF EXISTS `tracking_links`;
CREATE TABLE `tracking_links` (
  `id_link` INT NOT NULL AUTO_INCREMENT,
  `id_campaign` INT NOT NULL,
  `id_channel` INT DEFAULT NULL,
  `destination` TEXT NOT NULL,
  `short_code` VARCHAR(50) DEFAULT NULL,
  `created_at` TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id_link`),
  UNIQUE KEY `uq_campaign_link` (`id_campaign`),
  UNIQUE KEY `short_code` (`short_code`),
  CONSTRAINT `fk_tracking_campaign` FOREIGN KEY (`id_campaign`) REFERENCES `campaigns` (`id_campaign`) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `fk_tracking_links_channel` FOREIGN KEY (`id_channel`) REFERENCES `channels` (`id_channel`) ON DELETE SET NULL ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- -----------------------------------------------------
-- Table `clicks`
-- -----------------------------------------------------
DROP TABLE IF EXISTS `clicks`;
CREATE TABLE `clicks` (
  `id_click` INT NOT NULL AUTO_INCREMENT,
  `id_link` INT NOT NULL,
  `user_agent` TEXT,
  `referrer` TEXT,
  `country` VARCHAR(50) DEFAULT NULL,
  `ip_address_hash` VARCHAR(64) DEFAULT NULL,
  `consent_given` TINYINT(1) DEFAULT '0',
  `utm_source` VARCHAR(100) DEFAULT NULL,
  `utm_medium` VARCHAR(100) DEFAULT NULL,
  `utm_campaign` VARCHAR(100) DEFAULT NULL,
  `utm_term` VARCHAR(100) DEFAULT NULL,
  `utm_content` VARCHAR(100) DEFAULT NULL,
  `clicked_at` TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP,
  `created_at` TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id_click`),
  CONSTRAINT `fk_click_link` FOREIGN KEY (`id_link`) REFERENCES `tracking_links` (`id_link`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- -----------------------------------------------------
-- Table `conversions`
-- -----------------------------------------------------
DROP TABLE IF EXISTS `conversions`;
CREATE TABLE `conversions` (
  `id_conversion` INT NOT NULL AUTO_INCREMENT,
  `id_click` INT NOT NULL,
  `revenue` DECIMAL(10, 2) DEFAULT NULL,
  `source` VARCHAR(100) DEFAULT NULL,
  `notes` TEXT,
  `type` ENUM('sale', 'lead', 'signup', 'download', 'contact', 'other') NOT NULL DEFAULT 'other',
  `created_at` TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id_conversion`),
  CONSTRAINT `fk_conversion_click` FOREIGN KEY (`id_click`) REFERENCES `clicks` (`id_click`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- -----------------------------------------------------
-- Table `notifications`
-- -----------------------------------------------------
DROP TABLE IF EXISTS `notifications`;
CREATE TABLE `notifications` (
  `id_notification` INT NOT NULL AUTO_INCREMENT,
  `id_user` INT NOT NULL,
  `title` VARCHAR(150) NOT NULL,
  `message` TEXT NOT NULL,
  `type` VARCHAR(50) DEFAULT 'info',
  `is_read` TINYINT(1) DEFAULT '0',
  `created_at` TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id_notification`),
  CONSTRAINT `fk_notifications_user` FOREIGN KEY (`id_user`) REFERENCES `users` (`id_user`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;


-- -----------------------------------------------------
-- Table `ad_account_connections`
-- -----------------------------------------------------
DROP TABLE IF EXISTS `ad_account_connections`;
CREATE TABLE `ad_account_connections` (
  `id_connection` INT NOT NULL AUTO_INCREMENT,
  `id_company` INT NOT NULL,
  `provider` ENUM('meta', 'google', 'tiktok') NOT NULL,
  `external_account_id` VARCHAR(255) NOT NULL,
  `access_token` TEXT NOT NULL,
  `refresh_token` TEXT DEFAULT NULL,
  `token_expires_at` TIMESTAMP NULL DEFAULT NULL,
  `status` ENUM('active', 'expired', 'revoked', 'error') DEFAULT 'active',
  `connected_by` INT NOT NULL,
  `connected_at` TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP,
  `last_sync_at` TIMESTAMP NULL DEFAULT NULL,
  PRIMARY KEY (`id_connection`),
  KEY `idx_ad_conn_company` (`id_company`),
  CONSTRAINT `fk_ad_conn_company` FOREIGN KEY (`id_company`) REFERENCES `companies` (`id_company`) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `fk_ad_conn_user` FOREIGN KEY (`connected_by`) REFERENCES `users` (`id_user`) ON DELETE RESTRICT ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- -----------------------------------------------------
-- Table `campaign_external_mapping`
-- -----------------------------------------------------
DROP TABLE IF EXISTS `campaign_external_mapping`;
CREATE TABLE `campaign_external_mapping` (
  `id_mapping` INT NOT NULL AUTO_INCREMENT,
  `id_campaign` INT NOT NULL,
  `id_connection` INT NOT NULL,
  `external_campaign_id` VARCHAR(255) NOT NULL,
  `created_at` TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id_mapping`),
  UNIQUE KEY `uq_campaign_connection` (`id_campaign`, `id_connection`),
  CONSTRAINT `fk_cem_campaign` FOREIGN KEY (`id_campaign`) REFERENCES `campaigns` (`id_campaign`) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `fk_cem_connection` FOREIGN KEY (`id_connection`) REFERENCES `ad_account_connections` (`id_connection`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- -----------------------------------------------------
-- Table `campaign_external_metrics`
-- -----------------------------------------------------
DROP TABLE IF EXISTS `campaign_external_metrics`;
CREATE TABLE `campaign_external_metrics` (
  `id_metric` INT NOT NULL AUTO_INCREMENT,
  `id_campaign` INT NOT NULL,
  `id_connection` INT NOT NULL,
  `metric_date` DATE NOT NULL,
  `impressions` INT NOT NULL DEFAULT 0,
  `spend` DECIMAL(10, 2) NOT NULL DEFAULT '0.00',
  `external_clicks` INT NOT NULL DEFAULT 0,
  `fetched_at` TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id_metric`),
  UNIQUE KEY `uq_campaign_conn_date` (`id_campaign`, `id_connection`, `metric_date`),
  CONSTRAINT `fk_cem_met_campaign` FOREIGN KEY (`id_campaign`) REFERENCES `campaigns` (`id_campaign`) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `fk_cem_met_connection` FOREIGN KEY (`id_connection`) REFERENCES `ad_account_connections` (`id_connection`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;


SET FOREIGN_KEY_CHECKS = 1;

-- Seed initial roles with fixed IDs
INSERT INTO `roles` (`id_role`, `name`) VALUES 
(1, 'Super_Admin'), 
(2, 'Owner'), 
(3, 'Manager') 
ON DUPLICATE KEY UPDATE name=VALUES(name);


