#!/usr/bin/env python3
"""
Script para inicializar o banco de dados e criar o usuário administrador
"""
import os
import sys
from datetime import datetime

# Adicionar o diretório atual ao path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def init_database():
    """Inicializa o banco de dados e cria o administrador"""
    try:
        # Carregar configurações do .env
        from dotenv import load_dotenv
        load_dotenv()
        
        # Importar módulos necessários
        from app import create_app
        from app.models import db, User
        
        # Criar aplicação Flask
        app = create_app()
        
        with app.app_context():
            print("🗄️ Inicializando banco de dados...")
            
            # Criar todas as tabelas
            db.create_all()
            print("✅ Tabelas criadas com sucesso!")
            
            # Verificar se o administrador já existe
            admin_email = os.environ.get('ADMIN_EMAIL')
            admin_username = os.environ.get('ADMIN_USERNAME', 'admin')
            
            existing_admin = User.query.filter_by(email=admin_email).first()
            
            if existing_admin:
                print(f"👤 Administrador já existe: {existing_admin.email}")
                
                # Atualizar dados do administrador se necessário
                admin_password = os.environ.get('ADMIN_PASSWORD')
                admin_full_name = os.environ.get('ADMIN_FULL_NAME', 'Administrador')
                admin_role = os.environ.get('ADMIN_ROLE', 'administrator')
                
                if existing_admin.role != admin_role:
                    existing_admin.role = admin_role
                    print(f"   🔄 Role atualizado para: {admin_role}")
                
                if existing_admin.full_name != admin_full_name:
                    existing_admin.full_name = admin_full_name
                    print(f"   🔄 Nome atualizado para: {admin_full_name}")
                
                # Atualizar senha se fornecida
                if admin_password and not existing_admin.check_password(admin_password):
                    existing_admin.set_password(admin_password)
                    print("   🔄 Senha atualizada")
                
                # Garantir que o administrador está confirmado e ativo
                if not existing_admin.confirmed:
                    existing_admin.confirmed = True
                    print("   ✅ Email confirmado")
                
                if not existing_admin.is_active:
                    existing_admin.is_active = True
                    print("   ✅ Conta ativada")
                
                db.session.commit()
                print("✅ Administrador atualizado com sucesso!")
                
            else:
                print("👤 Criando usuário administrador...")
                
                # Obter configurações do .env
                admin_password = os.environ.get('ADMIN_PASSWORD', 'admin123')
                admin_full_name = os.environ.get('ADMIN_FULL_NAME', 'Administrador do Sistema')
                admin_role = os.environ.get('ADMIN_ROLE', 'administrator')
                
                # Criar administrador
                admin = User(
                    email=admin_email,
                    full_name=admin_full_name,
                    role=admin_role,
                    confirmed=True,  # Administrador já confirmado
                    is_active=True
                )
                admin.set_password(admin_password)
                
                db.session.add(admin)
                db.session.commit()
                
                print(f"✅ Administrador criado com sucesso!")
                print(f"   📧 Email: {admin.email}")
                print(f"   👤 Nome: {admin.full_name}")
                print(f"   🔑 Role: {admin.role}")
                print(f"   ✅ Status: Confirmado e Ativo")
            
            # Mostrar estatísticas do banco
            total_users = User.query.count()
            admin_users = User.query.filter_by(role='administrator').count()
            regular_users = User.query.filter_by(role='user').count()
            
            print("\n📊 Estatísticas do banco de dados:")
            print(f"   👥 Total de usuários: {total_users}")
            print(f"   👑 Administradores: {admin_users}")
            print(f"   👤 Usuários comuns: {regular_users}")
            
    except Exception as e:
        print(f"❌ Erro ao inicializar banco de dados: {str(e)}")
        import traceback
        traceback.print_exc()

def main():
    """Função principal"""
    print("🔐 Inicialização do Sistema de Login com Firewall")
    print("=" * 60)
    
    if len(sys.argv) > 1 and sys.argv[1] == '--help':
        print("""
Uso: python init_admin.py [opções]

Opções:
  --help          Mostra esta ajuda

Este script:
1. Cria todas as tabelas do banco de dados
2. Cria o usuário administrador baseado nas configurações do .env
3. Atualiza o administrador se já existir

Configurações necessárias no .env:
ADMIN_EMAIL=email@exemplo.com
ADMIN_USERNAME=admin
ADMIN_PASSWORD=senha123
ADMIN_FULL_NAME=Nome do Administrador
ADMIN_ROLE=administrator
        """)
        return
    
    init_database()
    
    print("\n" + "=" * 60)
    print("✅ Inicialização concluída!")
    print("🚀 O sistema está pronto para uso.")

if __name__ == '__main__':
    main() 