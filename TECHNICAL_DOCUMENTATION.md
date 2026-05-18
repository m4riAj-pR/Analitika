# Documentación Técnica - Proyecto Analitika

## 1. Descripción General
**Analitika** es una plataforma integral de rastreo (tracking) y atribución para marketing digital. Su objetivo principal es permitir a los anunciantes entender el recorrido del usuario desde que hace clic en un anuncio hasta que se convierte en una oportunidad de venta, calculando métricas de rentabilidad en tiempo real.

---

## 2. Arquitectura Tecnológica
El proyecto utiliza un stack moderno y escalable:
*   **Backend:** FastAPI (Python 3.10+) - Framework de alto rendimiento.
*   **Base de Datos:** MySQL (Hosting en Railway) - Almacenamiento relacional.
*   **Seguridad:** JWT (JSON Web Tokens) para sesiones y BCrypt para hashing de contraseñas.
*   **Plantillas:** Jinja2 para el renderizado dinámico de Landing Pages.
*   **Notificaciones:** Servicio de Email mediante SendGrid API.
*   **Geolocalización:** Integración con `ip-api` para identificación geográfica.

---

## 3. Funcionalidades Principales (Core)
Actualmente, el sistema cumple con **22 funciones técnicas**, organizadas en 5 módulos:

### A. Gestión de Identidad y Seguridad (RBAC)
1.  **Autenticación JWT:** Gestión segura de sesiones.
2.  **Registro de Usuarios:** Onboarding de nuevos miembros del equipo.
3.  **Recuperación de Contraseña:** Flujo automatizado vía email con claves temporales.
4.  **Roles y Permisos:** 
    *   **Super Admin:** Control total global.
    *   **Owner:** Control total de su empresa, incluyendo eliminación de datos y exportación.
    *   **Manager:** Gestión y edición de campañas (sin permisos de eliminación).
5.  **Multi-Empresa (Multi-tenancy):** Aislamiento de datos; cada usuario solo ve lo que pertenece a su organización.

### B. Gestión de Campañas y Canales
6.  **CRUD de Campañas:** Ciclo de vida completo de las iniciativas de marketing.
7.  **Validación de Fechas:** Lógica de seguridad para evitar errores cronológicos.
8.  **Gestión de Canales:** Organización de tráfico por fuentes (Facebook, Google, etc.).
9.  **Firma de Creación:** Registro automático de quién creó cada campaña.

### C. Motor de Tracking y Conversión
10. **Generación de Enlaces (Tracking Links):** Creación de URLs únicas de rastreo.
11. **Extracción de UTMs:** Captura automática de etiquetas de marketing.
12. **Registro de Clics Avanzado:** Almacenamiento de IP, User-Agent y Referrer.
13. **Geolocalización IP:** Identificación automática del país del visitante.
14. **Landing Pages Dinámicas:** Renderizado en tiempo real de páginas de aterrizaje modernas.
15. **Registro de Conversiones (Leads):** Captura de intención de compra con un solo clic.

### D. Analítica e Inteligencia
16. **Cálculo de KPIs Financieros:** Automatización de métricas CPC, CPA, ROI, ROAS y AOV.
17. **Dashboard de Rendimiento:** Resumen visual de métricas críticas.
18. **Gráficas de Series Temporales:** Historial de clics por día.
19. **Alertas de Presupuesto:** Notificaciones al alcanzar el 80% y 100% del presupuesto.
20. **Motor de Recomendaciones:** Análisis automático basado en el rendimiento de la última semana.

### E. Herramientas de Administración
21. **Exportación CSV:** Descarga de datos de conversión (exclusivo para Owners/Admins).
22. **Sistema de Notificaciones:** Centro de alertas internas para el usuario.

---

## 4. Flujo de la Aplicación

### Flujo de Rastreo (Tracking Flow)
1.  **Entrada:** El usuario hace clic en un enlace como `https://analitika.app/c/5?utm_source=fb`.
2.  **Procesamiento:**
    *   El sistema identifica la campaña y el canal.
    *   Registra el clic y extrae las etiquetas UTM.
    *   Lanza una tarea en segundo plano (Background Task) para geolocalizar la IP.
3.  **Salida:** Se renderiza la `campana.html` (Landing Page) personalizada.

### Flujo de Conversión
1.  **Acción:** El usuario hace clic en "¡Asegurar mi oferta!".
2.  **Atribución:** El sistema vincula esa conversión con el `id_click` original, permitiendo saber exactamente qué anuncio generó la venta.
3.  **Actualización:** Se recalculan las métricas de la campaña instantáneamente.

### Flujo de Alertas de Presupuesto
1.  **Disparador:** Cuando un usuario revisa sus notificaciones, el sistema ejecuta un análisis de gasto.
2.  **Cálculo:** `(spent / budget) * 100`.
3.  **Notificación:** Si supera el 80%, inserta una alerta persistente en la base de datos para el dueño de la empresa.

---

## 5. Estructura de Datos (Tablas Clave)
*   **`users` / `persons`:** Datos de acceso y personales.
*   **`campaigns`:** Almacena presupuestos, gastos y estados.
*   **`tracking_links`:** El puente entre campañas y clics.
*   **`clicks`:** El "corazón" del rastreo (UTMs, IPs, metadata).
*   **`conversions`:** Resultados finales (ingresos, tipo de lead).
*   **`notifications`:** Alertas y recomendaciones del sistema.

---

## 6. Configuración y Despliegue
*   **Variables de Entorno:** Configuración crítica en `.env` (DB_URL, JWT_SECRET, SENDGRID_KEY).
*   **Migraciones:** El sistema cuenta con un motor de migraciones automáticas (`migrations.py`) que actualiza el esquema de la base de datos al iniciar la aplicación en Railway.
