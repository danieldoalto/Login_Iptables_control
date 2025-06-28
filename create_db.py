#!/usr/bin/env python3
"""
Script simples para criar o banco de dados
"""
import os
import sys

# Adicionar o diretório atual ao path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def create_database():
    """Cria o banco de dados"""
    try:
        # Carregar configurações do .env
        from dotenv import load_dotenv
        load_dotenv()
        
        print("🔧 Configurações do banco:")
        print(f"   DATABASE_URL: {os.environ.get('DATABASE_URL', 'sqlite:///firewall_login.db')}")
        
        # Importar módulos necessários
        from app import create_app
        from app.models import db, User
        
        # Criar aplicação Flask
        app = create_app()
        
        with app.app_context():
            print("🗄️ Criando banco de dados...")
            
            # Criar todas as tabelas
            db.create_all()
            print("✅ Tabelas criadas com sucesso!")
            
            # Verificar se o banco foi criado
            db_path = app.config['SQLALCHEMY_DATABASE_URI'].replace('sqlite:///', '')
            if os.path.exists(db_path):
                print(f"✅ Banco criado em: {db_path}")
                print(f"📏 Tamanho: {os.path.getsize(db_path)} bytes")
            else:
                print(f"❌ Banco não encontrado em: {db_path}")
            
            # Criar administrador
            admin_email = os.environ.get('ADMIN_EMAIL')
            admin_password = os.environ.get('ADMIN_PASSWORD', 'admin123')
            admin_full_name = os.environ.get('ADMIN_FULL_NAME', 'Administrador do Sistema')
            admin_role = os.environ.get('ADMIN_ROLE', 'administrator')
            
            print(f"👤 Criando administrador: {admin_email}")
            
            # Verificar se já existe
            existing_admin = User.query.filter_by(email=admin_email).first()
            
            if existing_admin:
                print("   🔄 Administrador já existe, atualizando...")
                existing_admin.full_name = admin_full_name
                existing_admin.role = admin_role
                existing_admin.set_password(admin_password)
                existing_admin.confirmed = True
                existing_admin.is_active = True
            else:
                print("   ➕ Criando novo administrador...")
                admin = User(
                    email=admin_email,
                    full_name=admin_full_name,
                    role=admin_role,
                    confirmed=True,
                    is_active=True
                )
                admin.set_password(admin_password)
                db.session.add(admin)
            
            db.session.commit()
            print("✅ Administrador salvo com sucesso!")
            
            # Verificar usuários no banco
            users = User.query.all()
            print(f"\n📊 Usuários no banco: {len(users)}")
            for user in users:
                print(f"   - {user.email} ({user.role}) - Confirmado: {user.confirmed}")
            
    except Exception as e:
        print(f"❌ Erro: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    create_database() 