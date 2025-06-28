"""
Módulo para envio de emails do sistema
"""
import logging
from flask import current_app, render_template
from flask_mail import Message
from app import mail
from threading import Thread
from datetime import datetime

logger = logging.getLogger(__name__)

def send_async_email(app, msg, email_type="genérico"):
    """Envia email de forma assíncrona"""
    with app.app_context():
        try:
            start_time = datetime.now()
            logger.info(f"📧 Iniciando envio de email {email_type} para: {msg.recipients}")
            
            mail.send(msg)
            
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            logger.info(f"✅ Email {email_type} enviado com sucesso para: {msg.recipients} (duração: {duration:.2f}s)")
            
        except Exception as e:
            logger.error(f"❌ Erro ao enviar email {email_type} para {msg.recipients}: {str(e)}")
            logger.exception(f"Detalhes do erro para email {email_type}:")

def send_email(subject, sender, recipients, text_body, html_body=None, email_type="genérico"):
    """Envia email usando Flask-Mail"""
    try:
        logger.info(f"📨 Preparando email {email_type}: {subject} -> {recipients}")
        
        msg = Message(subject, sender=sender, recipients=recipients)
        msg.body = text_body
        if html_body:
            msg.html = html_body
        
        # Enviar de forma assíncrona
        Thread(target=send_async_email, args=(current_app._get_current_object(), msg, email_type)).start()
        
        logger.info(f"📤 Email {email_type} adicionado à fila de envio")
        
    except Exception as e:
        logger.error(f"❌ Erro ao preparar email {email_type}: {str(e)}")
        raise

def send_confirmation_email(user):
    """Envia email de confirmação de registro"""
    try:
        logger.info(f"📧 Preparando email de confirmação para usuário: {user.email}")
        
        token = user.confirmation_token
        confirm_url = f"https://{current_app.config.get('SERVER_NAME', 'localhost')}/auth/confirm/{token}"
        
        subject = f"[{current_app.config['APP_NAME']}] Confirme seu email"
        
        # Renderizar template HTML
        html_body = render_template('emails/confirmation.html', 
                                  app_name=current_app.config['APP_NAME'],
                                  confirm_url=confirm_url)
        
        # Versão texto simples
        text_body = f"""
Olá!

Obrigado por se registrar no {current_app.config['APP_NAME']}.

Para ativar sua conta, clique no link abaixo:
{confirm_url}

Este link é válido por 1 hora.

Se você não se registrou em nosso sistema, ignore este email.

Atenciosamente,
Equipe {current_app.config['APP_NAME']}
"""
        
        send_email(
            subject=subject,
            sender=current_app.config['MAIL_DEFAULT_SENDER'],
            recipients=[user.email],
            text_body=text_body,
            html_body=html_body,
            email_type="confirmação"
        )
        
        logger.info(f"✅ Email de confirmação preparado para: {user.email}")
        
    except Exception as e:
        logger.error(f"❌ Erro ao preparar email de confirmação para {user.email}: {str(e)}")
        raise

def send_welcome_email(user):
    """Envia email de boas-vindas após confirmação"""
    try:
        logger.info(f"📧 Preparando email de boas-vindas para usuário: {user.email}")
        
        subject = f"[{current_app.config['APP_NAME']}] Bem-vindo! Sua conta foi ativada"
        login_url = f"https://{current_app.config.get('SERVER_NAME', 'localhost')}/auth/login"
        
        # Renderizar template HTML
        html_body = render_template('emails/welcome.html',
                                  app_name=current_app.config['APP_NAME'],
                                  login_url=login_url)
        
        # Versão texto simples
        text_body = f"""
Olá!

Sua conta no {current_app.config['APP_NAME']} foi ativada com sucesso!

Agora você pode fazer login em nosso sistema e ter acesso seguro aos nossos serviços.

Lembre-se:
- Suas sessões são válidas por 24 horas
- Seu IP será automaticamente liberado no firewall quando você fizer login
- Sempre faça logout quando terminar de usar o sistema

Para fazer login, acesse: {login_url}

Atenciosamente,
Equipe {current_app.config['APP_NAME']}
"""
        
        send_email(
            subject=subject,
            sender=current_app.config['MAIL_DEFAULT_SENDER'],
            recipients=[user.email],
            text_body=text_body,
            html_body=html_body,
            email_type="boas-vindas"
        )
        
        logger.info(f"✅ Email de boas-vindas preparado para: {user.email}")
        
    except Exception as e:
        logger.error(f"❌ Erro ao preparar email de boas-vindas para {user.email}: {str(e)}")
        raise

def send_login_notification(user, ip_address, user_agent=None):
    """Envia notificação de login realizado"""
    try:
        logger.info(f"📧 Preparando notificação de login para usuário: {user.email} (IP: {ip_address})")
        
        subject = f"[{current_app.config['APP_NAME']}] Login realizado em sua conta"
        login_time = datetime.now().strftime('%d/%m/%Y às %H:%M:%S')
        
        # Renderizar template HTML
        html_body = render_template('emails/login_notification.html',
                                  app_name=current_app.config['APP_NAME'],
                                  login_time=login_time,
                                  ip_address=ip_address,
                                  user_agent=user_agent or 'Não informado',
                                  admin_email=current_app.config.get('ADMIN_EMAIL', 'admin@localhost'))
        
        # Versão texto simples
        text_body = f"""
Olá!

Um login foi realizado em sua conta do {current_app.config['APP_NAME']}.

Detalhes do login:
- Data e hora: {login_time}
- IP: {ip_address}
- Navegador: {user_agent or 'Não informado'}

Se este login foi feito por você, pode ignorar este email.

Se você não fez este login, entre em contato conosco imediatamente.

Atenciosamente,
Equipe {current_app.config['APP_NAME']}
"""
        
        send_email(
            subject=subject,
            sender=current_app.config['MAIL_DEFAULT_SENDER'],
            recipients=[user.email],
            text_body=text_body,
            html_body=html_body,
            email_type="notificação de login"
        )
        
        logger.info(f"✅ Notificação de login preparada para: {user.email}")
        
    except Exception as e:
        logger.error(f"❌ Erro ao preparar notificação de login para {user.email}: {str(e)}")
        raise

def send_password_reset_email(user, token):
    """Envia email para reset de senha"""
    try:
        logger.info(f"📧 Preparando email de reset de senha para usuário: {user.email}")
        
        reset_url = f"https://{current_app.config.get('SERVER_NAME', 'localhost')}/auth/reset-password/{token}"
        
        subject = f"[{current_app.config['APP_NAME']}] Recuperação de senha"
        
        # Renderizar template HTML
        html_body = render_template('emails/password_reset.html',
                                  app_name=current_app.config['APP_NAME'],
                                  reset_url=reset_url)
        
        # Versão texto simples
        text_body = f"""
Olá!

Recebemos uma solicitação para redefinir a senha de sua conta no {current_app.config['APP_NAME']}.

Para redefinir sua senha, clique no link abaixo:
{reset_url}

Este link é válido por 1 hora.

Se você não solicitou a redefinição de senha, ignore este email.

Atenciosamente,
Equipe {current_app.config['APP_NAME']}
"""
        
        send_email(
            subject=subject,
            sender=current_app.config['MAIL_DEFAULT_SENDER'],
            recipients=[user.email],
            text_body=text_body,
            html_body=html_body,
            email_type="reset de senha"
        )
        
        logger.info(f"✅ Email de reset de senha preparado para: {user.email}")
        
    except Exception as e:
        logger.error(f"❌ Erro ao preparar email de reset de senha para {user.email}: {str(e)}")
        raise
