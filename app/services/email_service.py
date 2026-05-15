import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import logging

logger = logging.getLogger(__name__)

def send_email(to_email: str, subject: str, body: str):
    """
    Envía un correo electrónico usando SMTP.
    Requiere las variables de entorno:
    SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASSWORD, SMTP_FROM
    """
    smtp_host = os.getenv("SMTP_HOST")
    smtp_port = os.getenv("SMTP_PORT", "587")
    smtp_user = os.getenv("SMTP_USER")
    smtp_pass = os.getenv("SMTP_PASSWORD")
    smtp_from = os.getenv("SMTP_FROM", smtp_user)

    if not all([smtp_host, smtp_user, smtp_pass]):
        logger.warning(f"SMTP no configurado. El correo para {to_email} no se envió. Contenido: {body}")
        print(f"MOCK EMAIL to {to_email}: {subject} - {body}")
        return False

    try:
        msg = MIMEMultipart()
        msg['From'] = smtp_from
        msg['To'] = to_email
        msg['Subject'] = subject

        msg.attach(MIMEText(body, 'html'))

        server = smtplib.SMTP(smtp_host, int(smtp_port))
        server.starttls()
        server.login(smtp_user, smtp_pass)
        server.send_message(msg)
        server.quit()
        
        logger.info(f"Email enviado exitosamente a {to_email}")
        return True
    except Exception as e:
        logger.error(f"Error enviando email a {to_email}: {e}")
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
