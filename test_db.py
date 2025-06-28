#!/usr/bin/env python3
"""
Script simples para testar criação do banco de dados
"""
import os
import sys

# Adicionar o diretório atual ao path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_db_creation():
    """Testa a criação do banco de dados"""
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
            print("🗄️ Testando criação do banco de dados...")
            
            # Criar todas as tabelas
            db.create_all()
            print("✅ Tabelas criadas com sucesso!")
            
            # Verificar se as colunas existem
            from sqlalchemy import inspect
            inspector = inspect(db.engine)
            
            # Verificar tabela users
            if 'users' in inspector.get_table_names():
                columns = [col['name'] for col in inspector.get_columns('users')]
                print(f"📋 Colunas da tabela users: {columns}")
                
                # Verificar se as novas colunas existem
                required_columns = ['full_name', 'role']
                missing_columns = [col for col in required_columns if col not in columns]
                
                if missing_columns:
                    print(f"❌ Colunas faltando: {missing_columns}")
                else:
                    print("✅ Todas as colunas necessárias existem!")
                    
                    # Testar criação de usuário
                    test_user = User(
                        email='teste@exemplo.com',
                        full_name='Usuário Teste',
                        role='user',
                        confirmed=True
                    )
                    test_user.set_password('teste123')
                    
                    db.session.add(test_user)
                    db.session.commit()
                    
                    print("✅ Usuário de teste criado com sucesso!")
                    
                    # Verificar se o usuário foi criado
                    user = User.query.filter_by(email='teste@exemplo.com').first()
                    if user:
                        print(f"✅ Usuário encontrado: {user.email} ({user.role})")
                    else:
                        print("❌ Usuário não encontrado")
                    
            else:
                print("❌ Tabela users não encontrada")
            
    except Exception as e:
        print(f"❌ Erro: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    test_db_creation() 