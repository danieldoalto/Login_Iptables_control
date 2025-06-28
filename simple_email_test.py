#!/usr/bin/env python3
"""
Script simples para testar envio de email
"""
import os
import sys
from datetime import datetime

# Adicionar o diretório atual ao path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_simple_email():
    """Testa envio de email simples"""
    print("📧 Teste Simples de Email")
    print("=" * 40)
    
    try:
        # Carregar configurações do .env
        from dotenv import load_dotenv
        load_dotenv()
        
        # Importar módulos
        from app import create_app, mail
        from app.email import send_email
        
        # Criar app
        app = create_app()
        
        with app.app_context():
            # Inicializar mail
            mail.init_app(app)
            
            print(f"📧 Configuração:")
            print(f"   Servidor: {app.config.get('MAIL_SERVER')}")
            print(f"   Usuário: {app.config.get('MAIL_USERNAME')}")
            print()
            
            # Email de teste - enviar para o próprio email configurado
            subject = f"[{app.config['APP_NAME']}] Teste de Email"
            recipients = [app.config.get('MAIL_USERNAME')]  # Enviar para o próprio email
            
            text_body = """
Olá!

Este é um email de teste do sistema de login com firewall.

Data e hora: {}

Se você recebeu este email, a configuração está funcionando corretamente!

Atenciosamente,
Sistema de Login
""".format(datetime.now().strftime('%d/%m/%Y às %H:%M:%S'))
            
            html_body = f"""
<html>
<body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
    <div style="background-color: #e3f2fd; padding: 20px; border-radius: 10px; border: 1px solid #2196f3;">
        <h2 style="color: #1976d2; text-align: center;">✅ Teste de Email</h2>
        
        <p>Olá!</p>
        
        <p>Este é um email de teste do <strong>{app.config['APP_NAME']}</strong>.</p>
        
        <div style="background-color: white; padding: 15px; border-radius: 5px; margin: 20px 0;">
            <p><strong>Data e hora:</strong> {datetime.now().strftime('%d/%m/%Y às %H:%M:%S')}</p>
            <p><strong>Status:</strong> Sistema funcionando corretamente!</p>
        </div>
        
        <div style="background-color: #c8e6c9; padding: 15px; border-radius: 5px; margin: 20px 0;">
            <p style="margin: 0; color: #2e7d32;">
                <strong>🎉 Sucesso!</strong> Se você recebeu este email, 
                a configuração de email está funcionando perfeitamente.
            </p>
        </div>
        
        <hr style="margin: 30px 0; border: none; border-top: 1px solid #eee;">
        
        <p style="font-size: 12px; color: #666;">
            Este é um email de teste automático.<br>
            Sistema de Login com Firewall
        </p>
    </div>
</body>
</html>
"""
            
            print("📨 Enviando email de teste...")
            
            # Enviar email
            send_email(
                subject=subject,
                sender=app.config['MAIL_DEFAULT_SENDER'],
                recipients=recipients,
                text_body=text_body,
                html_body=html_body
            )
            
            print("✅ Email enviado com sucesso!")
            print(f"📧 Destinatário: {recipients[0]}")
            print()
            print("💡 Verifique sua caixa de entrada (e spam)")
            
    except ImportError as e:
        print(f"❌ Erro de importação: {str(e)}")
        print("   Execute: pip install -r requirements.txt")
    except Exception as e:
        print(f"❌ Erro: {str(e)}")
        print()
        print("💡 Dicas:")
        print("   1. Verifique se as credenciais estão corretas")
        print("   2. Para Gmail, use senha de app (não senha normal)")
        print("   3. Ative verificação em duas etapas no Gmail")

if __name__ == '__main__':
    test_simple_email() 