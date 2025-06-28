#!/usr/bin/env python3
"""
Script para configurar email do sistema
"""
import os
import getpass

def configure_email():
    """Configura as credenciais de email"""
    print("🔐 Configuração de Email - Sistema de Login com Firewall")
    print("=" * 60)
    
    print("Para usar Gmail:")
    print("1. Ative a verificação em duas etapas")
    print("2. Gere uma senha de app")
    print("3. Use a senha de app (não sua senha normal)")
    print()
    
    # Solicitar informações
    email = input("📧 Digite seu email (ex: seu-email@gmail.com): ").strip()
    
    if not email:
        print("❌ Email é obrigatório!")
        return False
    
    # Solicitar senha de forma segura
    password = getpass.getpass("🔑 Digite sua senha de app: ")
    
    if not password:
        print("❌ Senha é obrigatória!")
        return False
    
    # Configurar variáveis de ambiente
    os.environ['MAIL_USERNAME'] = email
    os.environ['MAIL_PASSWORD'] = password
    os.environ['MAIL_DEFAULT_SENDER'] = email
    os.environ['MAIL_SERVER'] = 'smtp.gmail.com'
    os.environ['MAIL_PORT'] = '587'
    os.environ['MAIL_USE_TLS'] = 'true'
    os.environ['ADMIN_EMAIL'] = email
    os.environ['APP_NAME'] = 'Sistema de Login com Firewall'
    
    # Salvar no arquivo .env
    env_content = f"""# Configurações do Sistema de Login com Firewall
# =============================================

# Ambiente da aplicação
FLASK_ENV=development

# Chave secreta (ALTERE EM PRODUÇÃO!)
SECRET_KEY=dev-secret-key-change-in-production

# Configurações do banco de dados
DATABASE_URL=sqlite:///firewall_login.db

# Configurações de email (Gmail)
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=true
MAIL_USERNAME={email}
MAIL_PASSWORD={password}
MAIL_DEFAULT_SENDER={email}

# Email do administrador
ADMIN_EMAIL={email}

# Configurações de logging
LOG_LEVEL=INFO
LOG_FILE=firewall_login.log

# Configurações do firewall
FIREWALL_CHAIN=FIREWALL_LOGIN_ALLOW
IPTABLES_PATH=/sbin/iptables
IP6TABLES_PATH=/sbin/ip6tables

# Configurações de rate limiting
RATELIMIT_STORAGE_URL=memory://
RATELIMIT_DEFAULT=100 per hour
"""
    
    try:
        with open('.env', 'w') as f:
            f.write(env_content)
        
        print("✅ Configuração salva no arquivo .env")
        print(f"📧 Email configurado: {email}")
        print()
        print("🚀 Agora você pode testar o envio de emails:")
        print("   python test_email.py")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro ao salvar configuração: {str(e)}")
        return False

def test_email_config():
    """Testa a configuração de email"""
    print("🧪 Testando configuração de email...")
    
    try:
        from dotenv import load_dotenv
        load_dotenv()
        
        # Verificar se as variáveis estão configuradas
        required_vars = ['MAIL_USERNAME', 'MAIL_PASSWORD', 'MAIL_DEFAULT_SENDER']
        missing_vars = []
        
        for var in required_vars:
            if not os.environ.get(var):
                missing_vars.append(var)
        
        if missing_vars:
            print(f"❌ Variáveis faltando: {', '.join(missing_vars)}")
            return False
        
        print("✅ Configuração de email válida!")
        return True
        
    except ImportError:
        print("❌ python-dotenv não está instalado")
        return False
    except Exception as e:
        print(f"❌ Erro ao testar configuração: {str(e)}")
        return False

def main():
    """Função principal"""
    if len(sys.argv) > 1 and sys.argv[1] == '--test':
        test_email_config()
        return
    
    # Verificar se já existe configuração
    if os.path.exists('.env'):
        print("📁 Arquivo .env já existe!")
        overwrite = input("Deseja sobrescrever? (s/N): ").strip().lower()
        if overwrite != 's':
            print("❌ Configuração cancelada")
            return
    
    # Configurar email
    if configure_email():
        print("\n🎉 Configuração concluída com sucesso!")
    else:
        print("\n❌ Falha na configuração")

if __name__ == '__main__':
    import sys
    main() 