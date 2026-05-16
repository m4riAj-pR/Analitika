import os
import json
import urllib.request
import urllib.error
import logging

logger = logging.getLogger(__name__)

def send_email(to_email: str, subject: str, body: str):
    """
    Envía un correo electrónico usando la API REST de SendGrid.
    Esto evita bloqueos de puertos SMTP en entornos como Railway Free.
    """
    api_key = os.getenv("SENDGRID_API_KEY")
    from_email = os.getenv("SENDGRID_FROM", "analitikaappmovil@gmail.com")

    if not api_key:
        logger.error("SENDGRID_API_KEY no configurada. No se pudo enviar el correo.")
        return False

    url = "https://api.sendgrid.com/v3/mail/send"
    
    data = {
        "personalizations": [
            {
                "to": [{"email": to_email}]
            }
        ],
        "from": {"email": from_email, "name": "Analitika"},
        "subject": subject,
        "content": [
            {
                "type": "text/html",
                "value": body
            }
        ]
    }

    try:
        req = urllib.request.Request(url)
        req.add_header("Authorization", f"Bearer {api_key}")
        req.add_header("Content-Type", "application/json")
        
        json_data = json.dumps(data).encode("utf-8")
        
        logger.info(f"Enviando correo vía SendGrid API a {to_email}...")
        
        with urllib.request.urlopen(req, data=json_data, timeout=15) as response:
            status = response.getcode()
            if status in [200, 201, 202]:
                logger.info(f"¡Correo enviado con éxito vía SendGrid a {to_email}!")
                return True
            else:
                logger.error(f"Error inesperado de SendGrid. Status: {status}")
                return False
                
    except urllib.error.HTTPError as e:
        error_body = e.read().decode("utf-8")
        logger.error(f"Error de API SendGrid ({e.code}): {error_body}")
        return False
    except Exception as e:
        logger.error(f"Error inesperado enviando vía SendGrid: {e}")
        return False

def send_password_reset_email(to_email: str, name: str, temp_pass: str):
    subject = "Restablecimiento de Contraseña - Analitika"
    body = f"""
    <html>
        <body style="font-family: Arial, sans-serif; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #eee; border-radius: 10px;">
                <h2 style="color: #6366f1;">Hola {name},</h2>
                <p>Has solicitado restablecer tu contraseña en <strong>Analitika</strong>.</p>
                <p>Tu clave temporal de acceso es:</p>
                <div style="background-color: #f3f4f6; padding: 15px; text-align: center; font-size: 24px; font-weight: bold; letter-spacing: 2px; color: #4f46e5; border-radius: 8px; margin: 20px 0;">
                    {temp_pass}
                </div>
                <p>Por favor, ingresa con esta clave y cámbiala lo antes posible desde tu perfil.</p>
                <hr style="border: 0; border-top: 1px solid #eee; margin: 20px 0;">
                <p style="font-size: 12px; color: #999;">Si no solicitaste este cambio, puedes ignorar este correo.</p>
            </div>
        </body>
    </html>
    """
    return send_email(to_email, subject, body)

def send_welcome_email(to_email: str, name: str):
    subject = "¡Bienvenido a Analitika!"
    body = f"""
    <html>
        <body style="font-family: Arial, sans-serif; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #eee; border-radius: 10px;">
                <h2 style="color: #6366f1;">¡Hola {name}!</h2>
                <p>Gracias por unirte a <strong>Analitika</strong>, la plataforma para optimizar tus campañas digitales.</p>
                <p>Ya puedes empezar a crear enlaces de seguimiento y analizar tus métricas en tiempo real.</p>
                <div style="text-align: center; margin: 30px 0;">
                    <a href="https://analitika.app/dashboard" style="background-color: #6366f1; color: white; padding: 12px 25px; text-decoration: none; border-radius: 5px; font-weight: bold;">Ir al Dashboard</a>
                </div>
                <p>Si tienes alguna duda, responde a este correo y nuestro equipo te ayudará.</p>
                <hr style="border: 0; border-top: 1px solid #eee; margin: 20px 0;">
                <p style="font-size: 12px; color: #999;">Analitika Team</p>
            </div>
        </body>
    </html>
    """
    return send_email(to_email, subject, body)
