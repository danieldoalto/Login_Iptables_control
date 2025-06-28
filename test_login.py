#!/usr/bin/env python3
"""
Script para testar o login do administrador
"""
import os
import sys

# Adicionar o diretório atual ao path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_admin_login():
    """Testa o login do administrador"""
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
            print("🔐 Testando login do administrador...")
            
            # Obter credenciais do .env
            admin_email = os.environ.get('ADMIN_EMAIL')
            admin_password = os.environ.get('ADMIN_PASSWORD', 'admin123')
            
            print(f"📧 Email: {admin_email}")
            print(f"🔑 Senha: {admin_password}")
            
            # Buscar usuário no banco
            user = User.query.filter_by(email=admin_email).first()
            
            if user:
                print(f"✅ Usuário encontrado: {user.email}")
                print(f"   👤 Nome: {user.full_name}")
                print(f"   🔑 Role: {user.role}")
                print(f"   ✅ Confirmado: {user.confirmed}")
                print(f"   ✅ Ativo: {user.is_active}")
                print(f"   🔒 Bloqueado: {user.is_locked()}")
                
                # Testar senha
                if user.check_password(admin_password):
                    print("✅ Senha correta!")
                    
                    # Verificar se pode fazer login
                    if user.confirmed and user.is_active and not user.is_locked():
                        print("✅ Usuário pode fazer login!")
                    else:
                        print("❌ Usuário não pode fazer login:")
                        if not user.confirmed:
                            print("   - Email não confirmado")
                        if not user.is_active:
                            print("   - Conta inativa")
                        if user.is_locked():
                            print("   - Conta bloqueada")
                else:
                    print("❌ Senha incorreta!")
            else:
                print("❌ Usuário não encontrado!")
                
                # Listar todos os usuários
                users = User.query.all()
                print(f"\n📊 Usuários no banco ({len(users)}):")
                for u in users:
                    print(f"   - {u.email} ({u.role})")
            
    except Exception as e:
        print(f"❌ Erro: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    test_admin_login() 