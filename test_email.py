#!/usr/bin/env python3
"""
Script independente para testar o envio de emails
"""
import os
import sys
from datetime import datetime

# Adicionar o diretório atual ao path para importar os módulos
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def create_test_user():
    """Cria um usuário de teste"""
    from app.models import User
    
    # Criar usuário de teste
    user = User(email='danieldoalto@gmail.com')
    user.confirmation_token = 'test-token-123456'
    user.confirmed = False
    user.created_at = datetime.utcnow()
    
    return user

def test_email_functions():
    """Testa as funções de email"""
    print("🚀 Iniciando testes de email...")
    print("=" * 50)
    
    try:
        # Carregar configurações do .env
        from dotenv import load_dotenv
        load_dotenv()
        
        # Importar módulos necessários
        from app import create_app, mail
        from app.email import send_confirmation_email, send_welcome_email, send_login_notification
        
        # Criar aplicação Flask
        app = create_app()
        
        with app.app_context():
            # Inicializar mail
            mail.init_app(app)
            
            # Criar usuário de teste
            user = create_test_user()
            
            print(f"📧 Configuração de email:")
            print(f"   Servidor: {app.config.get('MAIL_SERVER')}")
            print(f"   Porta: {app.config.get('MAIL_PORT')}")
            print(f"   Usuário: {app.config.get('MAIL_USERNAME')}")
            print(f"   Remetente: {app.config.get('MAIL_DEFAULT_SENDER')}")
            print()
            
            # Teste 1: Email de confirmação
            print("📨 Teste 1: Email de confirmação")
            try:
                send_confirmation_email(user)
                print("   ✅ Email de confirmação enviado com sucesso!")
            except Exception as e:
                print(f"   ❌ Erro ao enviar email de confirmação: {str(e)}")
            print()
            
            # Teste 2: Email de boas-vindas
            print("📨 Teste 2: Email de boas-vindas")
            try:
                send_welcome_email(user)
                print("   ✅ Email de boas-vindas enviado com sucesso!")
            except Exception as e:
                print(f"   ❌ Erro ao enviar email de boas-vindas: {str(e)}")
            print()
            
            # Teste 3: Notificação de login
            print("📨 Teste 3: Notificação de login")
            try:
                send_login_notification(user, '192.168.1.100', 'Mozilla/5.0 (Test Browser)')
                print("   ✅ Notificação de login enviada com sucesso!")
            except Exception as e:
                print(f"   ❌ Erro ao enviar notificação de login: {str(e)}")
            print()
            
    except ImportError as e:
        print(f"❌ Erro de importação: {str(e)}")
        print("   Certifique-se de que o ambiente virtual está ativo e as dependências instaladas")
    except Exception as e:
        print(f"❌ Erro geral: {str(e)}")

def main():
    """Função principal"""
    print("🔐 Teste de Email - Sistema de Login com Firewall")
    print("=" * 60)
    
    # Verificar se as configurações foram fornecidas
    if len(sys.argv) > 1 and sys.argv[1] == '--help':
        print("""
Uso: python test_email.py [opções]

Opções:
  --help          Mostra esta ajuda

Para usar este script:

1. Configure suas credenciais de email no arquivo .env
2. Para Gmail:
   - Ative a verificação em duas etapas
   - Gere uma senha de app
   - Use a senha de app no campo MAIL_PASSWORD

3. Execute: python test_email.py

O script irá:
- Carregar configurações do arquivo .env
- Usar as funções do módulo app.email
- Testar 3 tipos de emails: confirmação, boas-vindas e notificação de login
        """)
        return
    
    # Executar testes
    test_email_functions()
    
    print("=" * 60)
    print("✅ Testes concluídos!")
    print("📝 Verifique sua caixa de entrada para confirmar o recebimento dos emails")

if __name__ == '__main__':
    main() 