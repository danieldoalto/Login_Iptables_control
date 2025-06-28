import smtplib
import imaplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.header import decode_header
import ssl

# Configurações do Zoho Mail
EMAIL_ADDRESS = "system.administrator@dansoft.net.br"  # Substitua pelo seu e-mail
PASSWORD = "zSM8QHcf7Kuz"  # Senha normal ou senha de aplicativo (com 2FA)
SMTP_SERVER = "smtp.zoho.com"
SMTP_PORT = 587  # Porta para TLS
IMAP_SERVER = "imap.zoho.com"
IMAP_PORT = 993  # Porta para SSL

# Função para enviar e-mail via SMTP
def send_email(to_email, subject, body):
    try:
        # Criar mensagem
        msg = MIMEMultipart()
        msg['From'] = EMAIL_ADDRESS
        msg['To'] = to_email
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain'))

        # Configurar conexão SMTP com TLS
        context = ssl.create_default_context()
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls(context=context)  # Ativar TLS
            server.login(EMAIL_ADDRESS, PASSWORD)
            server.sendmail(EMAIL_ADDRESS, to_email, msg.as_string())
        print(f"E-mail enviado para {to_email} com sucesso!")
    except Exception as e:
        print(f"Erro ao enviar e-mail: {e}")

# Função para receber e-mails via IMAP
def fetch_emails(max_emails=5):
    try:
        # Conectar ao servidor IMAP
        mail = imaplib.IMAP4_SSL(IMAP_SERVER, IMAP_PORT)
        mail.login(EMAIL_ADDRESS, PASSWORD)
        mail.select("inbox")  # Selecionar caixa de entrada

        # Buscar e-mails (todos, não lidos, etc.)
        status, messages = mail.search(None, "ALL")  # Use "UNSEEN" para e-mails não lidos
        email_ids = messages[0].split()[:max_emails]  # Limitar aos últimos 'max_emails'

        emails = []
        for email_id in email_ids:
            status, msg_data = mail.fetch(email_id, "(RFC822)")
            raw_email = msg_data[0][1]
            
            # Parsear e-mail
            from email.message import EmailMessage
            msg = EmailMessage()
            msg.set_content(raw_email)
            
            # Decodificar assunto
            subject, encoding = decode_header(msg['subject'])[0]
            if isinstance(subject, bytes):
                subject = subject.decode(encoding if encoding else 'utf-8')
            
            # Obter remetente
            from_address = msg['from']
            
            # Obter corpo do e-mail (apenas texto por simplicidade)
            body = ""
            if msg.is_multipart():
                for part in msg.walk():
                    if part.get_content_type() == "text/plain":
                        body = part.get_payload(decode=True).decode()
                        break
            else:
                body = msg.get_payload(decode=True).decode()

            emails.append({
                'from': from_address,
                'subject': subject,
                'body': body
            })

        # Fechar conexão
        mail.logout()
        return emails
    except Exception as e:
        print(f"Erro ao receber e-mails: {e}")
        return []

# Exemplo de uso
if __name__ == "__main__":
    # Enviar e-mail
    send_email(
        to_email="danieldoalto@gmail.com",
        subject="Teste de envio via Zoho Mail",
        body="Olá, este é um e-mail de teste enviado via Python!"
    )

    # Receber e-mails
    emails = fetch_emails(max_emails=3)  # Receber até 3 e-mails
    for i, email in enumerate(emails, 1):
        print(f"\nE-mail {i}:")
        print(f"De: {email['from']}")
        print(f"Assunto: {email['subject']}")
        print(f"Corpo: {email['body'][:200]}...")  # Mostrar apenas os primeiros 200 caracteres