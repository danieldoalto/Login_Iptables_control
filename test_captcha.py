#!/usr/bin/env python3
"""
Script para testar o sistema de captcha
"""
import os
import sys

# Adicionar o diretório atual ao path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_captcha():
    """Testa o sistema de captcha"""
    try:
        # Carregar configurações do .env
        from dotenv import load_dotenv
        load_dotenv()
        
        # Importar módulos necessários
        from app import create_app
        from app.captcha import captcha_manager, generate_captcha, validate_captcha
        
        # Criar aplicação Flask
        app = create_app()
        
        with app.app_context():
            print("🧮 Testando sistema de captcha...")
            
            # Verificar configurações
            print(f"📋 Configurações:")
            print(f"   CAPTCHA_ENABLED: {app.config.get('CAPTCHA_ENABLED')}")
            print(f"   CAPTCHA_DIFFICULTY: {app.config.get('CAPTCHA_DIFFICULTY')}")
            
            # Testar geração de captcha
            print(f"\n🎯 Testando geração de captcha...")
            question, answer = generate_captcha()
            
            if question and answer:
                print(f"   Pergunta: {question}")
                print(f"   Resposta: {answer}")
                
                # Testar validação
                print(f"\n✅ Testando validação...")
                
                # Teste com resposta correta
                is_valid = validate_captcha(answer, answer)
                print(f"   Resposta correta ({answer}): {'✅ Válida' if is_valid else '❌ Inválida'}")
                
                # Teste com resposta incorreta
                is_valid = validate_captcha(answer + 1, answer)
                print(f"   Resposta incorreta ({answer + 1}): {'✅ Válida' if is_valid else '❌ Inválida'}")
                
                # Teste com string
                is_valid = validate_captcha(str(answer), answer)
                print(f"   Resposta como string ('{answer}'): {'✅ Válida' if is_valid else '❌ Inválida'}")
                
            else:
                print("   ❌ Captcha desabilitado ou erro na geração")
            
            # Testar diferentes dificuldades
            print(f"\n🎲 Testando diferentes dificuldades...")
            
            difficulties = ['easy', 'medium', 'hard']
            for difficulty in difficulties:
                app.config['CAPTCHA_DIFFICULTY'] = difficulty
                captcha_manager.configure(app)
                
                question, answer = generate_captcha()
                if question and answer:
                    print(f"   {difficulty.upper()}: {question} = {answer}")
                else:
                    print(f"   {difficulty.upper()}: Captcha desabilitado")
            
    except Exception as e:
        print(f"❌ Erro: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    test_captcha() 