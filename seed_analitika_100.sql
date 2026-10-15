-- =====================================================
-- DATASET DE PRUEBA: 100 REGISTROS PARA LA EMPRESA ANALITIKA
-- =====================================================
SET FOREIGN_KEY_CHECKS = 0;

-- 1. Asegurar Usuario y Empresa Analitika
INSERT INTO `persons` (`id_person`, `name`, `email`, `phone`)
VALUES (999, 'Admin Analitika', 'admin@analitika.com', '+573001234567')
ON DUPLICATE KEY UPDATE `name` = VALUES(`name`);

INSERT INTO `users` (`id_user`, `id_person`, `id_company`, `id_role`, `username`, `password_hash`, `status`)
VALUES (999, 999, NULL, 2, 'analitika_owner', '$2b$12$e8YkY.k4X7Z9e1k4Z7Z9e.k4X7Z9e1k4Z7Z9e.k4X7Z9e1k4Z7Z9e', 'active')
ON DUPLICATE KEY UPDATE `username` = VALUES(`username`);

INSERT INTO `companies` (`id_company`, `id_user`, `name`)
VALUES (999, 999, 'Analitika')
ON DUPLICATE KEY UPDATE `name` = VALUES(`name`);

UPDATE `users` SET `id_company` = 999 WHERE `id_user` = 999;

INSERT INTO `user_company` (`id_user`, `id_company`)
VALUES (999, 999)
ON DUPLICATE KEY UPDATE `id_company` = VALUES(`id_company`);

-- 2. Conexión de prueba con Meta Ads
INSERT INTO `ad_account_connections` (`id_connection`, `id_company`, `provider`, `external_account_id`, `account_name`, `access_token`, `status`, `connected_by`)
VALUES (999, 999, 'meta', 'act_1112068198074147', 'Analitika Meta Ads Business', 'test_encrypted_token_sample', 'active', 999)
ON DUPLICATE KEY UPDATE `account_name` = VALUES(`account_name`);

-- 3. Campañas publicitarias de Analitika
INSERT INTO `campaigns` (`id_campaign`, `id_company`, `name`, `description`, `status`, `start_date`, `end_date`, `spent`, `budget`)
VALUES (901, 999, 'Campaña Meta Brand Awareness Q1', 'Campaña estratégica de prueba para Analitika', 'draft', '2026-08-31', '2026-09-30', 1200.0, 5000.0)
ON DUPLICATE KEY UPDATE `spent` = VALUES(`spent`), `budget` = VALUES(`budget`);
INSERT INTO `campaigns` (`id_campaign`, `id_company`, `name`, `description`, `status`, `start_date`, `end_date`, `spent`, `budget`)
VALUES (902, 999, 'Generación de Leads B2B Meta Ads', 'Campaña estratégica de prueba para Analitika', 'active', '2026-09-15', '2026-10-30', 3450.5, 8000.0)
ON DUPLICATE KEY UPDATE `spent` = VALUES(`spent`), `budget` = VALUES(`budget`);
INSERT INTO `campaigns` (`id_campaign`, `id_company`, `name`, `description`, `status`, `start_date`, `end_date`, `spent`, `budget`)
VALUES (903, 999, 'Conversión Ecommerce Primavera', 'Campaña estratégica de prueba para Analitika', 'active', '2026-09-25', '2026-11-04', 5600.0, 10000.0)
ON DUPLICATE KEY UPDATE `spent` = VALUES(`spent`), `budget` = VALUES(`budget`);
INSERT INTO `campaigns` (`id_campaign`, `id_company`, `name`, `description`, `status`, `start_date`, `end_date`, `spent`, `budget`)
VALUES (904, 999, 'Retargeting Clientes Carrito Abandonado', 'Campaña estratégica de prueba para Analitika', 'active', '2026-09-30', '2026-10-30', 2150.75, 4500.0)
ON DUPLICATE KEY UPDATE `spent` = VALUES(`spent`), `budget` = VALUES(`budget`);
INSERT INTO `campaigns` (`id_campaign`, `id_company`, `name`, `description`, `status`, `start_date`, `end_date`, `spent`, `budget`)
VALUES (905, 999, 'Lanzamiento App Móvil Analitika', 'Campaña estratégica de prueba para Analitika', 'paused', '2026-10-05', '2026-11-14', 890.0, 3000.0)
ON DUPLICATE KEY UPDATE `spent` = VALUES(`spent`), `budget` = VALUES(`budget`);

-- Canales y Tracking Links
INSERT INTO `channels` (`id_channel`, `id_campaign`, `name`, `description`)
VALUES (901, 901, 'Facebook Feed', 'Anuncios en Feed de Facebook')
ON DUPLICATE KEY UPDATE `name` = VALUES(`name`);
INSERT INTO `channels` (`id_channel`, `id_campaign`, `name`, `description`)
VALUES (902, 902, 'Instagram Stories', 'Historias patrocinadas en Instagram')
ON DUPLICATE KEY UPDATE `name` = VALUES(`name`);
INSERT INTO `channels` (`id_channel`, `id_campaign`, `name`, `description`)
VALUES (903, 903, 'Instagram Reels', 'Reels promocionados')
ON DUPLICATE KEY UPDATE `name` = VALUES(`name`);
INSERT INTO `channels` (`id_channel`, `id_campaign`, `name`, `description`)
VALUES (904, 904, 'Facebook Marketplace', 'Catálogo dinámico de productos')
ON DUPLICATE KEY UPDATE `name` = VALUES(`name`);
INSERT INTO `channels` (`id_channel`, `id_campaign`, `name`, `description`)
VALUES (905, 905, 'Audience Network', 'Red de anuncios de Meta')
ON DUPLICATE KEY UPDATE `name` = VALUES(`name`);

INSERT INTO `tracking_links` (`id_link`, `id_campaign`, `id_channel`, `destination`, `short_code`)
VALUES (901, 901, 901, 'https://analitika.com/landing?utm_source=meta&utm_medium=cpc&utm_campaign=camp_901', 'ana_901_1')
ON DUPLICATE KEY UPDATE `short_code` = VALUES(`short_code`);
INSERT INTO `tracking_links` (`id_link`, `id_campaign`, `id_channel`, `destination`, `short_code`)
VALUES (902, 902, 902, 'https://analitika.com/landing?utm_source=meta&utm_medium=cpc&utm_campaign=camp_902', 'ana_902_2')
ON DUPLICATE KEY UPDATE `short_code` = VALUES(`short_code`);
INSERT INTO `tracking_links` (`id_link`, `id_campaign`, `id_channel`, `destination`, `short_code`)
VALUES (903, 903, 903, 'https://analitika.com/landing?utm_source=meta&utm_medium=cpc&utm_campaign=camp_903', 'ana_903_3')
ON DUPLICATE KEY UPDATE `short_code` = VALUES(`short_code`);
INSERT INTO `tracking_links` (`id_link`, `id_campaign`, `id_channel`, `destination`, `short_code`)
VALUES (904, 904, 904, 'https://analitika.com/landing?utm_source=meta&utm_medium=cpc&utm_campaign=camp_904', 'ana_904_4')
ON DUPLICATE KEY UPDATE `short_code` = VALUES(`short_code`);
INSERT INTO `tracking_links` (`id_link`, `id_campaign`, `id_channel`, `destination`, `short_code`)
VALUES (905, 905, 905, 'https://analitika.com/landing?utm_source=meta&utm_medium=cpc&utm_campaign=camp_905', 'ana_905_5')
ON DUPLICATE KEY UPDATE `short_code` = VALUES(`short_code`);

-- 4. Mapeo de Campañas con Meta Ads
INSERT INTO `campaign_external_mapping` (`id_mapping`, `id_campaign`, `id_connection`, `external_campaign_id`, `external_campaign_name`, `sync_enabled`)
VALUES (901, 901, 999, 'meta_camp_1607_901', 'Campaña Meta Brand Awareness Q1', 1)
ON DUPLICATE KEY UPDATE `external_campaign_name` = VALUES(`external_campaign_name`);
INSERT INTO `campaign_external_mapping` (`id_mapping`, `id_campaign`, `id_connection`, `external_campaign_id`, `external_campaign_name`, `sync_enabled`)
VALUES (902, 902, 999, 'meta_camp_1607_902', 'Generación de Leads B2B Meta Ads', 1)
ON DUPLICATE KEY UPDATE `external_campaign_name` = VALUES(`external_campaign_name`);
INSERT INTO `campaign_external_mapping` (`id_mapping`, `id_campaign`, `id_connection`, `external_campaign_id`, `external_campaign_name`, `sync_enabled`)
VALUES (903, 903, 999, 'meta_camp_1607_903', 'Conversión Ecommerce Primavera', 1)
ON DUPLICATE KEY UPDATE `external_campaign_name` = VALUES(`external_campaign_name`);
INSERT INTO `campaign_external_mapping` (`id_mapping`, `id_campaign`, `id_connection`, `external_campaign_id`, `external_campaign_name`, `sync_enabled`)
VALUES (904, 904, 999, 'meta_camp_1607_904', 'Retargeting Clientes Carrito Abandonado', 1)
ON DUPLICATE KEY UPDATE `external_campaign_name` = VALUES(`external_campaign_name`);
INSERT INTO `campaign_external_mapping` (`id_mapping`, `id_campaign`, `id_connection`, `external_campaign_id`, `external_campaign_name`, `sync_enabled`)
VALUES (905, 905, 999, 'meta_camp_1607_905', 'Lanzamiento App Móvil Analitika', 1)
ON DUPLICATE KEY UPDATE `external_campaign_name` = VALUES(`external_campaign_name`);

-- 5. Métricas diarias externas (Meta Ads Insights)
INSERT INTO `campaign_external_metrics` (`id_mapping`, `metric_date`, `impressions`, `spend`, `external_clicks`, `reach`) VALUES
(902, '2026-09-15', 7986, 224.41, 349, 6661),
(903, '2026-09-16', 6315, 263.70, 355, 4985),
(902, '2026-09-17', 5841, 239.91, 227, 4588),
(903, '2026-09-18', 5140, 160.81, 274, 4239),
(902, '2026-09-19', 6568, 285.13, 344, 5081),
(903, '2026-09-20', 5496, 92.94, 116, 4619),
(902, '2026-09-21', 7109, 238.21, 345, 6381),
(903, '2026-09-22', 2240, 111.81, 108, 1994),
(902, '2026-09-23', 7162, 294.51, 414, 5691),
(903, '2026-09-24', 4799, 131.38, 209, 3677),
(902, '2026-09-25', 2935, 116.61, 98, 2626),
(903, '2026-09-26', 2904, 44.77, 107, 2220),
(902, '2026-09-27', 1903, 100.44, 96, 1705),
(903, '2026-09-28', 8124, 265.67, 381, 6288),
(902, '2026-09-29', 3935, 105.47, 135, 3097),
(903, '2026-09-30', 6790, 228.22, 364, 6013),
(902, '2026-10-01', 6459, 299.34, 251, 5759),
(903, '2026-10-02', 3803, 117.45, 200, 2981),
(902, '2026-10-03', 7178, 124.93, 172, 5804),
(903, '2026-10-04', 2433, 97.80, 91, 1826),
(902, '2026-10-05', 3003, 185.17, 180, 2482),
(903, '2026-10-06', 6696, 227.22, 224, 5220),
(902, '2026-10-07', 7934, 305.36, 451, 6482),
(903, '2026-10-08', 4267, 62.84, 98, 3547),
(902, '2026-10-09', 5914, 102.83, 177, 4953),
(903, '2026-10-10', 5219, 186.47, 235, 4212),
(902, '2026-10-11', 1603, 30.45, 62, 1271),
(903, '2026-10-12', 4977, 81.88, 196, 4148),
(902, '2026-10-13', 5207, 143.09, 211, 4470),
(903, '2026-10-14', 6010, 301.83, 304, 4874);

-- 6. Dataset de 100 Clicks y Navegaciones para Analitika
INSERT INTO `clicks` (`id_click`, `id_link`, `user_agent`, `referrer`, `country`, `ip_address_hash`, `consent_given`, `utm_source`, `utm_medium`, `utm_campaign`, `utm_term`, `utm_content`, `clicked_at`) VALUES
(1001, 901, 'Mozilla/5.0 (iPhone; CPU iPhone OS 17_4 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148 [FBAN/FBIOS;FBDV/iPhone14,2;FBMD/iPhone;FBSN/iOS;FBSV/17.4;FBSS/3;FBCR/Claro;FBID/phone;FBLC/es_ES;FBOP/5]', 'https://instagram.com/', 'México', 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b801', 1, 'meta', 'cpc', 'camp_901', 'analitica software', 'story_desliza_arriba', '2026-10-13 14:36:55'),
(1002, 901, 'Mozilla/5.0 (iPhone; CPU iPhone OS 17_4 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148 [FBAN/FBIOS;FBDV/iPhone14,2;FBMD/iPhone;FBSN/iOS;FBSV/17.4;FBSS/3;FBCR/Claro;FBID/phone;FBLC/es_ES;FBOP/5]', 'https://l.facebook.com/', 'México', 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b802', 1, 'meta', 'cpc', 'camp_901', 'reportes automaticos', 'banner_azul_cta', '2026-10-02 19:34:55'),
(1003, 905, 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.3 Safari/605.1.15', 'https://m.facebook.com/', 'Perú', 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b803', 1, 'meta', 'cpc', 'camp_905', 'analitica software', 'video_demo_15s', '2026-10-05 23:16:55'),
(1004, 902, 'Mozilla/5.0 (Linux; Android 14; SM-S918B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.6261.119 Mobile Safari/537.36 [FB_IAB/FB4A;FBAV/455.0.0.44.109;]', 'https://instagram.com/', 'Colombia', 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b804', 0, 'meta', 'cpc', 'camp_902', 'analitica software', 'carrusel_beneficios', '2026-10-07 18:14:55'),
(1005, 901, 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.3 Safari/605.1.15', 'https://l.facebook.com/', 'Chile', 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b805', 0, 'meta', 'cpc', 'camp_901', 'meta ads tracking', 'story_desliza_arriba', '2026-10-07 08:34:55'),
(1006, 901, 'Mozilla/5.0 (iPhone; CPU iPhone OS 17_4 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148 [FBAN/FBIOS;FBDV/iPhone14,2;FBMD/iPhone;FBSN/iOS;FBSV/17.4;FBSS/3;FBCR/Claro;FBID/phone;FBLC/es_ES;FBOP/5]', 'https://m.facebook.com/', 'México', 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b806', 1, 'meta', 'cpc', 'camp_901', 'dashboard ventas', 'banner_azul_cta', '2026-10-06 22:29:55'),
(1007, 903, 'Mozilla/5.0 (Linux; Android 14; SM-S918B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.6261.119 Mobile Safari/537.36 [FB_IAB/FB4A;FBAV/455.0.0.44.109;]', 'https://instagram.com/', 'España', 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b807', 1, 'meta', 'cpc', 'camp_903', 'meta ads tracking', 'banner_azul_cta', '2026-10-01 17:24:55'),
(1008, 905, 'Mozilla/5.0 (Linux; Android 14; SM-S918B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.6261.119 Mobile Safari/537.36 [FB_IAB/FB4A;FBAV/455.0.0.44.109;]', 'https://m.facebook.com/', 'Perú', 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b808', 1, 'meta', 'cpc', 'camp_905', 'reportes automaticos', 'video_demo_15s', '2026-10-08 04:58:55'),
(1009, 901, 'Mozilla/5.0 (Linux; Android 14; SM-S918B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.6261.119 Mobile Safari/537.36 [FB_IAB/FB4A;FBAV/455.0.0.44.109;]', 'https://l.facebook.com/', 'España', 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b809', 1, 'meta', 'cpc', 'camp_901', 'analitica software', 'video_demo_15s', '2026-10-02 16:19:55'),
(1010, 903, 'Mozilla/5.0 (Linux; Android 14; SM-S918B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.6261.119 Mobile Safari/537.36 [FB_IAB/FB4A;FBAV/455.0.0.44.109;]', 'https://l.instagram.com/', 'Chile', 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b810', 1, 'meta', 'cpc', 'camp_903', 'bi pymes', 'video_demo_15s', '2026-10-09 13:25:55'),
(1011, 905, 'Mozilla/5.0 (Linux; Android 13; Pixel 7 Pro) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.6167.178 Mobile Safari/537.36 Instagram 319.0.0.33.109', 'https://instagram.com/', 'Estados Unidos', 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b811', 1, 'meta', 'cpc', 'camp_905', 'reportes automaticos', 'post_descuento_20', '2026-10-07 08:23:55'),
(1012, 902, 'Mozilla/5.0 (Linux; Android 13; Pixel 7 Pro) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.6167.178 Mobile Safari/537.36 Instagram 319.0.0.33.109', 'https://l.instagram.com/', 'Colombia', 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b812', 1, 'meta', 'cpc', 'camp_902', 'analitica software', 'video_demo_15s', '2026-10-01 07:24:55'),
(1013, 904, 'Mozilla/5.0 (Linux; Android 13; Pixel 7 Pro) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.6167.178 Mobile Safari/537.36 Instagram 319.0.0.33.109', 'https://l.facebook.com/', 'Chile', 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b813', 1, 'meta', 'cpc', 'camp_904', 'bi pymes', 'story_desliza_arriba', '2026-10-09 20:46:55'),
(1014, 901, 'Mozilla/5.0 (iPhone; CPU iPhone OS 17_4 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148 [FBAN/FBIOS;FBDV/iPhone14,2;FBMD/iPhone;FBSN/iOS;FBSV/17.4;FBSS/3;FBCR/Claro;FBID/phone;FBLC/es_ES;FBOP/5]', 'https://instagram.com/', 'España', 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b814', 0, 'meta', 'cpc', 'camp_901', 'bi pymes', 'video_demo_15s', '2026-10-05 06:17:55'),
(1015, 903, 'Mozilla/5.0 (Linux; Android 13; Pixel 7 Pro) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.6167.178 Mobile Safari/537.36 Instagram 319.0.0.33.109', 'https://m.facebook.com/', 'Argentina', 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b815', 1, 'meta', 'cpc', 'camp_903', 'meta ads tracking', 'story_desliza_arriba', '2026-10-01 17:30:55'),
(1016, 903, 'Mozilla/5.0 (Linux; Android 14; SM-S918B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.6261.119 Mobile Safari/537.36 [FB_IAB/FB4A;FBAV/455.0.0.44.109;]', 'https://l.facebook.com/', 'Estados Unidos', 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b816', 1, 'meta', 'cpc', 'camp_903', 'analitica software', 'banner_azul_cta', '2026-10-07 07:50:55'),
(1017, 903, 'Mozilla/5.0 (Linux; Android 14; SM-S918B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.6261.119 Mobile Safari/537.36 [FB_IAB/FB4A;FBAV/455.0.0.44.109;]', 'https://l.facebook.com/', 'México', 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b817', 1, 'meta', 'cpc', 'camp_903', 'analitica software', 'banner_azul_cta', '2026-10-04 12:40:55'),
(1018, 905, 'Mozilla/5.0 (Linux; Android 14; SM-S918B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.6261.119 Mobile Safari/537.36 [FB_IAB/FB4A;FBAV/455.0.0.44.109;]', 'https://m.facebook.com/', 'Perú', 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b818', 1, 'meta', 'cpc', 'camp_905', 'dashboard ventas', 'carrusel_beneficios', '2026-10-03 13:54:55'),
(1019, 904, 'Mozilla/5.0 (Linux; Android 14; SM-S918B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.6261.119 Mobile Safari/537.36 [FB_IAB/FB4A;FBAV/455.0.0.44.109;]', 'https://m.facebook.com/', 'México', 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b819', 1, 'meta', 'cpc', 'camp_904', 'meta ads tracking', 'post_descuento_20', '2026-10-03 19:25:55'),
(1020, 902, 'Mozilla/5.0 (Linux; Android 14; SM-S918B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.6261.119 Mobile Safari/537.36 [FB_IAB/FB4A;FBAV/455.0.0.44.109;]', 'https://l.facebook.com/', 'España', 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b820', 0, 'meta', 'cpc', 'camp_902', 'reportes automaticos', 'video_demo_15s', '2026-10-02 04:42:55'),
(1021, 901, 'Mozilla/5.0 (iPhone; CPU iPhone OS 17_4 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148 [FBAN/FBIOS;FBDV/iPhone14,2;FBMD/iPhone;FBSN/iOS;FBSV/17.4;FBSS/3;FBCR/Claro;FBID/phone;FBLC/es_ES;FBOP/5]', 'https://m.facebook.com/', 'Colombia', 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b821', 1, 'meta', 'cpc', 'camp_901', 'meta ads tracking', 'banner_azul_cta', '2026-10-03 21:17:55'),
(1022, 904, 'Mozilla/5.0 (Linux; Android 14; SM-S918B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.6261.119 Mobile Safari/537.36 [FB_IAB/FB4A;FBAV/455.0.0.44.109;]', 'https://m.facebook.com/', 'Estados Unidos', 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b822', 1, 'meta', 'cpc', 'camp_904', 'dashboard ventas', 'post_descuento_20', '2026-10-06 07:46:55'),
(1023, 901, 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.3 Safari/605.1.15', 'https://instagram.com/', 'Chile', 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b823', 1, 'meta', 'cpc', 'camp_901', 'analitica software', 'banner_azul_cta', '2026-10-14 04:58:55'),
(1024, 903, 'Mozilla/5.0 (iPhone; CPU iPhone OS 17_4 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148 [FBAN/FBIOS;FBDV/iPhone14,2;FBMD/iPhone;FBSN/iOS;FBSV/17.4;FBSS/3;FBCR/Claro;FBID/phone;FBLC/es_ES;FBOP/5]', 'https://m.facebook.com/', 'México', 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b824', 1, 'meta', 'cpc', 'camp_903', 'bi pymes', 'video_demo_15s', '2026-10-05 23:40:55'),
(1025, 904, 'Mozilla/5.0 (Linux; Android 14; SM-S918B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.6261.119 Mobile Safari/537.36 [FB_IAB/FB4A;FBAV/455.0.0.44.109;]', 'https://l.facebook.com/', 'Perú', 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b825', 1, 'meta', 'cpc', 'camp_904', 'reportes automaticos', 'banner_azul_cta', '2026-10-14 10:27:55'),
(1026, 905, 'Mozilla/5.0 (iPhone; CPU iPhone OS 17_4 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148 [FBAN/FBIOS;FBDV/iPhone14,2;FBMD/iPhone;FBSN/iOS;FBSV/17.4;FBSS/3;FBCR/Claro;FBID/phone;FBLC/es_ES;FBOP/5]', 'https://l.facebook.com/', 'México', 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b826', 1, 'meta', 'cpc', 'camp_905', 'bi pymes', 'post_descuento_20', '2026-10-10 17:20:55'),
(1027, 901, 'Mozilla/5.0 (Linux; Android 14; SM-S918B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.6261.119 Mobile Safari/537.36 [FB_IAB/FB4A;FBAV/455.0.0.44.109;]', 'https://l.instagram.com/', 'Colombia', 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b827', 1, 'meta', 'cpc', 'camp_901', 'meta ads tracking', 'post_descuento_20', '2026-10-09 02:17:55'),
(1028, 905, 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.3 Safari/605.1.15', 'https://m.facebook.com/', 'México', 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b828', 1, 'meta', 'cpc', 'camp_905', 'analitica software', 'story_desliza_arriba', '2026-10-03 05:58:55'),
(1029, 903, 'Mozilla/5.0 (iPhone; CPU iPhone OS 17_4 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148 [FBAN/FBIOS;FBDV/iPhone14,2;FBMD/iPhone;FBSN/iOS;FBSV/17.4;FBSS/3;FBCR/Claro;FBID/phone;FBLC/es_ES;FBOP/5]', 'https://l.facebook.com/', 'Estados Unidos', 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b829', 1, 'meta', 'cpc', 'camp_903', 'reportes automaticos', 'video_demo_15s', '2026-10-14 07:01:55'),
(1030, 901, 'Mozilla/5.0 (Linux; Android 14; SM-S918B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.6261.119 Mobile Safari/537.36 [FB_IAB/FB4A;FBAV/455.0.0.44.109;]', 'https://l.facebook.com/', 'Estados Unidos', 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b830', 0, 'meta', 'cpc', 'camp_901', 'dashboard ventas', 'post_descuento_20', '2026-10-12 20:36:55'),
(1031, 905, 'Mozilla/5.0 (Linux; Android 14; SM-S918B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.6261.119 Mobile Safari/537.36 [FB_IAB/FB4A;FBAV/455.0.0.44.109;]', 'https://l.facebook.com/', 'Estados Unidos', 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b831', 0, 'meta', 'cpc', 'camp_905', 'reportes automaticos', 'story_desliza_arriba', '2026-10-03 16:34:55'),
(1032, 903, 'Mozilla/5.0 (Linux; Android 14; SM-S918B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.6261.119 Mobile Safari/537.36 [FB_IAB/FB4A;FBAV/455.0.0.44.109;]', 'https://instagram.com/', 'México', 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b832', 1, 'meta', 'cpc', 'camp_903', 'dashboard ventas', 'carrusel_beneficios', '2026-10-05 04:22:55'),
(1033, 901, 'Mozilla/5.0 (iPhone; CPU iPhone OS 17_4 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148 [FBAN/FBIOS;FBDV/iPhone14,2;FBMD/iPhone;FBSN/iOS;FBSV/17.4;FBSS/3;FBCR/Claro;FBID/phone;FBLC/es_ES;FBOP/5]', 'https://l.instagram.com/', 'Estados Unidos', 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b833', 1, 'meta', 'cpc', 'camp_901', 'analitica software', 'banner_azul_cta', '2026-10-03 08:27:55'),
(1034, 903, 'Mozilla/5.0 (Linux; Android 14; SM-S918B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.6261.119 Mobile Safari/537.36 [FB_IAB/FB4A;FBAV/455.0.0.44.109;]', 'https://instagram.com/', 'Colombia', 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b834', 1, 'meta', 'cpc', 'camp_903', 'meta ads tracking', 'carrusel_beneficios', '2026-10-11 23:55:55'),
(1035, 905, 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36', 'https://l.facebook.com/', 'Argentina', 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b835', 1, 'meta', 'cpc', 'camp_905', 'analitica software', 'video_demo_15s', '2026-10-09 13:38:55'),
(1036, 901, 'Mozilla/5.0 (Linux; Android 13; Pixel 7 Pro) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.6167.178 Mobile Safari/537.36 Instagram 319.0.0.33.109', 'https://m.facebook.com/', 'México', 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b836', 1, 'meta', 'cpc', 'camp_901', 'dashboard ventas', 'carrusel_beneficios', '2026-10-10 22:53:55'),
(1037, 903, 'Mozilla/5.0 (Linux; Android 13; Pixel 7 Pro) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.6167.178 Mobile Safari/537.36 Instagram 319.0.0.33.109', 'https://l.instagram.com/', 'México', 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b837', 1, 'meta', 'cpc', 'camp_903', 'analitica software', 'banner_azul_cta', '2026-10-01 03:40:55'),
(1038, 903, 'Mozilla/5.0 (iPhone; CPU iPhone OS 17_4 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148 [FBAN/FBIOS;FBDV/iPhone14,2;FBMD/iPhone;FBSN/iOS;FBSV/17.4;FBSS/3;FBCR/Claro;FBID/phone;FBLC/es_ES;FBOP/5]', 'https://l.facebook.com/', 'España', 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b838', 1, 'meta', 'cpc', 'camp_903', 'meta ads tracking', 'video_demo_15s', '2026-10-05 12:46:55'),
(1039, 904, 'Mozilla/5.0 (Linux; Android 13; Pixel 7 Pro) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.6167.178 Mobile Safari/537.36 Instagram 319.0.0.33.109', 'https://l.facebook.com/', 'Colombia', 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b839', 0, 'meta', 'cpc', 'camp_904', 'dashboard ventas', 'story_desliza_arriba', '2026-10-14 18:24:55'),
(1040, 905, 'Mozilla/5.0 (Linux; Android 13; Pixel 7 Pro) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.6167.178 Mobile Safari/537.36 Instagram 319.0.0.33.109', 'https://m.facebook.com/', 'Chile', 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b840', 0, 'meta', 'cpc', 'camp_905', 'meta ads tracking', 'carrusel_beneficios', '2026-10-14 16:17:55'),
(1041, 902, 'Mozilla/5.0 (Linux; Android 14; SM-S918B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.6261.119 Mobile Safari/537.36 [FB_IAB/FB4A;FBAV/455.0.0.44.109;]', 'https://l.facebook.com/', 'España', 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b841', 1, 'meta', 'cpc', 'camp_902', 'bi pymes', 'story_desliza_arriba', '2026-10-12 01:40:55'),
(1042, 902, 'Mozilla/5.0 (Linux; Android 14; SM-S918B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.6261.119 Mobile Safari/537.36 [FB_IAB/FB4A;FBAV/455.0.0.44.109;]', 'https://m.facebook.com/', 'Chile', 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b842', 0, 'meta', 'cpc', 'camp_902', 'meta ads tracking', 'post_descuento_20', '2026-10-09 22:33:55'),
(1043, 901, 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.3 Safari/605.1.15', 'https://l.facebook.com/', 'Perú', 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b843', 1, 'meta', 'cpc', 'camp_901', 'bi pymes', 'carrusel_beneficios', '2026-10-08 15:24:55'),
(1044, 902, 'Mozilla/5.0 (Linux; Android 14; SM-S918B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.6261.119 Mobile Safari/537.36 [FB_IAB/FB4A;FBAV/455.0.0.44.109;]', 'https://l.facebook.com/', 'México', 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b844', 1, 'meta', 'cpc', 'camp_902', 'meta ads tracking', 'banner_azul_cta', '2026-10-09 05:38:55'),
(1045, 905, 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.3 Safari/605.1.15', 'https://instagram.com/', 'Colombia', 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b845', 0, 'meta', 'cpc', 'camp_905', 'meta ads tracking', 'video_demo_15s', '2026-10-02 09:00:55'),
(1046, 903, 'Mozilla/5.0 (iPhone; CPU iPhone OS 17_4 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148 [FBAN/FBIOS;FBDV/iPhone14,2;FBMD/iPhone;FBSN/iOS;FBSV/17.4;FBSS/3;FBCR/Claro;FBID/phone;FBLC/es_ES;FBOP/5]', 'https://l.facebook.com/', 'Estados Unidos', 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b846', 1, 'meta', 'cpc', 'camp_903', 'meta ads tracking', 'post_descuento_20', '2026-10-01 19:00:55'),
(1047, 901, 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.3 Safari/605.1.15', 'https://m.facebook.com/', 'México', 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b847', 0, 'meta', 'cpc', 'camp_901', 'bi pymes', 'banner_azul_cta', '2026-10-03 18:08:55'),
(1048, 905, 'Mozilla/5.0 (Linux; Android 14; SM-S918B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.6261.119 Mobile Safari/537.36 [FB_IAB/FB4A;FBAV/455.0.0.44.109;]', 'https://instagram.com/', 'Chile', 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b848', 0, 'meta', 'cpc', 'camp_905', 'meta ads tracking', 'story_desliza_arriba', '2026-10-08 10:38:55'),
(1049, 901, 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36', 'https://instagram.com/', 'Chile', 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b849', 1, 'meta', 'cpc', 'camp_901', 'meta ads tracking', 'story_desliza_arriba', '2026-10-12 16:34:55'),
(1050, 904, 'Mozilla/5.0 (Linux; Android 14; SM-S918B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.6261.119 Mobile Safari/537.36 [FB_IAB/FB4A;FBAV/455.0.0.44.109;]', 'https://instagram.com/', 'Chile', 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b850', 1, 'meta', 'cpc', 'camp_904', 'analitica software', 'carrusel_beneficios', '2026-10-09 01:23:55'),
(1051, 905, 'Mozilla/5.0 (Linux; Android 13; Pixel 7 Pro) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.6167.178 Mobile Safari/537.36 Instagram 319.0.0.33.109', 'https://instagram.com/', 'Perú', 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b851', 1, 'meta', 'cpc', 'camp_905', 'dashboard ventas', 'story_desliza_arriba', '2026-10-04 19:39:55'),
(1052, 902, 'Mozilla/5.0 (iPhone; CPU iPhone OS 17_4 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148 [FBAN/FBIOS;FBDV/iPhone14,2;FBMD/iPhone;FBSN/iOS;FBSV/17.4;FBSS/3;FBCR/Claro;FBID/phone;FBLC/es_ES;FBOP/5]', 'https://instagram.com/', 'Argentina', 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b852', 1, 'meta', 'cpc', 'camp_902', 'reportes automaticos', 'carrusel_beneficios', '2026-10-13 11:04:55'),
(1053, 902, 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36', 'https://m.facebook.com/', 'México', 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b853', 0, 'meta', 'cpc', 'camp_902', 'analitica software', 'video_demo_15s', '2026-10-04 18:35:55'),
(1054, 901, 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.3 Safari/605.1.15', 'https://l.instagram.com/', 'Estados Unidos', 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b854', 1, 'meta', 'cpc', 'camp_901', 'bi pymes', 'post_descuento_20', '2026-10-06 11:49:55'),
(1055, 901, 'Mozilla/5.0 (iPhone; CPU iPhone OS 17_4 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148 [FBAN/FBIOS;FBDV/iPhone14,2;FBMD/iPhone;FBSN/iOS;FBSV/17.4;FBSS/3;FBCR/Claro;FBID/phone;FBLC/es_ES;FBOP/5]', 'https://l.instagram.com/', 'México', 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855', 1, 'meta', 'cpc', 'camp_901', 'reportes automaticos', 'post_descuento_20', '2026-10-14 10:39:55'),
(1056, 901, 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.3 Safari/605.1.15', 'https://m.facebook.com/', 'Perú', 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b856', 1, 'meta', 'cpc', 'camp_901', 'reportes automaticos', 'story_desliza_arriba', '2026-10-08 08:47:55'),
(1057, 904, 'Mozilla/5.0 (Linux; Android 13; Pixel 7 Pro) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.6167.178 Mobile Safari/537.36 Instagram 319.0.0.33.109', 'https://l.instagram.com/', 'Argentina', 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b857', 1, 'meta', 'cpc', 'camp_904', 'dashboard ventas', 'post_descuento_20', '2026-10-05 08:17:55'),
(1058, 902, 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36', 'https://l.instagram.com/', 'México', 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b858', 1, 'meta', 'cpc', 'camp_902', 'analitica software', 'carrusel_beneficios', '2026-10-10 06:01:55'),
(1059, 903, 'Mozilla/5.0 (Linux; Android 13; Pixel 7 Pro) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.6167.178 Mobile Safari/537.36 Instagram 319.0.0.33.109', 'https://l.facebook.com/', 'Colombia', 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b859', 1, 'meta', 'cpc', 'camp_903', 'bi pymes', 'video_demo_15s', '2026-10-10 17:14:55'),
(1060, 904, 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36', 'https://l.instagram.com/', 'Chile', 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b860', 0, 'meta', 'cpc', 'camp_904', 'bi pymes', 'post_descuento_20', '2026-10-02 07:05:55'),
(1061, 901, 'Mozilla/5.0 (Linux; Android 13; Pixel 7 Pro) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.6167.178 Mobile Safari/537.36 Instagram 319.0.0.33.109', 'https://l.instagram.com/', 'Perú', 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b861', 0, 'meta', 'cpc', 'camp_901', 'meta ads tracking', 'carrusel_beneficios', '2026-10-06 17:05:55'),
(1062, 904, 'Mozilla/5.0 (Linux; Android 13; Pixel 7 Pro) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.6167.178 Mobile Safari/537.36 Instagram 319.0.0.33.109', 'https://m.facebook.com/', 'Perú', 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b862', 1, 'meta', 'cpc', 'camp_904', 'bi pymes', 'post_descuento_20', '2026-10-14 22:13:55'),
(1063, 904, 'Mozilla/5.0 (Linux; Android 14; SM-S918B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.6261.119 Mobile Safari/537.36 [FB_IAB/FB4A;FBAV/455.0.0.44.109;]', 'https://l.instagram.com/', 'Colombia', 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b863', 1, 'meta', 'cpc', 'camp_904', 'reportes automaticos', 'banner_azul_cta', '2026-10-06 14:53:55'),
(1064, 901, 'Mozilla/5.0 (iPhone; CPU iPhone OS 17_4 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148 [FBAN/FBIOS;FBDV/iPhone14,2;FBMD/iPhone;FBSN/iOS;FBSV/17.4;FBSS/3;FBCR/Claro;FBID/phone;FBLC/es_ES;FBOP/5]', 'https://l.instagram.com/', 'Colombia', 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b864', 1, 'meta', 'cpc', 'camp_901', 'dashboard ventas', 'banner_azul_cta', '2026-10-09 16:00:55'),
(1065, 902, 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.3 Safari/605.1.15', 'https://instagram.com/', 'España', 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b865', 1, 'meta', 'cpc', 'camp_902', 'bi pymes', 'carrusel_beneficios', '2026-10-05 23:51:55'),
(1066, 901, 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.3 Safari/605.1.15', 'https://l.facebook.com/', 'Argentina', 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b866', 0, 'meta', 'cpc', 'camp_901', 'meta ads tracking', 'video_demo_15s', '2026-09-30 19:01:55'),
(1067, 901, 'Mozilla/5.0 (iPhone; CPU iPhone OS 17_4 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148 [FBAN/FBIOS;FBDV/iPhone14,2;FBMD/iPhone;FBSN/iOS;FBSV/17.4;FBSS/3;FBCR/Claro;FBID/phone;FBLC/es_ES;FBOP/5]', 'https://m.facebook.com/', 'México', 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b867', 1, 'meta', 'cpc', 'camp_901', 'reportes automaticos', 'video_demo_15s', '2026-10-10 03:48:55'),
(1068, 901, 'Mozilla/5.0 (Linux; Android 13; Pixel 7 Pro) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.6167.178 Mobile Safari/537.36 Instagram 319.0.0.33.109', 'https://m.facebook.com/', 'Perú', 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b868', 1, 'meta', 'cpc', 'camp_901', 'meta ads tracking', 'video_demo_15s', '2026-10-01 19:11:55'),
(1069, 901, 'Mozilla/5.0 (Linux; Android 14; SM-S918B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.6261.119 Mobile Safari/537.36 [FB_IAB/FB4A;FBAV/455.0.0.44.109;]', 'https://instagram.com/', 'Colombia', 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b869', 1, 'meta', 'cpc', 'camp_901', 'meta ads tracking', 'story_desliza_arriba', '2026-10-07 01:06:55'),
(1070, 902, 'Mozilla/5.0 (iPhone; CPU iPhone OS 17_4 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148 [FBAN/FBIOS;FBDV/iPhone14,2;FBMD/iPhone;FBSN/iOS;FBSV/17.4;FBSS/3;FBCR/Claro;FBID/phone;FBLC/es_ES;FBOP/5]', 'https://m.facebook.com/', 'Colombia', 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b870', 1, 'meta', 'cpc', 'camp_902', 'meta ads tracking', 'story_desliza_arriba', '2026-10-12 19:58:55'),
(1071, 905, 'Mozilla/5.0 (iPhone; CPU iPhone OS 17_4 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148 [FBAN/FBIOS;FBDV/iPhone14,2;FBMD/iPhone;FBSN/iOS;FBSV/17.4;FBSS/3;FBCR/Claro;FBID/phone;FBLC/es_ES;FBOP/5]', 'https://instagram.com/', 'Argentina', 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b871', 1, 'meta', 'cpc', 'camp_905', 'meta ads tracking', 'banner_azul_cta', '2026-10-04 01:45:55'),
(1072, 901, 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.3 Safari/605.1.15', 'https://l.instagram.com/', 'Colombia', 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b872', 1, 'meta', 'cpc', 'camp_901', 'meta ads tracking', 'post_descuento_20', '2026-10-12 02:31:55'),
(1073, 905, 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36', 'https://l.instagram.com/', 'Perú', 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b873', 1, 'meta', 'cpc', 'camp_905', 'reportes automaticos', 'carrusel_beneficios', '2026-10-08 06:03:55'),
(1074, 901, 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36', 'https://l.instagram.com/', 'México', 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b874', 1, 'meta', 'cpc', 'camp_901', 'reportes automaticos', 'story_desliza_arriba', '2026-10-06 23:06:55'),
(1075, 904, 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36', 'https://m.facebook.com/', 'Perú', 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b875', 1, 'meta', 'cpc', 'camp_904', 'meta ads tracking', 'carrusel_beneficios', '2026-10-09 05:21:55'),
(1076, 903, 'Mozilla/5.0 (Linux; Android 13; Pixel 7 Pro) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.6167.178 Mobile Safari/537.36 Instagram 319.0.0.33.109', 'https://l.facebook.com/', 'Argentina', 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b876', 1, 'meta', 'cpc', 'camp_903', 'analitica software', 'video_demo_15s', '2026-10-06 08:07:55'),
(1077, 902, 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.3 Safari/605.1.15', 'https://l.instagram.com/', 'Perú', 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b877', 1, 'meta', 'cpc', 'camp_902', 'analitica software', 'carrusel_beneficios', '2026-10-10 13:03:55'),
(1078, 902, 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36', 'https://instagram.com/', 'Perú', 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b878', 1, 'meta', 'cpc', 'camp_902', 'meta ads tracking', 'post_descuento_20', '2026-10-03 01:29:55'),
(1079, 904, 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36', 'https://instagram.com/', 'México', 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b879', 1, 'meta', 'cpc', 'camp_904', 'dashboard ventas', 'carrusel_beneficios', '2026-10-12 20:47:55'),
(1080, 902, 'Mozilla/5.0 (Linux; Android 14; SM-S918B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.6261.119 Mobile Safari/537.36 [FB_IAB/FB4A;FBAV/455.0.0.44.109;]', 'https://m.facebook.com/', 'Perú', 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b880', 1, 'meta', 'cpc', 'camp_902', 'reportes automaticos', 'story_desliza_arriba', '2026-10-02 00:09:55'),
(1081, 901, 'Mozilla/5.0 (Linux; Android 14; SM-S918B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.6261.119 Mobile Safari/537.36 [FB_IAB/FB4A;FBAV/455.0.0.44.109;]', 'https://instagram.com/', 'México', 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b881', 1, 'meta', 'cpc', 'camp_901', 'meta ads tracking', 'banner_azul_cta', '2026-10-03 10:22:55'),
(1082, 901, 'Mozilla/5.0 (iPhone; CPU iPhone OS 17_4 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148 [FBAN/FBIOS;FBDV/iPhone14,2;FBMD/iPhone;FBSN/iOS;FBSV/17.4;FBSS/3;FBCR/Claro;FBID/phone;FBLC/es_ES;FBOP/5]', 'https://instagram.com/', 'Colombia', 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b882', 1, 'meta', 'cpc', 'camp_901', 'bi pymes', 'banner_azul_cta', '2026-10-15 07:23:55'),
(1083, 904, 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.3 Safari/605.1.15', 'https://l.instagram.com/', 'España', 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b883', 1, 'meta', 'cpc', 'camp_904', 'analitica software', 'carrusel_beneficios', '2026-10-04 17:10:55'),
(1084, 901, 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.3 Safari/605.1.15', 'https://l.instagram.com/', 'Colombia', 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b884', 1, 'meta', 'cpc', 'camp_901', 'analitica software', 'video_demo_15s', '2026-10-12 04:36:55'),
(1085, 903, 'Mozilla/5.0 (iPhone; CPU iPhone OS 17_4 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148 [FBAN/FBIOS;FBDV/iPhone14,2;FBMD/iPhone;FBSN/iOS;FBSV/17.4;FBSS/3;FBCR/Claro;FBID/phone;FBLC/es_ES;FBOP/5]', 'https://m.facebook.com/', 'Colombia', 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b885', 1, 'meta', 'cpc', 'camp_903', 'bi pymes', 'story_desliza_arriba', '2026-10-02 00:31:55'),
(1086, 902, 'Mozilla/5.0 (Linux; Android 13; Pixel 7 Pro) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.6167.178 Mobile Safari/537.36 Instagram 319.0.0.33.109', 'https://l.instagram.com/', 'Perú', 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b886', 1, 'meta', 'cpc', 'camp_902', 'meta ads tracking', 'story_desliza_arriba', '2026-10-05 19:53:55'),
(1087, 905, 'Mozilla/5.0 (iPhone; CPU iPhone OS 17_4 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148 [FBAN/FBIOS;FBDV/iPhone14,2;FBMD/iPhone;FBSN/iOS;FBSV/17.4;FBSS/3;FBCR/Claro;FBID/phone;FBLC/es_ES;FBOP/5]', 'https://l.facebook.com/', 'México', 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b887', 1, 'meta', 'cpc', 'camp_905', 'meta ads tracking', 'banner_azul_cta', '2026-10-12 00:18:55'),
(1088, 905, 'Mozilla/5.0 (iPhone; CPU iPhone OS 17_4 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148 [FBAN/FBIOS;FBDV/iPhone14,2;FBMD/iPhone;FBSN/iOS;FBSV/17.4;FBSS/3;FBCR/Claro;FBID/phone;FBLC/es_ES;FBOP/5]', 'https://m.facebook.com/', 'Colombia', 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b888', 1, 'meta', 'cpc', 'camp_905', 'reportes automaticos', 'post_descuento_20', '2026-10-08 23:01:55'),
(1089, 903, 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36', 'https://l.instagram.com/', 'Colombia', 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b889', 1, 'meta', 'cpc', 'camp_903', 'meta ads tracking', 'story_desliza_arriba', '2026-10-11 02:02:55'),
(1090, 905, 'Mozilla/5.0 (Linux; Android 14; SM-S918B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.6261.119 Mobile Safari/537.36 [FB_IAB/FB4A;FBAV/455.0.0.44.109;]', 'https://m.facebook.com/', 'México', 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b890', 1, 'meta', 'cpc', 'camp_905', 'analitica software', 'banner_azul_cta', '2026-10-11 19:28:55'),
(1091, 905, 'Mozilla/5.0 (Linux; Android 13; Pixel 7 Pro) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.6167.178 Mobile Safari/537.36 Instagram 319.0.0.33.109', 'https://instagram.com/', 'Perú', 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b891', 0, 'meta', 'cpc', 'camp_905', 'meta ads tracking', 'post_descuento_20', '2026-10-09 09:24:55'),
(1092, 904, 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.3 Safari/605.1.15', 'https://l.facebook.com/', 'Estados Unidos', 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b892', 0, 'meta', 'cpc', 'camp_904', 'bi pymes', 'carrusel_beneficios', '2026-10-01 20:22:55'),
(1093, 901, 'Mozilla/5.0 (Linux; Android 14; SM-S918B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.6261.119 Mobile Safari/537.36 [FB_IAB/FB4A;FBAV/455.0.0.44.109;]', 'https://l.facebook.com/', 'México', 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b893', 1, 'meta', 'cpc', 'camp_901', 'dashboard ventas', 'post_descuento_20', '2026-10-03 18:39:55'),
(1094, 903, 'Mozilla/5.0 (Linux; Android 14; SM-S918B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.6261.119 Mobile Safari/537.36 [FB_IAB/FB4A;FBAV/455.0.0.44.109;]', 'https://l.instagram.com/', 'Perú', 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b894', 1, 'meta', 'cpc', 'camp_903', 'bi pymes', 'carrusel_beneficios', '2026-10-06 07:04:55'),
(1095, 901, 'Mozilla/5.0 (Linux; Android 14; SM-S918B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.6261.119 Mobile Safari/537.36 [FB_IAB/FB4A;FBAV/455.0.0.44.109;]', 'https://instagram.com/', 'Chile', 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b895', 1, 'meta', 'cpc', 'camp_901', 'meta ads tracking', 'post_descuento_20', '2026-10-03 01:39:55'),
(1096, 901, 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36', 'https://instagram.com/', 'España', 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b896', 0, 'meta', 'cpc', 'camp_901', 'bi pymes', 'story_desliza_arriba', '2026-10-15 13:27:55'),
(1097, 905, 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.3 Safari/605.1.15', 'https://l.instagram.com/', 'Colombia', 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b897', 1, 'meta', 'cpc', 'camp_905', 'meta ads tracking', 'story_desliza_arriba', '2026-10-04 05:50:55'),
(1098, 901, 'Mozilla/5.0 (Linux; Android 14; SM-S918B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.6261.119 Mobile Safari/537.36 [FB_IAB/FB4A;FBAV/455.0.0.44.109;]', 'https://instagram.com/', 'Argentina', 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b898', 0, 'meta', 'cpc', 'camp_901', 'meta ads tracking', 'post_descuento_20', '2026-10-04 13:21:55'),
(1099, 905, 'Mozilla/5.0 (Linux; Android 14; SM-S918B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.6261.119 Mobile Safari/537.36 [FB_IAB/FB4A;FBAV/455.0.0.44.109;]', 'https://m.facebook.com/', 'México', 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b899', 1, 'meta', 'cpc', 'camp_905', 'reportes automaticos', 'post_descuento_20', '2026-10-13 11:10:55'),
(1100, 901, 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.3 Safari/605.1.15', 'https://l.facebook.com/', 'Colombia', 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b8100', 1, 'meta', 'cpc', 'camp_901', 'meta ads tracking', 'story_desliza_arriba', '2026-10-09 08:45:55');

-- 7. Conversiones y Ventas generadas a partir de los Clicks de Meta
INSERT INTO `conversions` (`id_click`, `revenue`, `source`, `notes`, `type`, `created_at`) VALUES
(1002, 0.00, 'meta_ads', 'Conversión atribuida a campaña Meta Ads (CONTACT)', 'contact', '2026-10-02 19:51:55'),
(1010, 0.00, 'meta_ads', 'Conversión atribuida a campaña Meta Ads (LEAD)', 'lead', '2026-10-09 13:41:55'),
(1011, 0.00, 'meta_ads', 'Conversión atribuida a campaña Meta Ads (DOWNLOAD)', 'download', '2026-10-07 08:29:55'),
(1012, 0.00, 'meta_ads', 'Conversión atribuida a campaña Meta Ads (CONTACT)', 'contact', '2026-10-01 07:32:55'),
(1014, 0.00, 'meta_ads', 'Conversión atribuida a campaña Meta Ads (DOWNLOAD)', 'download', '2026-10-05 06:35:55'),
(1015, 0.00, 'meta_ads', 'Conversión atribuida a campaña Meta Ads (LEAD)', 'lead', '2026-10-01 17:59:55'),
(1020, 160.49, 'meta_ads', 'Conversión atribuida a campaña Meta Ads (SALE)', 'sale', '2026-10-02 05:09:55'),
(1021, 0.00, 'meta_ads', 'Conversión atribuida a campaña Meta Ads (CONTACT)', 'contact', '2026-10-03 21:29:55'),
(1022, 0.00, 'meta_ads', 'Conversión atribuida a campaña Meta Ads (DOWNLOAD)', 'download', '2026-10-06 07:56:55'),
(1024, 163.13, 'meta_ads', 'Conversión atribuida a campaña Meta Ads (SALE)', 'sale', '2026-10-05 23:51:55'),
(1028, 0.00, 'meta_ads', 'Conversión atribuida a campaña Meta Ads (DOWNLOAD)', 'download', '2026-10-03 06:18:55'),
(1033, 0.00, 'meta_ads', 'Conversión atribuida a campaña Meta Ads (CONTACT)', 'contact', '2026-10-03 08:56:55'),
(1035, 0.00, 'meta_ads', 'Conversión atribuida a campaña Meta Ads (LEAD)', 'lead', '2026-10-09 13:54:55'),
(1049, 0.00, 'meta_ads', 'Conversión atribuida a campaña Meta Ads (DOWNLOAD)', 'download', '2026-10-12 16:51:55'),
(1050, 0.00, 'meta_ads', 'Conversión atribuida a campaña Meta Ads (SIGNUP)', 'signup', '2026-10-09 01:35:55'),
(1054, 0.00, 'meta_ads', 'Conversión atribuida a campaña Meta Ads (DOWNLOAD)', 'download', '2026-10-06 12:15:55'),
(1059, 0.00, 'meta_ads', 'Conversión atribuida a campaña Meta Ads (DOWNLOAD)', 'download', '2026-10-10 17:28:55'),
(1066, 0.00, 'meta_ads', 'Conversión atribuida a campaña Meta Ads (CONTACT)', 'contact', '2026-09-30 19:13:55'),
(1067, 0.00, 'meta_ads', 'Conversión atribuida a campaña Meta Ads (LEAD)', 'lead', '2026-10-10 04:12:55'),
(1081, 0.00, 'meta_ads', 'Conversión atribuida a campaña Meta Ads (LEAD)', 'lead', '2026-10-03 10:42:55'),
(1083, 0.00, 'meta_ads', 'Conversión atribuida a campaña Meta Ads (CONTACT)', 'contact', '2026-10-04 17:19:55'),
(1087, 0.00, 'meta_ads', 'Conversión atribuida a campaña Meta Ads (CONTACT)', 'contact', '2026-10-12 00:21:55'),
(1088, 0.00, 'meta_ads', 'Conversión atribuida a campaña Meta Ads (SIGNUP)', 'signup', '2026-10-08 23:26:55'),
(1095, 0.00, 'meta_ads', 'Conversión atribuida a campaña Meta Ads (CONTACT)', 'contact', '2026-10-03 02:03:55'),
(1098, 0.00, 'meta_ads', 'Conversión atribuida a campaña Meta Ads (CONTACT)', 'contact', '2026-10-04 13:35:55'),
(1099, 0.00, 'meta_ads', 'Conversión atribuida a campaña Meta Ads (LEAD)', 'lead', '2026-10-13 11:27:55');

SET FOREIGN_KEY_CHECKS = 1;
-- Fin del dataset de prueba.