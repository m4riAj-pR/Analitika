import random
from datetime import datetime, timedelta

def generate_seed_sql():
    lines = []
    lines.append("-- =====================================================")
    lines.append("-- DATASET DE PRUEBA: 100 REGISTROS PARA LA EMPRESA ANALITIKA")
    lines.append("-- =====================================================")
    lines.append("SET FOREIGN_KEY_CHECKS = 0;")
    lines.append("")
    
    # 1. Asegurar la empresa Analitika
    lines.append("-- 1. Asegurar Usuario y Empresa Analitika")
    lines.append("INSERT INTO `persons` (`id_person`, `name`, `email`, `phone`)")
    lines.append("VALUES (999, 'Admin Analitika', 'admin@analitika.com', '+573001234567')")
    lines.append("ON DUPLICATE KEY UPDATE `name` = VALUES(`name`);")
    lines.append("")
    
    lines.append("INSERT INTO `users` (`id_user`, `id_person`, `id_company`, `id_role`, `username`, `password_hash`, `status`)")
    lines.append("VALUES (999, 999, NULL, 2, 'analitika_owner', '$2b$12$e8YkY.k4X7Z9e1k4Z7Z9e.k4X7Z9e1k4Z7Z9e.k4X7Z9e1k4Z7Z9e', 'active')")
    lines.append("ON DUPLICATE KEY UPDATE `username` = VALUES(`username`);")
    lines.append("")
    
    lines.append("INSERT INTO `companies` (`id_company`, `id_user`, `name`)")
    lines.append("VALUES (999, 999, 'Analitika')")
    lines.append("ON DUPLICATE KEY UPDATE `name` = VALUES(`name`);")
    lines.append("")
    
    lines.append("UPDATE `users` SET `id_company` = 999 WHERE `id_user` = 999;")
    lines.append("")
    
    lines.append("INSERT INTO `user_company` (`id_user`, `id_company`)")
    lines.append("VALUES (999, 999)")
    lines.append("ON DUPLICATE KEY UPDATE `id_company` = VALUES(`id_company`);")
    lines.append("")
    
    # 2. Conexión de prueba con Meta Ads
    lines.append("-- 2. Conexión de prueba con Meta Ads")
    lines.append("INSERT INTO `ad_account_connections` (`id_connection`, `id_company`, `provider`, `external_account_id`, `account_name`, `access_token`, `status`, `connected_by`)")
    lines.append("VALUES (999, 999, 'meta', 'act_1112068198074147', 'Analitika Meta Ads Business', 'test_encrypted_token_sample', 'active', 999)")
    lines.append("ON DUPLICATE KEY UPDATE `account_name` = VALUES(`account_name`);")
    lines.append("")
    
    # 3. 5 Campañas publicitarias
    lines.append("-- 3. Campañas publicitarias de Analitika")
    campaigns = [
        (901, "Campaña Meta Brand Awareness Q1", "draft", 1200.0, 5000.0, -45, -15),
        (902, "Generación de Leads B2B Meta Ads", "active", 3450.50, 8000.0, -30, 15),
        (903, "Conversión Ecommerce Primavera", "active", 5600.00, 10000.0, -20, 20),
        (904, "Retargeting Clientes Carrito Abandonado", "active", 2150.75, 4500.0, -15, 15),
        (905, "Lanzamiento App Móvil Analitika", "paused", 890.00, 3000.0, -10, 30),
    ]
    
    now = datetime.now()
    for cid, cname, status, spent, budget, start_delta, end_delta in campaigns:
        s_date = (now + timedelta(days=start_delta)).strftime("%Y-%m-%d")
        e_date = (now + timedelta(days=end_delta)).strftime("%Y-%m-%d")
        lines.append(f"INSERT INTO `campaigns` (`id_campaign`, `id_company`, `name`, `description`, `status`, `start_date`, `end_date`, `spent`, `budget`)")
        lines.append(f"VALUES ({cid}, 999, '{cname}', 'Campaña estratégica de prueba para Analitika', '{status}', '{s_date}', '{e_date}', {spent}, {budget})")
        lines.append(f"ON DUPLICATE KEY UPDATE `spent` = VALUES(`spent`), `budget` = VALUES(`budget`);")
    lines.append("")
    
    # Canales
    lines.append("-- Canales y Tracking Links")
    channels = [
        (901, 901, "Facebook Feed", "Anuncios en Feed de Facebook"),
        (902, 902, "Instagram Stories", "Historias patrocinadas en Instagram"),
        (903, 903, "Instagram Reels", "Reels promocionados"),
        (904, 904, "Facebook Marketplace", "Catálogo dinámico de productos"),
        (905, 905, "Audience Network", "Red de anuncios de Meta"),
    ]
    for ch_id, camp_id, ch_name, ch_desc in channels:
        lines.append(f"INSERT INTO `channels` (`id_channel`, `id_campaign`, `name`, `description`)")
        lines.append(f"VALUES ({ch_id}, {camp_id}, '{ch_name}', '{ch_desc}')")
        lines.append(f"ON DUPLICATE KEY UPDATE `name` = VALUES(`name`);")
    lines.append("")
    
    # Tracking links
    for idx, (ch_id, camp_id, ch_name, _) in enumerate(channels, 1):
        code = f"ana_{camp_id}_{idx}"
        dest = f"https://analitika.com/landing?utm_source=meta&utm_medium=cpc&utm_campaign=camp_{camp_id}"
        lines.append(f"INSERT INTO `tracking_links` (`id_link`, `id_campaign`, `id_channel`, `destination`, `short_code`)")
        lines.append(f"VALUES ({camp_id}, {camp_id}, {ch_id}, '{dest}', '{code}')")
        lines.append(f"ON DUPLICATE KEY UPDATE `short_code` = VALUES(`short_code`);")
    lines.append("")
    
    # 4. Mapeo a Meta Ads
    lines.append("-- 4. Mapeo de Campañas con Meta Ads")
    for idx, (cid, cname, _, _, _, _, _) in enumerate(campaigns, 1):
        ext_id = f"meta_camp_1607_{cid}"
        lines.append(f"INSERT INTO `campaign_external_mapping` (`id_mapping`, `id_campaign`, `id_connection`, `external_campaign_id`, `external_campaign_name`, `sync_enabled`)")
        lines.append(f"VALUES ({cid}, {cid}, 999, '{ext_id}', '{cname}', 1)")
        lines.append(f"ON DUPLICATE KEY UPDATE `external_campaign_name` = VALUES(`external_campaign_name`);")
    lines.append("")
    
    # 5. Métricas diarias agregadas (30 días de métricas = 30 registros)
    lines.append("-- 5. Métricas diarias externas (Meta Ads Insights)")
    lines.append("INSERT INTO `campaign_external_metrics` (`id_mapping`, `metric_date`, `impressions`, `spend`, `external_clicks`, `reach`) VALUES")
    metric_rows = []
    for day in range(30, 0, -1):
        m_date = (now - timedelta(days=day)).strftime("%Y-%m-%d")
        mapping_id = 902 if day % 2 == 0 else 903
        impressions = random.randint(1200, 8500)
        reach = int(impressions * random.uniform(0.75, 0.90))
        ext_clicks = int(impressions * random.uniform(0.02, 0.06))
        spend = round(ext_clicks * random.uniform(0.40, 1.20), 2)
        metric_rows.append(f"({mapping_id}, '{m_date}', {impressions}, {spend:.2f}, {ext_clicks}, {reach})")
    lines.append(",\n".join(metric_rows) + ";")
    lines.append("")
    
    # 6. 100 Clicks individuales con datos analíticos de usuario
    lines.append("-- 6. Dataset de 100 Clicks y Navegaciones para Analitika")
    lines.append("INSERT INTO `clicks` (`id_click`, `id_link`, `user_agent`, `referrer`, `country`, `ip_address_hash`, `consent_given`, `utm_source`, `utm_medium`, `utm_campaign`, `utm_term`, `utm_content`, `clicked_at`) VALUES")
    
    user_agents = [
        "Mozilla/5.0 (iPhone; CPU iPhone OS 17_4 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148 [FBAN/FBIOS;FBDV/iPhone14,2;FBMD/iPhone;FBSN/iOS;FBSV/17.4;FBSS/3;FBCR/Claro;FBID/phone;FBLC/es_ES;FBOP/5]",
        "Mozilla/5.0 (Linux; Android 14; SM-S918B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.6261.119 Mobile Safari/537.36 [FB_IAB/FB4A;FBAV/455.0.0.44.109;]",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.3 Safari/605.1.15",
        "Mozilla/5.0 (Linux; Android 13; Pixel 7 Pro) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.6167.178 Mobile Safari/537.36 Instagram 319.0.0.33.109"
    ]
    countries = ["Colombia", "Colombia", "Colombia", "México", "México", "España", "Chile", "Perú", "Argentina", "Estados Unidos"]
    referrers = ["https://l.facebook.com/", "https://m.facebook.com/", "https://instagram.com/", "https://l.instagram.com/"]
    terms = ["analitica software", "dashboard ventas", "meta ads tracking", "bi pymes", "reportes automaticos"]
    contents = ["banner_azul_cta", "video_demo_15s", "carrusel_beneficios", "post_descuento_20", "story_desliza_arriba"]
    
    click_rows = []
    conversion_candidate_ids = []
    
    random.seed(42)
    for i in range(1, 101):
        click_id = 1000 + i
        link_id = random.choice([901, 902, 903, 904, 905])
        ua = random.choice(user_agents)
        ref = random.choice(referrers)
        country = random.choice(countries)
        ip_hash = f"e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b8{i:02d}"
        consent = 1 if random.random() > 0.15 else 0
        utm_camp = f"camp_{link_id}"
        term = random.choice(terms)
        content = random.choice(contents)
        
        # Fecha en los últimos 15 días distribuida
        minutes_ago = random.randint(10, 15 * 24 * 60)
        c_time = (now - timedelta(minutes=minutes_ago)).strftime("%Y-%m-%d %H:%M:%S")
        
        click_rows.append(
            f"({click_id}, {link_id}, '{ua}', '{ref}', '{country}', '{ip_hash}', {consent}, 'meta', 'cpc', '{utm_camp}', '{term}', '{content}', '{c_time}')"
        )
        
        # 25% de probabilidad de generar conversión
        if random.random() < 0.25:
            conversion_candidate_ids.append((click_id, minutes_ago))
            
    lines.append(",\n".join(click_rows) + ";")
    lines.append("")
    
    # 7. Conversiones asociadas a los clicks
    lines.append("-- 7. Conversiones y Ventas generadas a partir de los Clicks de Meta")
    lines.append("INSERT INTO `conversions` (`id_click`, `revenue`, `source`, `notes`, `type`, `created_at`) VALUES")
    conv_rows = []
    conv_types = ["sale", "lead", "signup", "contact", "download"]
    for c_id, min_ago in conversion_candidate_ids:
        ctype = random.choice(conv_types)
        rev = round(random.uniform(49.99, 450.00), 2) if ctype == "sale" else 0.00
        notes = f"Conversión atribuida a campaña Meta Ads ({ctype.upper()})"
        conv_time = (now - timedelta(minutes=max(1, min_ago - random.randint(2, 30)))).strftime("%Y-%m-%d %H:%M:%S")
        conv_rows.append(f"({c_id}, {rev:.2f}, 'meta_ads', '{notes}', '{ctype}', '{conv_time}')")
        
    lines.append(",\n".join(conv_rows) + ";")
    lines.append("")
    lines.append("SET FOREIGN_KEY_CHECKS = 1;")
    lines.append("-- Fin del dataset de prueba.")
    
    return "\n".join(lines)

if __name__ == "__main__":
    sql_content = generate_seed_sql()
    with open("c:/Users/parra/analitika_CRUD/seed_analitika_100.sql", "w", encoding="utf-8") as f:
        f.write(sql_content)
    print("Generado seed_analitika_100.sql exitosamente.")
